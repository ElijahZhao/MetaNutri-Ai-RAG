"""Refusal eval-set structure checks (no API calls)."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def _load(name):
    return json.load(open(DATA / name, encoding="utf-8"))


def test_refusal_set_size_and_categories():
    qs = _load("refusal_questions.json")
    assert len(qs) == 40
    cnt = Counter(x["category"] for x in qs)
    assert cnt == {"offtopic": 15, "not_in_kb": 15, "boundary": 10}


def test_refusal_set_fields_complete():
    qs = _load("refusal_questions.json")
    for it in qs:
        assert it["id"].startswith("R") and it["question"]
        assert it["category"] in ("offtopic", "not_in_kb", "boundary")


def test_refusal_set_no_overlap_with_eval_set():
    qs = _load("refusal_questions.json")
    ev = _load("eval_questions.json")
    eval_q = {x["question"] for x in ev}
    for it in qs:
        assert it["question"] not in eval_q, f"duplicate with eval set: {it['question']}"


def test_refusal_report_shape():
    rep = _load("refusal_report.json")
    s = rep["summary"]
    for key in ["refusal_rate_rag", "refusal_rate_norag", "refusal_rate_strict_assistant", "n"]:
        assert key in s
    assert s["n"] == 40
    assert len(rep["items"]) == 40
    for it in rep["items"]:
        assert it["id"] in {x["id"] for x in _load("refusal_questions.json")}
