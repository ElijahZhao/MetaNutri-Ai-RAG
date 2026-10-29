"""Prompt assembly and evaluation-judgment logic tests (no API)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import MAX_CONTEXT_CHARS  # noqa: E402
from src.evaluation import (  # noqa: E402
    has_key_info,
    norm,
)
from src.generation import Generator, SYSTEM_PROMPT  # noqa: E402


def test_build_prompt_numbering_and_truncation():
    g = Generator.__new__(Generator)  # no client needed for build_prompt
    chunks = [{"text": "A" * 100, "type": "food"}, {"text": "B" * 100, "type": "food"},
              {"text": "C" * 100, "type": "guideline"}]
    p = g.build_prompt("问题", chunks)
    assert "[1]" in p and "[2]" in p and "[3]" in p
    assert "用户问题：问题" in p


def test_build_prompt_context_cap():
    g = Generator.__new__(Generator)
    chunks = [{"text": "X" * (MAX_CONTEXT_CHARS + 500), "type": "food"},
              {"text": "Y" * 50, "type": "food"}]
    p = g.build_prompt("q", chunks)
    assert "[1]" in p and "[2]" not in p  # over-cap chunk 2 dropped
    assert len(p) <= MAX_CONTEXT_CHARS + 600  # head/tail tolerance


def test_system_prompt_has_coverage_rule():
    assert "覆盖" in SYSTEM_PROMPT and "引用" in SYSTEM_PROMPT


def test_norm_units():
    assert norm("300～350g") == "300-350g"
    assert norm("6 000步") == "6000步"
    assert norm("食盐不超过5克") == "食盐不超过5g"


def test_has_key_info_numeric():
    assert has_key_info("每天食盐不超过5g[1]", "成年人每天摄入食盐不超过5g", "食盐")
    assert has_key_info("约300-350g", "蛋类300~350g", "蛋类")
    assert has_key_info("6000步", "每天6 000步", "6 000步")
    assert has_key_info("95.8g", "每100克可食部含96.0g", "秋黄瓜") is False


def test_has_key_info_gold_key_phrase():
    assert has_key_info("儿童青少年不应饮酒。", "成年人饮酒不超过15g", "儿童青少年", "不应饮酒")
    # tolerate inserted connector: 超重和肥胖 vs 超重肥胖
    assert has_key_info("易导致超重和肥胖。", "不暴饮暴食", "暴饮暴食", "超重肥胖")


def test_has_key_info_single_char_fallback():
    assert has_key_info("橙子每100克含维生素C 33.0mg[1]", "每100克可食部含33.0mg", "橙")


def test_has_key_info_ignores_100g_denominator():
    # "100g" is the per-100g denominator, not a key value
    assert has_key_info("每100克含1530kJ", "每100克可食部含1530kJ", "小米")
    assert has_key_info("每100克约358千卡", "每100克可食部含1530kJ", "小米") is False
