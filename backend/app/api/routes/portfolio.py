"""
Core portfolio generation endpoint used by the frontend (POST /api/portfolio/generate).

It shares one implementation with POST /api/v1/recommend, and accepts the
frontend's `risk_strategy` field as well as `risk_profile`, so the app keeps
working without any client change.
Later steps: LLM explanations (F-05) will fill `explanation_bullets`.
Target: full round trip within 3.0s (NFR-1.1).
"""
from fastapi import APIRouter

from app.api.routes.recommend import recommend
from app.schemas.portfolio import RecommendRequest, RecommendResponse

router = APIRouter()


@router.post("/generate", response_model=RecommendResponse)
async def generate_portfolio(request: RecommendRequest) -> dict:
    return await recommend(request)
