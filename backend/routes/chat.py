import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
backend/routes/chat.py
POST /api/chat/message
Connects ChatInterface in your React frontend to your local Ollama LLM.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter()

ollama = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

PROFILE_QUESTIONS = [
    ("name",       "Welcome to Scheme Sathi! What is your full name?"),
    ("occupation", "Nice to meet you, {name}! What is your current occupation? (e.g. Student, Farmer, Worker)"),
    ("caste",      "Got it. Which category do you belong to? (General / OBC / SC / ST)"),
    ("income",     "Almost done! What is your approximate annual household income in rupees?"),
]

class ChatInput(BaseModel):
    message: str
    current_step: int = 0
    profile: dict = {}

@router.post("/message")
def chat(data: ChatInput):
    step = data.current_step
    profile = data.profile.copy()

    # Store the user's answer for the current step
    if step < len(PROFILE_QUESTIONS):
        field = PROFILE_QUESTIONS[step][0]
        profile[field] = data.message

    next_step = step + 1

    # If profile is complete, use LLM to generate a summary response
    if next_step >= len(PROFILE_QUESTIONS):
        prompt = f"""
The user has completed their profile:
Name: {profile.get('name')}
Occupation: {profile.get('occupation')}
Category: {profile.get('caste')}
Income: {profile.get('income')}

In 2-3 friendly sentences, confirm their profile and tell them you're finding matching government schemes.
"""
        resp = ollama.chat.completions.create(
            model="deepseek-r1:7b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200, temperature=0.7
        )
        reply = resp.choices[0].message.content.strip()
        return {
            "response":  reply,
            "next_step": next_step,
            "profile":   profile,
            "schemes":   None   # frontend triggers /api/schemes/match separately
        }

    # Otherwise ask the next profile question
    _, question_template = PROFILE_QUESTIONS[next_step]
    question = question_template.format(**profile)

    return {
        "response":  question,
        "next_step": next_step,
        "profile":   profile,
        "schemes":   None
    }
