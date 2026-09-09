"""
FastAPI entrypoint. Async request handlers support NFR-1.3 (50 concurrent users).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, portfolio, explain

app = FastAPI(
    title="Portfolio Allocation API",
    description="Quant + LLM-explained portfolio allocation engine (educational simulation only).",
    version="0.1.0",
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
app.include_router(explain.router, prefix="/api/explain", tags=["explain"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
