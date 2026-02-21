import json
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database_layer.models import Scheme

def insert_many_schemes(db: Session, schemes: list) -> dict:
    counts = {"inserted": 0, "updated": 0, "failed": 0}
    for data in schemes:
        try:
            existing = db.query(Scheme).filter(
                Scheme.source_url == data.get("source_url")
            ).first()
            if existing:
                existing.scheme_name         = data.get("scheme_name", "")
                existing.description         = data.get("description", "")
                existing.benefits            = json.dumps(data.get("benefits", []))
                existing.eligibility         = json.dumps(data.get("eligibility", []))
                existing.documents_required  = json.dumps(data.get("documents_required", []))
                existing.application_process = json.dumps(data.get("application_process", []))
                counts["updated"] += 1
            else:
                s = Scheme(
                    scheme_name         = data.get("scheme_name", ""),
                    description         = data.get("description", ""),
                    source_url          = data.get("source_url", ""),
                    benefits            = json.dumps(data.get("benefits", [])),
                    eligibility         = json.dumps(data.get("eligibility", [])),
                    documents_required  = json.dumps(data.get("documents_required", [])),
                    application_process = json.dumps(data.get("application_process", [])),
                    scrape_status       = "failed" if data.get("error") else "success",
                )
                db.add(s)
                counts["inserted"] += 1
        except Exception as e:
            print(f"Failed: {e}")
            db.rollback()
            counts["failed"] += 1
    return counts

def get_all_schemes(db: Session):
    return db.query(Scheme).filter(Scheme.is_active == True).all()

def get_scheme_by_id(db: Session, scheme_id: int):
    return db.query(Scheme).filter(Scheme.id == scheme_id).first()

def search_schemes(db: Session, keyword: str):
    kw = f"%{keyword.lower()}%"
    return db.query(Scheme).filter(
        or_(Scheme.scheme_name.ilike(kw), Scheme.description.ilike(kw))
    ).all()
