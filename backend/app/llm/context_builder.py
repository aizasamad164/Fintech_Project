from typing import Any, Dict, Optional


async def build_user_context(active_portfolio: Optional[Dict[str, Any]] = None) -> str:
    """
    Describes what the user currently has open, for the agent's system prompt.
    Accepts either a dashboard portfolio (`allocations`) or a saved portfolio
    (`positions`, loaded from the Tracking tab).
    """
    if not active_portfolio:
        return "ACTIVE DASHBOARD CONTEXT: No portfolio is loaded in this chat."

    lines = ["ACTIVE DASHBOARD CONTEXT:"]
    if active_portfolio.get("positions"):
        lines.append(f"- A SAVED portfolio is loaded: '{active_portfolio.get('portfolio_name', 'My portfolio')}' "
                     f"(id {active_portfolio.get('id', '?')}), strategy {active_portfolio.get('risk_strategy', '?')}, "
                     f"initial investment ${float(active_portfolio.get('initial_investment', 0)):,.2f}.")
        held = [f"{p['ticker']} ({float(p['shares_held']):g} sh @ ${float(p['buy_price']):,.2f})"
                for p in active_portfolio["positions"]]
        lines.append(f"- Positions: {', '.join(held)}")
        lines.append("- For performance questions call get_portfolio_performance (no arguments needed).")
        return "\n".join(lines)

    value = float(active_portfolio.get("total_value") or active_portfolio.get("portfolio_value") or 0)
    if value:
        lines.append(f"- Portfolio value on screen: ${value:,.2f}")
    if active_portfolio.get("risk_strategy"):
        lines.append(f"- Strategy: {active_portfolio['risk_strategy']}; sector: {active_portfolio.get('target_sector', 'All')}")
    allocs = active_portfolio.get("allocations", [])
    if allocs:
        lines.append("- Holdings on screen: " + ", ".join(
            f"{a.get('ticker')} {a.get('weight_pct', 0)}%" for a in allocs))
    return "\n".join(lines)
