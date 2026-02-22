import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database_layer.db import get_db
from database_layer import crud
from backend.matcher import match_schemes

router = APIRouter()


class ProfileInput(BaseModel):
    name:       str = ""
    occupation: str = ""
    caste:      str = ""
    income:     str = "500000"


def parse_json_field(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return [value] if value else []
    return []


def scheme_to_result(s, occupation="General", caste="All"):
    steps = parse_json_field(s.application_process)
    documents = parse_json_field(s.documents_required)

    flat_steps = []
    for step in steps:
        if isinstance(step, str):
            flat_steps.append(step)
        elif isinstance(step, dict):
            text = step.get("details") or step.get("step") or step.get("description") or str(step)
            flat_steps.append(text)

    flat_docs = []
    for doc in documents:
        if isinstance(doc, str):
            flat_docs.append(doc)
        elif isinstance(doc, dict):
            flat_docs.append(str(next(iter(doc.values()), "")))

    return {
        "id":        s.id,
        "title":     s.scheme_name,
        "category":  occupation,
        "caste":     caste,
        "summary":   s.description or "",
        "source":    s.source_url,
        "steps":     flat_steps,
        "documents": flat_docs,
    }


@router.get("")
def list_schemes(db: Session = Depends(get_db)):
    schemes = crud.get_all_schemes(db)
    return {"total": len(schemes), "schemes": [s.to_dict() for s in schemes]}


@router.post("/match")
def match_profile(profile: ProfileInput, db: Session = Depends(get_db)):
    all_schemes = crud.get_all_schemes(db)

    print(f"\nDEBUG: {len(all_schemes)} schemes in DB")
    print(f"DEBUG: occupation={profile.occupation} caste={profile.caste} income={profile.income}")

    matched = match_schemes(all_schemes, profile.dict())
    print(f"DEBUG: {len(matched)} matched\n")

    results = [scheme_to_result(s, profile.occupation, profile.caste) for s in matched]
    return {"schemes": results}
