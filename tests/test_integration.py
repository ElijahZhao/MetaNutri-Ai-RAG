"""Live integration smoke test (requires DASHSCOPE_API_KEY; skipped in CI)."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

pytestmark = pytest.mark.skipif(
    not os.environ.get("DASHSCOPE_API_KEY"),
    reason="DASHSCOPE_API_KEY not set (CI: skipped; local: run with .env)",
)


def test_end_to_end_qa():
    from src.generation import Generator, extract_citations
    from src.retrieval import Retriever

    r, g = Retriever(), Generator()
    hits = r.search("每100克鸡蛋含多少蛋白质？", top_k=6)
    assert hits
    ans = g.answer("每100克鸡蛋含多少蛋白质？", hits)
    cites = extract_citations(ans)
    assert cites and all(1 <= c <= len(hits) for c in cites)
    assert "13.3" in ans or "13" in ans
