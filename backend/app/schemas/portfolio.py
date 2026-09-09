from pydantic import BaseModel


class AllocationItem(BaseModel):
    ticker: str
    weight: float
    amount: float
    shares: int


class PortfolioResponse(BaseModel):
    allocations: list[AllocationItem]
    one_year_performance_pct: float
    projected_return: float
    explanation_bullets: list[str]
    disclaimer: str = (
        "This output is an educational simulation only and does not "
        "constitute regulated financial advice."
    )
