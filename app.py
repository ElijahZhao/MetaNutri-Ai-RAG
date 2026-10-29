"""Nutri-RAG · Streamlit demo app.

Chat interface with citation display + offline evaluation dashboard.

Run locally:  streamlit run app.py   (requires .env with DASHSCOPE_API_KEY)
Deploy:      Streamlit Community Cloud (set DASHSCOPE_API_KEY in secrets)
"""
import json
import os
import sys
import tarfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent

# 1) secrets -> env (for Streamlit Community Cloud)
if os.environ.get("DASHSCOPE_API_KEY") is None:
    try:
        if st.secrets.get("DASHSCOPE_API_KEY"):
            os.environ["DASHSCOPE_API_KEY"] = st.secrets["DASHSCOPE_API_KEY"]
    except Exception:  # nosec B110
        pass

# 2) restore vector store from tarball if missing (repo ignores chroma_db/)
db_dir = ROOT / "data" / "chroma_db"
if not db_dir.exists():
    with tarfile.open(ROOT / "data" / "chroma_db.tar.gz", "r:gz") as tf:
        tf.extractall(ROOT / "data", filter="data")  # reject unsafe tar members

sys.path.insert(0, str(ROOT))

from src.config import TOP_K  # noqa: E402
from src.generation import Generator, extract_citations  # noqa: E402
from src.retrieval import Retriever  # noqa: E402

st.set_page_config(page_title="Nutri-RAG · 健康饮食问答", page_icon="🥗", layout="wide")

st.title("Nutri-RAG · 健康饮食问答")
st.caption("基于《中国居民膳食指南（2022）》与中国食物成分数据的检索增强生成（RAG）演示")
st.warning("⚠️ 免责声明：本应用仅供学习研究演示，不构成医疗建议。健康问题请咨询专业医师或注册营养师。")


@st.cache_resource
def load_engine():
    return Retriever(), Generator()


retriever, generator = load_engine()

tab_chat, tab_eval = st.tabs(["💬 问答", "📊 评测结果"])

with tab_chat:
    st.markdown(
        "输入饮食营养问题，例如：*高血压人群饮食上应该注意什么？* · *每100克鸡蛋含多少蛋白质？* · "
        "*反式脂肪酸每天摄入量上限是多少？*"
    )
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("请输入你的饮食营养问题"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("检索资料并生成回答…"):
                hits = retriever.search(prompt, top_k=TOP_K)
                answer = generator.answer(prompt, hits)
            st.markdown(answer)
            cites = sorted(set(c for c in extract_citations(answer) if 1 <= c <= len(hits)))
            with st.expander(f"引用来源（{len(cites)} 条）"):
                for n in cites:
                    src = hits[n - 1]
                    head = src["text"].strip().split("\n")[0]
                    st.markdown(f"**[{n}] {head}**")
                    st.caption(src["text"][:400])
        st.session_state.messages.append({"role": "assistant", "content": answer})

with tab_eval:
    st.subheader("离线评测指标（50 条评测集 · qwen-plus）")
    rep_path = ROOT / "data" / "eval_report.json"
    if rep_path.exists():
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
        s = rep["summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("检索命中率", f"{s['retrieval_hit_rate']:.0%}")
        c2.metric("生成忠实度", f"{s['faithfulness']:.0%}")
        c3.metric("引用溯源率", f"{s['rag_citation_rate']:.0%}")
        c4.metric("消融增益", f"+{s['ablation_gain']:.0%}")
        st.caption(
            f"消融对照：无 RAG 关键信息覆盖 {s['gold_cover_norag']:.0%} → RAG {s['gold_cover_rag']:.0%}。"
            "差异集中在库内专有数值（如牛奶钙、猪里脊蛋白质、红薯能量）与细节题；RAG 回答全部带引用溯源，可逐条核验。"
        )
        st.subheader("按类别")
        try:
            import pandas as pd
            rows = [
                {"类别": "成分（营养数值）", **rep["by_category"]["composition"]},
                {"类别": "指南（膳食建议）", **rep["by_category"]["guideline"]},
                {"类别": "禁忌与特殊情况", **rep["by_category"]["special"]},
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        except ImportError:
            st.write(rep["by_category"])
        with st.expander("评测集逐条明细（50 条）"):
            for it in rep["items"]:
                flag = "✅" if it["faithful"] else "❌"
                st.markdown(
                    f"{flag} **{it['id']}** · {it['question']}  · "
                    f"命中={it['retrieval_hit']} · 引用有效={it['citations_valid']} · "
                    f"RAG覆盖={it['gold_covered_rag']} · 无RAG覆盖={it['gold_covered_norag']}"
                )
    else:
        st.info("评测报告缺失：未找到 data/eval_report.json")
