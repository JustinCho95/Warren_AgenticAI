import json
import anthropic
from config.settings import ANTHROPIC_API_KEY, ORCHESTRATOR_MODEL, THINKING_BUDGET_ANALYSIS, THINKING_BUDGET_DECISION
from prompts.system_prompt import build_system_prompt
from memory.session_store import save_session
from database.portfolio_db import init_db

# Tool imports
from mcp_servers.fundamentals_server import get_fundamentals
from mcp_servers.news_sentiment_server import get_news_and_sentiment
from mcp_servers.earnings_server import get_earnings_summary
from mcp_servers.smart_money_server import get_smart_money
from mcp_servers.portfolio_server import get_portfolio_analysis
from tools.technicals import get_technical_signals
from tools.research_memory import search_my_research, save_my_research

# Tool definitions for Claude
TOOLS = [
    {
        "name": "get_fundamentals",
        "description": "Fetch P/E ratio, margins, FCF, debt, and valuation ratios for a stock. Source: FMP.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_news_and_sentiment",
        "description": "Fetch recent news headlines and aggregated sentiment score for a stock. Source: Finnhub.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_earnings_summary",
        "description": "Fetch last 4 quarters of EPS actual vs estimate, beat/miss rate. Source: FMP.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_smart_money",
        "description": "Check if Berkshire, Pershing Square, ARK, Pabrai, Appaloosa hold this stock. Source: FMP 13F.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_portfolio_analysis",
        "description": "Return current portfolio holdings, cost basis, P&L, and sector allocation.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_technical_signals",
        "description": "Compute RSI, MACD, MA50/200, 52-week range, and trend for a stock. Source: yfinance.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "search_my_research",
        "description": "Semantic search over personal research notes and investment theses. Always call this first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "ticker": {"type": "string", "description": "Optional ticker filter"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_my_research",
        "description": "Save a research note or investment thesis to the personal vector store.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "ticker": {"type": "string"},
                "note_type": {
                    "type": "string",
                    "enum": ["thesis", "earnings_note", "risk", "general"],
                    "description": "Type of research note",
                },
            },
            "required": ["text", "ticker"],
        },
    },
]

TOOL_MAP = {
    "get_fundamentals": get_fundamentals,
    "get_news_and_sentiment": get_news_and_sentiment,
    "get_earnings_summary": get_earnings_summary,
    "get_smart_money": get_smart_money,
    "get_portfolio_analysis": lambda: get_portfolio_analysis(),
    "get_technical_signals": get_technical_signals,
    "search_my_research": search_my_research,
    "save_my_research": save_my_research,
}


def _is_decision_query(question: str) -> bool:
    decision_keywords = ["buy", "sell", "hold", "should i", "recommend", "score", "rating"]
    return any(kw in question.lower() for kw in decision_keywords)


def run(question: str, history: list[dict] | None = None) -> str:
    """
    Main ReAct loop. Takes a question and conversation history,
    calls tools as needed, and returns Warren's final answer.
    """
    init_db()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Load portfolio for system prompt
    try:
        portfolio = get_portfolio_analysis()
    except Exception:
        portfolio = None

    system = build_system_prompt(portfolio)
    messages = list(history or [])
    messages.append({"role": "user", "content": question})

    # Choose thinking budget based on query type
    thinking_budget = (
        THINKING_BUDGET_DECISION if _is_decision_query(question) else THINKING_BUDGET_ANALYSIS
    )

    # ReAct loop — max 10 iterations to prevent infinite loops
    for _ in range(10):
        response = client.messages.create(
            model=ORCHESTRATOR_MODEL,
            max_tokens=thinking_budget + 4096,
            thinking={"type": "enabled", "budget_tokens": thinking_budget},
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        # If no tool calls, we have the final answer
        if response.stop_reason == "end_turn":
            break

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            tool_fn = TOOL_MAP.get(tool_name)

            if tool_fn is None:
                result = {"error": f"Unknown tool: {tool_name}"}
            else:
                try:
                    result = tool_fn(**tool_input)
                except Exception as e:
                    result = {"error": str(e)}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": tool_results})

    # Extract final text answer
    final_answer = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_answer = block.text
            break

    # Save session in background
    try:
        save_session(messages)
    except Exception:
        pass

    return final_answer
