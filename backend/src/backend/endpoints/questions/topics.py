from fastapi import APIRouter


router = APIRouter(tags=["questions"])


@router.get("/topics")
def get_topics():
    """
    Retrieve a list of available topics.
    """
    # TODO: Rimpiazzare con richiesta di un topic all'IA
    topics = {
        "arte": "Arte e Architettura",
        "letteratura": "Letteratura",
        "cinema": "Cinema e Televisione",
        "musica": "Musica",
        "cibo": "Cibo e Tradizioni Gastronomiche",
        "storia": "Storia e Personaggi Storici",
        "lingua": "Lingua e Dialetti",
        "sport": "Sport e Cultura Popolare",
        "geografia": "Geografia e Regioni",
        "folclore": "Folclore, Feste e Religione"
    }

    return topics


@router.get("/topics/random")
def get_random_topic():
    """
    Retrieve a random topic.
    """
    import random
    topics = get_topics()
    random_topic = random.choice(list(topics.keys()))
    return {"topic": random_topic, "name": topics[random_topic]}