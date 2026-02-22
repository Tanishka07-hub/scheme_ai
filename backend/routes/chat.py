import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import httpx

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
    schemes: list = []
    history: list = []

def clean_reply(content: str) -> str:
    """Strip DeepSeek <think>...</think> blocks and any meta-commentary."""
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    # Remove lines that look like prompt echoing e.g. "--- This response..."
    lines = [l for l in content.splitlines() if not l.strip().startswith("---")]
    return "\n".join(lines).strip()

def format_income(income_str):
    try:
        amount = int(income_str)
        s = str(amount)
        if len(s) > 3:
            last3 = s[-3:]
            rest = s[:-3]
            groups = []
            while len(rest) > 2:
                groups.append(rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.append(rest)
            groups.reverse()
            return "₹" + ",".join(groups) + "," + last3
        return "₹" + s
    except:
        return "₹" + str(income_str)

def fetch_matched_schemes(profile: dict) -> list:
    try:
        payload = {
            "name":       profile.get("name", ""),
            "occupation": profile.get("occupation", ""),
            "caste":      profile.get("caste", ""),
            "income":     str(profile.get("income", "500000")),
        }
        print(f"DEBUG fetch_matched_schemes payload: {payload}")
        with httpx.Client() as client:
            resp = client.post(
                "http://localhost:8000/api/schemes/match",
                json=payload,
                timeout=10
            )
            data = resp.json()
            print(f"DEBUG schemes returned: {len(data.get('schemes', []))}")
            return data.get("schemes", [])
    except Exception as e:
        print(f"Error fetching schemes: {e}")
        return []

def build_scheme_context(schemes: list) -> str:
    if not schemes:
        return "No matching government schemes found for this user."
    lines = ["Here are the government schemes this user is eligible for:\n"]
    for i, s in enumerate(schemes, 1):
        lines.append(f"{i}. {s.get('title', 'Unknown')}")
        lines.append(f"   Summary: {s.get('summary', 'N/A')}")
        if s.get("steps"):
            lines.append(f"   How to apply: {'; '.join(s['steps'][:2])}")
        if s.get("documents"):
            lines.append(f"   Documents needed: {', '.join(s['documents'][:3])}")
        if s.get("source"):
            lines.append(f"   More info: {s['source']}")
        lines.append("")
    return "\n".join(lines)

@router.post("/message")
def chat(data: ChatInput):
    step = data.current_step
    profile = data.profile.copy()
    schemes = data.schemes or []
    history = data.history or []

    # PHASE 1: Profile collection
    if step < len(PROFILE_QUESTIONS):
        field = PROFILE_QUESTIONS[step][0]
        profile[field] = data.message
        next_step = step + 1

        if next_step >= len(PROFILE_QUESTIONS):
            schemes = fetch_matched_schemes(profile)
            scheme_context = build_scheme_context(schemes)
            income_fmt = format_income(profile.get("income", ""))
            num_schemes = len(schemes)

            # Direct instruction — no "write a response" meta-framing
            prompt = f"""You are Sathi, a helpful Indian government scheme assistant. Reply naturally as Sathi.

The user's profile:
- Name: {profile.get('name')}
- Occupation: {profile.get('occupation')}
- Category: {profile.get('caste')}
- Annual Income: {income_fmt}

They qualify for {num_schemes} government scheme(s):
{scheme_context}

Greet them by name, confirm their profile details (use {income_fmt} for income), tell them they qualify for {num_schemes} scheme(s), name each scheme, and invite them to ask for details. Be warm and concise."""

            resp = ollama.chat.completions.create(
                model="deepseek-r1:7b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500, temperature=0.7
            )
            reply = clean_reply(resp.choices[0].message.content or "")

            return {
                "response":  reply,
                "next_step": next_step,
                "profile":   profile,
                "schemes":   schemes,
            }

        _, question_template = PROFILE_QUESTIONS[next_step]
        question = question_template.format(**profile)
        return {
            "response":  question,
            "next_step": next_step,
            "profile":   profile,
            "schemes":   schemes,
        }

    # PHASE 2: Free-form chat
    scheme_context = build_scheme_context(schemes)
    income_fmt = format_income(profile.get("income", ""))

    system_prompt = f"""You are Sathi, a friendly Indian government scheme assistant. Respond naturally and helpfully.

User Profile:
- Name: {profile.get('name')}
- Occupation: {profile.get('occupation')}
- Category: {profile.get('caste')}
- Annual Income: {income_fmt}

{scheme_context}

Rules:
- Only discuss the schemes listed above.
- Always use full scheme names, never abbreviations.
- If asked for a list, list all schemes with full names and one-line summaries.
- Give step-by-step guidance when asked how to apply.
- Be friendly, clear, and concise.
- Match the user's language (Hindi or English).
- Do not invent schemes not in the list."""

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": data.message})

    resp = ollama.chat.completions.create(
        model="deepseek-r1:7b",
        messages=messages,
        max_tokens=1500, temperature=0.7
    )
    reply = clean_reply(resp.choices[0].message.content or "")

    return {
        "response":  reply,
        "next_step": step,
        "profile":   profile,
        "schemes":   schemes,
    }