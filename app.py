"""Nutri-RAG · Streamlit demo app.

Chat interface with citation cards + offline evaluation dashboard.
Brand styling: nutrition-green visual system, hero header, sidebar summary.

Run locally:  streamlit run app.py   (requires .env with DASHSCOPE_API_KEY)
Deploy:      Streamlit Community Cloud (set DASHSCOPE_API_KEY in secrets)
"""
import html
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

# ---------------------------------------------------------------- brand css
CSS = """
<style>
:root{
  --brand:#16a34a; --brand-dark:#166534; --brand-soft:#f0fdf4;
  --accent:#f59e0b; --card-bg:#ffffff; --text:#1f2937; --muted:#6b7280;
  --border:#e5e7eb;
  --shadow:0 1px 3px rgba(16,24,40,.06),0 1px 2px rgba(16,24,40,.04);
}
html[data-theme="dark"]{
  --card-bg:#1e293b; --text:#f1f5f9; --muted:#94a3b8; --border:#334155; --brand-soft:#123524;
}
.block-container{padding-top:1.8rem;}
.hero{margin:.4rem 0 1.2rem;}
.hero h1{font-size:2.1rem;font-weight:800;letter-spacing:-.02em;margin:0 0 .35rem;color:var(--text);}
.hero .sub{color:var(--muted);font-size:1rem;margin:0 0 .9rem;}
.pills{display:flex;flex-wrap:wrap;gap:.5rem;}
.pill{background:var(--brand-soft);color:var(--brand-dark);border:1px solid var(--border);
  border-radius:999px;padding:.28rem .8rem;font-size:.82rem;font-weight:600;}
html[data-theme="dark"] .pill{color:#4ade80;}
.side-card{background:var(--card-bg);border:1px solid var(--border);border-radius:14px;
  padding:.9rem 1rem;margin-bottom:.8rem;box-shadow:var(--shadow);font-size:.88rem;}
.side-card .t{font-weight:700;color:var(--brand-dark);margin:.35rem 0 .2rem;font-size:.82rem;letter-spacing:.02em;}
html[data-theme="dark"] .side-card .t{color:#4ade80;}
.side-card .t:first-child{margin-top:0;}
.side-card .row{color:var(--text);margin:.1rem 0;}
.side-card .muted{color:var(--muted);font-size:.8rem;}
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin:.6rem 0 1.1rem;}
.metric-card{background:var(--card-bg);border:1px solid var(--border);border-radius:14px;
  padding:.85rem 1rem;box-shadow:var(--shadow);}
.metric-card .m-label{color:var(--muted);font-size:.8rem;font-weight:600;margin-bottom:.3rem;}
.metric-card .m-value{font-size:1.65rem;font-weight:800;letter-spacing:-.02em;}
.metric-card .m-value.ok{color:var(--brand);}
.metric-card .m-value.plus{color:var(--accent);}
.cite-card{background:var(--card-bg);border:1px solid var(--border);border-left:3px solid var(--brand);
  border-radius:10px;padding:.6rem .8rem;margin:.45rem 0;box-shadow:var(--shadow);}
.cite-card .head{display:flex;align-items:center;gap:.5rem;margin-bottom:.25rem;}
.cite-badge{background:var(--brand);color:#fff;border-radius:6px;padding:.05rem .45rem;
  font-size:.78rem;font-weight:700;}
.cite-tag{border-radius:6px;padding:.05rem .45rem;font-size:.74rem;font-weight:700;}
.cite-tag.food{background:#ecfdf5;color:#047857;}
.cite-tag.guide{background:#fff7ed;color:#c2410c;}
html[data-theme="dark"] .cite-tag.food{background:#064e3b;color:#6ee7b7;}
html[data-theme="dark"] .cite-tag.guide{background:#431407;color:#fdba74;}
.cite-card .body{color:var(--text);font-size:.86rem;line-height:1.55;}
.ablation{background:var(--card-bg);border:1px solid var(--border);border-radius:14px;
  padding:1rem 1.2rem;margin:.6rem 0 1.1rem;box-shadow:var(--shadow);}
.ablation .a-title{font-weight:700;margin-bottom:.6rem;font-size:.95rem;}
.ablation .bar{height:22px;border-radius:999px;background:var(--brand-soft);overflow:hidden;position:relative;display:flex;}
.ablation .bar .seg{height:100%;display:flex;align-items:center;justify-content:center;
  font-size:.72rem;font-weight:700;color:#fff;}
.ablation .bar .seg.rag{background:var(--brand);}
.ablation .legend{display:flex;gap:1.4rem;margin-top:.55rem;font-size:.82rem;color:var(--muted);flex-wrap:wrap;}
.ablation .legend b{color:var(--text);}
.chat-hint{color:var(--muted);font-size:.88rem;margin:.2rem 0 .6rem;}
.footer{color:var(--muted);font-size:.78rem;text-align:center;margin:2rem 0 .4rem;}
.dtable{width:100%;border-collapse:collapse;background:var(--card-bg);border:1px solid var(--border);
  border-radius:12px;overflow:hidden;box-shadow:var(--shadow);font-size:.85rem;}
.dtable th{background:var(--brand-soft);color:var(--brand-dark);text-align:left;padding:.5rem .8rem;
  font-weight:700;white-space:nowrap;}
html[data-theme="dark"] .dtable th{color:#4ade80;}
.dtable td{padding:.45rem .8rem;border-top:1px solid var(--border);color:var(--text);vertical-align:top;}
.dtable tr:hover td{background:var(--brand-soft);}
@media (max-width:900px){.metric-grid{grid-template-columns:repeat(2,1fr);}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar
def _load_summary():
    rep_path = ROOT / "data" / "eval_report.json"
    if not rep_path.exists():
        return None
    return json.loads(rep_path.read_text(encoding="utf-8"))["summary"]


with st.sidebar:
    st.markdown("### 🥗 Nutri-RAG")
    s = _load_summary()
    size_html = (
        f"<div class='side-card'>"
        f"<div class='t'>📦 数据规模</div>"
        f"<div class='row'>325 种食物 × 32 项营养</div>"
        f"<div class='row'>17 段指南 · 342 知识切片</div>"
        f"<div class='t'>🎯 评测 · 50 条</div>"
        f"<div class='row'>命中 {s['retrieval_hit_rate']:.0%} · 忠实 {s['faithfulness']:.0%}</div>"
        f"<div class='row'>引用 {s['rag_citation_rate']:.0%} · 消融 +{s['ablation_gain']:.0%}</div>"
        f"<div class='muted'>无 RAG {s['gold_cover_norag']:.0%} → RAG {s['gold_cover_rag']:.0%}</div>"
        f"</div>"
        if s else "<div class='side-card muted'>评测报告缺失</div>"
    )
    st.markdown(size_html, unsafe_allow_html=True)
    st.markdown(
        "**MetaNutri 生态**  \n"
        "· [MetaNutri 主仓](https://github.com/ElijahZhao/MetaNutri---AI-)  \n"
        "· [ppgr-predictor](https://github.com/ElijahZhao/ppgr-predictor)  \n"
        "· [Nutri-RAG](https://github.com/ElijahZhao/nutri-rag) 本仓库  \n"
        "· [在线演示](https://metanutri-ai-rag-question-answering.streamlit.app/)"
    )
    st.divider()
    if st.button("🗑 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------- hero
st.markdown(
    """
    <div class="hero">
      <h1>🥗 Nutri-RAG · 健康饮食问答</h1>
      <p class="sub">基于《中国居民膳食指南（2022）》与《中国食物成分表》的检索增强生成（RAG）演示</p>
      <div class="pills">
        <span class="pill">🧩 342 知识切片</span>
        <span class="pill">🧪 50 条评测集</span>
        <span class="pill">🔀 均衡双路检索</span>
        <span class="pill">📚 引用溯源</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="chat-hint">直接提问，或点示例试试 👇</p>',
    unsafe_allow_html=True,
)


@st.cache_resource
def load_engine():
    return Retriever(), Generator()


retriever, generator = load_engine()

EXAMPLES = [
    "高血压人群饮食上应该注意什么？",
    "每100克鸡蛋含多少蛋白质？",
    "反式脂肪酸每天摄入量上限是多少？",
]


def ask(question):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("检索资料并生成回答…"):
            hits = retriever.search(question, top_k=TOP_K)
            answer = generator.answer(question, hits)
        st.markdown(answer)
        cites = sorted(set(c for c in extract_citations(answer) if 1 <= c <= len(hits)))
        if cites:
            with st.expander(f"📎 引用来源（{len(cites)} 条）"):
                for n in cites:
                    src = hits[n - 1]
                    typ = "食物" if src.get("type") == "food" else "指南"
                    cls = "food" if typ == "食物" else "guide"
                    head = html.escape(src["text"].strip().split("\n")[0][:60])
                    body = html.escape(src["text"][:400])
                    st.markdown(
                        f'<div class="cite-card"><div class="head">'
                        f'<span class="cite-badge">[{n}]</span>'
                        f'<span class="cite-tag {cls}">{typ}</span>'
                        f'<span style="color:var(--muted);font-size:.82rem;">{head}</span></div>'
                        f'<div class="body">{body}</div></div>',
                        unsafe_allow_html=True,
                    )
    st.session_state.messages.append({"role": "assistant", "content": answer})


tab_chat, tab_eval = st.tabs(["💬 问答", "📊 评测结果"])

with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    cols = st.columns(len(EXAMPLES))
    for col, q in zip(cols, EXAMPLES):
        if col.button(q, use_container_width=True):
            ask(q)

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("请输入你的饮食营养问题（如：高尿酸人群能吃哪些豆制品？）"):
        ask(prompt)

with tab_eval:
    st.markdown("#### 离线评测指标 · 50 条评测集 · qwen-plus")
    rep_path = ROOT / "data" / "eval_report.json"
    if rep_path.exists():
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
        s = rep["summary"]
        st.markdown(
            f"""
            <div class="metric-grid">
              <div class="metric-card"><div class="m-label">🎯 检索命中率</div>
                <div class="m-value ok">{s['retrieval_hit_rate']:.0%}</div></div>
              <div class="metric-card"><div class="m-label">✅ 生成忠实度</div>
                <div class="m-value ok">{s['faithfulness']:.0%}</div></div>
              <div class="metric-card"><div class="m-label">📚 引用溯源率</div>
                <div class="m-value ok">{s['rag_citation_rate']:.0%}</div></div>
              <div class="metric-card"><div class="m-label">🚀 消融增益</div>
                <div class="m-value plus">+{s['ablation_gain']:.0%}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        norag = s["gold_cover_norag"]
        rag = s["gold_cover_rag"]
        st.markdown(
            f"""
            <div class="ablation">
              <div class="a-title">🔬 消融对比 · 关键信息覆盖（无 RAG vs RAG）</div>
              <div class="bar">
                <div class="seg" style="width:{norag*100:.0f}%;background:#d1d5db;color:#374151;">
                  无 RAG {norag*100:.0f}%</div>
                <div class="seg rag" style="width:{(rag-norag)*100:.0f}%;">
                  +RAG {(rag-norag)*100:.0f}%</div>
              </div>
              <div class="legend"><span>无 RAG 直答：<b>{norag*100:.0f}%</b></span>
                <span>RAG：<b>{rag*100:.0f}%</b></span>
                <span>差异集中在库内专有数值与细节题，RAG 全部带引用可核验</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader("按类别")
        bc = rep["by_category"]
        cat_rows = [
            ("成分（营养数值）", bc["composition"]["retrieval_hit_rate"], bc["composition"]["faithfulness"]),
            ("指南（膳食建议）", bc["guideline"]["retrieval_hit_rate"], bc["guideline"]["faithfulness"]),
            ("禁忌与特殊情况", bc["special"]["retrieval_hit_rate"], bc["special"]["faithfulness"]),
        ]
        cat_html = (
            "<table class='dtable'><tr><th>类别</th><th>检索命中率</th><th>生成忠实度</th></tr>"
            + "".join(
                f"<tr><td>{name}</td><td>{hit:.0%}</td><td>{faith:.0%}</td></tr>"
                for name, hit, faith in cat_rows
            )
            + "</table>"
        )
        st.markdown(cat_html, unsafe_allow_html=True)

        cat_map = {"composition": "成分", "guideline": "指南", "special": "禁忌"}
        cat_sel = st.selectbox("筛选类别", ["全部", "成分", "指南", "禁忌"])
        rows = [
            it for it in rep["items"]
            if cat_sel == "全部" or cat_map.get(it["category"]) == cat_sel
        ]
        if rows:
            detail_html = (
                "<table class='dtable'><tr><th>ID</th><th>类别</th><th>问题</th>"
                "<th>命中</th><th>引用有效</th><th>RAG覆盖</th><th>无RAG覆盖</th></tr>"
                + "".join(
                    "<tr>"
                    f"<td>{it['id']}</td><td>{cat_map.get(it['category'], '-')}</td>"
                    f"<td>{html.escape(it['question'][:40])}</td>"
                    f"<td>{'✅' if it['retrieval_hit'] else '❌'}</td>"
                    f"<td>{'✅' if it['citations_valid'] else '❌'}</td>"
                    f"<td>{'✅' if it['gold_covered_rag'] else '❌'}</td>"
                    f"<td>{'✅' if it['gold_covered_norag'] else '❌'}</td>"
                    "</tr>"
                    for it in rows
                )
                + "</table>"
            )
            st.markdown(detail_html, unsafe_allow_html=True)
        st.caption(f"共 {len(rows)} 条 · 全部 50 条：检索命中 50/50 · 忠实 50/50 · 引用 50/50")
    else:
        st.info("评测报告缺失：未找到 data/eval_report.json")

st.markdown(
    '<div class="footer">⚠️ 本应用仅供学习研究演示，不构成医疗建议。健康问题请咨询专业医师或注册营养师。</div>',
    unsafe_allow_html=True,
)
