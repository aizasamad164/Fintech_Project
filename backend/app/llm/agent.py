# backend/app/llm/agent.py
import json
from typing import List, Dict, Any, Optional

from app.config import settings
from app.llm.groq_client import groq_client
from app.llm.tools import AGENT_TOOLS, execute_tool_call
from app.llm.disclaimer import append_disclaimer
from app.llm.context_builder import build_user_context
from app.llm.chat_session import ChatSessionManager

MODEL_NAME = settings.groq_model

BASE_SYSTEM_PROMPT = """You are an AI Investment Research Analyst inside StockSense, an educational fintech app for beginners.
The user can already see their portfolio card, charts and holdings in the app. Your job is to explain, answer questions, and add context.

DYNAMIC TOOL USAGE GUIDELINES:
Analyze the user's intent carefully and decide which tool(s) to execute:
1. GENERAL QUESTIONS / CONVERSATION: If the user asks general questions (e.g. "How do you work?", "What is volatility?"), DO NOT call any tools. Answer directly in clear, beginner-friendly terms.
2. NEW PORTFOLIO / REBALANCING REQUESTS: Call `optimize_portfolio` (pass their amount, sector and risk strategy), then call `get_market_news` for the top 1-2 holdings to provide real-world context.
3. LIVE PERFORMANCE QUESTIONS: If a saved portfolio is loaded in context and the user asks about performance or P&L, call `get_portfolio_performance`, then `get_market_news` for the biggest moving holding.
4. SINGLE STOCK INQUIRIES: Call `get_ml_prediction` and `get_market_news` for the requested ticker. Use `get_stock_price` for a simple price check.

EXPLANATION STYLE:
- Avoid dense Wall Street jargon. Use simple, everyday analogies.
- Explain concepts simply (e.g. "inverse volatility" = "allocating slightly more capital to steadier stocks").
- Keep answers short: a few short paragraphs or a short bulleted list. Use **bold** sparingly.
- When you mention news, treat it as context, not as proof of why a price moved.
- Never say "You should buy X". Frame all responses as research and education. Never claim to execute trades."""

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
            tool_res = await execute_tool_call(func_name, func_args, user_portfolio_data=active_portfolio)

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