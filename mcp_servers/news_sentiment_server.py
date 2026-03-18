import time
import finnhub
from mcp.server.fastmcp import FastMCP
from config.settings import FINNHUB_API_KEY
from database.portfolio_db import get_cached_result, save_to_cache, log_tool_call

mcp = FastMCP("news_sentiment")


@mcp.tool()
def get_news_and_sentiment(ticker: str) -> dict:
    """
    Fetch recent news headlines and an aggregated sentiment score for a stock.
    Returns the 10 most recent articles and a sentiment summary.
    Source: Finnhub API.
    """
    cache_key = f"news:{ticker.upper()}"
    cached = get_cached_result(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        client = finnhub.Client(api_key=FINNHUB_API_KEY)

        # Get company news (last 7 days)
        from datetime import datetime, timedelta
        today = datetime.utcnow().strftime("%Y-%m-%d")
        week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        news = client.company_news(ticker.upper(), _from=week_ago, to=today)

        # Get sentiment
        sentiment_data = client.news_sentiment(ticker.upper())

        # Summarise headlines
        headlines = [
            {
                "headline": article.get("headline"),
                "source": article.get("source"),
                "datetime": article.get("datetime"),
                "url": article.get("url"),
            }
            for article in (news or [])[:10]
        ]

        buzz = sentiment_data.get("buzz", {})
        sentiment = sentiment_data.get("sentiment", {})

        result = {
            "ticker": ticker.upper(),
            "source": "Finnhub",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "article_count": len(news or []),
            "headlines": headlines,
            "buzz_weekly_average": buzz.get("weeklyAverage"),
            "buzz_articles_in_last_week": buzz.get("articlesInLastWeek"),
            "sentiment_score": sentiment.get("bullishPercent"),
            "bearish_percent": sentiment.get("bearishPercent"),
            "sector_bullish_percent": sentiment_data.get("sectorAverageBullishPercent"),
        }

        save_to_cache(cache_key, result)
        log_tool_call("get_news_and_sentiment", ticker, "success", int((time.time() - start) * 1000))
        return result

    except Exception as e:
        log_tool_call("get_news_and_sentiment", ticker, "error", int((time.time() - start) * 1000))
        return {"error": str(e), "ticker": ticker, "source": "Finnhub"}


if __name__ == "__main__":
    mcp.run()
