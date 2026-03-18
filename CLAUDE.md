# Warren 2.0 — Claude-Native Investment Research Agent

## What Warren Is
Warren is a personal AI investment research agent built for long-term fundamental investing.
It connects to your live Questrade portfolio, researches stocks using real financial APIs,
tracks what top institutional investors are doing, remembers every conversation, and sends
automated email reports with Buy/Hold/Sell scores for every holding.

This is NOT a chatbot with web search. Every number comes from structured financial APIs
with source citations and timestamps.

---

## Architecture Overview
```
User Interfaces (Streamlit chat, portfolio view, smart money view, email reports)
        ↓
Agent Layer (Orchestrator, Scheduler, Portfolio Scorer, Email Composer, Evaluator)
        ↓
Parallel Subagents (Research, News, Technical, Risk, Smart Money — run simultaneously)
        ↓
MCP Server Layer (Questrade, Gmail, Market Data, Earnings, Smart Money, Memory, Portfolio)
        ↓
Memory & RAG Layer (Conversation memory, Research notes, Email history, Frameworks, SQLite)
        ↓
Claude Capabilities (Extended Thinking, Citations API, Prompt Caching, Batch API, Files API)
        ↓
External Data Sources (Questrade API, FMP, Finnhub, yfinance, SEC EDGAR, Gmail)
```

---

## The 7 Tools

### MCP Servers (external API integrations — standalone, reusable)

| Tool | File | What it does | API |
|---|---|---|---|
| get_fundamentals | mcp_servers/fundamentals_server.py | P/E, margins, FCF, debt, valuation | FMP |
| get_news_and_sentiment | mcp_servers/news_sentiment_server.py | Recent news + sentiment score | Finnhub |
| get_earnings_summary | mcp_servers/earnings_server.py | Last 4 quarters, beat/miss rate | FMP |
| get_smart_money | mcp_servers/smart_money_server.py | 13F institutional holdings + overlap | FMP + EDGAR |
| get_portfolio_analysis | mcp_servers/portfolio_server.py | Live holdings, P&L, sector allocation | Questrade + SQLite |

### Plain Python Tools (internal/local — tightly coupled to Warren)

| Tool | File | What it does | API |
|---|---|---|---|
| get_technical_signals | tools/technicals.py | RSI, MACD, MA50/200, 52-week range | yfinance |
| search_my_research | tools/research_memory.py | RAG over personal notes and theses | ChromaDB |

---

## Folder Structure
```
warren/
├── .env                          # API keys — never commit to git
├── requirements.txt              # All Python packages — pip install -r requirements.txt
├── main.py                       # CLI entry point only — no business logic
├── CLAUDE.md                     # This file
│
├── config/
│   └── settings.py               # Single source of truth for all constants:
│                                 #   model names, thinking budgets, scoring weights,
│                                 #   API base URLs, cache TTL, DB paths, watchlist CIKs
│
├── data/
│   ├── warren.db                 # SQLite DB — created at runtime (not a placeholder)
│   │                             #   tables: positions, cache, audit_log, scores
│   └── chroma/                   # ChromaDB vector files — written at runtime
│                                 #   stores embeddings of your research notes
│
├── database/
│   ├── schema.sql                # Raw SQL table definitions for warren.db
│   └── portfolio_db.py           # All SQLite read/write functions:
│                                 #   get_cached_result(), save_to_cache(),
│                                 #   log_tool_call(), save_score()
│
├── tools/                        # Plain Python tools — called directly by orchestrator
│   ├── technicals.py             # RSI, MACD, MA50/200, 52-week range via yfinance
│   │                             #   (plain tool because yfinance is a Python lib, not REST)
│   └── research_memory.py        # Semantic search over your personal notes via ChromaDB
│                                 #   (plain tool because it's internal to Warren)
│
├── agents/
│   ├── orchestrator.py           # Warren's brain — ReAct loop:
│   │                             #   receives question → picks tools → calls them →
│   │                             #   reasons over results → returns structured answer
│   └── evaluator.py              # Separate Claude-as-judge instance (uses Haiku)
│                                 #   scores orchestrator answers for accuracy/completeness
│
├── memory/
│   ├── vector_store.py           # ChromaDB wrapper:
│   │                             #   save_research(text, metadata) — embeds and stores
│   │                             #   search_research(query) — semantic similarity search
│   └── session_store.py          # Conversation history management:
│                                 #   saves each session (auto-summarised by Claude),
│                                 #   retrieves past context across sessions
│
├── prompts/
│   └── system_prompt.py          # Builds Warren's system prompt dynamically each call:
│                                 #   injects current portfolio, date, holdings,
│                                 #   investing philosophy, and scoring framework
│
├── mcp_servers/                  # Standalone MCP servers — Claude calls these as native tools
│   ├── fundamentals_server.py    # FMP API → get_fundamentals tool
│   │                             #   returns: P/E, margins, FCF, debt, valuation
│   ├── news_sentiment_server.py  # Finnhub API → get_news_and_sentiment tool
│   │                             #   returns: headlines + aggregated sentiment score
│   ├── earnings_server.py        # FMP API → get_earnings_summary tool
│   │                             #   returns: last 4 quarters EPS actual vs estimate, beat/miss rate
│   ├── smart_money_server.py     # FMP + EDGAR → get_smart_money tool
│   │                             #   returns: 13F filings for watchlist funds (buys/sells/holds)
│   └── portfolio_server.py       # Questrade + SQLite → get_portfolio_analysis tool
│                                 #   returns: live holdings, cost basis, P&L, sector allocation
│
├── dashboard/                    # Phase 2 — Streamlit UI (empty for now)
│
└── evals/
    ├── test_cases.json           # Ground truth Q&A pairs for benchmarking Warren
    └── run_evals.py              # Runs Warren against all test cases, scores via evaluator,
                                  #   prints pass/fail report to measure quality over time
```

---

## Key Conventions — Always Follow These

**API calls**
- Always check SQLite cache before making any API call (24hr TTL)
- Always return a dict with `source`, `fetched_at`, and `ticker` fields
- Wrap every external call in try/except and return `{"error": str(e)}` on failure
- Never hardcode API keys — always import from config/settings.py

**Claude integration**
- ORCHESTRATOR_MODEL = claude-sonnet-4-6
- EVAL_MODEL = claude-haiku-4-5-20251001
- Simple queries → Haiku, no extended thinking
- Analysis queries → Sonnet, 8000 token thinking budget
- Decision queries → Sonnet, 16000 token thinking budget
- Always enable interleaved thinking for decision queries
- Every tool result must be logged to audit_log in SQLite

**Memory**
- Every session must be auto-summarised and saved to ChromaDB after completion
- Always query search_my_research before answering any stock question
- Conversation history passed in full on every Claude API call — no truncation

**Code style**
- snake_case for all function and variable names
- Type hints on all function signatures
- One tool per file in tools/
- No business logic in main.py — it is CLI only

---

## Data Sources

| Source | Used for | Free tier |
|---|---|---|
| FMP API (financialmodelingprep.com) | Fundamentals, earnings, 13F | 250 req/day |
| Finnhub (finnhub.io) | News, sentiment | 60 req/min |
| yfinance | Price history, technicals | Unlimited |
| edgartools | SEC EDGAR 13F filings | Unlimited |
| Questrade API | Live portfolio (Phase 2) | Free with account |
| Gmail MCP | Email delivery (Phase 4) | Free with Google account |

---

## Portfolio Scoring Weights (Buy/Hold/Sell Engine)

| Signal | Weight |
|---|---|
| Fundamentals | 30% |
| Earnings trajectory | 25% |
| News sentiment | 20% |
| Smart money positioning | 15% |
| Technical trend | 10% |

Score maps to: **Strong Buy → Buy → Hold → Watch → Sell**

---

## Smart Money Watchlist
```python
WATCHLIST_FUNDS = {
    "Berkshire Hathaway": "0001067983",
    "Pershing Square":    "0001336528",
    "Pabrai Funds":       "0001173334",
    "ARK Invest":         "0001579982",
    "Appaloosa":          "0001029390",
}
```

---

## Build Phases

| Phase | What gets built |
|---|---|
| Phase 1 | 5 MCP servers (external APIs) + 2 plain tools (internal), SQLite layer, CLI orchestrator, basic eval |
| Phase 2 | Questrade integration, Streamlit dashboard (chat, portfolio view, smart money view) |
| Phase 3 | Multi-agent architecture, parallel subagents via LangGraph |
| Phase 4 | Portfolio scorer, email composer, Gmail MCP, automated reports |
| Phase 5 | Full conversation memory RAG, email history RAG, Files API, DCF modelling |

**Current status: Phase 1 — complete**

---

## Current Progress

- [x] Repo created
- [x] Visual Studio setup
- [x] Claude Code setup
- [x] Folder structure created
- [x] Virtual environment set up
- [x] All packages installed
- [x] API keys configured in .env
- [x] config/settings.py
- [x] database/schema.sql
- [x] database/portfolio_db.py
- [x] mcp_servers/fundamentals_server.py
- [x] mcp_servers/news_sentiment_server.py
- [x] mcp_servers/earnings_server.py
- [x] mcp_servers/smart_money_server.py
- [x] mcp_servers/portfolio_server.py
- [x] tools/technicals.py
- [x] tools/research_memory.py
- [x] agents/orchestrator.py
- [x] agents/evaluator.py
- [x] prompts/system_prompt.py
- [x] main.py