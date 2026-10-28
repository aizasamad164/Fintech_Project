# backend/app/llm/tools.py
"""Agent tool schemas + dispatcher (report Appendix C)."""
import asyncio
import json
from typing import Any, Dict, List, Optional

from app.data.market_data import get_latest_ticker_price
from app.data.news import get_ticker_news
from app.compliance import shariah
from app.optimization.portfolio_service import run_portfolio_rebalancing
from app.optimization.portfolio_tracker import calculate_portfolio_performance
from app.signals.signal_router import get_signal

AGENT_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "optimize_portfolio",
            "description": (
                "Calculates new portfolio allocations (top 3-5 holdings) using inverse volatility and ML "
                "model signals. CALL THIS ONLY when the user explicitly asks to allocate capital, build a "
                "new portfolio, or rebalance funds."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "portfolio_value": {"type": "number", "description": "Total dollar amount to invest (e.g. 2000, 5000, 10000)"},
                    "target_sector": {"type": "string", "description": "'Technology', 'Healthcare', 'Pharmaceuticals', 'Renewable_Energy', or 'All'"},
                    "risk_strategy": {"type": "string", "enum": ["conservative", "balanced", "aggressive"],
                                      "description": "How much price swing the user accepts (default balanced)"},
                    "top_n": {"type": "integer", "description": "Number of holdings, 3 to 5 (default depends on strategy)"},
                    "model_scope": {"type": "string", "enum": ["sector", "global"],
                                    "description": "'sector' (default) = the specialised per-sector models; 'global' = the cross-sector clustering model that scores all stocks together"},
                    "shariah_only": {"type": "boolean",
                                     "description": "True ONLY if the user asks for a Halal / Islamic / Shariah-compliant portfolio. Restricts the choice to screened compliant stocks."},
                },
                "required": ["portfolio_value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_portfolio_performance",
            "description": (
                "Fetches live market prices, gain/loss in USD and percentage return for the user's saved "
                "portfolio that is loaded in this chat. CALL THIS when the user asks how their saved "
                "portfolio is performing or why it is up/down."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ml_prediction",
            "description": (
                "Fetches the machine learning signal (BUY/HOLD/SELL), confidence and predicted 5-day return "
                "for one stock. CALL THIS when the user asks for AI signals or predictions on a ticker."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock symbol (e.g. NVDA, AAPL, LLY)"},
                    "sector": {"type": "string", "description": "Technology, Healthcare, Pharmaceuticals, Renewable_Energy, or General"},
                    "model_scope": {"type": "string", "enum": ["sector", "global"],
                                    "description": "'sector' (default) or 'global' (cross-sector clustering model)"},
                    "risk_strategy": {"type": "string", "enum": ["conservative", "balanced", "aggressive"],
                                      "description": "Only used with model_scope='global' (default balanced)"},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_news",
            "description": (
                "Fetches recent news headlines and publishers for a stock symbol. CALL THIS to add "
                "real-world context to top holdings or to investigate price moves."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock symbol (e.g. NVDA, TSLA)"},
                    "limit": {"type": "integer", "description": "Number of articles to retrieve (default 3)"},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Fetches the latest live price for a stock symbol. CALL THIS for simple price checks.",
            "parameters": {
                "type": "object",
                "properties": {"ticker": {"type": "string", "description": "Stock symbol (e.g. NVDA, AAPL)"}},
                "required": ["ticker"],
            },
        },
    },
]


def _slim_rebalance(result: Dict[str, Any]) -> Dict[str, Any]:
    """The full payload carries 12-month trend arrays the LLM doesn't need;
    trimming them keeps us well inside Groq's token limits."""
    keep = ("ticker", "name", "sector", "weight_pct", "actual_usd_allocated", "shares", "price",
            "year_return_pct", "volatility", "ml_signal", "ml_confidence", "predicted_5d_return")
    return {
        "status": result.get("status"),
        "message": result.get("message"),
        "risk_strategy": result.get("risk_strategy"),
        "target_sector": result.get("target_sector"),
        "model_scope": result.get("model_scope"),
        "shariah_only": result.get("shariah_only"),
        "shariah": result.get("shariah"),
        "notes": result.get("notes"),
        "summary": result.get("summary"),
        "allocations": [{k: a.get(k) for k in keep} for a in result.get("allocations", [])],
    }


async def execute_tool_call(tool_name: str, raw_arguments: Any,
                            user_portfolio_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        if isinstance(raw_arguments, str):
            args = json.loads(raw_arguments) if raw_arguments.strip() else {}
        elif isinstance(raw_arguments, dict):
            args = raw_arguments
        else:
            args = {}
    except Exception as parse_err:  # noqa: BLE001
        return {"error": f"Invalid tool arguments JSON: {parse_err}"}

    try:
        if tool_name == "optimize_portfolio":
            result = await run_portfolio_rebalancing(
                portfolio_value=float(args.get("portfolio_value", 10000.0)),
                target_sector=args.get("target_sector"),
                risk_strategy=args.get("risk_strategy", "balanced"),
                top_n=int(args["top_n"]) if args.get("top_n") else None,
                allow_fractional=True,
                model_scope=args.get("model_scope") or "sector",
                shariah_only=bool(args.get("shariah_only", False)),
            )
            return _slim_rebalance(result)

        if tool_name == "get_portfolio_performance":
            positions = (user_portfolio_data or {}).get("positions", [])
            if not positions:
                return {"error": "No saved portfolio is loaded in this chat. Ask the user to open one from the Tracking tab."}
            return await asyncio.to_thread(calculate_portfolio_performance, positions)

        if tool_name == "get_ml_prediction":
            ticker = str(args.get("ticker", "")).strip()
            signal = await asyncio.to_thread(
                get_signal, ticker, str(args.get("sector") or "General").strip(),
                args.get("model_scope") or "sector", args.get("risk_strategy") or "balanced")
            # Tell the model (and user) the stock's Shariah screening result alongside the signal
            signal["shariah_status"] = shariah.status(ticker) or "not_screened"
            return signal

        if tool_name == "get_market_news":
            return await asyncio.to_thread(
                get_ticker_news, str(args.get("ticker", "")).strip(), int(args.get("limit", 3)))

        if tool_name in ("get_stock_price", "get_stock_fundamentals"):  # old name kept for compatibility
            return await asyncio.to_thread(get_latest_ticker_price, str(args.get("ticker", "")).strip())

        return {"error": f"Unknown tool: '{tool_name}'"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to execute tool '{tool_name}': {e}"}
