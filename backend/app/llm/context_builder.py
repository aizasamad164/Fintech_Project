from typing import Dict, Any, Optional

async def build_user_context(active_portfolio: Optional[Dict[str, Any]] = None) -> str:
    """
    Formats active dashboard context (currently loaded portfolio, active risk settings, tickers)
    to inject into the agent system context.
    """
    if not active_portfolio:
        return "ACTIVE DASHBOARD CONTEXT: No active portfolio currently loaded in user view."
    
    tickers = active_portfolio.get("tickers", [])
    portfolio_value = active_portfolio.get("total_value", 10000.0)
    allocations = active_portfolio.get("allocations", [])
    
    context_lines = [
        "ACTIVE DASHBOARD CONTEXT:",
        f"- Target Portfolio Value: ${portfolio_value:,.2f}",
        f"- Active Tickers in View: {', '.join(tickers) if tickers else 'None'}"
    ]
    
    if allocations:
        formatted = [f"{item.get('ticker')}: {item.get('weight_pct', 0)}%" for item in allocations]
        context_lines.append(f"- Current Portfolio Breakdown: {', '.join(formatted)}")
        
    return "\n".join(context_lines)