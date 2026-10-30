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
from src.hybrid import HybridRetriever  # noqa: E402

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
                     "反式脂肪酸每天摄入量上限是多少？", "高尿酸人群能吃哪些豆制品？",
                     "每100克牛奶含多少钙？", "吃鸡蛋要不要弃蛋黄？"],
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
        "rename_btn": "重命名",
        "pin_btn": "置顶",
        "unpin_btn": "取消置顶",
        "del_conv": "删除",
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
        "err_api": "服务暂时不可用，请稍后重试；若持续失败请检查 API 配置。",
        "vis_title": "🧭 评测覆盖总览 · 50 题",
        "vis_norag": "无 RAG 覆盖 {0} · RAG 补齐 {1}",
        "vis_ok": "双覆盖（RAG + 无 RAG）",
        "vis_gain": "RAG 增量补齐（无 RAG 未覆盖）",
        "vis_hint": "悬停每格查看题目；橙色 = RAG 增量价值所在",
        "ref_title": "🛡️ 拒答评测 · 防幻觉（10 条资料外问题）",
        "ref_sub": "资料不足时，系统正确拒答（明确说“资料未收录”）而不是编造的比例",
        "ref_col": ["系统", "拒答率"],
        "ref_rag": "Nutri-RAG（RAG 管线）",
        "ref_norag": "裸 LLM（无 RAG）",
        "ref_strict": "裸 LLM + 强制拒答指令",
        "ref_exp": "查看逐条拒答原文（{} 条）",
        "ref_q": "问题", "ref_ans": "回答摘录", "ref_ok": "✅ 正确拒答", "ref_bad": "❌ 编造/未拒答",
        "ref_note": "结论：检索 + 明确的知识库边界才是防幻觉的根本，仅靠提示词不够",
        "sweep_title": "🔬 超参数消融 · top-k × 相似度阈值（9 组 × 50 题）",
        "sweep_col": ["top-k", "阈值", "检索命中", "引用", "关键覆盖", "忠实度"],
        "sweep_opt": "🏆 最优点：top-k = 5、不加阈值（全部 100%）—— 已设为默认",
        "sweep_note": "top-k=3 有 3 题源切片挤不进上下文；top-k=8 上下文过长、偶发遗漏关键信息；阈值在 0.5 以下影响有限",
        "hyb_title": "🧪 混合检索对比 · BM25 + 向量（RRF 融合）",
        "hyb_col": ["模式", "检索命中", "引用", "忠实度"],
        "hyb_vec": "纯向量（当前默认）",
        "hyb_mix": "混合（BM25 + 向量）",
        "hyb_note": "检索层无增益（纯向量已饱和），融合上下文偶发诱导越界引用编号 → 保持纯向量默认",
        "ea_title": "🔍 消融失败案例 · 裸 LLM 为什么答错（6 条）",
        "ea_hint": "展开查看：同样的 50 题，无 RAG 时这 6 条被 LLM 答错/答偏",
        "ea_mode": "失败模式",
        "ea_norag": "裸 LLM（无 RAG）",
        "ea_rag": "RAG（带引用）",
        "ea_modes": {"precision": "精度损失", "source": "区域数据错位",
                     "stance": "立场混合", "framework": "框架/经验替代规范"},
        "ea_see": "查看完整归因 → docs/error-analysis.md",
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
                     "What is the daily upper limit for trans fatty acids?",
                     "Which soy products can people with high uric acid eat?",
                     "How much calcium is in 100g of milk?",
                     "Should I discard the egg yolk when eating eggs?",
                     "What foods should a nutritious breakfast include?",
                     "How much protein is in 100g of pork tenderloin?"],
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
        "rename_btn": "Rename",
        "pin_btn": "Pin",
        "unpin_btn": "Unpin",
        "del_conv": "Delete",
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
        "err_api": "Service temporarily unavailable — please retry shortly; if it persists, check the API configuration.",
        "vis_title": "🧭 Evaluation Coverage Overview · 50 items",
        "vis_norag": "No-RAG coverage {0} · RAG recovered {1}",
        "vis_ok": "Covered both ways (RAG + no-RAG)",
        "vis_gain": "Recovered by RAG (missed without RAG)",
        "vis_hint": "Hover a cell to see the question; orange = where RAG adds value",
        "ref_title": "🛡️ Refusal Evaluation · Anti-hallucination (10 out-of-scope questions)",
        "ref_sub": "When knowledge is insufficient, how often does the system correctly refuse (\"not in the sources\") instead of fabricating?",
        "ref_col": ["System", "Refusal rate"],
        "ref_rag": "Nutri-RAG (RAG pipeline)",
        "ref_norag": "Bare LLM (no RAG)",
        "ref_strict": "Bare LLM + forced-refusal instruction",
        "ref_exp": "View per-item refusal answers ({})",
        "ref_q": "Question", "ref_ans": "Answer excerpt", "ref_ok": "✅ Correctly refused", "ref_bad": "❌ Fabricated / not refused",
        "ref_note": "Takeaway: retrieval + an explicit knowledge-base boundary — not prompting alone — prevents hallucination",
        "sweep_title": "🔬 Hyper-parameter Sweep · top-k × similarity threshold (9 runs × 50 questions)",
        "sweep_col": ["top-k", "Threshold", "Hit", "Citation", "Coverage", "Faithfulness"],
        "sweep_opt": "🏆 Sweet spot: top-k = 5, no threshold (all 100%) — now the default",
        "sweep_note": "top-k=3: 3 source chunks cannot fit in context; top-k=8: longer context, occasional omission; threshold negligible below 0.5",
        "hyb_title": "🧪 Hybrid Retrieval Comparison · BM25 + vector (RRF fusion)",
        "hyb_col": ["Mode", "Hit", "Citation", "Faithfulness"],
        "hyb_vec": "Vector only (current default)",
        "hyb_mix": "Hybrid (BM25 + vector)",
        "hyb_note": "No retrieval gain (pure vector already saturated); fused context occasionally induces out-of-range citations → keep vector default",
        "ea_title": "🔍 Ablation Failure Cases · Why the bare LLM misses (6 items)",
        "ea_hint": "Expand to compare no-RAG vs RAG answers on the 6 cases a bare LLM gets wrong",
        "ea_mode": "Failure mode",
        "ea_norag": "Bare LLM (no RAG)",
        "ea_rag": "RAG (with citations)",
        "ea_modes": {"precision": "Precision loss", "source": "Regional data mismatch",
                     "stance": "Stance blending", "framework": "Framework/habit replacing rule"},
        "ea_see": "Full error analysis → docs/error-analysis.md",
        "footer": "⚠️ For research/demo purposes only, not medical advice. Consult a doctor or registered dietitian for health issues.",
    },
}

# ---------------------------------------------------------------- brand css
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+SC:wght@400;600;700;900&display=swap');
:root{
  --brand:#15803d; --brand-dark:#14532d; --brand-soft:#f3f7f1;
  --accent:#d97706; --card-bg:#ffffff; --text:#1f2937; --muted:#6b7280;
  --border:#e5e7eb;
  --shadow:0 1px 3px rgba(16,24,40,.06),0 1px 2px rgba(16,24,40,.04);
  --font-sans:'Inter','Noto Sans SC',system-ui,sans-serif;
}
html[data-theme="dark"]{
  --card-bg:#1e293b; --text:#f1f5f9; --muted:#94a3b8; --border:#334155; --brand-soft:#122a1d; --sidebar-bg:#161b22;
}
*{font-family:var(--font-sans);}
.block-container{padding-top:1.6rem;}
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(1100px 520px at 8% -4%, rgba(21,128,61,.05), transparent 60%),
    radial-gradient(900px 480px at 105% 2%, rgba(217,119,6,.04), transparent 55%),
    linear-gradient(180deg,#fbfaf7 0%,#f6f4ef 100%);
}
[data-testid="stSidebar"]{background:var(--sidebar-bg,#faf9f6);}
[data-testid="stSidebar"] > div:first-child{border-right:1px solid var(--border);}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{background:transparent;}
.hero{position:relative;overflow:hidden;border:1px solid var(--border);border-radius:22px;
  padding:1.5rem 1.7rem;margin:.2rem 0 1rem;box-shadow:var(--shadow);
  background:linear-gradient(120deg,#eef4ea 0%,#ffffff 42%,#fdf6e8 78%,#f0f5ec 100%);
  background-size:220% 220%;animation:heroShift 16s ease-in-out infinite;}
@keyframes heroShift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.hero::after{content:"";position:absolute;top:-70px;right:-70px;width:220px;height:220px;
  background:radial-gradient(circle,rgba(21,128,61,.10),transparent 65%);pointer-events:none;}
.hero h1{font-size:2.05rem;font-weight:900;letter-spacing:-.02em;margin:0 0 .35rem;color:var(--text);}
.hero .sub{color:var(--muted);font-size:.97rem;margin:0 0 .95rem;}
.pills{display:flex;flex-wrap:wrap;gap:.55rem;}
.pill{background:var(--card-bg);color:var(--brand-dark);border:1px solid var(--brand);
  border-radius:999px;padding:.32rem .9rem;font-size:.82rem;font-weight:600;
  transition:transform .15s ease,box-shadow .15s ease;}
.pill:hover{transform:translateY(-2px);box-shadow:0 6px 14px rgba(21,128,61,.18);}
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
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.85rem;margin:.6rem 0 1.1rem;}
.metric-card{background:var(--card-bg);border:1px solid var(--border);border-radius:14px;
  padding:.9rem 1rem;box-shadow:var(--shadow);transition:transform .15s ease,box-shadow .15s ease;}
.metric-card:hover{transform:translateY(-3px);box-shadow:0 10px 22px rgba(16,24,40,.10);}
.metric-card .m-label{color:var(--muted);font-size:.8rem;font-weight:600;margin-bottom:.3rem;}
.metric-card .m-value{font-size:1.7rem;font-weight:900;letter-spacing:-.02em;}
.metric-card .m-value.ok{color:var(--brand);}
.metric-card .m-value.plus{color:var(--accent);}
.cite-card{background:var(--card-bg);border:1px solid var(--border);border-left:3px solid var(--brand);
  border-radius:10px;padding:.6rem .8rem;margin:.45rem 0;box-shadow:var(--shadow);
  transition:border-color .12s ease;}
.cite-card:hover{border-left-color:var(--accent);}
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
div[data-testid="stChatInput"]:focus-within{box-shadow:0 0 0 3px rgba(21,128,61,.18);}
div[data-testid="stChatInput"] textarea{font-size:.95rem;}
div[data-testid="stChatMessage"]{background:var(--card-bg);border:1px solid var(--border);
  border-radius:16px;padding:.35rem .8rem;margin-bottom:.55rem;box-shadow:var(--shadow);
  transition:box-shadow .15s ease;}
div[data-testid="stChatMessage"]:hover{box-shadow:0 6px 16px rgba(16,24,40,.08);}
.stButton > button{border-radius:999px;border:1px solid var(--border);background:var(--card-bg);
  font-weight:600;color:var(--text);transition:all .15s ease;}
.stButton > button:hover{border-color:var(--brand);color:var(--brand);box-shadow:0 0 0 3px rgba(21,128,61,.12);}
div[data-testid="stTabs"] button[aria-selected="true"]{color:var(--brand);font-weight:700;}
[data-testid="stSidebar"] [data-testid="stButton"] > button{font-size:.84rem;text-align:left;}
[data-testid="stSidebar"] [data-testid="stPopover"] > button{border-radius:10px;font-weight:700;color:var(--muted);}
.eval-vis{background:var(--card-bg);border:1px solid var(--border);border-radius:14px;
  padding:1rem 1.2rem;margin:.6rem 0 1.1rem;box-shadow:var(--shadow);}
.vis-title{font-weight:700;margin-bottom:.8rem;font-size:.95rem;}
.cat-sec{margin-bottom:.85rem;}
.cat-sec-name{font-size:.8rem;font-weight:600;color:var(--muted);margin-bottom:.35rem;}
.matrix{display:grid;grid-template-columns:repeat(10,1fr);gap:4px;}
.mcell{aspect-ratio:1.6/1;border-radius:5px;display:flex;align-items:center;justify-content:center;
  font-size:.6rem;font-weight:700;color:#fff;cursor:help;transition:transform .1s ease;}
.mcell.ok{background:#15803d;}
.mcell.gain{background:#d97706;}
.mcell:hover{transform:scale(1.15);box-shadow:0 2px 8px rgba(16,24,40,.25);z-index:2;}
.vis-legend{display:flex;align-items:center;gap:.5rem;font-size:.8rem;color:var(--muted);
  margin:.9rem 0 .3rem;flex-wrap:wrap;}
.vis-hint{font-size:.76rem;color:var(--muted);}
.lg{width:14px;height:14px;border-radius:4px;display:inline-block;margin-left:.4rem;}
.lg-ok{background:#15803d;}
.lg-gain{background:#d97706;}
.dtable-wrap{overflow-x:auto;border-radius:12px;}
.qa-mini{background:var(--brand-soft);border-left:3px solid var(--brand);border-radius:8px;
  padding:.5rem .75rem;margin:.2rem 0 .6rem;color:var(--text);font-size:.88rem;line-height:1.55;}
.qa-mini.bad{background:#fdf2f2;border-left-color:#dc2626;}
.qa-mini.good{background:var(--brand-soft);border-left-color:var(--brand);}
/* 自定义 tab（segmented control）突出样式 —— 仅主区，不影响侧边栏语言组 */
.stMain [data-testid="stButtonGroup"] {
  width: 100%;
  gap: .35rem;
  background: var(--brand-soft);
  border: 1px solid transparent;
  border-radius: 12px;
  padding: .25rem;
}
.stMain [data-testid="stButtonGroup"] button {
  font-size: 1.02rem;
  font-weight: 650;
  padding: .5rem 1.1rem;
  border-radius: 9px;
  transition: all .15s ease;
}
.stMain [data-testid="stButtonGroup"] button[aria-checked="true"] {
  background: var(--brand);
  color: #fff;
  border-color: var(--brand);
  box-shadow: 0 2px 8px rgba(23, 132, 98, .28);
}
.stMain [data-testid="stButtonGroup"] button:not([aria-checked="true"]):hover {
  background: #fff;
  border-color: var(--brand);
  color: var(--brand);
}
@media (max-width:900px){
  .stMain [data-testid="stButtonGroup"]{padding:.15rem;gap:.2rem;}
  .stMain [data-testid="stButtonGroup"] button{font-size:.85rem;padding:.35rem .45rem;}
  .metric-grid{grid-template-columns:repeat(2,1fr);}
  .matrix{grid-template-columns:repeat(5,1fr);}
  .mcell{aspect-ratio:1.2/1;}
  .hero h1{font-size:1.5rem;}
  .hero{padding:1.1rem 1.2rem;}
  .pill{font-size:.76rem;padding:.26rem .7rem;}
  .side-ecosystem{font-size:.8rem;}
  .dtable{min-width:640px;}
  .stButton > button{font-size:.76rem;padding:.3rem .5rem;}
}
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


# ------------------------------------------------------- inline rename (DeepSeek-style)
def _commit_rename(cid):
    val = st.session_state.get(f"rename_{cid}", "").strip()
    if val:
        st.session_state.conversations[cid]["title"] = val
    st.session_state.renaming_cid = None


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
        st.session_state.conversations[cid] = {"title": "", "messages": [], "pinned": False}
        st.session_state.current_conv = cid
        st.rerun()

    def _conv_label(cid):
        t = convs[cid]["title"]
        return t if t else f"对话 {list(convs).index(cid) + 1}"

    # pinned first, then creation order
    order = sorted(
        list(convs),
        key=lambda c: (not convs[c].get("pinned", False), list(convs).index(c)),
    )
    for cid in order:
        label = _conv_label(cid)
        if st.session_state.get("renaming_cid") == cid:
            st.text_input(
                L["rename_title"], value=label, key=f"rename_{cid}", label_visibility="collapsed",
                on_change=_commit_rename, args=(cid,), placeholder=L["rename_ph"],
            )
            continue
        marker = "🟢 " if cid == cur else "   "
        c1, c2 = st.columns([0.78, 0.22], vertical_alignment="center")
        if c1.button(f"{marker}{label}", use_container_width=True, key=f"conv_{cid}"):
            if cid != cur:
                st.session_state.current_conv = cid
                st.rerun()
        with c2.popover("⋮", key=f"menu_{cid}"):
            if st.button("✏️ " + L["rename_btn"], use_container_width=True):
                st.session_state.pop(f"rename_{cid}", None)  # clear stale widget state
                st.session_state.renaming_cid = cid
                st.rerun()
            pinned = convs[cid].get("pinned", False)
            pin_label = ("📌 " + L["unpin_btn"]) if pinned else ("📌 " + L["pin_btn"])
            if st.button(pin_label, use_container_width=True):
                convs[cid]["pinned"] = not pinned
                st.rerun()
            if len(convs) > 1 and st.button("🗑 " + L["del_conv"], use_container_width=True):
                del st.session_state.conversations[cid]
                if cid == cur:
                    st.session_state.current_conv = next(k for k in convs if k != cid)
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
    return HybridRetriever(top_k=TOP_K), Generator()


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
        try:
            with st.spinner(L["spinner"]):
                hits = retriever.search(question, top_k=TOP_K)
            answer = st.write_stream(
                generator.answer_stream(question, hits, language=st.session_state.lang)
            )
        except Exception as e:
            # API / network / quota failures: show a readable error instead of a crash page
            msg = L["err_api"]
            st.error(msg)
            conv["messages"].append({"role": "assistant", "content": msg})
            return
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


# ------------------------------------------------------------------ custom tabs
# session_state-driven views instead of st.tabs: chat history, streaming
# answers and the input box live only inside the chat view, so switching to
# the eval view shows a clean page (no input box, no leaked conversation).
st.session_state.setdefault("tab", "chat")

_tab_sel = st.segmented_control(
    "",
    [L["tab_chat"], L["tab_eval"]],
    default=L["tab_chat"] if st.session_state.tab == "chat" else L["tab_eval"],
    key="tab_sel",
    label_visibility="collapsed",
)
# widget 值是权威：点击后 Streamlit 自带 rerun，这里直接取最新值
tab_now = "eval" if _tab_sel == L["tab_eval"] else "chat"
st.session_state["tab"] = tab_now

if tab_now == "chat":
    conv = st.session_state.conversations[st.session_state.current_conv]

    for m in conv["messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    _ncol = 4 if st.session_state.lang == "en" else 3
    for i in range(0, len(EXAMPLES), _ncol):
        cols = st.columns(_ncol)
        for col, q in zip(cols, EXAMPLES[i:i + _ncol]):
            if col.button(q, use_container_width=True):
                ask(q)

    if prompt := st.chat_input(L["input_ph"], key="main_chat_input"):
        ask(prompt)

else:
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
        # ---- coverage matrix + per-category sections ----
        cat_keys = ("composition", "guideline", "special")
        cat_secs = ""
        for k in cat_keys:
            sub = [it for it in rep["items"] if it["category"] == k]
            npct = sum(1 for it in sub if it["gold_covered_norag"]) / len(sub)
            npct_str, gap_str = f"{npct:.0%}", f"{1 - npct:.0%}"
            cells = "".join(
                f'<div class="mcell {"ok" if (it["gold_covered_norag"] and it["gold_covered_rag"]) else "gain"}'
                f' title="{html.escape(it["id"] + " · " + it["question"])}">{it["id"]}</div>'
                for it in sub
            )
            cat_secs += (
                f'<div class="cat-sec"><div class="cat-sec-name">{L["cat_names"][k]} · {len(sub)}'
                f' · {L["vis_norag"].format(npct_str, gap_str)}</div>'
                f'<div class="matrix">{cells}</div></div>'
            )
        st.markdown(
            f"""
            <div class="eval-vis">
              <div class="vis-title">{L['vis_title']}</div>
              {cat_secs}
              <div class="vis-legend">
                <span class="lg lg-ok"></span>{L['vis_ok']}
                <span class="lg lg-gain"></span>{L['vis_gain']}
              </div>
              <div class="vis-hint">{L['vis_hint']}</div>
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
            f"<div class='dtable-wrap'><table class='dtable'><tr><th>{L['th_cat']}</th><th>{L['th_hit']}</th>"
            f"<th>{L['th_faith']}</th></tr>{cat_rows}</table></div>",
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
            st.markdown(
                f"<div class='dtable-wrap'>{detail_html}</div>", unsafe_allow_html=True
            )
        st.caption(L["caption"].format(len(rows)))
    else:
        st.info(L["eval_missing"])

    # ------------------------------------------------------------- 1) refusal eval
    ref_path = ROOT / "data" / "refusal_report.json"
    if ref_path.exists():
        rep_r = json.loads(ref_path.read_text(encoding="utf-8"))
        rs = rep_r["summary"]
        pct = lambda x: f"{x*100:.0f}%"
        st.markdown(f"### {L['ref_title']}")
        st.caption(L["ref_sub"])
        rows_r = [
            (L["ref_rag"], rs["refusal_rate_rag"]),
            (L["ref_norag"], rs["refusal_rate_norag"]),
            (L["ref_strict"], rs["refusal_rate_strict_assistant"]),
        ]
        tbl_r = f"<table class='dtable'><tr><th>{L['ref_col'][0]}</th><th>{L['ref_col'][1]}</th></tr>"
        for name, v in rows_r:
            ok = "✓" if v == 1.0 else ("△" if v >= 0.5 else "✗")
            tbl_r += f"<tr><td>{name}</td><td>{pct(v)} {ok}</td></tr>"
        st.markdown(f"<div class='dtable-wrap'>{tbl_r}</table></div>", unsafe_allow_html=True)
        with st.expander(L["ref_exp"].format(rs["n"])):
            for it in rep_r["items"]:
                tag = L["ref_ok"] if it["refused_rag"] else L["ref_bad"]
                st.markdown(f"**{it['id']} · {it['question']}** — {tag}")
                st.markdown(f"<div class='qa-mini'>{html.escape(it['answer_rag'][:220])}</div>",
                            unsafe_allow_html=True)
        st.caption(f"💡 {L['ref_note']}")
    else:
        st.caption("refusal_report.json 缺失")

    # ------------------------------------------------------------- 2) hyper-param sweep
    sweep_path = ROOT / "data" / "sweep_report.json"
    if sweep_path.exists():
        rep_s = json.loads(sweep_path.read_text(encoding="utf-8"))
        st.markdown(f"### {L['sweep_title']}")
        tbl_s = f"<table class='dtable'><tr>{''.join(f'<th>{c}</th>' for c in L['sweep_col'])}</tr>"
        for r_ in rep_s["rows"]:
            hit = f"{r_['retrieval_hit_rate']*100:.0f}%"
            cite = f"{r_['citation_rate']*100:.0f}%"
            cover = f"{r_['gold_cover_rate']*100:.0f}%"
            faith = f"{r_['faithfulness']*100:.0f}%"
            hi = " style='font-weight:700;color:var(--brand);'" if (
                r_["retrieval_hit_rate"] == 1.0 and r_["faithfulness"] == 1.0
                and r_["citation_rate"] == 1.0 and r_["gold_cover_rate"] == 1.0
            ) else ""
            tbl_s += (f"<tr><td{hi}>{r_['top_k']}</td><td>{r_['min_score']}</td>"
                      f"<td{hi}>{hit}</td><td{hi}>{cite}</td><td{hi}>{cover}</td><td{hi}>{faith}</td></tr>")
        st.markdown(f"<div class='dtable-wrap'>{tbl_s}</table></div>", unsafe_allow_html=True)
        st.markdown(f"**{L['sweep_opt']}**")
        st.caption(L["sweep_note"])
    else:
        st.caption("sweep_report.json 缺失")

    # ------------------------------------------------------------- 3) hybrid comparison
    hyb_path = ROOT / "data" / "hybrid_report.json"
    if hyb_path.exists():
        rep_h = json.loads(hyb_path.read_text(encoding="utf-8"))
        st.markdown(f"### {L['hyb_title']}")
        tbl_h = f"<table class='dtable'><tr>{''.join(f'<th>{c}</th>' for c in L['hyb_col'])}</tr>"
        for key, name in (("vector", L["hyb_vec"]), ("hybrid", L["hyb_mix"])):
            v = rep_h["summary"][key]
            tbl_h += (f"<tr><td>{name}</td><td>{v['retrieval_hit_rate']*100:.0f}%</td>"
                      f"<td>{v['citation_rate']*100:.0f}%</td><td>{v['faithfulness']*100:.0f}%</td></tr>")
        st.markdown(f"<div class='dtable-wrap'>{tbl_h}</table></div>", unsafe_allow_html=True)
        st.caption(f"💡 {L['hyb_note']}")
    else:
        st.caption("hybrid_report.json 缺失")

    # ------------------------------------------------------------- 4) ablation failure cases
    ea_ids = ("C05", "C09", "C15", "S06", "S09", "S13")
    ea_modes = {"C05": "precision", "C09": "precision", "C15": "source",
                "S06": "stance", "S09": "framework", "S13": "framework"}
    if rep_path.exists():
        rep_e = json.loads(rep_path.read_text(encoding="utf-8"))
        cases = [it for it in rep_e["items"] if it["id"] in ea_ids]
        cases.sort(key=lambda x: ea_ids.index(x["id"]))
        st.markdown(f"### {L['ea_title']}")
        st.caption(L["ea_hint"])
        for it in cases:
            mode = L["ea_modes"][ea_modes[it["id"]]]
            with st.expander(f"{it['id']} · {it['question']} — [{L['ea_mode']}：{mode}]"):
                st.markdown(f"**{L['ea_norag']}**")
                st.markdown(f"<div class='qa-mini bad'>{html.escape(it['answer_norag'][:260])}</div>",
                            unsafe_allow_html=True)
                st.markdown(f"**{L['ea_rag']}**")
                st.markdown(f"<div class='qa-mini good'>{html.escape(it['answer_rag'][:260])}</div>",
                            unsafe_allow_html=True)
        st.caption(L["ea_see"])

st.markdown(f'<div class="footer">{L["footer"]}</div>', unsafe_allow_html=True)
