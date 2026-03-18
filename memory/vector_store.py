import chromadb
from chromadb.utils import embedding_functions
from config.settings import CHROMA_PATH

_client: chromadb.PersistentClient | None = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        ef = embedding_functions.DefaultEmbeddingFunction()
        _collection = _client.get_or_create_collection(
            name="warren_research",
            embedding_function=ef,
        )
    return _collection


def save_research(text: str, metadata: dict) -> None:
    """Embed and store a research note."""
    import uuid
    collection = _get_collection()
    doc_id = str(uuid.uuid4())
    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id],
    )


def search_research(query: str, n_results: int = 5, where: dict | None = None) -> list[dict]:
    """Semantic search over stored research notes."""
    collection = _get_collection()
    kwargs = {
        "query_texts": [query],
        "n_results": min(n_results, collection.count() or 1),
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        output.append({
            "text": doc,
            "metadata": meta,
            "relevance_score": round(1 - dist, 4),
        })

    return output
