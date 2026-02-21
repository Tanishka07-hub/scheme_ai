"""
backend/matcher.py
Matches user profile against all schemes in DB using eligibility keywords.
Simple rule-based for now — swap for vector similarity later.
"""

CASTE_KEYWORDS = {
    "SC": ["sc", "scheduled caste", "dalit"],
    "ST": ["st", "scheduled tribe", "tribal", "adivasi"],
    "OBC": ["obc", "other backward"],
    "General": ["general", "all categories", "all citizens"],
}

OCCUPATION_KEYWORDS = {
    "Student":      ["student", "scholar", "education", "school", "college", "university"],
    "Farmer":       ["farmer", "agriculture", "kisan", "crop", "farm"],
    "Worker":       ["worker", "labour", "artisan", "craftsman", "weaver"],
    "Professional": ["professional", "entrepreneur", "business", "startup"],
    "Unemployed":   ["unemployed", "job seeker", "self-employment"],
}

def match_schemes(schemes: list, profile: dict) -> list:
    """
    Returns schemes that are likely relevant to the user's profile.
    Scores each scheme and returns top matches.
    """
    user_caste = profile.get("caste", "").strip()
    user_occ   = profile.get("occupation", "").strip()
    try:
        user_income = int(str(profile.get("income", "500000")).replace(",", ""))
    except ValueError:
        user_income = 500000

    scored = []
    for scheme in schemes:
        score = 0
        eligibility_text = " ".join(scheme.eligibility or []).lower()
        full_text = f"{scheme.scheme_name} {scheme.description} {eligibility_text}".lower()

        # Caste match
        for kw in CASTE_KEYWORDS.get(user_caste, []):
            if kw in full_text:
                score += 3
                break
        if "all" in eligibility_text or "any citizen" in eligibility_text:
            score += 1

        # Occupation match
        for kw in OCCUPATION_KEYWORDS.get(user_occ, []):
            if kw in full_text:
                score += 3
                break

        # Income match — rough heuristic
        if user_income < 250000 and any(w in full_text for w in ["bpl", "below poverty", "low income", "poor"]):
            score += 2

        if score > 0:
            scored.append((score, scheme))

    # Sort by score descending, return top 10
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:10]]
