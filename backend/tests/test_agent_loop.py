"""
Agent tool-calling loop with a fake Groq client (no key/network needed):
the fake model first asks for get_portfolio_performance, then answers.
"""
import asyncio
import json
from types import SimpleNamespace as NS

import pytest

from app.llm import agent


class FakeCompletions:
    def __init__(self):
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            tc = NS(id="call_1", function=NS(name="get_portfolio_performance", arguments="{}"))
            msg = NS(content=None, tool_calls=[tc])
        else:
            tool_msg = [m for m in kwargs["messages"] if m["role"] == "tool"][-1]
            data = json.loads(tool_msg["content"])
            msg = NS(content=f"Your portfolio has {data['summary']['positions_count']} holdings.", tool_calls=None)
        return NS(choices=[NS(message=msg)])


def test_agent_runs_tool_then_answers(monkeypatch):
    fake = FakeCompletions()
    monkeypatch.setattr(agent, "groq_client", NS(chat=NS(completions=fake)))
    monkeypatch.setattr("app.llm.tools.calculate_portfolio_performance",
                        lambda positions: {"summary": {"positions_count": len(positions)}, "holdings": []})
    saved = {"id": "p1", "portfolio_name": "Test", "risk_strategy": "balanced", "initial_investment": 1000,
             "positions": [{"ticker": "AAPL", "sector": "Technology", "shares_held": 2, "buy_price": 150}]}

    out = asyncio.run(agent.run_investment_agent("s1", "How is my portfolio doing?", active_portfolio=saved))

    assert out["content"].startswith("Your portfolio has 1 holdings.")
    assert [t["tool_name"] for t in out["tool_calls_executed"]] == ["get_portfolio_performance"]
    assert "SAVED portfolio is loaded" in fake.calls[0]["messages"][0]["content"]
    assert fake.calls[0]["model"] == agent.MODEL_NAME
