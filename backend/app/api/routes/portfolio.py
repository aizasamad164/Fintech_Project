# backend/app/api/routes/portfolio.py
"""
Portfolio endpoints (report section 3):

  POST   /api/portfolio/rebalance            build a 3-5 holding portfolio + explanation
  POST   /api/portfolio/save                 persist an accepted portfolio
  GET    /api/portfolio/list?user_id=...     a user's saved portfolios
  GET    /api/portfolio/{id}/performance     live P&L for one saved portfolio
  DELETE /api/portfolio/{id}?user_id=...     remove a saved portfolio
"""
from __future__ import annotations

import asyncio
import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.data import portfolio_store
from app.data.news import get_ticker_news
from app.llm.explainer import explain_portfolio
from app.optimization.portfolio_service import run_portfolio_rebalancing
from app.optimization.portfolio_tracker import calculate_portfolio_performance
from app.api.routes.recommend import recommend
from app.schemas.portfolio import RecommendRequest, RecommendResponse

router = APIRouter()
DISCLAIMER = ("This output is an educational simulation only and does not "
              "constitute regulated financial advice.")


def _check_uuid(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="user_id must be a UUID")


# ---------------------------------------------------------------- rebalance
class RebalanceRequest(BaseModel):
    portfolio_value: float = Field(5000, ge=100, le=10_000_000)
    target_sector: str = "All"
    risk_strategy: Literal["conservative", "balanced", "aggressive"] = "balanced"
    top_n: Optional[int] = Field(None, ge=3, le=5)
    include_explanation: bool = True


@router.post("/rebalance")
async def rebalance(req: RebalanceRequest):
    result = await run_portfolio_rebalancing(
        portfolio_value=req.portfolio_value,
        target_sector=req.target_sector,
        risk_strategy=req.risk_strategy,
        top_n=req.top_n,
    )
    if result.get("status") != "success":
        raise HTTPException(status_code=503, detail=result.get("message", "Could not build portfolio"))

    result["explanation"], result["explanation_source"] = [], "none"
    if req.include_explanation:
        # Headlines for the top 2 holdings give the explanation real-world context
        top = [a["ticker"] for a in result["allocations"][:2]]
        try:
            news = await asyncio.wait_for(
                asyncio.gather(*[asyncio.to_thread(get_ticker_news, t, 2) for t in top]), timeout=3)
            headlines = {n["ticker"]: [a["title"] for a in n["articles"]] for n in news}
        except Exception:  # noqa: BLE001 - news is optional context
            headlines = {}
        result["explanation"], result["explanation_source"] = await explain_portfolio(result, headlines)

    result["disclaimer"] = DISCLAIMER
    return result


# ---------------------------------------------------------------- save
class PositionIn(BaseModel):
    ticker: str
    sector: str = "General"
    shares_held: float = Field(..., gt=0)
    buy_price: float = Field(..., gt=0)
    cost_basis: Optional[float] = None


class SaveRequest(BaseModel):
    user_id: str
    portfolio_name: str = "My Advisory Portfolio"
    target_sector: str = "All"
    risk_strategy: str = "balanced"
    initial_investment: float = Field(..., gt=0)
    positions: List[PositionIn] = Field(..., min_length=1)

    @field_validator("user_id")
    @classmethod
    def _uuid(cls, v: str) -> str:
        return str(uuid.UUID(v))


@router.post("/save")
async def save(req: SaveRequest):
    try:
        saved = await asyncio.to_thread(
            portfolio_store.save_portfolio, req.user_id, req.portfolio_name, req.target_sector,
            req.risk_strategy, req.initial_investment, [p.model_dump() for p in req.positions])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not save portfolio: {exc}")
    return {"status": "success", "storage": portfolio_store.storage_mode(), "portfolio": saved}


# ---------------------------------------------------------------- list / performance / delete
@router.get("/list")
async def list_saved(user_id: str = Query(...)):
    uid = _check_uuid(user_id)
    items = await asyncio.to_thread(portfolio_store.list_portfolios, uid)
    return {"status": "success", "storage": portfolio_store.storage_mode(), "portfolios": items}


@router.get("/{portfolio_id}/performance")
async def performance(portfolio_id: str, user_id: str = Query(...)):
    uid = _check_uuid(user_id)
    saved = await asyncio.to_thread(portfolio_store.get_portfolio, portfolio_id, uid)
    if not saved:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    perf = await asyncio.to_thread(calculate_portfolio_performance, saved.get("positions", []))
    return {
        "status": "success",
        "portfolio": {k: saved.get(k) for k in
                      ("id", "portfolio_name", "target_sector", "risk_strategy", "initial_investment", "created_at")},
        **perf,
    }


@router.delete("/{portfolio_id}")
async def delete(portfolio_id: str, user_id: str = Query(...)):
    uid = _check_uuid(user_id)
    if not await asyncio.to_thread(portfolio_store.delete_portfolio, portfolio_id, uid):
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"status": "success"}



# ---------------------------------------------------------------- generate (used by frontend)
@router.post("/generate", response_model=RecommendResponse)
async def generate_portfolio(request: RecommendRequest) -> dict:
    return await recommend(request)