import time
from mcp.server.fastmcp import FastMCP
from database.portfolio_db import get_cached_result, save_to_cache, log_tool_call, init_db, _get_connection

mcp = FastMCP("portfolio")


@mcp.tool()
def get_portfolio_analysis() -> dict:
    """
    Return the current portfolio: all holdings with cost basis, current price,
    unrealised P&L, and sector allocation breakdown.
    Source: Local SQLite database (manually maintained in Phase 1; Questrade live feed in Phase 2).
    """
    cache_key = "portfolio:all"
    cached = get_cached_result(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        init_db()
        with _get_connection() as conn:
            rows = conn.execute("SELECT * FROM positions").fetchall()

        positions = [dict(row) for row in rows]

        # Sector breakdown
        sector_map: dict[str, int] = {}
        for p in positions:
            sector = p.get("sector") or "Unknown"
            sector_map[sector] = sector_map.get(sector, 0) + 1

        result = {
            "source": "SQLite (local)",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "position_count": len(positions),
            "positions": positions,
            "sector_allocation": sector_map,
        }

        save_to_cache(cache_key, result)
        log_tool_call("get_portfolio_analysis", None, "success", int((time.time() - start) * 1000))
        return result

    except Exception as e:
        log_tool_call("get_portfolio_analysis", None, "error", int((time.time() - start) * 1000))
        return {"error": str(e), "source": "SQLite"}


if __name__ == "__main__":
    mcp.run()
