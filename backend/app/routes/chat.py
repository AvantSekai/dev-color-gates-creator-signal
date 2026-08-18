import anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.llm import LLMConfigError, ask

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    try:
        return ask(question)
    except LLMConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except anthropic.APIError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"LLM request failed: {exc}",
        ) from exc
