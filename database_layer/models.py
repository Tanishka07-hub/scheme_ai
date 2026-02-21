import json
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Scheme(Base):
    __tablename__ = "schemes"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    scheme_name         = Column(String(300), nullable=False, index=True)
    description         = Column(Text, nullable=True)
    source_url          = Column(String(500), unique=True, nullable=False)
    benefits            = Column(Text, default="[]")
    eligibility         = Column(Text, default="[]")
    documents_required  = Column(Text, default="[]")
    application_process = Column(Text, default="[]")
    is_active           = Column(Boolean, default=True)
    quality_score       = Column(Float, nullable=True)
    scrape_status       = Column(String(50), default="success")
    created_at          = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id":                   self.id,
            "scheme_name":          self.scheme_name,
            "description":          self.description,
            "benefits":             json.loads(self.benefits or "[]"),
            "eligibility":          json.loads(self.eligibility or "[]"),
            "documents_required":   json.loads(self.documents_required or "[]"),
            "application_process":  json.loads(self.application_process or "[]"),
            "source_url":           self.source_url,
            "quality_score":        self.quality_score,
            "is_active":            self.is_active,
        }
