# backend/app/llm/tools.py
import json
from typing import Dict, Any, List

from app.signals.models.model_loader import predict_ticker_signal
from app.optimization.portfolio_service import run_portfolio_rebalancing
from app.data.news import get_ticker_news
from app.data.market_data import get_latest_ticker_price

# Agent Tool Schemas (OpenAI-compatible format for Groq / Qwen / Llama models)
AGENT_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_ml_prediction",
            "description": "Fetch machine learning signal (BUY/HOLD/SELL), confidence score, and predicted 5-day return for a stock symbol within a specific sector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock symbol (e.g. NVDA, AAPL, LLY, PFE)"
                    },
                    "sector": {
                        "type": "string",
                        "description": "Sector: Technology, Healthcare, Pharmaceuticals, Renewable_Energy, or General"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_portfolio",
            "description": "Calculates a focused, risk-managed portfolio allocation (top 3-5 holdings) using inverse volatility and ML model signals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "portfolio_value": {
                        "type": "number",
                        "description": "Total dollar amount to invest (e.g., 2000, 5000, 10000)"
                    },
                    "target_sector": {
                        "type": "string",
                        "description": "Specific sector focus (e.g., 'Technology', 'Healthcare', 'Pharmaceuticals', 'Renewable_Energy', or 'All')"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top holdings to select for the portfolio (default 5 for focused real-world allocations)"
                    },
                    "allow_fractional": {
                        "type": "boolean",
                        "description": "Whether fractional share quantities are permitted (default True)"
                    }
                },
                "required": ["portfolio_value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_news",
            "description": "Fetch recent financial market headlines, sources, and links for a stock ticker.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock symbol (e.g. NVDA, TSLA, ABT)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of news articles to retrieve (default 3 to 5)"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_fundamentals",
            "description": "Fetch latest live price and fundamental data for a given stock ticker.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock symbol (e.g. NVDA, AAPL)"
                    }
                },
                "required": ["ticker"]
            }
        }
    }
]


async def execute_tool_call(tool_name: str, raw_arguments: Any) -> Dict[str, Any]:
    """
    Executes tool calls requested by the LLM agent and returns structured dictionary responses.
    """
    # Parse JSON string arguments if necessary
    try:
        if isinstance(raw_arguments, str):
            args = json.loads(raw_arguments) if raw_arguments.strip() else {}
        elif isinstance(raw_arguments, dict):
            args = raw_arguments
        else:
            args = {}
    except Exception as parse_err:
        return {"error": f"Invalid tool arguments JSON: {str(parse_err)}"}

    try:
        if tool_name == "get_ml_prediction":
            ticker = args.get("ticker", "").strip()
            sector = args.get("sector", "General").strip()
            return predict_ticker_signal(ticker=ticker, sector=sector)

        elif tool_name == "optimize_portfolio":
            portfolio_val = float(args.get("portfolio_value", 10000.0))
            target_sector = args.get("target_sector")
            top_n = int(args.get("top_n", 5))
            allow_fractional = bool(args.get("allow_fractional", True))

            return await run_portfolio_rebalancing(
                portfolio_value=portfolio_val,
                target_sector=target_sector,
                top_n=top_n,
                allow_fractional=allow_fractional
            )

        elif tool_name == "get_market_news":
            ticker = args.get("ticker", "").strip()
            limit = int(args.get("limit", 3))
            return get_ticker_news(ticker=ticker, limit=limit)

        elif tool_name == "get_stock_fundamentals":
            ticker = args.get("ticker", "").strip()
            res = get_latest_ticker_price(ticker=ticker)
            if hasattr(res, "__await__"):
                return await res
            return res

        else:
            return {"error": f"Unknown tool: '{tool_name}'"}

    except Exception as e:
        return {"error": f"Failed to execute tool '{tool_name}': {str(e)}"}