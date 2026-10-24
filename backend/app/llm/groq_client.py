import os
from groq import AsyncGroq

def get_groq_client() -> AsyncGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing from backend/.env")
    return AsyncGroq(api_key=api_key)

groq_client = get_groq_client()