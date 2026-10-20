"""
FastAPI entrypoint. Async request handlers support NFR-1.3 (50 concurrent users).
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, portfolio, explain, market, recommend
from app.data.indicators import warm_up

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
    title="Portfolio Allocation API",
    description="Quant + LLM-explained portfolio allocation engine (educational simulation only).",
    version="0.1.0",
    lifespan=lifespan,
)

# TODO: restrict allow_origins to actual frontend domain(s) before production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(recommend.router, prefix="/api/v1", tags=["recommend"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(explain.router, prefix="/api/explain", tags=["explain"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
