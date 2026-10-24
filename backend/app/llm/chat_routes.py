# backend/app/llm/chat_routes.py
"""
POST /api/chat/message  {session_id, message, user_id?, portfolio_id?, active_portfolio?}

- portfolio_id + user_id: loads that SAVED portfolio so the agent can answer
  live-performance questions (intent D in the report).
- active_portfolio: the dashboard portfolio currently on screen (optional).
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.data import portfolio_store
from app.llm.agent import run_investment_agent
from app.llm.groq_client import groq_available

router = APIRouter(prefix="/chat", tags=["AI Agent"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    active_portfolio: Optional[Dict[str, Any]] = None


class ToolTrace(BaseModel):
    tool_name: str
    arguments: Any = None


class ChatResponse(BaseModel):
    session_id: str
    role: str
    content: str
    tools_used: List[ToolTrace] = []
    status: str = "success"


@router.post("/message", response_model=ChatResponse)
async def chat_message(req: ChatRequest):
    if not groq_available():
        return ChatResponse(session_id=req.session_id, role="assistant", status="unavailable",
                            content="The AI advisor isn't configured yet: add GROQ_API_KEY to backend/.env "
                                    "and restart the backend.")

    context = req.active_portfolio
    if req.portfolio_id and req.user_id:
        saved = await asyncio.to_thread(portfolio_store.get_portfolio, req.portfolio_id, req.user_id)
        if saved:
            context = saved

    try:
        out = await run_investment_agent(session_id=req.session_id, user_message=req.message,
                                         active_portfolio=context)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent failed")
        return ChatResponse(session_id=req.session_id, role="assistant", status="error",
                            content=f"Sorry, the advisor hit a problem and couldn't answer ({type(exc).__name__}: "
                                    f"{str(exc)[:200]}). Please try again in a moment.")

    return ChatResponse(
        session_id=req.session_id,
        role=out["role"],
        content=out["content"],
        tools_used=[ToolTrace(tool_name=t["tool_name"], arguments=t.get("arguments"))
                    for t in out.get("tool_calls_executed", [])],
    )
