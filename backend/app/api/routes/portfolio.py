"""
Core portfolio generation endpoint.
Orchestrates: data ingestion (F-02) -> signal generation (F-03) -> optimization (F-04).
Target: full round trip within 3.0s (NFR-1.1).
"""
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class PortfolioRequest(BaseModel):
    budget: float                  # FR-1.2
    risk_strategy: str             # FR-1.3: "conservative" | "balanced" | "aggressive"
    sectors: list[str]             # FR-1.4: e.g. ["technology"] or ["combined"]


@router.post("/generate")
async def generate_portfolio(request: PortfolioRequest):
    # TODO:
    # 1. app.data.market_data -> fetch OHLCV for candidate pool (FR-2.1)
    # 2. app.data.indicators -> compute technical indicators (FR-2.3)
    # 3. app.signals.* -> pattern detection + ML probability scores (FR-3.1-3.3)
    # 4. app.optimization.allocator -> mean-variance weights (FR-4.1)
    # 5. app.optimization.discretize -> dollar amounts + share counts (FR-4.2)
    # 6. app.optimization.performance -> 1yr historical return projection (FR-4.3)
    raise NotImplementedError
