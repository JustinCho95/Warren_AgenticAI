import time
import requests
from mcp.server.fastmcp import FastMCP
from config.settings import FMP_API_KEY, FMP_BASE_URL
from database.portfolio_db import get_cached_result, save_to_cache, log_tool_call

mcp = FastMCP("earnings")


@mcp.tool()
def get_earnings_summary(ticker: str) -> dict:
    """
    Fetch the last 4 quarters of earnings: EPS actual vs estimate,
    beat/miss rate, and revenue surprises.
    Source: Financial Modeling Prep API.
    """
    cache_key = f"earnings:{ticker.upper()}"
    cached = get_cached_result(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        url = f"{FMP_BASE_URL}/earnings-surprises/{ticker}?apikey={FMP_API_KEY}"
        data = requests.get(url, timeout=10).json()

        if not data:
            raise ValueError(f"No earnings data found for {ticker}")

        quarters = []
        beats = 0
        for q in data[:4]:
            actual = q.get("actualEarningResult")
            estimate = q.get("estimatedEarning")
            beat = actual is not None and estimate is not None and actual >= estimate
            if beat:
                beats += 1
            quarters.append({
                "date": q.get("date"),
                "actual_eps": actual,
                "estimated_eps": estimate,
                "beat": beat,
                "surprise_pct": (
                    round((actual - estimate) / abs(estimate) * 100, 2)
                    if estimate and estimate != 0 else None
                ),
            })

        result = {
            "ticker": ticker.upper(),
            "source": "FMP",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "beat_rate": f"{beats}/{len(quarters)}",
            "quarters": quarters,
        }

        save_to_cache(cache_key, result)
        log_tool_call("get_earnings_summary", ticker, "success", int((time.time() - start) * 1000))
        return result

    except Exception as e:
        log_tool_call("get_earnings_summary", ticker, "error", int((time.time() - start) * 1000))
        return {"error": str(e), "ticker": ticker, "source": "FMP"}


if __name__ == "__main__":
    mcp.run()
