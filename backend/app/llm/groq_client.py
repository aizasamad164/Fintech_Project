"""
FR-5.2: Submit the JSON context to Groq Cloud API (llama-3.1-8b) to generate
3 plain-language bullet-point explanations for the portfolio structure.
"""
from groq import Groq
from app.config import settings

_client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = (
    "You are a financial education assistant. Explain the given portfolio "
    "allocation in exactly 3 plain-English bullet points, avoiding jargon. "
    "This is an educational simulation, not financial advice."
)


async def get_explanation(context: dict) -> list[str]:
    """Returns 3 plain-English bullet points explaining the allocation."""
    response = _client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": str(context)},
        ],
    )
    text = response.choices[0].message.content
    # TODO: parse bullet points out of `text` into a list[str]
    return [text]
