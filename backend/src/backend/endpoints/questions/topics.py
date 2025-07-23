from fastapi import APIRouter


router = APIRouter(tags=["questions"])


@router.get("/topics/random")
def get_random_topic():
    """
    Ritorna un argomento casuale per le domande.
    """
    import random
    topics = [
        "🎨 Arte",
        "📚 Letteratura",
        "🎬 Cinema",
        "🎵 Musica",
        "🍝 Cibo",
        "🏛️ Storia",
        "🗣️ Lingua",
        "⚽ Sport",
        "🌍 Geografia",
        "🎭 Folclore",
        "🔬 Scienza"
    ]
    return {"topic": random.choice(topics)}
