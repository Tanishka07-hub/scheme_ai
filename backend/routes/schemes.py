import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
backend/routes/schemes.py
GET  /api/schemes         → list all schemes from DB
POST /api/schemes/match   → match schemes to user profile
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database_layer.db import get_db
from database_layer import crud
from backend.matcher import match_schemes

router = APIRouter()

class ProfileInput(BaseModel):
    name: str = ""
    occupation: str = ""
    caste: str = ""
    income: str = "500000"

@router.get("")
def list_schemes(db: Session = Depends(get_db)):
    schemes = crud.get_all_schemes(db)
    return {"total": len(schemes), "schemes": [s.to_dict() for s in schemes]}

@router.post("/match")
def match_profile(profile: ProfileInput, db: Session = Depends(get_db)):
    all_schemes = crud.get_all_schemes(db)
    matched = match_schemes(all_schemes, profile.dict())
    # Shape output to match what your React ResultsList component expects:
    # { id, title, category, caste, summary, source, steps }
    results = []
    for s in matched:
        results.append({
            "id":       s.id,
            "title":    s.scheme_name,
            "category": profile.occupation or "General",
            "caste":    profile.caste or "All",
            "summary":  s.description or "",
            "source":   s.source_url,
            "steps":    s.application_process or [],
        })
    return {"schemes": results}
