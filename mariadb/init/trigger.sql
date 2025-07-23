-- 1. Inizializza leaderboard dopo inserimento utente
DELIMITER //
CREATE OR REPLACE TRIGGER trg_leaderboard_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
  INSERT IGNORE INTO leaderboard (user_id, score, num_ratings, num_questions, num_answers)
  VALUES (NEW.id, 0, 0, 0, 0);
END;
//
DELIMITER ;

-- 2. Log su inserimento report
DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_reports
AFTER INSERT ON reports
FOR EACH ROW
BEGIN
  IF NEW.question_id IS NOT NULL THEN
    INSERT INTO logs (user_id, action_id, question_id,score, action_type, timestamp)
    VALUES (NEW.user_id, NEW.id, NEW.question_id,0, 'report', NOW());
  ELSEIF NEW.answer_id IS NOT NULL THEN
    INSERT INTO logs (user_id, action_id, answer_id, score, action_type, timestamp)
    VALUES (NEW.user_id, NEW.id, NEW.answer_id, 0, 'report', NOW());
  END IF;
END;
//
DELIMITER ;

-- 3. Log dopo inserimento di domanda
DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_question_insert
AFTER INSERT ON questions
FOR EACH ROW
BEGIN
  IF NEW.user_id IS NOT NULL THEN
    INSERT INTO logs (user_id, action_id, score, action_type, timestamp)
    VALUES (NEW.user_id, NEW.id, 0, 'question', NOW());
  ELSEIF NEW.llm_id IS NOT NULL THEN
    INSERT INTO logs (llm_id, action_id, score, action_type, timestamp)
    VALUES (NEW.llm_id, NEW.id, 0, 'question', NOW());
  END IF;
END;
//
DELIMITER ;

-- 4. Log dopo inserimento valutazione domanda + update score log originale
DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_questions_evaluation
AFTER INSERT ON questions_evaluation
FOR EACH ROW
BEGIN
  INSERT INTO logs (question_id, llm_id, action_id, score, action_type, timestamp)
  VALUES (NEW.question_id, NEW.llm_id, NEW.id, NEW.cultural_specificity, 'question_evaluation', NOW());

  UPDATE logs
  SET score = score + NEW.cultural_specificity
  WHERE action_type = 'question'
    AND action_id = NEW.question_id;
END;
//
DELIMITER ;

-- 5. Log dopo inserimento risposta
DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_answer_insert
AFTER INSERT ON answers
FOR EACH ROW
BEGIN
  IF NEW.user_id IS NOT NULL THEN
    INSERT INTO logs (user_id, action_id, score, action_type, timestamp)
    VALUES (NEW.user_id, NEW.id, 0, 'answer', NOW());
  ELSEIF NEW.llm_id IS NOT NULL THEN
    INSERT INTO logs (llm_id, action_id, score, action_type, timestamp)
    VALUES (NEW.llm_id, NEW.id, 0, 'answer', NOW());
  END IF;
END;
//
DELIMITER ;

-- 6. Log dopo valutazione risposta + update log originale
DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_answer_evaluation
AFTER INSERT ON answers_evaluation
FOR EACH ROW
BEGIN
  INSERT INTO logs (answer_id, llm_id, action_id, score, action_type, timestamp)
  VALUES (NEW.answer_id, NEW.llm_id, NEW.id, NEW.validity, 'answer_evaluation', NOW());

  UPDATE logs
  SET score = score + NEW.validity
  WHERE action_type = 'answer'
    AND action_id = NEW.answer_id;
END;
//
DELIMITER ;

-- 7. Log rating e aggiorna punteggio autore risposta
DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_ratings
AFTER INSERT ON ratings
FOR EACH ROW
BEGIN
  DECLARE answer_author INT DEFAULT NULL;
  DECLARE rater_score   INT DEFAULT 2;
  DECLARE correct_flag  BOOLEAN;

  -- Trova autore risposta
  SELECT user_id INTO answer_author
  FROM answers
  WHERE id = NEW.answer_id
  LIMIT 1;

  -- Controllo correttezza flag IA
  SET correct_flag = (
    (NEW.flag_ia = TRUE AND EXISTS (
      SELECT 1 FROM answers WHERE id = NEW.answer_id AND type = 'llm'
    ))
    OR
    (NEW.flag_ia = FALSE AND EXISTS (
      SELECT 1 FROM answers WHERE id = NEW.answer_id AND type = 'human'
    ))
  );

  IF correct_flag THEN
    SET rater_score = rater_score + 1;
  END IF;

  -- Log rating dato
  INSERT INTO logs (user_id, action_id, score, action_type, timestamp)
  VALUES (NEW.user_id, NEW.id, rater_score, 'rating', NOW());

  -- Aggiorna punteggio dell'autore risposta
  IF answer_author IS NOT NULL THEN
    UPDATE logs
    SET score = score + NEW.rating
    WHERE action_type = 'answer'
      AND action_id = NEW.answer_id
      AND user_id = answer_author;
  END IF;
END;
//
DELIMITER ;

-- 8. Aggiorna leaderboard dopo un nuovo log
DELIMITER //
CREATE OR REPLACE TRIGGER trg_leaderboard_update
AFTER INSERT ON logs
FOR EACH ROW
BEGIN
  IF NEW.user_id IS NOT NULL THEN
    UPDATE leaderboard
    SET score = score + NEW.score,
        num_ratings = num_ratings + IF(NEW.action_type = 'rating', 1, 0),
        num_questions = num_questions + IF(NEW.action_type = 'question', 1, 0),
        num_answers = num_answers + IF(NEW.action_type = 'answer', 1, 0)
    WHERE user_id = NEW.user_id;
  END IF;
END;
//
DELIMITER ;

-- 9. Aggiorna score leaderboard se cambia score nel log
DELIMITER //
CREATE OR REPLACE TRIGGER trg_leaderboard_update_score
AFTER UPDATE ON logs
FOR EACH ROW
BEGIN
  IF NEW.score <> OLD.score AND NEW.user_id IS NOT NULL THEN
    UPDATE leaderboard
    SET score = score + (NEW.score - OLD.score)
    WHERE user_id = NEW.user_id;
  END IF;
END;
//
DELIMITER ;
