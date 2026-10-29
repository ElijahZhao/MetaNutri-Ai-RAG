"""Nutri-RAG · Streamlit demo app.

Chat interface with citation cards + offline evaluation dashboard.
i18n (zh/en), multi-conversation sidebar, brand green visual system.

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

# ---------------------------------------------------------------- i18n texts
I18N = {
    "zh": {
        "hero_title": "🥗 Nutri-RAG · 健康饮食问答",
        "hero_sub": "基于《中国居民膳食指南（2022）》与《中国食物成分表》的检索增强生成（RAG）演示",
        "pill_kb": "🧩 342 知识切片",
        "pill_eval": "🧪 50 条评测集",
        "pill_dual": "🔀 均衡双路检索",
        "pill_cite": "📚 引用溯源",
        "hint": "直接提问，或点示例试试 👇",
        "tab_chat": "💬 问答",
        "tab_eval": "📊 评测结果",
        "examples": ["高血压人群饮食上应该注意什么？", "每100克鸡蛋含多少蛋白质？",
                     "反式脂肪酸每天摄入量上限是多少？"],
        "input_ph": "请输入你的饮食营养问题（如：高尿酸人群能吃哪些豆制品？）",
        "side_data": "📦 数据规模",
        "side_data_rows": ["325 种食物 × 32 项营养", "17 段指南 · 342 知识切片"],
        "side_eval": "🎯 评测 · 50 条",
        "side_hit": "命中 {} · 忠实 {}",
        "side_cite": "引用 {} · 消融 +{}",
        "side_norag": "无 RAG {} → RAG {}",
        "eco_title": "🔗 MetaNutri 生态",
        "eco": [("MetaNutri 主仓", "全栈精准营养平台",
                 "https://github.com/ElijahZhao/MetaNutri---AI-"),
                ("ppgr-predictor", "餐后血糖预测",
                 "https://github.com/ElijahZhao/ppgr-predictor"),
                ("Nutri-RAG", "本仓库 · RAG 健康饮食问答",
                 "https://github.com/ElijahZhao/nutri-rag"),
                ("在线演示", "就是本页面",
                 "https://metanutri-ai-rag-question-answering.streamlit.app/")],
        "new_conv": "➕ 新建对话",
        "rename_btn": "✏️ 重命名",
        "del_conv": "🗑 删除会话",
        "rename_title": "重命名会话",
        "rename_ph": "新名称",
        "save": "保存",
        "spinner": "检索资料并生成回答…",
        "cite_exp": "📎 引用来源（{} 条）",
        "cite_food": "食物",
        "cite_guide": "指南",
        "eval_title": "离线评测指标 · 50 条评测集 · qwen-plus",
        "m_hit": "🎯 检索命中率",
        "m_faith": "✅ 生成忠实度",
        "m_cite": "📚 引用溯源率",
        "m_ab": "🚀 消融增益",
        "abl_title": "🔬 消融对比 · 关键信息覆盖（无 RAG vs RAG）",
        "abl_norag": "无 RAG {}",
        "abl_rag": "+RAG {}",
        "abl_l1": "无 RAG 直答：{}",
        "abl_l2": "RAG：{}",
        "abl_l3": "差异集中在库内专有数值与细节题，RAG 全部带引用可核验",
        "by_cat": "按类别",
        "cat_names": {"composition": "成分（营养数值）", "guideline": "指南（膳食建议）",
                      "special": "禁忌与特殊情况"},
        "th_cat": "类别", "th_hit": "检索命中率", "th_faith": "生成忠实度",
        "filter": "筛选类别", "filter_all": "全部",
        "filter_cats": {"composition": "成分", "guideline": "指南", "special": "禁忌"},
        "th_id": "ID", "th_q": "问题", "th_hit2": "命中", "th_cite2": "引用有效",
        "th_rag": "RAG覆盖", "th_norag": "无RAG覆盖",
        "caption": "共 {} 条 · 全部 50 条：检索命中 50/50 · 忠实 50/50 · 引用 50/50",
        "eval_missing": "评测报告缺失：未找到 data/eval_report.json",
        "footer": "⚠️ 本应用仅供学习研究演示，不构成医疗建议。健康问题请咨询专业医师或注册营养师。",
    },
    "en": {
        "hero_title": "🥗 Nutri-RAG · Healthy Diet Q&A",
        "hero_sub": "Retrieval-Augmented Generation (RAG) demo powered by the Chinese Food Composition Tables and the 2022 Dietary Guidelines for Chinese Residents",
        "pill_kb": "🧩 342 Knowledge Chunks",
        "pill_eval": "🧪 50-Q Evaluation Set",
        "pill_dual": "🔀 Balanced Dual-Route Retrieval",
        "pill_cite": "📚 Citation Tracing",
        "hint": "Ask a question, or try an example 👇",
        "tab_chat": "💬 Chat",
        "tab_eval": "📊 Evaluation",
        "examples": ["What should people with hypertension pay attention to in their diet?",
                     "How much protein is in 100g of eggs?",
                     "What is the daily upper limit for trans fatty acids?"],
        "input_ph": "Ask a diet & nutrition question (e.g. which soy products can people with high uric acid eat?)",
        "side_data": "📦 Data",
        "side_data_rows": ["325 foods × 32 nutrients", "17 guideline sections · 342 chunks"],
        "side_eval": "🎯 Evaluation · 50 items",
        "side_hit": "Hit {} · Faithful {}",
        "side_cite": "Citation {} · Ablation +{}",
        "side_norag": "No-RAG {} → RAG {}",
        "eco_title": "🔗 MetaNutri Ecosystem",
        "eco": [("MetaNutri", "Full-stack precision nutrition platform",
                 "https://github.com/ElijahZhao/MetaNutri---AI-"),
                ("ppgr-predictor", "Post-meal glucose prediction",
                 "https://github.com/ElijahZhao/ppgr-predictor"),
                ("Nutri-RAG", "This repo · RAG diet Q&A",
                 "https://github.com/ElijahZhao/nutri-rag"),
                ("Live demo", "This very page",
                 "https://metanutri-ai-rag-question-answering.streamlit.app/")],
        "new_conv": "➕ New chat",
        "rename_btn": "✏️ Rename",
        "del_conv": "🗑 Delete",
        "rename_title": "Rename chat",
        "rename_ph": "New name",
        "save": "Save",
        "spinner": "Retrieving knowledge and generating the answer…",
        "cite_exp": "📎 Sources ({} items)",
        "cite_food": "Food",
        "cite_guide": "Guideline",
        "eval_title": "Offline evaluation · 50 questions · qwen-plus",
        "m_hit": "🎯 Retrieval Hit Rate",
        "m_faith": "✅ Faithfulness",
        "m_cite": "📚 Citation Rate",
        "m_ab": "🚀 Ablation Gain",
        "abl_title": "🔬 Ablation · Key-info coverage (No-RAG vs RAG)",
        "abl_norag": "No-RAG {}",
        "abl_rag": "+RAG {}",
        "abl_l1": "No-RAG direct answer: {}",
        "abl_l2": "RAG: {}",
        "abl_l3": "Gap concentrated in repo-exclusive numbers & detail questions; all RAG answers are citable",
        "by_cat": "By category",
        "cat_names": {"composition": "Composition (nutrient values)", "guideline": "Guidelines (diet advice)",
                      "special": "Cautions & special cases"},
        "th_cat": "Category", "th_hit": "Hit rate", "th_faith": "Faithfulness",
        "filter": "Filter category", "filter_all": "All",
        "filter_cats": {"composition": "Composition", "guideline": "Guideline", "special": "Cautions"},
        "th_id": "ID", "th_q": "Question", "th_hit2": "Hit", "th_cite2": "Citation",
        "th_rag": "RAG cover", "th_norag": "No-RAG cover",
        "caption": "{} rows · All 50: hit 50/50 · faithful 50/50 · citation 50/50",
        "eval_missing": "Evaluation report missing: data/eval_report.json not found",
        "footer": "⚠️ For research/demo purposes only, not medical advice. Consult a doctor or registered dietitian for health issues.",
    },
}

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
.block-container{padding-top:1.6rem;}
.hero{background:linear-gradient(135deg,var(--brand-soft),var(--card-bg) 60%);
  border:1px solid var(--border);border-radius:20px;padding:1.4rem 1.6rem;margin:.2rem 0 1rem;
  box-shadow:var(--shadow);}
.hero h1{font-size:2rem;font-weight:800;letter-spacing:-.02em;margin:0 0 .35rem;color:var(--text);}
.hero .sub{color:var(--muted);font-size:.98rem;margin:0 0 .9rem;}
.pills{display:flex;flex-wrap:wrap;gap:.5rem;}
.pill{background:var(--card-bg);color:var(--brand-dark);border:1px solid var(--brand);
  border-radius:999px;padding:.3rem .85rem;font-size:.82rem;font-weight:600;}
html[data-theme="dark"] .pill{color:#4ade80;}
.side-card{background:var(--card-bg);border:1px solid var(--border);border-radius:14px;
  padding:.9rem 1rem;margin-bottom:.8rem;box-shadow:var(--shadow);font-size:.88rem;}
.side-card .t{font-weight:700;color:var(--brand-dark);margin:.35rem 0 .2rem;font-size:.82rem;letter-spacing:.02em;}
html[data-theme="dark"] .side-card .t{color:#4ade80;}
.side-card .t:first-child{margin-top:0;}
.side-card .row{color:var(--text);margin:.1rem 0;}
.side-card .muted{color:var(--muted);font-size:.8rem;}
.side-ecosystem{font-size:.86rem;line-height:1.9;}
.side-ecosystem .ec-title{font-weight:700;color:var(--brand-dark);margin-bottom:.2rem;}
html[data-theme="dark"] .side-ecosystem .ec-title{color:#4ade80;}
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
div[data-testid="stChatInput"]{border:1.5px solid var(--brand);border-radius:14px;box-shadow:var(--shadow);}
div[data-testid="stChatInput"]:focus-within{box-shadow:0 0 0 3px rgba(22,163,74,.18);}
div[data-testid="stChatInput"] textarea{font-size:.95rem;}
div[data-testid="stChatMessage"]{background:var(--card-bg);border:1px solid var(--border);
  border-radius:16px;padding:.35rem .8rem;margin-bottom:.55rem;box-shadow:var(--shadow);}
.stButton > button{border-radius:999px;border:1px solid var(--border);background:var(--card-bg);
  font-weight:600;color:var(--text);transition:all .15s ease;}
.stButton > button:hover{border-color:var(--brand);color:var(--brand);box-shadow:0 0 0 3px rgba(22,163,74,.12);}
div[data-testid="stTabs"] button[aria-selected="true"]{color:var(--brand);font-weight:700;}
div[data-testid="stRadio"] label{border-radius:10px;padding:.3rem .6rem;transition:background .12s ease;}
div[data-testid="stRadio"] label:hover{background:var(--brand-soft);}
[data-testid="stSidebar"] .stTextInput input{border-radius:10px;border:1px solid var(--border);}
@media (max-width:900px){.metric-grid{grid-template-columns:repeat(2,1fr);}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------ state init
if "lang" not in st.session_state:
    st.session_state.lang = "zh"
if "conversations" not in st.session_state:
    st.session_state.conversations = {"conv_0": {"title": "", "messages": []}}
    st.session_state.current_conv = "conv_0"

L = I18N[st.session_state.lang]


# ---------------------------------------------------------------- rename dialog
@st.dialog(L["rename_title"])
def rename_dialog(cid):
    conv = st.session_state.conversations[cid]
    new_title = st.text_input(L["rename_ph"], value=conv["title"] or "对话",
                              label_visibility="collapsed")
    c1, c2 = st.columns(2)
    if c1.button(L["save"], use_container_width=True):
        conv["title"] = new_title.strip()
        st.rerun()
    if c2.button("✕", use_container_width=True):
        st.rerun()


# ------------------------------------------------------------------ sidebar
def _load_summary():
    rep_path = ROOT / "data" / "eval_report.json"
    if not rep_path.exists():
        return None
    return json.loads(rep_path.read_text(encoding="utf-8"))["summary"]


with st.sidebar:
    lang_sel = st.segmented_control("Language", ["中文", "English"],
                                    label_visibility="collapsed")
    if lang_sel:
        new_lang = "zh" if lang_sel == "中文" else "en"
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

    s = _load_summary()
    if s:
        hit_pct, faith_pct = f"{s['retrieval_hit_rate']:.0%}", f"{s['faithfulness']:.0%}"
        cite_pct, ab_pct = f"{s['rag_citation_rate']:.0%}", f"{s['ablation_gain']:.0%}"
        norag_pct, rag_pct = f"{s['gold_cover_norag']:.0%}", f"{s['gold_cover_rag']:.0%}"
        size_html = (
            f"<div class='side-card'>"
            f"<div class='t'>{L['side_data']}</div>"
            f"<div class='row'>{L['side_data_rows'][0]}</div>"
            f"<div class='row'>{L['side_data_rows'][1]}</div>"
            f"<div class='t'>{L['side_eval']}</div>"
            f"<div class='row'>{L['side_hit'].format(hit_pct, faith_pct)}</div>"
            f"<div class='row'>{L['side_cite'].format(cite_pct, ab_pct)}</div>"
            f"<div class='muted'>{L['side_norag'].format(norag_pct, rag_pct)}</div>"
            f"</div>"
        )
    else:
        size_html = "<div class='side-card muted'>eval report missing</div>"
    st.markdown(size_html, unsafe_allow_html=True)

    eco_items = "".join(
        f"· <a href='{u}'>{name}</a> — {desc}<br>" for name, desc, u in L["eco"]
    )
    st.markdown(
        f'<div class="side-ecosystem"><div class="ec-title">{L["eco_title"]}</div>{eco_items}</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    convs = st.session_state.conversations
    cur = st.session_state.current_conv

    if st.button(L["new_conv"], use_container_width=True):
        cid = f"conv_{len(convs)}"
        st.session_state.conversations[cid] = {"title": "", "messages": []}
        st.session_state.current_conv = cid
        st.rerun()

    def _conv_label(cid):
        t = convs[cid]["title"]
        return t if t else f"对话 {list(convs).index(cid) + 1}"

    sel = st.radio(
        "会话", list(convs), index=list(convs).index(cur),
        format_func=_conv_label, label_visibility="collapsed",
    )
    if sel != cur:
        st.session_state.current_conv = sel
        st.rerun()

    c1, c2 = st.columns(2)
    if c1.button(L["rename_btn"], use_container_width=True):
        rename_dialog(cur)
    if len(convs) > 1 and c2.button(L["del_conv"], use_container_width=True):
        del st.session_state.conversations[cur]
        st.session_state.current_conv = next(k for k in convs if k != cur)
        st.rerun()

# ---------------------------------------------------------------------- hero
st.markdown(
    f"""
    <div class="hero">
      <h1>{L['hero_title']}</h1>
      <p class="sub">{L['hero_sub']}</p>
      <div class="pills">
        <span class="pill">{L['pill_kb']}</span>
        <span class="pill">{L['pill_eval']}</span>
        <span class="pill">{L['pill_dual']}</span>
        <span class="pill">{L['pill_cite']}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<p class="chat-hint">{L["hint"]}</p>', unsafe_allow_html=True)


@st.cache_resource
def load_engine():
    return Retriever(), Generator()


retriever, generator = load_engine()

EXAMPLES = L["examples"]


def ask(question):
    conv = st.session_state.conversations[st.session_state.current_conv]
    conv["messages"].append({"role": "user", "content": question})
    if not conv["title"]:
        conv["title"] = question[:14] + ("…" if len(question) > 14 else "")
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner(L["spinner"]):
            hits = retriever.search(question, top_k=TOP_K)
            answer = generator.answer(question, hits)
        st.markdown(answer)
        cites = sorted(set(c for c in extract_citations(answer) if 1 <= c <= len(hits)))
        if cites:
            with st.expander(L["cite_exp"].format(len(cites))):
                for n in cites:
                    src = hits[n - 1]
                    typ = "food" if src.get("type") == "food" else "guide"
                    tag = L["cite_food"] if typ == "food" else L["cite_guide"]
                    head = html.escape(src["text"].strip().split("\n")[0][:60])
                    body = html.escape(src["text"][:400])
                    st.markdown(
                        f'<div class="cite-card"><div class="head">'
                        f'<span class="cite-badge">[{n}]</span>'
                        f'<span class="cite-tag {typ}">{tag}</span>'
                        f'<span style="color:var(--muted);font-size:.82rem;">{head}</span></div>'
                        f'<div class="body">{body}</div></div>',
                        unsafe_allow_html=True,
                    )
    conv["messages"].append({"role": "assistant", "content": answer})


tab_chat, tab_eval = st.tabs([L["tab_chat"], L["tab_eval"]])

with tab_chat:
    conv = st.session_state.conversations[st.session_state.current_conv]

    for m in conv["messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    cols = st.columns(len(EXAMPLES))
    for col, q in zip(cols, EXAMPLES):
        if col.button(q, use_container_width=True):
            ask(q)

    if prompt := st.chat_input(L["input_ph"]):
        ask(prompt)

with tab_eval:
    st.markdown(f"#### {L['eval_title']}")
    rep_path = ROOT / "data" / "eval_report.json"
    if rep_path.exists():
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
        s = rep["summary"]
        st.markdown(
            f"""
            <div class="metric-grid">
              <div class="metric-card"><div class="m-label">{L['m_hit']}</div>
                <div class="m-value ok">{s['retrieval_hit_rate']:.0%}</div></div>
              <div class="metric-card"><div class="m-label">{L['m_faith']}</div>
                <div class="m-value ok">{s['faithfulness']:.0%}</div></div>
              <div class="metric-card"><div class="m-label">{L['m_cite']}</div>
                <div class="m-value ok">{s['rag_citation_rate']:.0%}</div></div>
              <div class="metric-card"><div class="m-label">{L['m_ab']}</div>
                <div class="m-value plus">+{s['ablation_gain']:.0%}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        norag = s["gold_cover_norag"]
        rag = s["gold_cover_rag"]
        norag_str, rag_str = f"{norag*100:.0f}", f"{rag*100:.0f}"
        gap_str = f"{(rag-norag)*100:.0f}"
        st.markdown(
            f"""
            <div class="ablation">
              <div class="a-title">{L['abl_title']}</div>
              <div class="bar">
                <div class="seg" style="width:{norag_str}%;background:#d1d5db;color:#374151;">
                  {L['abl_norag'].format(norag_str)}</div>
                <div class="seg rag" style="width:{gap_str}%;">
                  {L['abl_rag'].format(gap_str)}</div>
              </div>
              <div class="legend"><span>{L['abl_l1'].format(norag_str)}</span>
                <span>{L['abl_l2'].format(rag_str)}</span>
                <span>{L['abl_l3']}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader(L["by_cat"])
        bc = rep["by_category"]
        cat_rows = "".join(
            f"<tr><td>{L['cat_names'][k]}</td><td>{bc[k]['retrieval_hit_rate']:.0%}</td>"
            f"<td>{bc[k]['faithfulness']:.0%}</td></tr>"
            for k in ("composition", "guideline", "special")
        )
        st.markdown(
            f"<table class='dtable'><tr><th>{L['th_cat']}</th><th>{L['th_hit']}</th>"
            f"<th>{L['th_faith']}</th></tr>{cat_rows}</table>",
            unsafe_allow_html=True,
        )

        cat_map = L["filter_cats"]
        sel_cat = st.selectbox(
            L["filter"], [L["filter_all"]] + list(cat_map.values())
        )
        rows = [
            it for it in rep["items"]
            if sel_cat == L["filter_all"] or cat_map.get(it["category"]) == sel_cat
        ]
        if rows:
            detail_html = (
                f"<table class='dtable'><tr><th>{L['th_id']}</th><th>{L['th_cat']}</th>"
                f"<th>{L['th_q']}</th><th>{L['th_hit2']}</th><th>{L['th_cite2']}</th>"
                f"<th>{L['th_rag']}</th><th>{L['th_norag']}</th></tr>"
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
        st.caption(L["caption"].format(len(rows)))
    else:
        st.info(L["eval_missing"])

st.markdown(f'<div class="footer">{L["footer"]}</div>', unsafe_allow_html=True)
