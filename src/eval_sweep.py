"""Hyper-parameter sweep: top-k x similarity threshold on the 50-case eval set.

Run: python3 src/eval_sweep.py   (writes data/sweep_report.json)
Grid: top_k in {3,5,8} x min_score in {0.2,0.35,0.5} = 9 runs x 50 questions.
For each run we measure: retrieval hit rate, citation rate, gold-info coverage
and faithfulness (rule-based, same as src/evaluation.py).
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
from src.retrieval import Retriever

EVAL_FILE = "data/eval_questions.json"
REPORT_FILE = "data/sweep_report.json"

TOP_KS = [3, 5, 8]
THRESHOLDS = [0.2, 0.35, 0.5]


def run_grid(top_k: int, min_score: float, questions, retriever, generator):
    agg = {"hit": [0, 0], "cite": [0, 0], "cover": [0, 0], "faith": [0, 0]}
    empty_ctx = 0
    for it in questions:
        q, gold, kw, cat = it["question"], it["gold"], it["source_keyword"], it["category"]
        gk = it.get("gold_key", "")
        hits = retriever.search(q, top_k=top_k, min_score=min_score)
        if not hits:
            empty_ctx += 1
        hit = any(norm(kw) in norm(h["text"]) for h in hits)
        ans = generator.answer(q, hits)
        cites = extract_citations(ans)
        cite_ok = len(cites) > 0 and all(1 <= c <= len(hits) for c in cites)
        covered = has_key_info(ans, gold, kw, gk)
        for key, ok in (("hit", hit), ("cite", cite_ok), ("cover", covered),
                        ("faith", cite_ok and covered)):
            agg[key][1] += 1
            agg[key][0] += int(ok)
    return {
        "top_k": top_k, "min_score": min_score,
        "retrieval_hit_rate": round(agg["hit"][0] / agg["hit"][1], 4),
        "citation_rate": round(agg["cite"][0] / agg["cite"][1], 4),
        "gold_cover_rate": round(agg["cover"][0] / agg["cover"][1], 4),
        "faithfulness": round(agg["faith"][0] / agg["faith"][1], 4),
        "empty_context_cases": empty_ctx,
    }


def main():
    questions = json.load(open(EVAL_FILE, encoding="utf-8"))
    retriever = Retriever()
    generator = Generator()
    rows = []
    total = len(TOP_KS) * len(THRESHOLDS)
    n = 0
    for k in TOP_KS:
        for th in THRESHOLDS:
            t0 = time.time()
            row = run_grid(k, th, questions, retriever, generator)
            row["seconds"] = round(time.time() - t0, 1)
            rows.append(row)
            n += 1
            print(f"[{n}/{total}] top_k={k} threshold={th}: {row}", flush=True)
    report = {
        "grid": {"top_k": TOP_KS, "min_score": THRESHOLDS},
        "current_defaults": {"top_k": 6, "min_score": None},
        "rows": rows,
        "summary": {
            "best_faithfulness": max(r["faithfulness"] for r in rows),
            "best_config_by_faithfulness": max(rows, key=lambda r: r["faithfulness"]),
            "best_balance": max(rows, key=lambda r: r["faithfulness"] + r["retrieval_hit_rate"]),
        },
    }
    json.dump(report, open(REPORT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n=== SWEEP REPORT ===")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print("rows:")
    for r in rows:
        print(f"  k={r['top_k']} th={r['min_score']}: hit={r['retrieval_hit_rate']} "
              f"cite={r['citation_rate']} cover={r['gold_cover_rate']} "
              f"faith={r['faithfulness']} empty={r['empty_context_cases']}")


if __name__ == "__main__":
    main()
