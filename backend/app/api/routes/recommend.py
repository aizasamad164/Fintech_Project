"""
Week 2 deliverable: POST /api/v1/recommend

Given a budget, a risk profile and a sector selection, returns the complete
allocation payload (weights, dollar amounts, share counts, 1-year performance).
Target: full round trip within 3.0 s (NFR-1.1).
"""
import logging

from fastapi import APIRouter, HTTPException

from app.core.exceptions import InsufficientDataError
from app.optimization.recommender import build_recommendation
from app.schemas.portfolio import RecommendRequest, RecommendResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest) -> dict:
    try:
        return await build_recommendation(
            budget=request.budget,
            risk_profile=request.risk_profile,
            sectors=request.sectors,
            fractional_shares=request.fractional_shares,
        )
    except InsufficientDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:  # noqa: BLE001
        logger.exception("Recommendation failed")
        raise HTTPException(status_code=502, detail="Could not build a recommendation. See server logs.")
