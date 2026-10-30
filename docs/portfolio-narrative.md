# Nutri-RAG · Portfolio Narrative（作品集叙事线）

> 申请季用途：PS 段落、简历 bullet、GitHub 项目描述、面试对答。三仓联动视角。
> Language: EN primary (for applications) · 中文对照

---

## 1. One-liner（GitHub 项目描述 / 简历首行）

**EN:** Nutri-RAG — a citation-grounded RAG health-Q&A engine for China's official nutrition data, evaluated to 100% hit / citation / faithfulness with a 10-question anti-hallucination refusal suite and a 9-run hyper-parameter sweep — the evidence layer of the MetaNutri ecosystem.

**中文：** Nutri-RAG —— 基于中国官方营养数据的可溯源 RAG 健康问答引擎：50 题评测检索/引用/忠实度 100%，10 题拒答评测 100% 防幻觉，9 组超参数消融选定最优配置——MetaNutri 生态的证据层。

---

## 2. PS 段落（~180 words, ready to adapt）

While building **MetaNutri**, a full-stack precision-nutrition platform with a post-meal glucose predictor, I realized a recommendation is only as good as the evidence behind it. That insight became **Nutri-RAG**: I curated 325 foods × 32 nutrients and 17 guideline sections from China's official food-composition tables and the 2022 Dietary Guidelines into 342 knowledge chunks, indexed them in ChromaDB, and served them through a dual-route retrieval + LLM pipeline that answers every question with per-claim citations.

"It works" was never the bar. A 50-case evaluation set drove the system to 100% retrieval hit, citation and faithfulness — an 88%→100% leap over a bare LLM on the same questions. The 9-configuration hyper-parameter sweep (top-k × similarity threshold) let the data, not intuition, pick top-k=5 as the sweet spot. A 10-question refusal suite showed the RAG pipeline refusing out-of-scope questions 100% of the time while a bare LLM fabricates all of them. All of it shipped with CI — 26 passing tests, a bilingual Streamlit demo with streaming answers, and an evaluation dashboard that puts the whole research chain (refusal rates, ablation tables, failure-mode analysis) on one page.

To me, AI engineering is exactly this: making a claim measurable, and making the evidence visible. Nutri-RAG is my attempt to do both.

**中文对照：** 在构建 MetaNutri（全栈精准营养平台 + 餐后血糖预测）的过程中，我意识到：一条建议的价值取决于它背后的证据。这个洞察催生了 Nutri-RAG：我把中国官方食物成分表（325 种食物 × 32 项营养）与 2022 膳食指南（17 段）清洗成 342 个知识切片，存入 ChromaDB，通过均衡双路检索 + LLM 生成管线回答每个问题，并给每句话附上可核验的引用。

"能跑"从来不是目标。50 题评测集把检索命中率、引用率、忠实度全部推到 100%——同一组问题下裸 LLM 仅 88%→100% 的差距正是 RAG 的价值。9 组超参数消融（top-k × 相似度阈值）让数据而非直觉选出最优 top-k=5。10 题拒答评测证明：RAG 对资料外问题 100% 正确拒答，裸 LLM 则 100% 编造。这一切随 CI 一起交付上线——26 个测试、中英双语流式问答 demo、以及把拒答率/消融表/失败归因全部呈现在一页的评测面板。

对我而言，AI 工程恰恰是：让结论可度量，让证据可见。Nutri-RAG 是我对这两件事的实践。

---

## 3. Resume bullets（简历条目，选 2-3 条）

**EN:**
- **Nutri-RAG** — citation-grounded RAG health Q&A over China's official nutrition data: 325 foods × 32 nutrients + 17 guideline sections → 342 ChromaDB chunks, dual-route retrieval + qwen-plus generation, every claim citable `[n]`.
- **Rigorous evaluation** — 50-case benchmark at **100% retrieval hit / citation / faithfulness** (bare-LLM ablation 88%→100%); 9-run hyper-parameter sweep (top-k ∈ {3,5,8} × threshold) picked the data-driven optimum; 10-question refusal suite: **100% anti-hallucination vs 0% for the bare LLM**.
- **Shipped end-to-end** — bilingual (zh/en) Streamlit demo with streaming answers, multi-session & i18n UX, GitHub CI (26 tests + bandit), README with evaluation screenshots; part of the MetaNutri ecosystem (full-stack platform + ppgr glucose predictor).

**中文：**
- **Nutri-RAG** —— 基于中国官方营养数据的可溯源 RAG 健康问答：325 食物 × 32 营养 + 17 段指南 → 342 ChromaDB 切片，均衡双路检索 + qwen-plus 生成，每句可引用 `[n]`。
- **严谨评测** —— 50 题评测检索/引用/忠实度 100%（裸 LLM 消融 88%→100%）；9 组超参数消融（top-k × 阈值）数据驱动选优；10 题拒答评测防幻觉 100%（裸 LLM 为 0%）。
- **端到端交付** —— 中英双语流式问答 demo、多会话 i18n 交互、GitHub CI（26 测试 + bandit）、README 含评测截图；MetaNutri 生态（全栈平台 + ppgr 血糖预测）的一部分。

---

## 4. 三仓联动叙事（面试 / 项目介绍用）

**The MetaNutri story in three repos:**

```
MetaNutri (main)  →  Full-stack precision-nutrition platform (Vercel)
       │
       ├── MetaNutri-Ai-ppgr-predictor  →  Post-meal glucose prediction (Streamlit)
       └── MetaNutri-Ai-RAG             →  The evidence layer: RAG Q&A over official data (Streamlit)
```

1. **Why an ecosystem, not one repo?** — A nutrition recommendation chain needs three layers: *understanding* (what to eat), *prediction* (how your body reacts), and *evidence* (why — grounded, citable facts). One full-stack app can't carry all three convincingly, so I split them into three focused, independently deployable projects.
2. **Nutri-RAG's role** — it is the *evidence layer*: every answer in the ecosystem traces back to a specific chunk of China's official food-composition tables or the 2022 Dietary Guidelines. No guesswork, no hallucinated numbers.
3. **What the evaluation proves** — 50-case benchmark at 100% hit/citation/faithfulness; refusal suite proving 100% anti-hallucination vs 0% bare LLM; 9-run sweep selecting top-k=5; failure-mode analysis showing *why* a bare LLM gets nutrition numbers wrong (precision loss, regional data mismatch, stance blending, framework replacing the guideline).
4. **Same discipline across repos** — CI with tests on all three; README with screenshots and honest negative results (hybrid retrieval: no gain, keep vector default).

**中文对照：**

- **为什么是生态而非单仓？** 一条营养建议链需要三层：理解（吃什么）、预测（身体如何反应）、证据（为什么——有依据、可溯源的事实）。单个全栈应用难以同时可信地承载三层，因此拆成三个聚焦、可独立部署的项目。
- **Nutri-RAG 的角色** —— 证据层：生态中每一条回答都追溯到中国官方食物成分表或 2022 膳食指南的特定切片。没有猜测，没有幻觉数字。
- **评测证明了什么** —— 50 题检索/引用/忠实度 100%；拒答套件证明 100% 防幻觉（裸 LLM 为 0%）；9 组消融选定 top-k=5；失败归因说明裸 LLM 为何在营养数值上出错（精度损失、区域数据错位、立场混合、经验替代规范）。
- **同样的工程纪律贯穿三仓** —— 每个仓库都有带测试的 CI；README 带截图与诚实的负结果（混合检索无增益，保持纯向量默认）。

---

## 5. 面试 Q&A 速查

**Q: Why RAG instead of fine-tuning?**
A: The knowledge base changes (new guidelines, new data) and needs per-claim traceability. RAG gives me: (1) answers that cite the exact source chunk, (2) a refusal boundary for out-of-scope questions, (3) zero training cost to update knowledge. My refusal suite proves the boundary works: 100% vs 0% for the bare LLM.

**Q: What did the hyper-parameter sweep teach you?**
A: top-k=3 misses source chunks (94% hit), top-k=8 bloats context and loses coverage (98%), top-k=5 is the sweet spot; the similarity threshold barely matters below 0.5. I changed the production default to top-k=5 based on data, not intuition.

**Q: Why did you keep pure vector retrieval over hybrid?**
A: I built a BM25+vector hybrid with RRF fusion and benchmarked it: retrieval hit stayed 100% (pure vector was already saturated), but citation quality dropped to 96% because fused context induced out-of-range citation numbers. Keeping vector-only is the evidence-backed choice — reporting a negative result is part of doing research.
