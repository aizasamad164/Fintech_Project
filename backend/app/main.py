"""
FastAPI entrypoint.  Run from the backend/ folder:
    uvicorn app.main:app --reload --port 8000
Interactive API docs: http://localhost:8000/docs
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, explain, insights, news, portfolio, recommend
from app.config import settings
from app.data.indicators import warm_up
from app.data.portfolio_store import storage_mode
from app.llm.chat_routes import router as chat_router
from app.llm.groq_client import groq_available
from app.signals.models.model_loader import MODELS_DIR, SECTOR_MODEL_MAP

# NOTE: app/api/routes/market.py is not mounted: it imports fetch_ohlcv, which
# no longer exists in app/data/market_data.py. Re-add it once that's restored.

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # The first indicator computation after start-up is slow (library warm-up);
    # pay for it now instead of on the first user request.
    try:
        await asyncio.to_thread(warm_up)
    except Exception:  # noqa: BLE001 — never block start-up on a warm-up failure
        logger.exception("Indicator warm-up failed")
    yield


app = FastAPI(
    title="StockSense API",
    description="Quant + LLM-explained portfolio allocation engine (educational simulation only).",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(recommend.router, prefix="/api/v1", tags=["recommend"])
app.include_router(explain.router, prefix="/api/explain", tags=["explain"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(chat_router, prefix="/api")  # -> POST /api/chat/...


@app.get("/health")
async def health_check():
    """Quick check that everything the app needs is in place."""
    models = {s: os.path.exists(os.path.join(MODELS_DIR, f)) for s, (f, _) in SECTOR_MODEL_MAP.items()}
    return {
        "status": "ok",
        "models_found": models,
        "groq_configured": groq_available(),
        "groq_model": settings.groq_model,
        "portfolio_storage": storage_mode(),
    }