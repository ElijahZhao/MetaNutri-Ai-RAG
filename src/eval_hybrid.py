"""Vector-only vs hybrid (BM25+vector) comparison on the 50-case eval set.

Run: python3 src/eval_hybrid.py   (writes data/hybrid_report.json)
Measures retrieval hit rate + faithfulness (needs LLM calls for hybrid answers).
"""
import json
import os
import sys
import time

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
load_dotenv(".env")

from src.evaluation import has_key_info, norm
from src.generation import Generator, extract_citations
from src.hybrid import HybridRetriever
from src.retrieval import Retriever

EVAL_FILE = "data/eval_questions.json"
REPORT_FILE = "data/hybrid_report.json"


def run(mode, questions, retriever, generator, top_k=6):
    agg = {"hit": [0, 0], "cite": [0, 0], "cover": [0, 0], "faith": [0, 0]}
    per_item = []
    for it in questions:
        q, gold, kw, cat = it["question"], it["gold"], it["source_keyword"], it["category"]
        gk = it.get("gold_key", "")
        hits = retriever.search(q, top_k=top_k) if hasattr(retriever, "search") else retriever(q, top_k)
        hit = any(norm(kw) in norm(h["text"]) for h in hits)
        ans = generator.answer(q, hits)
        cites = extract_citations(ans)
        cite_ok = len(cites) > 0 and all(1 <= c <= len(hits) for c in cites)
        covered = has_key_info(ans, gold, kw, gk)
        for key, ok in (("hit", hit), ("cite", cite_ok), ("cover", covered),
                        ("faith", cite_ok and covered)):
            agg[key][1] += 1
            agg[key][0] += int(ok)
        per_item.append({"id": it["id"], "hit": hit, "faithful": cite_ok and covered})
    return {
        "mode": mode,
        "retrieval_hit_rate": round(agg["hit"][0] / agg["hit"][1], 4),
        "citation_rate": round(agg["cite"][0] / agg["cite"][1], 4),
        "gold_cover_rate": round(agg["cover"][0] / agg["cover"][1], 4),
        "faithfulness": round(agg["faith"][0] / agg["faith"][1], 4),
        "items": per_item,
    }


def main():
    questions = json.load(open(EVAL_FILE, encoding="utf-8"))
    generator = Generator()

    t0 = time.time()
    vec = Retriever()
    row_vec = run("vector", questions, vec, generator)
    print("vector done", round(time.time() - t0, 1), "s", flush=True)

    t0 = time.time()
    hyb = HybridRetriever()
    row_hyb = run("hybrid", questions, hyb, generator)
    print("hybrid done", round(time.time() - t0, 1), "s", flush=True)

    report = {
        "summary": {
            "vector": {k: row_vec[k] for k in ("retrieval_hit_rate", "citation_rate", "gold_cover_rate", "faithfulness")},
            "hybrid": {k: row_hyb[k] for k in ("retrieval_hit_rate", "citation_rate", "gold_cover_rate", "faithfulness")},
        },
        "rows": [row_vec, row_hyb],
    }
    json.dump(report, open(REPORT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n=== HYBRID COMPARISON ===")
    print("vector:", report["summary"]["vector"])
    print("hybrid:", report["summary"]["hybrid"])


if __name__ == "__main__":
    main()
