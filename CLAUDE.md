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

| Tool | File | What it does | API |
|---|---|---|---|
| get_fundamentals | tools/fundamentals.py | P/E, margins, FCF, debt, valuation | FMP |
| get_news_and_sentiment | tools/news_sentiment.py | Recent news + sentiment score | Finnhub |
| get_technical_signals | tools/technicals.py | RSI, MACD, MA50/200, 52-week range | yfinance |
| get_earnings_summary | tools/earnings.py | Last 4 quarters, beat/miss rate | FMP |
| search_my_research | tools/research_memory.py | RAG over personal notes and theses | ChromaDB |
| get_portfolio_analysis | tools/portfolio.py | Live holdings, P&L, sector allocation | Questrade + SQLite |
| get_smart_money | tools/smart_money.py | 13F institutional holdings + overlap | FMP + EDGAR |

---

## Folder Structure
```
warren/
├── .env                          # API keys — never commit
├── requirements.txt
├── main.py                       # CLI entry point
├── CLAUDE.md                     # This file
├── config/
│   └── settings.py               # All constants, model names, API keys, weights
├── data/
│   ├── warren.db                 # SQLite — portfolio, audit log, cache, scores
│   └── chroma/                   # ChromaDB vector store
├── database/
│   ├── schema.sql                # All table definitions
│   └── portfolio_db.py           # CRUD — positions, cache, audit log, scores
├── tools/                        # One file per tool — plain Python in Phase 1
├── agents/
│   ├── orchestrator.py           # Main ReAct agent loop
│   └── evaluator.py              # Claude-as-judge scoring
├── memory/
│   ├── vector_store.py           # ChromaDB read/write wrapper
│   └── session_store.py          # Conversation history management
├── prompts/
│   └── system_prompt.py          # System prompt builder
├── mcp_servers/                  # Phase 2 — MCP wrappers for each tool
├── dashboard/                    # Phase 2 — Streamlit UI
└── evals/
    ├── test_cases.json           # Ground truth Q&A for eval suite
    └── run_evals.py              # Batch eval runner
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
| Phase 1 | All 7 tools as plain Python, SQLite layer, CLI orchestrator, basic eval |
| Phase 2 | MCP servers wrapping all tools, Questrade integration, Streamlit dashboard |
| Phase 3 | Multi-agent architecture, parallel subagents via LangGraph |
| Phase 4 | Portfolio scorer, email composer, Gmail MCP, automated reports |
| Phase 5 | Full conversation memory RAG, email history RAG, Files API, DCF modelling |

**Current status: Phase 1 — not yet started**

---

## Current Progress

- [x] Repo created
- [x] Visual Studio setup
- [x] Claude Code setup
- [ ] Folder structure created
- [ ] Virtual environment set up
- [ ] All packages installed
- [ ] API keys configured in .env
- [ ] config/settings.py
- [ ] database/schema.sql
- [ ] database/portfolio_db.py
- [ ] tools/fundamentals.py
- [ ] tools/news_sentiment.py
- [ ] tools/technicals.py
- [ ] tools/earnings.py
- [ ] tools/research_memory.py
- [ ] tools/portfolio.py
- [ ] tools/smart_money.py
- [ ] agents/orchestrator.py
- [ ] agents/evaluator.py
- [ ] prompts/system_prompt.py
- [ ] main.py