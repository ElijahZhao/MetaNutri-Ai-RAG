"""Generation module: assemble context, call Bailian qwen, return answer with citations.

Run from repo root: python3 -m src.generation "你的问题"  (self-test)
"""
import os
import re
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
load_dotenv(".env")

from openai import OpenAI

from src.config import (
    DASHSCOPE_BASE,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_CONTEXT_CHARS,
)

SYSTEM_PROMPT = """你是一名基于参考资料回答的健康饮食助手。严格规则：
1. 只依据用户提供的参考资料回答；资料未收录的内容必须明确说"资料中未收录"，禁止编造或估算。
2. 涉及食物营养成分时，以"每100克可食部"口径给出数值与单位。
3. 关键信息（数值、建议、结论）后必须用[编号]标注引用来源，编号对应参考资料序号。
4. 引用必须来自参考资料，不得虚构引用编号。
5. {LANG_RULE}
6. 若资料中对问题给出了明确的关键数值或时间点（如摄入上限、建议时间、推荐量），回答应覆盖这些要点，不得遗漏直接相关的关键数字。"""

LANG_RULES = {
    "zh": "回答使用简体中文，结构清晰、简洁。",
    "en": "Answer entirely in English (matching the language of the user's question). Keep numbers, units and citation numbers precise; give the Chinese food name in parentheses after the English name where it adds clarity.",
}


class Generator:
    def __init__(self):
        self._client = OpenAI(
            api_key=os.environ["DASHSCOPE_API_KEY"], base_url=DASHSCOPE_BASE
        )

    def build_prompt(self, query: str, chunks: list[dict]) -> str:
        parts, used = [], 0
        for i, c in enumerate(chunks, 1):
            used += len(c["text"])
            if used > MAX_CONTEXT_CHARS and i > 1:
                break
            parts.append(f"[{i}] {c['text']}")
        context = "\n\n".join(parts)
        return (
            f"参考资料：\n{context}\n\n"
            f"用户问题：{query}\n\n"
            f"请结合参考资料回答用户问题，并按规则标注引用编号。"
        )

    def answer(self, query: str, chunks: list[dict], language: str = "zh") -> str:
        lang_rule = LANG_RULES.get(language, LANG_RULES["zh"])
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(LANG_RULE=lang_rule)},
            {"role": "user", "content": self.build_prompt(query, chunks)},
        ]
        r = self._client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return r.choices[0].message.content.strip()

    def answer_stream(self, query: str, chunks: list[dict], language: str = "zh"):
        """Streaming variant for the UI: yields text deltas as the LLM generates.
        Non-streaming answer() stays the default for eval/tests."""
        lang_rule = LANG_RULES.get(language, LANG_RULES["zh"])
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(LANG_RULE=lang_rule)},
            {"role": "user", "content": self.build_prompt(query, chunks)},
        ]
        r = self._client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            stream=True,
        )
        for chunk in r:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def extract_citations(answer: str) -> list[int]:
    """Parse [n] citation markers from answer text."""
    return [int(m) for m in re.findall(r"\[(\d+)\]", answer)]


if __name__ == "__main__":
    from src.retrieval import Retriever

    q = sys.argv[1] if len(sys.argv) > 1 else "每天应该吃多少蔬菜水果？"
    retriever = Retriever()
    hits = retriever.search(q)
    g = Generator()
    ans = g.answer(q, hits)
    print(f"\nQ: {q}\n\n{ans}\n")
    print("引用编号:", extract_citations(ans))
    print("检索结果数:", len(hits))
