import time
import requests
from mcp.server.fastmcp import FastMCP
from config.settings import FMP_API_KEY, FMP_BASE_URL
from database.portfolio_db import get_cached_result, save_to_cache, log_tool_call

mcp = FastMCP("fundamentals")


@mcp.tool()
def get_fundamentals(ticker: str) -> dict:
    """
    Fetch key fundamental metrics for a stock: P/E ratio, profit margins,
    free cash flow, debt levels, and valuation ratios.
    Source: Financial Modeling Prep API.
    """
    cache_key = f"fundamentals:{ticker.upper()}"
    cached = get_cached_result(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        profile_url = f"{FMP_BASE_URL}/profile/{ticker}?apikey={FMP_API_KEY}"
        ratios_url = f"{FMP_BASE_URL}/ratios-ttm/{ticker}?apikey={FMP_API_KEY}"
        cashflow_url = f"{FMP_BASE_URL}/cash-flow-statement/{ticker}?limit=1&apikey={FMP_API_KEY}"

        profile_resp = requests.get(profile_url, timeout=10).json()
        ratios_resp = requests.get(ratios_url, timeout=10).json()
        cashflow_resp = requests.get(cashflow_url, timeout=10).json()

        if not profile_resp:
            raise ValueError(f"No profile data found for {ticker}")

        profile = profile_resp[0]
        ratios = ratios_resp[0] if ratios_resp else {}
        cashflow = cashflow_resp[0] if cashflow_resp else {}

        result = {
            "ticker": ticker.upper(),
            "source": "FMP",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "company_name": profile.get("companyName"),
            "sector": profile.get("sector"),
            "market_cap": profile.get("mktCap"),
            "price": profile.get("price"),
            "pe_ratio": ratios.get("peRatioTTM"),
            "price_to_book": ratios.get("priceToBookRatioTTM"),
            "price_to_sales": ratios.get("priceToSalesRatioTTM"),
            "ev_to_ebitda": ratios.get("enterpriseValueMultipleTTM"),
            "gross_margin": ratios.get("grossProfitMarginTTM"),
            "operating_margin": ratios.get("operatingProfitMarginTTM"),
            "net_margin": ratios.get("netProfitMarginTTM"),
            "return_on_equity": ratios.get("returnOnEquityTTM"),
            "debt_to_equity": ratios.get("debtEquityRatioTTM"),
            "current_ratio": ratios.get("currentRatioTTM"),
            "free_cash_flow": cashflow.get("freeCashFlow"),
            "revenue": cashflow.get("netIncome"),
        }

        save_to_cache(cache_key, result)
        log_tool_call("get_fundamentals", ticker, "success", int((time.time() - start) * 1000))
        return result

    except Exception as e:
        log_tool_call("get_fundamentals", ticker, "error", int((time.time() - start) * 1000))
        return {"error": str(e), "ticker": ticker, "source": "FMP"}


if __name__ == "__main__":
    mcp.run()
