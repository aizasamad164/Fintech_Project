"""
FR-2.2: Calculate fundamental ratios (P/E ratio, Market Capitalization)
for candidate stock pools.
"""


async def get_fundamentals(ticker: str) -> dict:
    """Returns {'pe_ratio': float, 'market_cap': float} for the given ticker."""
    raise NotImplementedError
