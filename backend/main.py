import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
backend/main.py
FastAPI entry point — run with: uvicorn backend.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database_layer.db import init_db
from backend.routes import schemes, auth, chat

app = FastAPI(title="Scheme Sathi API", version="1.0.0")

# Allow React dev server (port 5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,    prefix="/api/auth",    tags=["Auth"])
app.include_router(schemes.router, prefix="/api/schemes", tags=["Schemes"])
app.include_router(chat.router,    prefix="/api/chat",    tags=["Chat"])

@app.on_event("startup")
def startup():
    init_db()
    print("✅ DB initialized")

@app.get("/")
def root():
    return {"status": "Scheme Sathi API running"}
