"""Shared StockSense configuration.

This file combines the configuration required by the current StockSense base
pipeline with the settings required by the enhanced clustering/ML pipeline.

Do not remove keys just because one pipeline does not use them: different
entry points in the repository import different parts of this configuration.
"""

# ---------------------------------------------------------------------------
# Sector universes
# ---------------------------------------------------------------------------
# These are based on the latest StockSense base repository.  The additional
# indicator settings are retained for forecasting/clustering compatibility.
SECTOR_CONFIGS = {
    "Technology": {
        "tickers": [
            "AAPL", "MSFT", "NVDA", "AMD", "AVGO",
            "QCOM", "ORCL", "CRM", "ADBE", "TXN",
        ],
        "max_pe": 80.0,
        "min_profit_margin": 0.05,
        "rsi_window": 14,
        "trend_sma": 50,
    },

    "Healthcare": {
        "tickers": [
            "UNH", "JNJ", "PFE", "ABT", "MRK",
            "TMO", "DHR", "ISRG", "MDT", "SYK",
        ],
        "max_pe": 60.0,
        "min_profit_margin": 0.02,
        "rsi_window": 10,
        "trend_sma": 100,
    },

    "Pharmaceuticals": {
        "tickers": [
            "LLY", "BMY", "NVO", "AZN", "NVS",
            "AMGN", "GILD", "REGN", "VRTX", "SNY",
        ],
        "max_pe": 70.0,
        "min_profit_margin": 0.00,
        "rsi_window": 10,
        "trend_sma": 100,
    },

    "Renewable_Energy": {
        "tickers": [
            "ENPH", "FSLR", "NEE", "SEDG", "RUN",
            "BEP", "CWEN", "HASI", "PLUG", "BLDP",
        ],
        "max_pe": 100.0,
        "min_profit_margin": -0.20,
        "rsi_window": 14,
        "trend_sma": 50,
    },
}

# Dedicated pharmaceutical subset used by main.py's pharma LSTM flow.
# Keep this separate from the Pharmaceuticals sector universe because the
# existing main.py fetches Healthcare first and then filters this list.
PHARMA_UNIVERSE = [
    "JNJ",
    "PFE",
    "MRK",
    "ABBV",
    "LLY",
    "BMY",
]


# ---------------------------------------------------------------------------
# Risk profiles
# ---------------------------------------------------------------------------
# target_return / max_volatility / quantile_threshold are required by the
# enhanced clustering + forecasting pipeline.
#
# prob_threshold is retained for older/base model entry points that use a
# fixed probability threshold instead of the dynamic quantile threshold.
RISK_PROFILES = {
    "conservative": {
        "target_return": 0.010,
        "max_volatility": 0.03,
        "quantile_threshold": 0.85,
        "prob_threshold": 0.65,
        "max_depth": 3,
    },
    "balanced": {
        "target_return": 0.015,
        "max_volatility": 0.05,
        "quantile_threshold": 0.75,
        "prob_threshold": 0.60,
        "max_depth": 4,
    },
    "aggressive": {
        "target_return": 0.025,
        "max_volatility": 0.10,
        "quantile_threshold": 0.60,
        "prob_threshold": 0.55,
        "max_depth": 6,
    },
}


# ---------------------------------------------------------------------------
# LSTM settings
# ---------------------------------------------------------------------------
# Kept compatible with the current base LSTM entry points.  The enhanced
# clustering/LSTM code can override these during tuning when appropriate.
MODEL_PARAMS = {
    "sequence_length": 30,
    "batch_size": 50,
    "epochs": 40,
    "learning_rate": 0.00025,
}

#-------------------------Sarah's config------------------------------------------------------------------------------------------------------------------------
# # Cleaned SECTOR_CONFIGS dictionary for config.py
# SECTOR_CONFIGS = {
#     "Technology": {
#         "tickers": [
#             "AAPL", "MSFT", "NVDA", "AMD", "AVGO", "QCOM", "ORCL", "CRM", "ADBE", "TXN"
#         ],
#         "max_pe": 80.0,
#         "min_profit_margin": 0.05
#     },
#     "Healthcare": {
#         "tickers": [
#             "UNH", "JNJ", "PFE", "ABT", "MRK", "TMO", "DHR", "ISRG", "MDT", "SYK"
#         ],
#         "max_pe": 60.0,
#         "min_profit_margin": 0.02
#     },
#     "Pharmaceuticals": {
#         "tickers": [
#             "LLY", "BMY", "NVO", "AZN", "NVS", "AMGN", "GILD", "REGN", "VRTX", "SNY"
#         ],
#         "max_pe": 70.0,
#         "min_profit_margin": 0.00
#     },
#     "Renewable_Energy": {
#     "tickers": [
#         "ENPH", "FSLR", "NEE", "SEDG", "RUN", "BEP", "CWEN", "HASI", "PLUG", "BLDP"
#     ],
#     "max_pe": 100.0,
#     "min_profit_margin": -0.20
# }
# }

# RISK_PROFILES = {
#     "conservative": {"target_return": 0.01, "prob_threshold": 0.65},
#     "balanced":     {"target_return": 0.02, "prob_threshold": 0.60},
#     "aggressive":   {"target_return": 0.03, "prob_threshold": 0.55}
# }
# # config.py

# PHARMA_UNIVERSE = [
#     "JNJ",   # Johnson & Johnson
#     "PFE",   # Pfizer
#     "MRK",   # Merck & Co.
#     "ABBV",  # AbbVie
#     "LLY",   # Eli Lilly
#     "BMY"    # Bristol Myers Squibb
# ]

# MODEL_PARAMS = {
#     "sequence_length": 30, # 20 trading days (~1 month lookback window)
#     "batch_size": 50,
#     "epochs": 40,
#     "learning_rate": 0.00025
# }