import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
FMP_API_KEY: str = os.getenv("FMP_API_KEY", "")
FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

# --- Claude Models ---
ORCHESTRATOR_MODEL: str = "claude-sonnet-4-6"
EVAL_MODEL: str = "claude-haiku-4-5-20251001"

# --- Thinking Budgets ---
THINKING_BUDGET_ANALYSIS: int = 8000    # analysis queries (Sonnet)
THINKING_BUDGET_DECISION: int = 16000   # decision queries (Sonnet)

# --- API Base URLs ---
FMP_BASE_URL: str = "https://financialmodelingprep.com/api/v3"
FINNHUB_BASE_URL: str = "https://finnhub.io/api/v1"

# --- Cache ---
CACHE_TTL_SECONDS: int = 86400  # 24 hours

# --- Database ---
DB_PATH: str = os.path.join(os.path.dirname(__file__), "..", "data", "warren.db")
CHROMA_PATH: str = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")

# --- Portfolio Scoring Weights ---
SCORING_WEIGHTS: dict[str, float] = {
    "fundamentals": 0.30,
    "earnings": 0.25,
    "news_sentiment": 0.20,
    "smart_money": 0.15,
    "technicals": 0.10,
}

# --- Smart Money Watchlist (CIK numbers from SEC EDGAR) ---
WATCHLIST_FUNDS: dict[str, str] = {
    "Berkshire Hathaway": "0001067983",
    "Pershing Square":    "0001336528",
    "Pabrai Funds":       "0001173334",
    "ARK Invest":         "0001579982",
    "Appaloosa":          "0001029390",
}
