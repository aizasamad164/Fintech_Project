from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.llm.agent import run_investment_agent

router = APIRouter(prefix="/chat", tags=["AI Agent"])

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    role: str
    content: str
    tool_calls_executed: List[Dict[str, Any]]

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        agent_output = await run_investment_agent(user_message=request.message)
        return ChatResponse(
            session_id=request.session_id,
            role=agent_output["role"],
            content=agent_output["content"],
            tool_calls_executed=agent_output["tool_calls_executed"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")