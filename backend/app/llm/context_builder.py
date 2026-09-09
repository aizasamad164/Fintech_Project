"""
FR-5.1: Compile quantitative allocation vectors, technical indicators, and
sector tags into a structured JSON context payload for the LLM.
"""


def build_context(allocation: dict, indicators: dict, sectors: list[str]) -> dict:
    return {
        "allocation": allocation,
        "indicators": indicators,
        "sectors": sectors,
    }
