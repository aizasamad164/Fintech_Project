"""
FR-5.x: LLM Explanation & Plain-English Translation Engine.
Falls back to a static explanation if Groq times out/fails (NFR-3.1).
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate_explanation(context: dict):
    """
    context: structured JSON payload (FR-5.1) containing allocation vectors,
    technical indicators, and sector tags.
    """
    # TODO:
    # try: app.llm.groq_client.get_explanation(context)  # FR-5.2
    # except (TimeoutError, GroqAPIError): return app.llm.fallback.static_explanation()
    #
    # Always append the educational disclaimer (FR-5.3):
    disclaimer = (
        "This output is an educational simulation only and does not constitute "
        "regulated financial advice."
    )
    raise NotImplementedError
