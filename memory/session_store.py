import json
import os
import anthropic
from datetime import datetime
from config.settings import ANTHROPIC_API_KEY, EVAL_MODEL
from memory.vector_store import save_research

_SESSION_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sessions")


def _ensure_session_dir() -> None:
    os.makedirs(_SESSION_DIR, exist_ok=True)


def save_session(messages: list[dict], session_id: str | None = None) -> str:
    """
    Save a conversation session to disk and auto-summarise it into ChromaDB.
    Returns the session_id.
    """
    _ensure_session_dir()
    if session_id is None:
        session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    session_path = os.path.join(_SESSION_DIR, f"{session_id}.json")
    with open(session_path, "w") as f:
        json.dump({"session_id": session_id, "messages": messages}, f, indent=2)

    # Auto-summarise into ChromaDB
    try:
        summary = _summarise_session(messages)
        save_research(
            text=summary,
            metadata={"session_id": session_id, "note_type": "session_summary"},
        )
    except Exception:
        pass  # Don't fail session save if summarisation fails

    return session_id


def load_session(session_id: str) -> list[dict]:
    """Load messages from a saved session."""
    session_path = os.path.join(_SESSION_DIR, f"{session_id}.json")
    if not os.path.exists(session_path):
        return []
    with open(session_path, "r") as f:
        data = json.load(f)
    return data.get("messages", [])


def list_sessions() -> list[str]:
    """Return all saved session IDs sorted by most recent."""
    _ensure_session_dir()
    files = [f.replace(".json", "") for f in os.listdir(_SESSION_DIR) if f.endswith(".json")]
    return sorted(files, reverse=True)


def _summarise_session(messages: list[dict]) -> str:
    """Use Claude Haiku to produce a concise summary of the conversation."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    conversation_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages if isinstance(m.get("content"), str)
    )
    response = client.messages.create(
        model=EVAL_MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    "Summarise this investment research conversation in 3-5 bullet points. "
                    "Focus on: stocks discussed, key findings, decisions made.\n\n"
                    f"{conversation_text}"
                ),
            }
        ],
    )
    return response.content[0].text
