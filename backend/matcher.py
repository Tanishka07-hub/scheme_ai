# 
"""
backend/matcher.py
Matches user profile against schemes using targeted scoring.
Tuned to the actual 9 schemes in gov_schemes_data.json.
"""
import json
import re


def get_text(scheme) -> str:
    parts = [scheme.scheme_name or "", scheme.description or ""]
    for field in [scheme.eligibility, scheme.benefits]:
        try:
            val = field
            if isinstance(val, str):
                val = json.loads(val)
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict):
                        parts.extend(str(v) for v in item.values())
            elif isinstance(val, dict):
                parts.extend(str(v) for v in val.values())
        except Exception:
            pass
    return " ".join(parts).lower()


def extract_income_limit(text: str):
    lakh = re.search(r'(\d+\.?\d*)\s*lakh', text)
    if lakh:
        return int(float(lakh.group(1)) * 100000)
    rupee = re.search(r'₹\s*([\d,]+)', text)
    if rupee:
        try:
            return int(rupee.group(1).replace(",", ""))
        except Exception:
            pass
    return None


def match_schemes(schemes: list, profile: dict) -> list:
    user_caste = profile.get("caste", "").strip()
    user_occ = profile.get("occupation", "").strip()
    try:
        user_income = int(str(profile.get("income", "500000")).replace(",", ""))
    except ValueError:
        user_income = 500000

    is_scst = user_caste in ["SC", "ST"]
    is_obc = user_caste == "OBC"
    is_student = user_occ == "Student"
    is_farmer = user_occ == "Farmer"
    is_worker = user_occ == "Worker"
    is_unemployed = user_occ == "Unemployed"
    is_professional = user_occ == "Professional"

    scored = []

    for scheme in schemes:
        score = 0
        name = (scheme.scheme_name or "").lower()
        url = scheme.source_url or ""

        if "marriage" in name or "famdpwog" in url:
            if user_income <= 100000:
                score += 6

        elif "vidyalaxmi" in name or "pmvs" in url:
            if is_student:
                score += 6
                if user_income <= 800000:
                    score += 3

        elif "daksh" in name or "pm-daksh" in url:
            if is_scst or is_obc:
                score += 5
            if is_worker or is_unemployed:  # ← farmer gets no bonus
                score += 3
            if is_farmer:                   # ← farmers shouldn't see this
                score = 0
            if user_income <= 300000:
                score += 2
        elif "internship" in name or "ip-mea" in url:
            if is_student:
                score += 5
                if is_scst or is_obc:
                    score += 3

        elif "kisan vikas" in name or "kvps" in url:
            if is_farmer:
                score += 6
            elif is_professional and user_income >= 200000:
                score += 3

        elif "savitribai" in name or "sjpfsgc" in url:
            if is_student:
                score += 6
                if is_scst or is_obc:
                    score += 3

        elif "ajay" in name or "pmajay" in url:
            if is_scst:
                score += 7
                if is_farmer or is_worker:
                    score += 2

        elif "pm vikas" in name or "pm-vikas" in url:
            if is_obc:
                score += 6
                if is_worker or is_unemployed:
                    score += 3

        elif "post graduate" in name or "pgspcscstc" in url:
            if is_scst and is_student:
                score += 10

        if score > 0:
            scored.append((score, scheme))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:10]]