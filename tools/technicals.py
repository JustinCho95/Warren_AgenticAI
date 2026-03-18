import time
import pandas as pd
import yfinance as yf
from database.portfolio_db import get_cached_result, save_to_cache, log_tool_call


def get_technical_signals(ticker: str) -> dict:
    """
    Compute technical indicators for a stock:
    RSI(14), MACD, MA50, MA200, current price, 52-week high/low.
    Uses yfinance for price history — no API key required.
    """
    cache_key = f"technicals:{ticker.upper()}"
    cached = get_cached_result(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)

        if df.empty:
            raise ValueError(f"No price data returned for {ticker}")

        close = df["Close"].squeeze()

        # RSI(14)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = float((100 - 100 / (1 + rs)).iloc[-1])

        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd = float(macd_line.iloc[-1])
        macd_signal = float(signal_line.iloc[-1])
        macd_histogram = round(macd - macd_signal, 4)

        # Moving averages
        ma50 = float(close.rolling(50).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])
        current_price = float(close.iloc[-1])

        # 52-week range
        high_52w = float(close.max())
        low_52w = float(close.min())
        pct_from_high = round((current_price - high_52w) / high_52w * 100, 2)

        # Trend signal
        if current_price > ma50 > ma200:
            trend = "bullish"
        elif current_price < ma50 < ma200:
            trend = "bearish"
        else:
            trend = "mixed"

        result = {
            "ticker": ticker.upper(),
            "source": "yfinance",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "price": round(current_price, 2),
            "ma50": round(ma50, 2),
            "ma200": round(ma200, 2),
            "rsi_14": round(rsi, 2),
            "macd": round(macd, 4),
            "macd_signal": round(macd_signal, 4),
            "macd_histogram": macd_histogram,
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "pct_from_52w_high": pct_from_high,
            "trend": trend,
        }

        save_to_cache(cache_key, result)
        log_tool_call("get_technical_signals", ticker, "success", int((time.time() - start) * 1000))
        return result

    except Exception as e:
        log_tool_call("get_technical_signals", ticker, "error", int((time.time() - start) * 1000))
        return {"error": str(e), "ticker": ticker, "source": "yfinance"}
