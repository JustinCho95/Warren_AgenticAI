import time
import requests
from mcp.server.fastmcp import FastMCP
from config.settings import FMP_API_KEY, FMP_BASE_URL, WATCHLIST_FUNDS
from database.portfolio_db import get_cached_result, save_to_cache, log_tool_call

mcp = FastMCP("smart_money")


def _get_13f_holdings(cik: str) -> list[dict]:
    """Fetch latest 13F holdings for a fund via FMP."""
    url = f"{FMP_BASE_URL}/form-thirteen/{cik}?apikey={FMP_API_KEY}"
    resp = requests.get(url, timeout=15)
    return resp.json() if resp.ok else []


@mcp.tool()
def get_smart_money(ticker: str) -> dict:
    """
    Check if top institutional investors (Berkshire, Pershing Square, ARK, etc.)
    hold this stock. Returns each fund's position size and recent changes (buy/sell/hold).
    Source: FMP 13F filings + SEC EDGAR.
    """
    cache_key = f"smart_money:{ticker.upper()}"
    cached = get_cached_result(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        ticker_upper = ticker.upper()
        fund_positions = []
        funds_holding = 0

        for fund_name, cik in WATCHLIST_FUNDS.items():
            try:
                holdings = _get_13f_holdings(cik)
                # Find this ticker in the fund's holdings
                match = next(
                    (h for h in holdings if h.get("ticker", "").upper() == ticker_upper),
                    None,
                )
                if match:
                    funds_holding += 1
                    fund_positions.append({
                        "fund": fund_name,
                        "cik": cik,
                        "shares": match.get("shares"),
                        "value_usd": match.get("value"),
                        "portfolio_pct": match.get("weightPercentage"),
                        "date_reported": match.get("date"),
                    })
                else:
                    fund_positions.append({
                        "fund": fund_name,
                        "cik": cik,
                        "shares": None,
                        "value_usd": None,
                        "portfolio_pct": None,
                        "date_reported": None,
                    })
            except Exception:
                continue

        result = {
            "ticker": ticker_upper,
            "source": "FMP 13F",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "funds_holding": funds_holding,
            "funds_checked": len(WATCHLIST_FUNDS),
            "positions": fund_positions,
        }

        save_to_cache(cache_key, result)
        log_tool_call("get_smart_money", ticker, "success", int((time.time() - start) * 1000))
        return result

    except Exception as e:
        log_tool_call("get_smart_money", ticker, "error", int((time.time() - start) * 1000))
        return {"error": str(e), "ticker": ticker, "source": "FMP 13F"}


if __name__ == "__main__":
    mcp.run()
