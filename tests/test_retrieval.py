"""Retrieval merge logic tests (collection & embed mocked, no API)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.retrieval import Retriever  # noqa: E402


def _mock_retriever(blocks):
    """blocks: dict {type: [{'text':..., 'score':..., 'type':...}]} for query result."""
    collection = MagicMock()

    def query(query_embeddings, n_results, where=None):
        if where is None:
            key = "all"
        else:
            key = where["type"]
        items = blocks[key][:n_results]
        return {
            "documents": [[i["text"] for i in items]],
            "distances": [[1 - i["score"] for i in items]],
            "metadatas": [[{"type": i["type"]} for i in items]],
        }

    collection.query.side_effect = query
    r = Retriever.__new__(Retriever)
    r.top_k = 6
    r.collection = collection
    r.embed = MagicMock(return_value=[0.1] * 8)
    return r


def test_balanced_quota_and_merge():
    r = _mock_retriever({
        "all": [
            {"text": f"food{i}", "score": 0.9 - i * 0.01, "type": "food"} for i in range(8)
        ],
        "food": [
            {"text": f"food{i}", "score": 0.9 - i * 0.01, "type": "food"} for i in range(8)
        ],
        "guideline": [
            {"text": "g0", "score": 0.5, "type": "guideline"},
            {"text": "g1", "score": 0.4, "type": "guideline"},
            {"text": "g2", "score": 0.3, "type": "guideline"},
        ],
    })
    hits = r.search("query")
    assert len(hits) == 6  # capped at top_k
    texts = [h["text"] for h in hits]
    # guideline path is guaranteed even though its scores are lower
    assert "g0" in texts and "g1" in texts and "g2" in texts
    # food path fills the remaining quota
    assert texts[0] == "food0"


def test_merge_dedup():
    """A chunk appearing in both paths appears once."""
    r = _mock_retriever({
        "all": [{"text": "dup", "score": 0.9, "type": "food"},
                {"text": "f1", "score": 0.8, "type": "food"}],
        "food": [{"text": "dup", "score": 0.9, "type": "food"},
                 {"text": "f1", "score": 0.8, "type": "food"}],
        "guideline": [{"text": "dup", "score": 0.7, "type": "guideline"}],
    })
    hits = r.search("query")
    texts = [h["text"] for h in hits]
    assert len(texts) == len(set(texts))
    assert texts.count("dup") == 1
