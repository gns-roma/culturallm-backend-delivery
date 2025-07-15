from typing import Annotated, Literal, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
import mariadb

from endpoints.questions.models import Question, QuestionValues
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user
from endpoints.answers.models import Answer
from endpoints.validate.models import RatingRequest
from endpoints.questions.questions_nlp import evaluate_coherence_qt, evaluate_cultural_background, answer_question


router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/")
def submit_question(
    data: QuestionValues,
    background_tasks: BackgroundTasks,
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    type: Literal["human", "llm"] = "human"
) -> Response:
    """
    Submit a question to the system.
    """
    if type == "human" and current_user is None:
        return Response(status_code=401, content="Unauthorized: User must be logged in to submit a human question.")
    
    username = current_user if type == "human" else None
    # TODO: Si potrebbe aggiungere un controllo per evitare domande duplicate, anche se poco probabile
    # che due utenti scrivano la stessa domanda

    query_user = """
        SELECT id
        FROM users 
        WHERE username = ?
    """
    params_user = (username,) if username else (None,)
    try:
        user_check = execute_query(db, query_user, params_user, fetchone=True, dict=True)
    except Exception as e:
        print(f"Errore durante l'inserimento risposta: {e}")
        raise HTTPException(status_code=500, detail="Errore interno durante l'inserimento della risposta")

    user_id = user_check['id'] if user_check else None
    insert_query = """
        INSERT INTO questions (question, topic, type, user_id) 
        VALUES (?, ?, ?, ?)
    """
    # TODO: Inserire subito risposta della IA alla domanda
    params = (data.question, data.topic, type, user_id)

    #Oppure potremmo inserirla, farla validare e in modo asincrono aggiornare la riga
    try:
        question_id = execute_query(db, insert_query, params, fetch=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Errore inserimento domanda")
    
    if question_id is None:
        raise HTTPException(status_code=500, detail="Errore interno: question_id non valido")
    
    
    background_tasks.add_task(evaluate_cultural_background, data.question, db, question_id)
    background_tasks.add_task(evaluate_coherence_qt, question_id, data.question, data.topic, db)

    query_evaluate = """
        SELECT cultural_specificity, coherence_qt
        FROM questions
        WHERE id = ?
    """
    params_evaluate = (question_id,)
    try:
        row = execute_query(db, query_evaluate, params_evaluate, fetchone=True, dict=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Errore durante la valutazione della domanda")
    
    if row is None:
        raise HTTPException(status_code=404, detail="Domanda non trovata dopo l'inserimento")
    
    if row['cultural_specificity'] >= 4 and row['coherence_qt']:
        # Se la domanda ha una specificità culturale alta e una coerenza con il topic, rispondi subito
        background_tasks.add_task(answer_question, question_id, data.question, 1, db)

    return Response(status_code=201)


@router.get("/random/to_answer")
def get_random_question_to_answer(
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    type: Literal["human", "llm"] = "human"
) -> Question:
    """
    Retrieve a random question.
    """    
    if current_user is None and type == "human":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: User must be logged in to answer a question.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if type == "human":
        username = current_user
    else:
        username = ""
        
    #Ritorna una domanda casuale che non è stata ne scritta ne a cui l'utente ha già risposto

    select_query = """
    SELECT  q.id, q.type, u.username, q.question, q.topic, q.cultural_specificity, q.cultural_specificity_notes
    FROM    questions q LEFT JOIN users u ON u.id = q.user_id
    WHERE   ( ? IS NULL OR q.user_id IS NULL OR q.user_id <> (SELECT id FROM users WHERE username = ?) )
    AND   q.id NOT IN (                                     
        SELECT a.question_id
        FROM   answers a
        WHERE  a.user_id = (SELECT id FROM users WHERE username = ?))
    ORDER BY RAND()
    LIMIT 1
    """
    params = (username, username, username)
    row = execute_query(db, select_query, params, fetchone=True, dict=True)
    if row is None:
        raise HTTPException(status_code=404, detail="Nessuna domanda disponibile.")
    return Question(**row)

@router.get("/random")
def get_random_question(
    db: Annotated[mariadb.Connection, Depends(db_connection)]
) -> Question:
    """
    Retrieve a random question.
    """    
    #Ritorna una domanda casuale con almeno una risposta
    select_query = """
    SELECT  q.id,q.type,u.username,q.question,q.topic,q.cultural_specificity,q.cultural_specificity_notes
    FROM    questions q JOIN answers a ON a.question_id = q.id LEFT JOIN users u ON u.id = q.user_id
    ORDER BY RAND()
    LIMIT 1
    """
    row = execute_query(db, select_query, fetchone=True, dict=True)
    if row is None:
        raise HTTPException(status_code=404, detail="Nessuna domanda disponibile.")
    return Question(**row)

@router.get("/qa_to_validate")
def get_single_answer_to_question(
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    questionType: Literal["human", "llm"] = "human",
) -> RatingRequest:
    """
    Restituisce UNA tupla domanda, risposta, topic che l'utente
    corrente non ha creato né già valutato.
    Preferisce la risposta con il minor numero di rating.
    """

    if questionType == "human" and current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: User must be logged in for this operation.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = current_user

    select_query = """
    SELECT a.id AS answer_id, a.question_id AS question_id, a.answer, q.question, q.topic
    FROM answers AS a INNER JOIN questions AS q ON a.question_id = q.id LEFT JOIN ratings AS r ON a.id = r.answer_id
    WHERE (a.user_id IS NULL OR a.user_id != (SELECT id FROM users WHERE username = ?))
    AND NOT EXISTS (
        SELECT 1
        FROM ratings AS r_check
        WHERE r_check.answer_id = a.id AND r_check.user_id = (SELECT id FROM users WHERE username = ?))
    GROUP BY a.id, a.question_id, q.question, a.answer, q.topic
    ORDER BY COUNT(r.id) ASC, RAND()
    LIMIT 1;"""
    params = (username, username)

    try:
        row = execute_query(db, select_query, params, fetch=False, fetchone=True, dict=True)
    except mariadb.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching question and answer.")

    if not row:
        raise HTTPException(status_code=404, detail="No suitable answer found for the given criteria.")

    return RatingRequest(**row)


@router.get("/{question_id}/answers")
def get_answers_to_question(question_id: int, 
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    type: Literal["human", "llm"] = "human")-> List[Answer]:

    if type == "human" and current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: User must be logged in to answer a question.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = current_user if type == "human" else None

    """
    Retrieve answers to a question by its ID
    """
    """
    Noi qua prendiamo una risposta casuale a una domanda, affinche il current_user la possa validare, 
    quindi dobbiamo escludere le risposte che l'utente ha scritto oppure che ha già valutato 
    """
    select_query = """
    SELECT  a.id, a.type, u.username, a.question_id, a.answer, COUNT(r_all.id) AS rating_count
    FROM    answers a LEFT JOIN users   u      ON u.id  = a.user_id            
    LEFT JOIN ratings r_all  ON r_all.answer_id = a.id      
    WHERE   a.question_id = ? 
    AND   ( ? IS NULL OR a.user_id IS NULL OR a.user_id <> (SELECT id FROM users WHERE username = ?) )
    AND   NOT EXISTS (                                     
        SELECT 1
        FROM   ratings r_me
        WHERE  r_me.answer_id = a.id
          AND  r_me.user_id   = (SELECT id FROM users WHERE username = ?)
    )
    GROUP BY a.id, a.type, u.username, a.question_id, a.answer
    ORDER BY rating_count ASC, RAND()
    """

    params = (question_id, username, username, username)
    rows = execute_query(db, select_query, params, dict=True)
    if not rows:
        raise HTTPException(status_code=404, detail="No answers found for the question")
    #Noi qua prendiamo tutte le risposte a una certa domanda,
    # affinche l'utente le possa poi validare, quindi dobbiamo 
    # filtrare le risposte che l'utente ha scritto lui o che ha già valutato
    #Il modello LLM invece dovrebbe valutare subito una risposta, appena un utente fa il submit
    return [Answer(**row) for row in rows]


@router.get("/{question_id}")
def get_question(question_id: int, db: Annotated[mariadb.Connection, Depends(db_connection)])->Question:
    """
    Retrieve a question by its ID.
    """
    query = """
    SELECT  q.id, q.type, u.username, q.question, q.topic, q.cultural_specificity, q.cultural_specificity_notes
    FROM    questions q LEFT JOIN users u ON u.id = q.user_id
    WHERE   q.id = ?
    """
    params = (question_id,)
    row = execute_query(db, query, params,fetchone=True, dict=True)
    if not row:
        raise HTTPException(status_code=404, detail="Nessuna domanda trovata")
    return Question(**row)