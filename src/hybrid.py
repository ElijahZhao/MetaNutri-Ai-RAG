"""Hybrid retrieval: BM25 (char-bigram, zero-dependency) fused with vector search via RRF.

Run from repo root: python3 -m src.hybrid  (self-test)
Comparison (vector-only vs hybrid) on the 50-case eval set: python3 src/eval_hybrid.py
"""
import math
import os
import re
import sys
from collections import Counter

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
load_dotenv(".env")

import chromadb

from src.config import CHROMA_DIR, COLLECTION

BIGRAM_RE = re.compile(r"[\u4e00-\u9fa5a-zA-Z0-9]")


def bigrams(text: str) -> list[str]:
    """Lowercased character bigrams of CJK/ASCII runs (space-separated words pass through)."""
    text = text.lower()
    toks = []
    for m in BIGRAM_RE.findall(text):
        toks.append(m)
    out = []
    for i in range(len(toks) - 1):
        out.append(toks[i] + toks[i + 1])
    return out


class BM25Index:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.n = len(docs)
        self.avgdl = sum(len(bigrams(d)) for d in docs) / max(self.n, 1)
        df = Counter()
        for d in docs:
            df.update(set(bigrams(d)))
        self.idf = {
            t: math.log(1 + (self.n - f + 0.5) / (f + 0.5))
            for t, f in df.items()
        }
        self.k1, self.b = k1, b

    def score(self, query: str, doc: str) -> float:
        q_toks = bigrams(query)
        if not q_toks:
            return 0.0
        dl = len(bigrams(doc))
        tf = Counter(bigrams(doc))
        score = 0.0
        for t in set(q_toks):
            f = tf.get(t, 0)
            if f == 0 or t not in self.idf:
                continue
            score += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return score

    def rank(self, query: str, limit: int | None = None) -> list[tuple[int, float]]:
        scored = [(i, self.score(query, d)) for i, d in enumerate(self.docs)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit] if limit else scored


def rrf_fuse(ranked_lists: list[list[tuple[int, float]]], k: int = 60) -> dict[int, float]:
    fused: dict[int, float] = {}
    for lst in ranked_lists:
        for rank, (doc_id, _score) in enumerate(lst):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return fused


class HybridRetriever:
    """BM25 + vector fusion. Keeps balanced food/guideline quota on the vector side,
    then fuses with BM25 via RRF and returns top-k."""

    def __init__(self, alpha: float = 0.5, top_k: int = 6):
        self.alpha = alpha
        self.top_k = top_k
        db = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = db.get_collection(COLLECTION)
        data = self.collection.get()
        self.docs: list[str] = data["documents"]
        self.metas: list[dict] = data["metadatas"]
        self.bm25 = BM25Index(self.docs)

        from src.retrieval import Retriever
        self._vec = Retriever(top_k=top_k)

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        k = top_k or self.top_k
        cand = max(k * 4, 20)  # fusion candidate pool: stable against k
        vec_hits = self._vec.search(query, top_k=cand)
        vec_ranked = [(self.docs.index(h["text"]), h["score"]) for h in vec_hits]
        bm_ranked = self.bm25.rank(query, limit=cand)
        fused = rrf_fuse([vec_ranked, bm_ranked])
        order = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
        out = []
        for doc_id, _ in order:
            out.append({
                "text": self.docs[doc_id],
                "score": round(fused[doc_id], 4),
                "type": self.metas[doc_id].get("type"),
            })
        return out


if __name__ == "__main__":
    h = HybridRetriever()
    for q in sys.argv[1:] or ["每天应该吃多少蔬菜水果？"]:
        print(f"\nQ: {q}")
        for hit in h.search(q):
            print(f"  [{hit['score']}] {hit['text'].strip().split(chr(10))[0][:50]}")
