from fastapi import APIRouter


router = APIRouter(tags=["questions"])


@router.get("/topics")
def get_topics():
    """
    Retrieve a list of available topics.
    """
    # TODO: Rimpiazzare con richiesta di un topic all'IA
    topics = [
        "cibo",
        "sport",
        "cinema",
        "musica",
    ]
    return {"topics": topics}


@router.get("/topics/random")
def get_random_topic():
    """
    Retrieve a random topic.
    """
    import random
    topics = get_topics()
    return {"topic": random.choice(topics["topics"])}