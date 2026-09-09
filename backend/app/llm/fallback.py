"""
NFR-3.1: If Groq API times out or fails, deliver the completed portfolio
table alongside this default static explanation instead of erroring out.
"""

STATIC_EXPLANATION = [
    "This portfolio was built by weighing each stock's risk and growth signals "
    "according to your selected strategy.",
    "Your budget was split across the selected assets to balance potential "
    "return against volatility.",
    "Live AI-generated commentary is temporarily unavailable, but the "
    "allocation and figures above are unaffected.",
]


def static_explanation() -> list[str]:
    return STATIC_EXPLANATION
