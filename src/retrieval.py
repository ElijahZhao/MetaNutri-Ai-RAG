"""Retrieval module: query ChromaDB vector store, return top-k chunks.

Run from repo root: python3 -m src.retrieval  (self-test)
"""
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
load_dotenv(".env")

import chromadb
from openai import OpenAI

from src.config import CHROMA_DIR, COLLECTION, DASHSCOPE_BASE, EMB_MODEL, TOP_K


class Retriever:
    def __init__(self, top_k: int = TOP_K):
        self.top_k = top_k
        self._client = OpenAI(
            api_key=os.environ["DASHSCOPE_API_KEY"], base_url=DASHSCOPE_BASE
        )
        db = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = db.get_collection(COLLECTION)

    def embed(self, text: str) -> list:
        try:
            r = self._client.embeddings.create(model=EMB_MODEL, input=text)
        except Exception as e:  # network / auth / quota failures surface readably
            raise RuntimeError(
                f"embedding API 调用失败（{type(e).__name__}）：{e}"
            ) from e
        return r.data[0].embedding

    def search(self, query: str, top_k: int | None = None, min_score: float | None = None) -> list[dict]:
        """Balanced two-path retrieval: food and guideline chunks are queried
        separately with equal quota, so neither type can squeeze the other out
        (food ~325 vs guideline ~9 would otherwise dominate).

        min_score: drop chunks below this cosine similarity (None = no threshold).
        """
        k = top_k or self.top_k
        emb = self.embed(query)
        food_k = max((k + 1) // 2, 1)
        # keep guide_k >= 1: ChromaDB rejects n_results=0 when k==1
        guide_k = max(k - food_k, 1)

        food = self.collection.query(
            query_embeddings=[emb], n_results=food_k, where={"type": "food"}
        )
        guide = self.collection.query(
            query_embeddings=[emb], n_results=guide_k, where={"type": "guideline"}
        )

        merged, seen = [], set()
        for block in (food, guide):
            for doc, dist, meta in zip(
                block["documents"][0], block["distances"][0], block["metadatas"][0]
            ):
                if doc in seen:
                    continue
                seen.add(doc)
                score = round(1 - dist, 4)
                if min_score is not None and score < min_score:
                    continue
                merged.append({"text": doc, "score": score, "type": meta.get("type")})
                if len(merged) >= k:
                    return merged
        return merged


if __name__ == "__main__":
    r = Retriever()
    for q in sys.argv[1:] or ["每天应该吃多少蔬菜水果？"]:
        print(f"\nQ: {q}")
        for hit in r.search(q):
            first = hit["text"].strip().split("\n")[0]
            print(f"  [{hit['score']}] {first}")
