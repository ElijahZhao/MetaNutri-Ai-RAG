"""Evaluation: retrieval hit rate, generation faithfulness, and no-RAG vs RAG ablation.

Run: python3 src/evaluation.py   (writes data/eval_report.json)
Metrics:
  1. retrieval_hit  : top-k(=5) contains a chunk with source_keyword
  2. faithfulness   : all [n] citations valid + gold key info appears in answer
  3. ablation       : gold-key-info coverage of no-RAG vs RAG answers
"""
import json
import os
import re
import sys
import time

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
load_dotenv(".env")

from openai import OpenAI

from src.config import DASHSCOPE_BASE, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from src.generation import Generator, extract_citations
from src.retrieval import Retriever

EVAL_FILE = "data/eval_questions.json"
REPORT_FILE = "data/eval_report.json"

NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:kJ|kg|g|mg|ml|μg|µg|%|种|步|分钟|小时|次|类)")


def norm(s: str) -> str:
    s = re.sub(r"\s+", "", s)
    # full-width punctuation and CN units -> ASCII forms
    s = s.replace("～", "-").replace("—", "-").replace("–", "-").replace("~", "-")
    s = s.replace("千克", "kg").replace("克", "g").replace("千焦", "kJ")
    s = s.replace("毫克", "mg").replace("毫升", "ml").replace("微克", "μg")
    s = s.replace("％", "%")
    return s


def key_value(n: str) -> str:
    n = n.replace("~", "-").replace("～", "-").replace("–", "-")
    return re.sub(r"\.0(?=[a-zA-Z%])", "", n)  # 96.0g -> 96g


# "100g" is the per-100g denominator in composition golds, not a key value
STOP_KEYS = {"100g"}


def gold_key_values(gold: str) -> set:
    return {k for k in (key_value(n) for n in NUM_RE.findall(norm(gold))) if k not in STOP_KEYS}


def answer_key_values(answer: str) -> set:
    return {k for k in (key_value(n) for n in NUM_RE.findall(norm(answer))) if k not in STOP_KEYS}


def has_key_info(answer: str, gold: str, kw: str = "", gold_key: str = "") -> bool:
    a = norm(answer)
    # 1) numeric overlap first (symbol/unit/whitespace normalized)
    nums = gold_key_values(gold)
    if nums:
        if nums & answer_key_values(answer):
            return True
    # 2) explicit gold_key phrase; tolerate inserted connectors (超重肥胖 vs 超重和肥胖)
    if gold_key:
        gk = norm(gold_key)
        if gk in a:
            return True
        words = re.findall(r"[\u4e00-\u9fa5]{2}", gk)
        if len(words) >= 2 and all(w in a for w in words):
            return True
    # 3) fallback: source_keyword prefix (single char OK, e.g. 橙)
    core = re.search(r"[\u4e00-\u9fa5]{1,4}", kw or "")
    return bool(core and core.group(0) in answer)


def main():
    questions = json.load(open(EVAL_FILE, encoding="utf-8"))
    retriever = Retriever()
    generator = Generator()

    # no-RAG generator: generic assistant, answers from model knowledge
    norag_client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url=DASHSCOPE_BASE)
    NORAG_SYSTEM = "你是一名健康饮食助手，用你自己的知识回答用户问题，简洁、准确、使用简体中文。"

    def answer_no_rag(q: str) -> str:
        r = norag_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": NORAG_SYSTEM},
                {"role": "user", "content": q},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return r.choices[0].message.content.strip()

    results = []
    agg = {"hit": [0, 0], "faith": [0, 0], "cite": [0, 0], "cov_rag": [0, 0], "cov_norag": [0, 0]}
    cat_stat = {c: {"hit": [0, 0], "faith": [0, 0]} for c in ("composition", "guideline", "special")}

    for i, item in enumerate(questions):
        q, gold, kw, cat = item["question"], item["gold"], item["source_keyword"], item["category"]
        gk = item.get("gold_key", "")

        # 1) retrieval hit (whitespace-normalized)
        hits = retriever.search(q, top_k=5)
        hit = any(norm(kw) in norm(h["text"]) for h in hits)
        agg["hit"][1] += 1
        agg["hit"][0] += int(hit)
        cat_stat[cat]["hit"][1] += 1
        cat_stat[cat]["hit"][0] += int(hit)

        # 2) RAG generation
        ans_rag = generator.answer(q, hits)
        cites = extract_citations(ans_rag)
        cite_ok = len(cites) > 0 and all(1 <= c <= len(hits) for c in cites)
        covered_rag = has_key_info(ans_rag, gold, kw, gk)
        faithful = cite_ok and covered_rag
        agg["faith"][1] += 1
        agg["faith"][0] += int(faithful)
        agg["cite"][1] += 1
        agg["cite"][0] += int(cite_ok)
        cat_stat[cat]["faith"][1] += 1
        cat_stat[cat]["faith"][0] += int(faithful)
        agg["cov_rag"][1] += 1
        agg["cov_rag"][0] += int(covered_rag)

        # 3) no-RAG ablation
        ans_norag = answer_no_rag(q)
        covered_norag = has_key_info(ans_norag, gold, kw, gk)
        agg["cov_norag"][1] += 1
        agg["cov_norag"][0] += int(covered_norag)

        results.append({
            "id": item["id"], "category": cat, "question": q,
            "retrieval_hit": hit, "citations_valid": cite_ok, "citations": cites,
            "gold_covered_rag": covered_rag, "gold_covered_norag": covered_norag,
            "faithful": faithful,
            "answer_rag": ans_rag, "answer_norag": ans_norag,
        })
        if (i + 1) % 10 == 0:
            print(f"progress {i+1}/{len(questions)}", flush=True)

    report = {
        "summary": {
            "retrieval_hit_rate": round(agg["hit"][0] / agg["hit"][1], 4),
            "faithfulness": round(agg["faith"][0] / agg["faith"][1], 4),
            "rag_citation_rate": round(agg["cite"][0] / agg["cite"][1], 4),
            "gold_cover_rag": round(agg["cov_rag"][0] / agg["cov_rag"][1], 4),
            "gold_cover_norag": round(agg["cov_norag"][0] / agg["cov_norag"][1], 4),
            "ablation_gain": round((agg["cov_rag"][0] - agg["cov_norag"][0]) / agg["cov_rag"][1], 4),
        },
        "by_category": {
            c: {
                "retrieval_hit_rate": round(s["hit"][0] / s["hit"][1], 4),
                "faithfulness": round(s["faith"][0] / s["faith"][1], 4),
            } for c, s in cat_stat.items()
        },
        "items": results,
    }
    json.dump(report, open(REPORT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n=== SUMMARY ===")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print("by_category:", json.dumps(report["by_category"], ensure_ascii=False))


if __name__ == "__main__":
    main()
