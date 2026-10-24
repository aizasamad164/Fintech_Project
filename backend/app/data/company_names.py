# backend/app/data/company_names.py
"""Display names for the tickers in app.ml_config.SECTOR_CONFIGS.
Static on purpose: yfinance's .info call is slow (~1s per ticker)."""

COMPANY_NAMES = {
    # Technology
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "NVDA": "Nvidia Corp.",
    "AMD": "Advanced Micro Devices", "AVGO": "Broadcom Inc.", "QCOM": "Qualcomm Inc.",
    "ORCL": "Oracle Corp.", "CRM": "Salesforce Inc.", "ADBE": "Adobe Inc.",
    "TXN": "Texas Instruments",
    # Healthcare
    "UNH": "UnitedHealth Group", "JNJ": "Johnson & Johnson", "PFE": "Pfizer Inc.",
    "ABT": "Abbott Laboratories", "MRK": "Merck & Co.", "TMO": "Thermo Fisher Scientific",
    "DHR": "Danaher Corp.", "ISRG": "Intuitive Surgical", "MDT": "Medtronic plc",
    "SYK": "Stryker Corp.",
    # Pharmaceuticals
    "LLY": "Eli Lilly & Co.", "BMY": "Bristol Myers Squibb", "NVO": "Novo Nordisk",
    "AZN": "AstraZeneca plc", "NVS": "Novartis AG", "AMGN": "Amgen Inc.",
    "GILD": "Gilead Sciences", "REGN": "Regeneron Pharmaceuticals",
    "VRTX": "Vertex Pharmaceuticals", "SNY": "Sanofi",
    # Renewable energy
    "ENPH": "Enphase Energy", "FSLR": "First Solar Inc.", "NEE": "NextEra Energy",
    "SEDG": "SolarEdge Technologies", "RUN": "Sunrun Inc.", "BEP": "Brookfield Renewable",
    "CWEN": "Clearway Energy", "HASI": "HA Sustainable Infrastructure",
    "PLUG": "Plug Power Inc.", "BLDP": "Ballard Power Systems",
    # Others the agent may be asked about
    "ABBV": "AbbVie Inc.", "TSLA": "Tesla Inc.", "GOOGL": "Alphabet Inc.",
    "META": "Meta Platforms", "AMZN": "Amazon.com Inc.",
}


def company_name(ticker: str) -> str:
    return COMPANY_NAMES.get(ticker.upper(), ticker.upper())
