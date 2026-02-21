"""
backend/routes/auth.py
POST /api/auth/register
POST /api/auth/login
Simple session-less auth — extend with JWT if needed later.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# In-memory store for hackathon — swap with a real Users DB table later
_users: dict[str, dict] = {}

class AuthInput(BaseModel):
    name: str = ""
    email: str
    password: str

@router.post("/register")
def register(data: AuthInput):
    if data.email in _users:
        raise HTTPException(status_code=400, detail="Email already registered")
    _users[data.email] = {"name": data.name, "email": data.email, "password": data.password}
    return {"name": data.name, "email": data.email, "message": "Registered successfully"}

@router.post("/login")
def login(data: AuthInput):
    user = _users.get(data.email)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"name": user["name"], "email": user["email"], "message": "Login successful"}
