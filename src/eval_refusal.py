"""Refusal evaluation: does the RAG system refuse out-of-scope questions instead of hallucinating?

Run: python3 src/eval_refusal.py   (writes data/refusal_report.json)
A question passes when the answer clearly signals the info is not in the knowledge base
(e.g. "资料中未收录", "无法回答") and does not fabricate specifics. Answers are printed
for a quick manual audit on top of the rule-based pass/fail.
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

from src.config import LLM_MODEL, LLM_PROFILES, LLM_PROVIDER, LLM_TEMPERATURE, LLM_MAX_TOKENS
from src.generation import Generator
from src.hybrid import HybridRetriever

REFUSAL_FILE = "data/refusal_questions.json"
REPORT_FILE = "data/refusal_report.json" if os.environ.get("LLM_PROVIDER", "qwen") == "qwen" \
    else f"data/refusal_report_{os.environ.get('LLM_PROVIDER', 'qwen')}.json"

REFUSAL_MARKERS = [
    "未收录", "资料未", "未提供", "无法回答", "不包含", "没有相关",
    "没有资料", "不涉及", "不在资料", "找不到", "没有提到", "未有",
    "cannot answer", "not found", "not in the", "no information", "do not have",
    "I don't have", "I can't", "out of scope", "not covered",
]


def is_refusal(answer: str) -> bool:
    a = answer.lower()
    return any(m in a for m in REFUSAL_MARKERS)


def main():
    questions = json.load(open(REFUSAL_FILE, encoding="utf-8"))
    retriever = HybridRetriever(top_k=int(os.environ.get("TOP_K", "8")))
    generator = Generator()

    _prof = LLM_PROFILES[LLM_PROVIDER]
    _prof_model = os.environ.get("LLM_MODEL", _prof["model"])
    # no-RAG baseline for comparison: a plain assistant
    norag_client = OpenAI(
        api_key=os.environ[_prof["key_env"]], base_url=_prof["base"], timeout=60.0
    )
    NORAG_SYSTEM = "你是一名健康饮食助手，用你自己的知识回答用户问题，简洁、准确、使用简体中文。"
    # a "strict assistant" that must refuse out-of-scope asks (what RAG *should* do)
    STRICT_SYSTEM = (
        "你是一名健康饮食助手。只回答与《中国食物成分表》或《中国居民膳食指南》相关的问题；"
        "与营养饮食无关或资料未收录的问题，必须明确回答“资料中未收录相关信息”，禁止编造。"
    )

    def answer_no_rag(q: str, system: str) -> str:
        r = norag_client.chat.completions.create(
            model=_prof_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": q}],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return r.choices[0].message.content.strip()

    results = []
    agg = {"rag": [0, 0], "norag": [0, 0], "strict": [0, 0]}

    for i, item in enumerate(questions):
        q = item["question"]
        hits = retriever.search(q, top_k=int(os.environ.get("TOP_K", "8")))
        ans_rag = generator.answer(q, hits)
        ans_norag = answer_no_rag(q, NORAG_SYSTEM)
        ans_strict = answer_no_rag(q, STRICT_SYSTEM)

        ok_rag = is_refusal(ans_rag)
        ok_norag = is_refusal(ans_norag)
        ok_strict = is_refusal(ans_strict)
        for k, ok in (("rag", ok_rag), ("norag", ok_norag), ("strict", ok_strict)):
            agg[k][1] += 1
            agg[k][0] += int(ok)

        results.append({
            "id": item["id"], "category": item["category"], "question": q,
            "refused_rag": ok_rag, "refused_norag": ok_norag, "refused_strict": ok_strict,
            "answer_rag": ans_rag, "answer_norag": ans_norag,
        })
        print(f"\n[{item['id']}] {q}")
        print(f"  RAG  : {('REFUSE' if ok_rag else '!! ANSWER !!')} :: {ans_rag[:120]}")
        print(f"  NoRAG: {('REFUSE' if ok_norag else '!! ANSWER !!')} :: {ans_norag[:120]}")
        if (i + 1) % 5 == 0:
            print(f"progress {i+1}/{len(questions)}", flush=True)

    report = {
        "summary": {
            "refusal_rate_rag": round(agg["rag"][0] / agg["rag"][1], 4),
            "refusal_rate_norag": round(agg["norag"][0] / agg["norag"][1], 4),
            "refusal_rate_strict_assistant": round(agg["strict"][0] / agg["strict"][1], 4),
            "n": len(questions),
        },
        "items": results,
    }
    json.dump(report, open(REPORT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n=== REFUSAL SUMMARY ===")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
