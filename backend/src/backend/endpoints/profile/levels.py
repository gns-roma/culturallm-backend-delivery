


def fibonacci_threshold(level: int) -> int:
    """
    Soglia di punti per un dato livello (Fibonacci * 50).
    Livello 1 e 2 = 50 punti, poi segue Fibonacci.
    """
    if level <= 1:
        return 50
    a, b = 1, 1
    for _ in range(2, level):
        a, b = b, a + b
    return b * 50




def get_level_and_threshold(score: int) -> dict:
    """
    Dato uno score, ritorna:
      - livello attuale
      - soglia livello successivo (per salire)
    """
    level = 1
    # Trova livello: score >= soglia per il livello successivo
    while score >= fibonacci_threshold(level + 1):
        level += 1
    
    next_threshold = fibonacci_threshold(level + 1)
    
    return {
        "level": level,
        "next_threshold": next_threshold
    }

# Esempio di uso:
# print(get_level_and_threshold(450))
# Output: {'level': 4, 'current_threshold': 300, 'next_threshold': 500}
