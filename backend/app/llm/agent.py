# backend/app/llm/agent.py
import json
from typing import List, Dict, Any, Optional

from app.config import settings
from app.llm.groq_client import groq_client
from app.llm.tools import AGENT_TOOLS, execute_tool_call
from app.llm.disclaimer import append_disclaimer
from app.llm.context_builder import build_user_context
from app.llm.chat_session import ChatSessionManager

MODEL_NAME = getattr(settings, "GROQ_MODEL", "qwen/qwen3.8-27b")

BASE_SYSTEM_PROMPT = """You are an AI Investment Explanation & Research Assistant inside a mobile fintech advisory app.

APPLICATION CONTEXT:
The user sees their visual portfolio allocation card rendered directly on the app UI. Your primary job is to provide conversational explanations, answer user questions, justify the top holdings, and layer in recent news in simple, beginner-friendly terms.

OPERATIONAL GUIDELINES:
1. DELEGATE ALL CALCULATIONS: Call `optimize_portfolio(portfolio_value=..., target_sector=..., top_n=5)` for rebalancing requests. Keep portfolio sizes focused (top 3–5 holdings).
2. MANDATORY NEWS FETCHING: Call `get_market_news` for the top 1–2 holdings returned by `optimize_portfolio` to give the user real-world context.
3. BEGINNER-FRIENDLY EXPLANATION:
   - Use plain, simple English. Avoid dense Wall Street jargon.
   - Explain risk concepts simply (e.g., "inverse volatility" = "putting slightly more money into steadier stocks").
4. CONCISE STRUCTURE:
   - **Portfolio Summary**: Highlight the top 3-5 holdings briefly.
   - **Why This Strategy Fits**: Explain why these specific stocks suit their goal (e.g., Aggressive vs. Conservative).
   - **Latest News & Catalysts**: Summarize real news headlines fetched for the top holdings.
   - **Short-Term AI Outlook**: Explain the ML model's prediction in plain words.
5. ADVISORY ONLY: Frame all responses as educational research. Never state "You should buy X" or pretend to execute live trades."""

async def run_investment_agent(
    session_id: str,
    user_message: str,
    active_portfolio: Optional[Dict[str, Any]] = None,
    max_steps: int = 6
) -> Dict[str, Any]:
    chat_history = await ChatSessionManager.get_history(session_id)
    context_str = await build_user_context(active_portfolio)
    full_system_instruction = f"{BASE_SYSTEM_PROMPT}\n\n{context_str}"

    messages = (
        [{"role": "system", "content": full_system_instruction}]
        + chat_history
        + [{"role": "user", "content": user_message}]
    )
    executed_tools = []

    for _ in range(max_steps):
        response = await groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=AGENT_TOOLS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=800
        )

        response_msg = response.choices[0].message
        tool_calls = response_msg.tool_calls

        if not tool_calls:
            final_content = append_disclaimer(response_msg.content or "")

            await ChatSessionManager.save_message(session_id, "user", user_message)
            await ChatSessionManager.save_message(
                session_id=session_id,
                role="assistant",
                content=final_content,
                metadata={"tool_calls_executed": executed_tools}
            )

            return {
                "role": "assistant",
                "content": final_content,
                "tool_calls_executed": executed_tools
            }

        messages.append({
            "role": "assistant",
            "content": response_msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in tool_calls
            ]
        })

        for tool_call in tool_calls:
            func_name = tool_call.function.name
            func_args = tool_call.function.arguments
            tool_res = await execute_tool_call(func_name, func_args)

            executed_tools.append({
                "tool_name": func_name,
                "arguments": func_args,
                "result": tool_res
            })

            content_str = json.dumps(tool_res) if isinstance(tool_res, (dict, list)) else str(tool_res)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": content_str
            })

    fallback_content = append_disclaimer("Step limit reached while processing requested tools.")
    await ChatSessionManager.save_message(session_id, "user", user_message)
    await ChatSessionManager.save_message(session_id, "assistant", fallback_content)

    return {
        "role": "assistant",
        "content": fallback_content,
        "tool_calls_executed": executed_tools
    }