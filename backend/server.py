"""
One World Tour — Claude guide proxy
Run: ANTHROPIC_API_KEY=sk-... uvicorn server:app --reload --port 8000
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

app = FastAPI(title="One World Tour API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.environ.get("ANTHROPIC_API_KEY")
client  = anthropic.Anthropic(api_key=api_key) if api_key else None

class GuideRequest(BaseModel):
    locationName: str
    question: str
    context: str = ""

@app.get("/health")
def health():
    return {"status": "ok", "ready": client is not None}

@app.post("/ask")
async def ask(req: GuideRequest):
    if not client:
        raise HTTPException(503, "ANTHROPIC_API_KEY not set")

    system = (
        f"You are a warm, knowledgeable local guide for {req.locationName}. "
        "Answer in 2-3 sentences, conversational and engaging. "
        "If you don't know something, say so honestly. "
        f"Background: {req.context[:600] if req.context else 'No extra context.'}"
    )

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=220,
        system=system,
        messages=[{"role": "user", "content": req.question}]
    )
    return {"answer": msg.content[0].text}
