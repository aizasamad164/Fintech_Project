from pydantic import AliasChoices, BaseModel, Field, field_validator

from app.data.price_history import resolve_sectors
from app.optimization.allocator import normalize_risk_profile

DISCLAIMER = (
    "This output is an educational simulation only and does not "
    "constitute regulated financial advice."
)


class AllocationItem(BaseModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    price: float | None = None      # latest close used for the share count
    weight: float                   # target weight from the optimizer (0-1)
    amount: float                   # dollars actually invested in this stock
    shares: float                   # fractional unless fractional_shares=false


class RecommendRequest(BaseModel):
    """Body of POST /api/v1/recommend (FR-1.2, FR-1.3, FR-1.4)."""

    budget: float = Field(..., ge=1, le=10_000_000, description="Cash to invest, in dollars.")
    risk_profile: str = Field(
        ...,
        validation_alias=AliasChoices("risk_profile", "risk_strategy"),
        description="conservative | balanced | aggressive",
    )
    sectors: list[str] = Field(
        default_factory=list,
        description="technology, healthcare, renewable_energy. Empty or ['combined'] = all sectors.",
    )
    fractional_shares: bool = True
    shariah_only: bool = False  # restrict to Shariah-compliant stocks (optional)

    @field_validator("risk_profile", mode="before")
    @classmethod
    def _check_risk_profile(cls, value):
        return normalize_risk_profile(value)

    @field_validator("sectors", mode="before")
    @classmethod
    def _check_sectors(cls, value):
        return resolve_sectors(value)


class RecommendResponse(BaseModel):
    budget: float
    risk_profile: str
    sectors: list[str]
    allocations: list[AllocationItem]
    invested_amount: float
    cash_left: float
    one_year_performance_pct: float
    projected_return: float
    price_data_as_of: str
    skipped_tickers: dict[str, str] = Field(default_factory=dict)
    shariah_only: bool = False
    explanation_bullets: list[str] = Field(default_factory=list)  # filled by the LLM layer (FR-5.x)
    generated_in_seconds: float
    disclaimer: str = DISCLAIMER


# Kept for the LLM explanation layer, which extends the payload above.
class PortfolioResponse(BaseModel):
    allocations: list[AllocationItem]
    one_year_performance_pct: float
    projected_return: float
    explanation_bullets: list[str]
    disclaimer: str = DISCLAIMER
