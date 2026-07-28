from __future__ import annotations


def calculate_heuristic_score(
    popularity: int,
    age_hours: float,
    title: str,
) -> tuple[int, float]:
    """Calculates simple scoring heuristics based on popularity metrics, age, and keywords.
    Returns:
        score: int (0 to 100)
        confidence: float (0.0 to 1.0)
    """
    # 1. Base Score calculation
    # Clamp base score from popularity (e.g. stars or points)
    base_score = min(int(popularity / 5.0), 70)
    
    # 2. Time decay factor
    # Newer opportunities get a slight boost or lose less score
    decay = max(0, 1.0 - (age_hours / 72.0)) # linear decay over 3 days
    score = int(base_score * decay)
    
    # 3. AI Relevance boost
    ai_keywords = ["ai", "llm", "gpt", "agent", "model", "openai", "claude", "gemini", "rag"]
    title_lower = title.lower()
    has_keyword = any(kw in title_lower for kw in ai_keywords)
    
    if has_keyword:
        score = min(score + 20, 100)
        confidence = 0.90
    else:
        confidence = 0.75
        
    # Ensure minimum score of 10 if popular
    if base_score > 0:
        score = max(score, 10)
        
    return score, confidence
