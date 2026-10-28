# backend/app/llm/explainer.py
"""
Three plain-English bullets explaining a generated portfolio (dashboard card).

Uses a small, fast Groq model with a strict JSON reply. If Groq is not
configured, times out, or returns something unusable, we build the bullets
from the real numbers instead (NFR-3.1) and report source="fallback".
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Tuple

from app.config import settings
from app.llm.groq_client import get_groq_client, groq_available

logger = logging.getLogger(__name__)

PROMPT = """You explain an educational stock portfolio to a complete beginner.
Write exactly 3 short bullets (max 35 words each), plain English, no jargon,
no "you should buy". Bullet 1: the overall idea of this mix for the chosen
strategy. Bullet 2: why the largest holding gets the biggest share. Bullet 3:
what the past-12-months number means, and that the past doesn't predict the future.
If headlines are given, you may mention one briefly as context, not as a cause.
If "screening" is given, mention it in bullet 1 in one short phrase (say "screened with third-party tools", never claim a religious ruling).
Reply ONLY with JSON: {"bullets": ["...", "...", "..."]}"""


def _facts(result: Dict[str, Any], headlines: Dict[str, List[str]]) -> Dict[str, Any]:
    s = result["summary"]
    return {
        "strategy": result["risk_strategy"],
        "sector": result["target_sector"],
        "budget_usd": s["total_portfolio_value"],
        "past_12m_return_pct": s["weighted_1y_return_pct"],
        "risk_rating_out_of_5": s["risk_rating"],
        "how_sizes_were_chosen": ("bigger positions for stocks the model expects to rise most"
                                  if result["risk_strategy"] == "aggressive"
                                  else "inverse volatility: steadier stocks get slightly more money"),
        "holdings": [
            {"ticker": a["ticker"], "name": a["name"], "weight_pct": a["weight_pct"],
             "volatility": a["volatility"], "ml_signal": a["ml_signal"],
             "past_12m_return_pct": a["year_return_pct"]}
            for a in result["allocations"]
        ],
        "recent_headlines": headlines,
        **({"screening": "Shariah-compliant stocks only"} if result.get("shariah_only") else {}),
    }


def fallback_bullets(result: Dict[str, Any]) -> List[str]:
    s, top = result["summary"], result["allocations"][0]
    style = {
        "conservative": "leans on steadier, established companies so one bad month hurts less",
        "balanced": "mixes steadier names with a few faster-growing ones",
        "aggressive": "leans into the names the model expects to grow fastest, which also swing more",
    }[result["risk_strategy"]]
    return [
        f"This {result['risk_strategy']} mix of {len(result['allocations'])} stocks {style}.",
        (f"{top['name']} gets the largest share ({top['weight_pct']}%) because the model expects it to "
         f"move the most in the short term, so this strategy puts more money behind it."
         if result["risk_strategy"] == "aggressive" else
         f"{top['name']} gets the largest share ({top['weight_pct']}%) because its price has been the "
         f"steadiest of these picks, and steadier stocks get slightly more money."),
        f"Over the past 12 months this mix would have returned about {s['weighted_1y_return_pct']}%. "
        f"That is history, not a promise of what happens next.",
    ]


async def explain_portfolio(result: Dict[str, Any], headlines: Dict[str, List[str]] | None = None,
                            timeout: float = 12.0) -> Tuple[List[str], str]:
    """Returns (bullets, source) where source is 'llm' or 'fallback'."""
    if not result.get("allocations"):
        return [], "fallback"
    if not groq_available():
        return fallback_bullets(result), "fallback"
    try:
        client = get_groq_client()
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=settings.groq_explain_model,
                messages=[{"role": "system", "content": PROMPT},
                          {"role": "user", "content": json.dumps(_facts(result, headlines or {}))}],
                temperature=0.3,
                max_tokens=600,
                response_format={"type": "json_object"},
            ),
            timeout=timeout,
        )
        bullets = json.loads(resp.choices[0].message.content or "{}").get("bullets", [])
        bullets = [str(b).strip() for b in bullets if str(b).strip()][:3]
        if len(bullets) == 3:
            return bullets, "llm"
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM explanation failed, using fallback: %s", exc)
    return fallback_bullets(result), "fallback"
