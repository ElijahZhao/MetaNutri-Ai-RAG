"""Eval-set structure checks (no API calls)."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def _load(name):
    return json.load(open(DATA / name, encoding="utf-8"))


def test_eval_set_size_and_categories():
    qs = _load("eval_questions.json")
    assert len(qs) == 50
    cnt = Counter(x["category"] for x in qs)
    assert cnt == {"composition": 20, "guideline": 15, "special": 15}


def test_eval_set_fields_complete():
    qs = _load("eval_questions.json")
    for it in qs:
        assert it["id"] and it["question"] and it["gold"] and it["source_keyword"]
        assert it["category"] in ("composition", "guideline", "special")
    # all 15 special cases carry an explicit gold_key
    special = [x for x in qs if x["category"] == "special"]
    assert len(special) == 15 and all(x.get("gold_key") for x in special)


def test_composition_gold_format():
    qs = _load("eval_questions.json")
    for it in qs:
        if it["category"] == "composition":
            assert it["gold"].startswith("每100克可食部含")


def test_eval_report_shape():
    rep = _load("eval_report.json")
    s = rep["summary"]
    for key in ["retrieval_hit_rate", "faithfulness", "rag_citation_rate",
                "gold_cover_rag", "gold_cover_norag", "ablation_gain"]:
        assert key in s and 0.0 <= s[key] <= 1.0
    assert len(rep["items"]) == 50
    for it in rep["items"]:
        assert it["id"] in {x["id"] for x in _load("eval_questions.json")}
