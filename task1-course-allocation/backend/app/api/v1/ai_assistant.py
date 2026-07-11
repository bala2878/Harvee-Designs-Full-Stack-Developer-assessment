from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.assistant_service import AIAssistantError, ask_assistant
from app.core.db import get_db

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class ToolCallLog(BaseModel):
    tool: str
    input: dict
    result: object


class AskResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallLog]


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await ask_assistant(db, payload.question)
    except AIAssistantError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return result
