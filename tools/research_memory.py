import time
from memory.vector_store import save_research, search_research
from database.portfolio_db import log_tool_call


def search_my_research(query: str, ticker: str | None = None, n_results: int = 5) -> dict:
    """
    Semantic search over your personal research notes and investment theses.
    Optionally filter by ticker. Returns the most relevant passages.
    Source: ChromaDB (local vector store).
    """
    start = time.time()
    try:
        where = {"ticker": ticker.upper()} if ticker else None
        results = search_research(query=query, n_results=n_results, where=where)

        log_tool_call("search_my_research", ticker, "success", int((time.time() - start) * 1000))
        return {
            "query": query,
            "ticker_filter": ticker,
            "source": "ChromaDB",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "results": results,
        }

    except Exception as e:
        log_tool_call("search_my_research", ticker, "error", int((time.time() - start) * 1000))
        return {"error": str(e), "query": query, "source": "ChromaDB"}


def save_my_research(text: str, ticker: str, note_type: str = "thesis") -> dict:
    """
    Save a research note or investment thesis to the vector store.
    note_type: 'thesis', 'earnings_note', 'risk', 'general'
    """
    start = time.time()
    try:
        metadata = {"ticker": ticker.upper(), "note_type": note_type}
        save_research(text=text, metadata=metadata)
        log_tool_call("save_my_research", ticker, "success", int((time.time() - start) * 1000))
        return {"status": "saved", "ticker": ticker.upper(), "note_type": note_type}
    except Exception as e:
        log_tool_call("save_my_research", ticker, "error", int((time.time() - start) * 1000))
        return {"error": str(e), "ticker": ticker}
