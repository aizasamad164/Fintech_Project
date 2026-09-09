"""
NFR-3.2: If live market data feeds are unresponsive, fall back to cached
data without surfacing unhandled errors to the client.
"""


class MarketDataUnavailableError(Exception):
    """Raised when both the live feed and the cache miss for a given ticker."""
    pass


class LLMServiceError(Exception):
    """Raised when the Groq API call fails; caller should use app.llm.fallback."""
    pass
