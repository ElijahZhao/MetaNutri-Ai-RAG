"""Data-pipeline integrity checks (no API calls)."""
import csv
import re
import sqlite3
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def test_food_csv_shape():
    rows = list(csv.DictReader(open(DATA / "foods_nutrition.csv", encoding="utf-8")))
    assert len(rows) == 325
    # 3 base cols (id/name/category) + 32 nutrient cols
    assert len(rows[0]) == 35
    for r in rows:
        assert r["name"].strip()


def test_kb_food_chunks_count():
    kb = (DATA / "kb_foods.txt").read_text(encoding="utf-8")
    chunks = [c for c in re.split(r"(?=【食物：)", kb) if c.strip()]
    assert len(chunks) == 325


def test_kb_guideline_chunks_count():
    kb = (DATA / "kb_guidelines.txt").read_text(encoding="utf-8")
    chunks = [c for c in re.split(r"(?=【膳食指南)", kb) if c.strip()]
    assert len(chunks) == 17


def test_vector_store_restored_and_count():
    db = DATA / "chroma_db"
    if not db.exists():
        with tarfile.open(DATA / "chroma_db.tar.gz", "r:gz") as tf:
            tf.extractall(DATA)
    assert db.exists()
    con = sqlite3.connect(db / "chroma.sqlite3")
    n = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    assert n == 342


def test_vector_store_backup_present():
    assert (DATA / "chroma_db.tar.gz").stat().st_size > 1_000_000


def test_sources_md_numbers_consistent():
    src = (DATA / "SOURCES.md").read_text(encoding="utf-8")
    assert "325" in src
    assert "17 段" in src
    assert "342 chunks" in src


def test_guideline_md_has_sections():
    d6 = (DATA / "dietary_guidelines_rule6_detail.md").read_text(encoding="utf-8")
    for kw in ["龋齿", "尿液颜色", "零食", "睡觉前", "暴饮暴食"]:
        assert kw in d6
