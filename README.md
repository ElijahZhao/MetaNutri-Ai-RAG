<div align="center">

# 🥗 Nutri-RAG

**Health-diet Q&A via Retrieval-Augmented Generation** — the LLM research module of the MetaNutri ecosystem

[![Online Demo](https://img.shields.io/badge/Streamlit-Online%20Demo-FF4B4B?logo=streamlit&logoColor=white)](https://metanutri-ai-rag-question-answering.streamlit.app/)
[![CI](https://github.com/ElijahZhao/nutri-rag/actions/workflows/ci-gates.yml/badge.svg)](https://github.com/ElijahZhao/nutri-rag/actions/workflows/ci-gates.yml)
[![License](https://img.shields.io/github/license/ElijahZhao/nutri-rag?color=8b5cf6)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)]()
[![Vector DB](https://img.shields.io/badge/VectorDB-ChromaDB-4ea94b)]()
[![LLM](https://img.shields.io/badge/LLM-qwen--plus-FF6B6B)]()
[![Embedding](https://img.shields.io/badge/Embedding-text--embedding--v3-8b5cf6)]()

</div>

**Nutri-RAG** is a research-grade RAG application that answers health-diet questions grounded in official Chinese nutrition data: the *China Food Composition Tables* (325 foods × 32 nutrients) and the *Dietary Guidelines for Chinese Residents (2022)* (8 principles + detailed practices).

## ✨ Highlights

- **Balanced two-path retrieval** — food chunks and guideline chunks are queried separately with equal quota, so guideline recommendations are never squeezed out by 325 food chunks
- **Citation-grounded answers** — every key claim carries a `[n]` reference to its source chunk, making answers fully traceable
- **Built-in evaluation** — 50-case eval set (composition / guideline / special) with no-RAG vs RAG ablation, regenerable with one command
- **Reproducible data pipeline** — official data sources, scraper → clean → chunk → vector store, all scripted
- **Lightweight deployment** — single-process Streamlit app on the free tier; vector store auto-restored from tarball

## 🏗️ Architecture

```mermaid
flowchart TD
    A["Official data sources<br/>China Food Composition Tables + Dietary Guidelines 2022"] --> B["Data pipeline<br/>scrape → clean → chunk"]
    B --> C[("ChromaDB vector store<br/>342 chunks")]
    C --> D["Python RAG pipeline<br/>retrieval → context assembly → LLM → answer + citations"]
    D --> E["Streamlit app<br/>chat UI + evaluation dashboard"]
```

## 🚀 Online Demo

Try it live: **[metanutri-ai-rag-question-answering.streamlit.app](https://metanutri-ai-rag-question-answering.streamlit.app/)**

Ask questions like *"高血压人群饮食上应该注意什么？"* or *"每100克鸡蛋含多少蛋白质？"* — every answer expands to its source citations for verification.

## 🖼️ Screenshots

**Chat** — Chinese interface; every answer carries `[n]` citations to source chunks:

![Chat - Chinese](assets/screenshots/screenshot-chat-zh.png)

**Evaluation dashboard** — 50-case coverage matrix by category (green = covered by both RAG and no-RAG, orange = RAG-only gain):

![Evaluation dashboard](assets/screenshots/screenshot-eval-zh.png)

**Chat** — English interface (full i18n, answers follow the UI language):

![Chat - English](assets/screenshots/screenshot-chat-en.png)

## ⚡ Quick Start

```bash
git clone https://github.com/ElijahZhao/nutri-rag.git
cd nutri-rag
pip install -r requirements.txt

# configure your Alibaba Bailian API key in .env:
#   DASHSCOPE_API_KEY=sk-...

# optional: rebuild the vector store (auto-restored from data/chroma_db.tar.gz if missing)
python3 src/kb.py --rebuild

streamlit run app.py
```

For deployment on Streamlit Community Cloud: set `DASHSCOPE_API_KEY` in **Advanced settings → Secrets** (TOML format), as shown in `.streamlit/secrets.toml.example`.

## 📁 Structure

```
├── app.py                  # Streamlit demo: chat + citations + eval dashboard
├── src/
│   ├── config.py           # pipeline configuration
│   ├── retrieval.py        # balanced two-path retrieval (food + guideline)
│   ├── generation.py       # context assembly + LLM answer with [n] citations
│   ├── kb.py               # vector store build/rebuild (ChromaDB)
│   └── evaluation.py       # 50-case eval + no-RAG vs RAG ablation
├── data/
│   ├── fetch_*.py          # data collection scripts (official sources)
│   ├── build_kb_texts.py   # chunking
│   ├── build_eval_set.py   # eval set generation
│   ├── eval_questions.json # 50-case eval set
│   ├── eval_report.json    # latest evaluation report
│   ├── kb_foods.txt        # 325 food chunks
│   ├── kb_guidelines.txt   # 17 guideline chunks
│   ├── chroma_db.tar.gz    # vector store backup (342 chunks)
│   └── SOURCES.md          # data provenance registry
└── requirements.txt
```

## 🧰 Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.12 |
| Demo UI | Streamlit |
| Vector store | ChromaDB (embedded, file-based) |
| Embedding | `text-embedding-v3` (Alibaba DashScope) |
| LLM | `qwen-plus` (OpenAI-compatible endpoint) |
| Eval | Custom 50-case set + ablation script |

## 📊 Evaluation

Offline evaluation on 50 hand-verified cases (20 composition / 15 guideline / 15 special; gold answers are real CSV values or verbatim guideline text — none hand-written), qwen-plus, 100 LLM calls total:

| Metric | Score |
|---|---|
| Retrieval hit rate | **100%** (50/50) |
| Generation faithfulness | **100%** (50/50) |
| Citation rate | **100%** (50/50) |
| Gold-info coverage, no-RAG → RAG | **88% → 100%** |

Per category — all three at **1.0** (retrieval hit & faithfulness). The ablation gap concentrates on corpus-specific values (e.g. milk calcium, lean pork protein, sweet potato energy) that a bare LLM cannot recall; RAG answers are additionally fully citation-traceable.

Regenerate the report with: `python3 src/evaluation.py`

## 📚 Data Sources

- **China Food Composition Tables** — National Institute for Nutrition and Health, China CDC ([nlc.chinanutri.cn](https://nlc.chinanutri.cn/fq/))
- **Dietary Guidelines for Chinese Residents (2022)** — Chinese Nutrition Society ([dg.cnsoc.org](http://dg.cnsoc.org/))

Full provenance, scraping scripts and rebuild instructions: [`data/SOURCES.md`](data/SOURCES.md)

## ⚠️ Disclaimer

This project is for research and educational demonstration only. It does not constitute medical advice. For health concerns, consult a licensed physician or registered dietitian.

## 🔗 Ecosystem

Nutri-RAG is the LLM research module of the **MetaNutri** ecosystem:

- **MetaNutri** — full-stack precision-nutrition platform ([repo](https://github.com/ElijahZhao/MetaNutri---AI-) · [demo](https://meta-nutri-ai.vercel.app/))
- **ppgr-predictor** — 2-hour postprandial glucose prediction ([repo](https://github.com/ElijahZhao/ppgr-predictor) · [demo](https://metanutri-ai-ppgr-predictor.streamlit.app/))
- **Nutri-RAG** (this repo) — health-diet Q&A via RAG

## ❓ FAQ

- **Why not a full-stack app?** The RAG narrative lives in the retrieval pipeline, citation grounding and evaluation — full-stack engineering is already demonstrated by MetaNutri itself.
- **Where does the data come from?** Official public sources only; every step is scripted and reproducible.
- **What does it cost to run?** Near-zero: all heavy computation is on the API side; the free Streamlit tier is sufficient.

## 📄 License

[MIT](LICENSE) — consistent with the MetaNutri ecosystem (MetaNutri & ppgr-predictor).

## 📝 Changelog

- **v0.3** — Streamlit demo (chat + citations + eval dashboard), deployed
- **v0.2** — RAG pipeline: balanced two-path retrieval, generation with citations, 50-case eval + ablation
- **v0.1** — Data pipeline: 325 foods × 32 nutrients, 17 guideline chunks, 342-chunk vector store
