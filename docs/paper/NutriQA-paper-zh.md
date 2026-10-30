# NutriQA：面向中文官方营养数据的可溯源 RAG 问答评测基准与实证研究

**赵昱林**（英文名 **Elijah Zhao**）

河南财经政法大学，郑州，中国

**通讯作者**：赵昱林（Elijah Zhao）  
邮箱：202334071131@stu.huel.edu.cn；elijahzhao04@163.com

**ORCID**：https://orcid.org/0009-0005-4623-8465

---

## 摘要

检索增强生成（RAG）在面向公众的营养问答中承担"答案必须忠实于官方来源"的硬约束，但中文官方营养数据缺少可审计的评测基准：数值忠实、拒答边界与幻觉抑制均未系统量化。本文提出 **NutriQA**——面向中文官方营养数据的可溯源 RAG 问答评测基准：200 题四类分类学（composition 60 / guideline 50 / special 50 / refusal 40），gold 采用三级溯源（官方食物成分表数值、膳食指南原文摘录、无 gold 拒答题），判定采用可完全审计的确定性规则（数值 ±1 容差 + 要点覆盖 + 编造检测）。在 qwen-plus、deepseek-chat、glm-5.3-flash 三个商用模型上全量实证：（1）混合检索（BM25 字 bigram + 向量 RRF，top_k=8）在 160 题上检索命中率 1.0，检索方法选择显著优于分块粒度；（2）检索优化将三模型 RAG 增益从 ~0.15-0.17 提升至 0.20-0.225，且检索命中与生成模型解耦；（3）新增 boundary 子类（库外食物 × 数值诱饵）量化出裸 LLM 对库外对象 100% 编造数值、跨模型区间互斥（差 3-4 倍），而 RAG 通过"检索到未收录 → 拒答"将其压缩至 ~0-2.5%；（4）确定性规则与人工标注一致率 0.949，优于通用 LLM judge 的 0.846。数据、代码与全部留证以 git tag v1.0.0 固定发布，支持独立复核与复现。

**关键词**：检索增强生成；评测基准；营养；幻觉；拒答；LLM-as-judge；可溯源性；封闭域问答

---

## 1 Introduction

大型语言模型（LLM）以封闭域检索增强生成（RAG）形式落地知识密集型问答时，忠实度（faithfulness）与可溯源性是两大核心考验：模型须将答案约束在检索资料之内，且任何数值都能回指官方来源。这在营养领域尤为关键——面向公众的营养咨询直接关系饮食行为与健康决策，中国疾控中心营养与健康所的「食物营养成分查询平台」（325 种常见食物 × 32 项营养成分）与《中国居民膳食指南（2022）》构成了权威的封闭数值域，但该领域缺少公开的、可审计的评测基准：既有通用 RAG 基准（RAGAS、RAGCHECKER）以英文维基式语料为主，中文营养数据的数值忠实、拒答边界与幻觉抑制缺乏系统量化。

本文围绕三个相互关联的缺口展开。第一，**评测数据缺口**：营养问答的正确性判定高度依赖数值精度与来源可溯源，现有基准未提供"官方数值 gold + 三级来源 + 确定性判定规则"的配套方案。第二，**拒答评测缺口**：UAEval4RAG 等近期工作开始系统评测不可回答查询的拒绝能力，但封闭官方域上"库外对象 × 数值诱饵"的边界幻觉（boundary hallucination）尚无基准可测。第三，**自动判定一致性缺口**：LLM-as-judge 与人工的一致性在通用域约为 80% 以上（Zheng et al., 2023），但在中文营养数值域是否成立、确定性规则是否更优，缺少领域证据。

为此我们提出 **NutriQA**：面向中文官方营养数据的可溯源 RAG 问答评测基准与实证研究，包含 200 题四类分类学（composition 60 / guideline 50 / special 50 / refusal 40）、三级 gold 溯源体系与完全可审计的确定性判定规则，并在三个商用模型（qwen-plus、deepseek-chat、glm-5.3-flash）上完成全量实证。主要发现：（1）检索方法选择（混合检索）显著优于分块粒度，top_k=8 下 160 题检索命中率 1.0；（2）检索优化将三模型 RAG 增益从 ~0.15-0.17 提升至 0.20-0.225，且检索命中与生成模型解耦；（3）RAG 把 boundary 题的 100% 数值幻觉压缩至 ~0-2.5%，跨模型编造互斥构成黑盒幻觉判定的新证据；（4）确定性规则与人工一致性 0.949，优于通用 LLM judge 的 0.846。全部数据、代码与留证以 git tag v1.0.0 固定发布，支持独立复核。

## 2 Related Work

**RAG 评测基准与指标。** RAG 评测已从单点指标走向模块化框架。RAGAS（Es et al., 2024）提出参考无关（reference-free）的忠实度、答案相关性与上下文相关性三元评测，用 LLM 拆句验证"答案声明可否从上下文推断"，但其评测集基于英文维基百科事件页。RAGCHECKER（Ru et al., 2024）将检索与生成分开诊断，meta 评测显示其与人工判断的相关性优于通用指标，面向长回答与模块化系统。综述层面，Gao et al.（2023）系统梳理 Naive/Advanced/Modular 三代 RAG 范式与评测框架，Yu et al.（2024）则专门综述了 RAG 评测的量化指标（相关性、准确性、忠实度）与基准局限。共同缺口：**数值密集的封闭官方域**（如食物成分表）未被上述基准覆盖——其语料是自然语言段落而非结构化的"食物×营养素×数值"表，gold 无需满足 ±1 数值容差。

**拒答与不可回答查询。** 近期工作意识到"答不出时应拒绝"是可靠 RAG 的关键。UAEval4RAG（Peng et al., 2024）定义六类不可回答查询并自动合成 queries，用 unanswered ratio 与 acceptable ratio 度量拒绝质量，揭示组件选择与提示设计对拒绝率-准确率的权衡；其在通用知识库上评测。我们在两个维度与其互补：领域为**中文官方封闭营养域**（数值 gold 而非通用知识），且新增 boundary 子类——库外食物 × 精确数值诱饵，单独量化"检索到未收录 → 拒答"对数值幻觉的抑制（RQ5）。

**LLM-as-judge 与自动判定一致性。** 用强 LLM 当裁判已与人工偏好对齐：Zheng et al.（2023）的 MT-Bench 与 Chatbot Arena 显示 GPT-4 judge 与人工一致率超 80%（接近人工间一致水平），同时指出位置、冗长、自我增强等偏差；后续工作沿两条线改进——分解式判定（Branch-Solve-Merge, Saha et al., 2024；RocketEval, Wei et al., 2025）与偏差对齐（PORTIA, Li et al., 2024）。我们的 RQ4 在该背景下提供了**中文营养数值域**的领域证据：通用 LLM judge 与人工一致 0.846，而显式编码 ±1 容差与要点覆盖的确定性规则达 0.949——对封闭数值域，可审计规则优于黑盒 judge。

**幻觉检测与编造量化。** 黑盒场景下，SelfCheckGPT（Manakul et al., 2023）以多采样一致性检测幻觉（事实性回答采样稳定、编造回答相互矛盾），无需外部库与概率接口。我们的 RQ5 在 boundary 子类上观察到同类现象的**跨模型版本**：同一库外题三模型给出互相矛盾的数值区间（差 3-4 倍）——编造缺乏跨模型共识，为采样一致性判据补充了"模型间一致性"证据。LLM-Check（Sriramanan et al., 2024）与 Luo et al.（2024）综述了白盒/黑盒检测方法的成本-效果权衡，但均未在封闭数值域量化 RAG 拒答对幻觉的压缩率（本文 100% → ~0-2.5%）。

**中文评测与营养问答。** 中文 LLM 评测以 CMMLU（Li et al., 2024，67 主题多任务理解）为代表，覆盖知识面广但非数值忠实评测。营养问答侧，NGQA（Zhang et al., 2025）用 NHANES/FNDS 构建个性化营养推理的图问答基准（ACL 2025）；SwissFKG（Rahman et al., 2025）构建瑞士食物知识图谱并以 Graph-RAG 回答营养查询；DietQA（Tsampos and Marakakis, 2025）与 KERL（Mohbat and Zaki, 2025）分别以知识图谱增强食谱检索与推荐；GastroBot（Zhou et al., 2024）是中文胃肠病 RAG 聊天机器人，用 RAGAS 评测忠实度 93.7%；ChatWikiFCD（Thornton et al., 2024）以 WikiFCD 结构化食物成分表 + LLM 提供可溯源回答。**空白**：上述工作或面向个性化推理/图谱检索，或使用非官方或英文数据源；尚无基于**中国官方食物成分表 + 膳食指南**、以数值 ±1 容差与确定性规则为判定口径的可审计评测基准。

---

## 3 Methods

### 3.1 基准构建（NutriQA Benchmark）

**数据源。** 两份权威官方来源：(1) 中国疾病预防控制中心营养与健康所「食物营养成分查询平台」（nlc.chinanutri.cn），325 种常见食物 × 32 项营养成分（能量/宏量营养素/维生素/矿物质，单位 g/mg/μg/kJ）；(2) 中国营养学会《中国居民膳食指南（2022）》平衡膳食八准则及准则六详细实践。原始抓取与清洗脚本见主仓 `data/fetch_*.py`、`data/build_kb_texts.py`，来源登记台账 `data/SOURCES.md`（325 食物 / 19 指南片段 / 344 向量库切片）。

**问题集（200 题，四类分类学）。** 全部人工起草并经领域核对：

**表 1.** NutriQA 基准分类学（200 题）。

| 类别 | 题数 | 考查能力 | 示例 |
|---|---|---|---|
| composition | 60 | 精确数值（±1 容差） | "橙子每100克含多少维生素C？"（gold：33.0mg） |
| guideline | 50 | 指南原文要点 | "成年人每天摄入食盐不超过多少克？"（gold：≤5g） |
| special | 50 | 特殊人群/实践细节 | "高血压人群在饮食上应该注意什么？" |
| refusal | 40 | 拒答（offtopic 15 / 库外 15 / boundary 10） | "魔芋爽每100克含多少钠？" |

**Gold 三级来源与判定口径。**
- L1：composition 数值直接由抓取脚本从 CSV 列值提取（提取失败即构建失败，无人工编造）；判定采用数值 ±1 容差，语义近似不给分。
- L2：guideline/special 采用指南原文逐字（gold 溯源抽查 8/8 数值精确匹配、5/5 原文命中）。
- L3：拒答无数值 gold。判拒答 = 模型识别出"未收录"且未给出数值。
- 忠实度判定为确定性规则：答案数值 ⊆ 检索资料数值（±1）+ 要点覆盖 gold + 无资料外编造。规则全部可审计、可复现（主仓 `src/evaluation.py`、`src/eval_refusal.py`）。

**与既有基准的差异化（边界题设计）。** 新增 boundary 子类（10 题）：库外食物 × 精确数值诱饵（如"魔芋爽钠含量"——知识库明确未收录，问题却伪装成可查数值），用于单独量化 RAG 对数值幻觉的抑制作用；与 UAEval4RAG（Peng et al., 2024，面向不可回答查询的通用评测）互补：其在通用知识库上测拒绝质量，本文在中文官方封闭数值域上测 boundary 幻觉的抑制率（RQ5）。

### 3.2 系统实现

**图 1** 给出完整评测流水线：官方食物成分数据与膳食指南经清洗切分构成 344 文档知识库；混合检索器（BM25 字 bigram + 稠密向量，RRF 融合）为三个商用 LLM 提供 top-k 上下文；答案经确定性规则对照三级 gold 溯源判定；全部指标可追溯至 git tag v1.0.0 固定的工件（图文件：`docs/figures/fig1_pipeline.png`）。

![NutriQA 评测流水线（v1.0.0）。](docs/figures/fig1_pipeline.png){width=100%}

**数据处理管道。** 抓取（1356 条全量清单 → 精选 325）→ 清洗（列缺失标记为"数据源未收录"，不估算；缺失率如实登记，如总膳食纤维 298/325、维生素A 231/325、碘 297/325）→ 知识切片（每食物一段 + 指南按准则/小节切分）→ 嵌入入库（ChromaDB，344 切片）。

**检索器（HybridRetriever）。** 双通道融合：BM25（中文二字词元 bigram）与稠密向量检索（text-embedding-v3，DashScope），以 Reciprocal Rank Fusion（RRF）融合排序，候选池放大为 max(k×4, 20) 以稳定 top-k 边界。评测采用 top_k=8；公开 demo 保持纯向量检索。

**生成模型。** 三个商用 API 模型，零样本（zero-shot）生成：qwen-plus（阿里 DashScope）、deepseek-chat（DeepSeek）、glm-5.3-flash（智谱，经火山引擎）。统一 temperature 与超时设置（timeout=60s），检索上下文带来源编号，要求模型按编号引用。

### 3.3 评测协议

- **生成评测**：160 题（composition/guideline/special）逐题跑 RAG 与 NoRAG 两个版本；指标含检索命中率（retrieval_hit，判定 gold 关键短语是否进入 top-k）、忠实度（faithfulness）、引用率（citation）、gold 覆盖（RAG vs NoRAG）与 RAG 增益（ablation gain）。
- **拒答评测**：40 题三个口径——RAG（带资料）、NoRAG（去资料）、Strict（去资料 + 明确"若不知道就拒答"指令）。
- **自动判定一致性**：40 条分层抽样（含 6 条已知不忠案例），由 qwen-plus（temperature=0）独立判定忠实度，与规则口径、人工标注三方对照；人工标注 39/40 有效，据此算 LLM-judge-人工一致性与规则-人工一致性。

---

## 4 Results

### 4.1 RQ1：检索方法选择 > 分块粒度

**图 2** 报告四种配置下的检索命中率。分块修复（指南切分正则 `（[一二三四五六七八九十]+）`）本身使纯向量在新 KB 上召回下降（k=5 时 15/160 未命中）；切换混合检索后 k=5 未命中降至 3，混合 + top_k=8 达到 160/160（图文件：`docs/figures/fig2_retrieval_ablation.png`）。

![RQ1——四种配置下的检索命中率（160 题）。](docs/figures/fig2_retrieval_ablation.png){width=75%}

**表 2.** 检索配置与命中率（160 题）。

| 检索方案 | 知识库 | top_k | 未命中数/160 | 检索命中率 |
|---|---|---|---|---|
| 纯向量 | 旧 342 | 5 | 13 | 0.9187 |
| 纯向量 | 新 344（分块修复） | 5 | **15** | 0.9063 |
| 混合（BM25+向量 RRF，候选池 20） | 新 344 | 5 | 3 | 0.9813 |
| **混合（候选池 20）** | 新 344 | **8** | **0** | **1.0000** |

- 指南切分正则修复（覆盖（一）~（十），17→19 片段，其中（八）从 1549 字降到 360 字）对纯向量检索反而引入扰动（13→15 未命中，净增 2 题源于片段边界变化）；**混合检索在两种知识库上都稳定修复至 3 题未命中，top_k=8 时全部命中**——检索方法的选择比分块粒度更能决定召回。
- 残余未命中（top_k=5 时）为长短语关键词排序边界问题（G45/S39/S48），gold 均可溯源，非基准缺陷。
- 观察到 top-k 边界敏感性：候选池大小改变 RRF 排名（k=5 时 G45 与 S40 在边界抖动），是 RAG 检索在 top-k 边界不稳定性的实证。

### 4.2 RQ2：生成忠实度——三模型对比（混合检索 + 新 KB + top_k=8）

**图 3** 给出最终配置下按类别的忠实度分解。三模型 composition 全部满分（1.0）；guideline 与 special 在 0.92-1.0 之间浮动，与"检索命中与生成质量解耦"的结论一致（图文件：`docs/figures/fig3_faithfulness_by_category.png`）。

![RQ2——最终配置下按类别的忠实度（混合检索，top_k=8）。](docs/figures/fig3_faithfulness_by_category.png){width=75%}

**表 3.** 主评测结果（160 题，混合检索 + 新 KB + top_k=8）。

| 指标 | qwen-plus | deepseek-chat | glm-5.3-flash |
|---|---|---|---|
| retrieval_hit_rate | 1.0 | 1.0 | 1.0 |
| faithfulness | 0.9625 | **0.9938** | 0.9875 |
| citation rate | 1.0 | 1.0 | 1.0 |
| gold_cover_rag | 0.9625 | 0.9938 | 0.9875 |
| gold_cover_norag | 0.7625 | 0.7688 | 0.7625 |
| **ablation_gain（RAG 增益）** | **0.20** | **0.225** | **0.225** |

按类别（faithfulness）：qwen composition 1.0 / guideline 0.92 / special 0.96；deepseek 1.0 / 1.0 / 0.98；glm 1.0 / 0.96 / 1.0。composition 三模型全满分，差异集中在 guideline/special 长句要点。

检索优化前（纯向量 k=5 + 旧 KB）qwen 为 0.9187 / 0.9187 / 0.1688。**检索优化（混合检索 + 分块修复 + k=8）把三模型 RAG 增益从 ~0.15-0.17 抬到 0.20-0.225**：NoRAG 覆盖三模型均在 0.76-0.77（模型先验相近），RAG 覆盖从 ~0.93 提升到 0.96-0.99，增益增量全部来自检索召回。**检索命中率与生成模型解耦**：hit 1.0 为检索器性质，不随模型变化，与生成无关的指标分离。

### 4.3 RQ3：拒答——三个口径跨模型

**图 4** 对比三个口径。带 RAG 上下文时三模型拒答率 0.975-1.0；无检索时几乎不拒答（0-0.025）；仅靠 Strict 指令只有 0.675-0.925——检索是决定性因素（图文件：`docs/figures/fig4_refusal_protocols.png`）。

![RQ3——三个口径下的拒答率（40 题）。](docs/figures/fig4_refusal_protocols.png){width=75%}

**表 4.** 三个口径下的拒答率（40 题）。

| 口径 | qwen-plus | deepseek-chat | glm-5.3-flash |
|---|---|---|---|
| refusal_rate_rag | 1.0 | 1.0 | 0.975 |
| refusal_rate_norag | 0.0 | 0.0 | 0.025 |
| refusal_rate_strict | 0.675 | 0.925 | 0.925 |

- **RAG 拒答率三模型 ≥0.975**：检索到"未收录"信息即拒答；boundary 子类 10/10 全拒。混合检索 top_k=8 下，旧配置的灰区题（R20 小龙虾→知识库"螯虾"别名）也被拒——检索配置影响拒答边界。
- **Strict 指令遵循差异**：deepseek = glm（0.925）> qwen（0.675）。Strict 口径（去资料 + 拒答指令）下 qwen 仍有 13/40 题编造——"资料边界控制 vs 模型指令约束"的实证。
- GLM 是唯一在 NoRAG 下主动拒答的模型（1/40，0.025）——模型自带拒答倾向的个体差异。

### 4.4 RQ4：自动判定一致性——规则优于通用 LLM judge

**图 5** 汇总分层 40 条样本（39 条有效）的一致性分析。确定性规则与人工一致性 0.949，超过预注册闸门 0.8 且高于通用 LLM judge（0.846）；规则与 judge 间一致 0.850（图文件：`docs/figures/fig5_judge_agreement.png`）。

![RQ4——分层 40 条样本上的判定一致性（39 条有效）。](docs/figures/fig5_judge_agreement.png){width=70%}

**表 5.** 判定一致性矩阵（分层样本）。

| 对比 | 一致条数 | 比例 |
|---|---|---|
| LLM judge vs 人工（39 条） | 33/39 | **0.846** |
| 规则口径 vs 人工 | 37/39 | **0.949** |
| 规则 vs LLM judge | 34/40 | 0.850 |

- 确定性规则（±1 容差 + 要点覆盖 + 编造检测）与人工一致性 0.949，**显著优于通用 LLM judge（0.846）**——可复现的自动判定优于黑盒 judge，论文主口径采用规则判定（可审计）。
- judge 系统性偏严：6 条分歧中 4 条 judge 判"不忠"、人工判"忠"，集中在 ±1 数值容差（C21：9.7 vs 9.3）与部分要点覆盖（G29：答出核心点漏补充句）——LLM-as-judge 对显式容差缺乏建模，为该方向补充中文营养数据域证据。

### 4.5 RQ5：boundary 裸 LLM 幻觉率——三模型 100% 编造

**图 6** 可视化 boundary 结果：10 道库外 × 数值诱饵题上，三模型裸 LLM 拒答率 0%、编造数值率 100%，而 RAG 拒答把 boundary 幻觉压至 ~0-2.5%（图文件：`docs/figures/fig6_boundary_hallucination.png`）。

![RQ5——boundary 幻觉：裸 LLM 编造（100%）vs RAG 拒答。](docs/figures/fig6_boundary_hallucination.png){width=75%}

**表 6.** Boundary 幻觉（10 道库外题）。

| 模型 | boundary 题数 | 裸 LLM 拒答 | 编造数值 | 幻觉率 |
|---|---|---|---|---|
| qwen-plus | 10 | 0 | 10 | **100%** |
| deepseek-chat | 10 | 0 | 10 | **100%** |
| glm-5.3-flash | 10 | 0 | 10 | **100%** |

- 对照：同一批题 RAG 版拒答率 ≥0.975 → **RAG 通过"检索到未收录 → 拒答"把 100% 数值幻觉压至 ~0-2.5%**。
- **跨模型编造互斥**：同一题三个模型给出互相矛盾的数值（例：魔芋爽钠 qwen 800-1200mg / deepseek 1500-2500mg / glm 500-900mg；青梅酒能量 qwen 200-250 kcal / deepseek 60-120 / glm 100-160，差 3-4 倍）。回答普遍呈"区间 + 免责声明"形式（"因品牌差异，建议查看包装"）——**置信区间式编造比单点编造更危险**，似真性更高。
- 结论：封闭域数值问答上，商用模型对库外对象无内部校准信号，100% 编造且不自知；RAG 拒答是当前唯一可靠防线。

---

## 5 Limitations

**L1 评测规模与数据覆盖。** 基准含 200 题（160 生成 + 40 拒答），相较 UAEval4RAG 等通用基准规模偏小；知识库覆盖 325 种常见食物，不含商标化加工食品（标签类数据缺失）。boundary 子类 10 题可精确量化"库外 × 数值诱饵"幻觉，但样本量限制了子类内的统计功效，未来可扩充至 30+ 题并做多重检验。

**L2 泛化食物名的 gold 指代歧义（C50 首行匹配瑕疵）。** composition 题中少量使用泛化食物词（如"虾"），gold 提取按数据表首行匹配（虾→虾皮 30.7g），与问题语义存在歧义——该题模型如实区分海虾/河虾/虾虎/虾皮并说明干制差异，仍判忠实，但 gold 本身指代不唯一。影响可数的个例（C50 等），不改变整体结论；v1.1 将禁用泛化词出题或强制带限定词 gold。

**L3 top-k 边界敏感性与配置依赖。** 4.1 已实证 RRF 边界在 k=5 时抖动（G45/S40），本文全部结论依赖 top_k=8 + 候选池 max(k×4,20) 的具体配置；超参数敏感性网格（k ∈ {3..12}）是明确后续工作，避免结论被单点配置过度外推。

**L4 官方源数据稀疏性的如实登记。** SOURCES 台账初版计数（307 食物）与 CSV 实际 325 行不一致，经复查修正；维生素 A 231/325、碘 297/325 的缺失率为官方平台原始状态，非基准缺陷——缺失营养素上评测题会系统性稀疏，需在解读时注意。

**L5 自动判定的残余误差。** 规则口径与人工一致性 0.949 非 1.0：G35/G36 两条例外源于规则对"编造检测"过严；通用 LLM judge 一致性仅 0.846 且对 ±1 显式容差缺乏建模（C21 9.7 vs 9.3 判"不忠"）。本文主口径采用可审计规则，但规则边界（如长句要点覆盖率阈值）仍需人工校准。

**L6 模型时点与可重复性。** 三个商用模型为 2026-10 时点 API 快照，模型迭代会改变绝对数字；zero-shot 生成未固定 seed，temperature 统一但非确定性采样。结论方向（检索>分块、RAG 抑制幻觉、跨模型编造互斥）预计稳健，绝对值须以仓库报告 JSON 为准。

---

## 6 Conclusion

本文构建了面向中文官方营养数据的可溯源 RAG 评测基准 NutriQA，并完成三模型全量实证。四点结论相互支撑：**检索层**——混合检索（BM25 字 bigram + 向量 RRF）在 top_k=8 下实现 160/160 命中，方法选择胜过分块粒度（RQ1）；**生成层**——检索优化把 RAG 增益抬到 0.20-0.225，且检索命中率与生成模型解耦，证明"检索决定上限、生成决定达成度"（RQ2）；**安全层**——boundary 子类首次量化出裸 LLM 对库外对象 100% 数值编造与跨模型编造互斥（RQ5），RAG 拒答是当前唯一可靠防线；**评测层**——显式编码容差与覆盖的确定性规则以 0.949 优于通用 LLM judge 的 0.846（RQ4），为封闭数值域评测提供可审计主口径。

NutriQA 的三个设计选择值得强调：三级 gold 溯源把"答案正确"落在可复核的数据出处上；±1 数值容差与要点覆盖把"忠实"变成机器可执行的规则；boundary 子类把"幻觉"变成可量化的指标。三者共同构成与通用英文基准的差异化——在官方封闭数值域，可溯源性与数值精度是评测的第一性问题。

局限与未来工作（详见 Limitations）：boundary 子类 10 题将扩充至 30+ 并做多重检验；top-k 敏感性将做 {3..12} 网格消融；泛化食物名 gold 指代歧义将在 v1.1 禁用；自动判定规则边界（长句要点覆盖率阈值）将引入人工校准流程。后续还将覆盖更多官方数据源（如港澳台及国际食物成分表）与更多语言，检验结论外推的稳健性。

---

## 数字复核记录（第三轮，草稿 vs 主仓报告）

2026-10-30 第三轮独立复核，全部通过：
- 4.2 表：qwen 1.0/0.9625/1.0/0.9625/0.7625/0.20；deepseek 1.0/0.9938/1.0/0.9938/0.7688/0.225；glm 1.0/0.9875/1.0/0.9875/0.7625/0.225 —— 与 `eval_report*.json` summary 逐一相等 ✓
- by_category：qwen 60/60·46/50·48/50；deepseek 60/60·50/50·49/50；glm 60/60·48/50·50/50 —— 由 items 逐题重算 ✓
- 4.3 表：qwen 1.0/0.0/0.675、deepseek 1.0/0.0/0.925、glm 0.975/0.025/0.925 —— 与 `refusal_report*.json` summary 相等 ✓
- boundary：三模型 RAG 拒 10/10、NoRAG 编造 10/10（幻觉率 100%）✓
- gold 溯源：composition 60/60（±1）、guideline/special 100/100 子句级命中 kb 原文（整串不中仅因【膳食指南·准则X】括号省略，属规范化差异）✓

---

## 待确认问题 → 已解决（2026-10-30）

1. ✅ **英文版对照**：已产出完整英文版 `nutriqa-paper-methods-results-en.md`（Research Square 投稿语言为英文，中文版为工作底稿）。
2. ✅ **Limitations**：已补 L1–L6（评测规模、C50 泛化词 gold 歧义、top-k 边界敏感性、官方源数据稀疏、自动判定残余误差、模型时点）。
3. ✅ **数字复核**：第三轮独立复核全部通过（4.2/4.3 表与报告 summary 逐一相等、by_category 由 items 重算、boundary 10/10 拒 + 10/10 编造、gold 溯源 60/60 + 100/100 子句级），复核记录已写入上文"数字复核记录"节。

---

## 声明

**数据与代码可用性**：全部数据、代码与留证固定于 nutri-rag 仓库 GitHub tag v1.0.0（MIT 协议）；完整复现指南见 docs/。

**资助**：无。

**利益冲突**：无。

**投稿渠道**：Research Square。

---

## 参考文献

1. Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). RAGAS: Automated Evaluation of Retrieval Augmented Generation. EACL 2024 System Demonstrations. https://aclanthology.org/2024.eacl-demo.16.pdf
2. Ru, D., et al. (2024). RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation. NeurIPS 2024, Datasets and Benchmarks Track. https://papers.nips.cc/paper_files/paper/2024/file/27245589131d17368cccdfa990cbf16e-Paper-Datasets_and_Benchmarks_Track.pdf
3. Gao, Y., et al. (2023). Retrieval-Augmented Generation for Large Language Models: A Survey. arXiv:2312.10997. https://arxiv.org/abs/2312.10997
4. Yu, H., et al. (2024). Evaluation of Retrieval-Augmented Generation: A Survey. arXiv:2405.07437. https://arxiv.org/abs/2405.07437
5. Peng, X., et al. (2024). Unanswerability Evaluation for Retrieval Augmented Generation. arXiv:2412.12300. https://arxiv.org/abs/2412.12300
6. Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023, Datasets and Benchmarks Track.
7. Saha, S., et al. (2024). Branch-Solve-Merge Improves Large Language Model Evaluation and Generation. NAACL 2024. https://aclanthology.org/2024.naacl-long.462.pdf
8. Wei, T., et al. (2025). RocketEval: Efficient Automated LLM Evaluation via Grading Checklist. ICLR 2025. https://proceedings.iclr.cc/paper_files/paper/2025/file/937defc32e8ad2daba66a0e434177ae9-Paper-Conference.pdf
9. Li, Z., et al. (2024). Split and Merge: Aligning Position Biases in LLM-based Evaluators. EMNLP 2024. https://aclanthology.org/2024.emnlp-main.621.pdf
10. Manakul, P., Liusie, A., & Gales, M. J. F. (2023). SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models. EMNLP 2023. https://aclanthology.org/2023.emnlp-main.557.pdf
11. Sriramanan, G., et al. (2024). LLM-Check: Investigating Detection of Hallucinations in Large Language Models. NeurIPS 2024. https://papers.nips.cc/paper_files/paper/2024/file/3c1e1fdf305195cd620c118aaa9717ad-Paper-Conference.pdf
12. Luo, J., et al. (2024). Hallucination Detection and Hallucination Mitigation: An Investigation. arXiv:2401.08358. https://arxiv.org/abs/2401.08358
13. Li, H., et al. (2024). CMMLU: Measuring Massive Multitask Language Understanding in Chinese. Findings of ACL 2024. https://aclanthology.org/2024.findings-acl.671.pdf
14. Zhang, Z., et al. (2025). NGQA: A Nutritional Graph Question Answering Benchmark for Personalized Health-aware Nutritional Reasoning. ACL 2025. https://aclanthology.org/2025.acl-long.296.pdf
15. Rahman, L. A., et al. (2025). Introducing the Swiss Food Knowledge Graph: AI for Context-Aware Nutrition Recommendation. ACM (DOI: 10.1145/3746264.3760494). https://doi.org/10.1145/3746264.3760494
16. Tsampos, I., & Marakakis, E. (2025). DietQA: A Comprehensive Framework for Personalized Multi-Diet Recipe Retrieval Using Knowledge Graphs, Retrieval-Augmented Generation, and Large Language Models. Computers, 14(4), 412. https://mdpi-res.com/d_attachment/computers/computers-14-00412/article_deploy/computers-14-00412.pdf
17. Mohbat, F., & Zaki, M. J. (2025). KERL: Knowledge-Enhanced Personalized Recipe Recommendation using Large Language Models. arXiv:2505.14629. https://arxiv.org/abs/2505.14629
18. Zhou, Q.-Q., et al. (2024). GastroBot: A Chinese Gastrointestinal Disease Chatbot Based on the Retrieval-Augmented Generation. Frontiers in Medicine, 11, 1392555. https://doi.org/10.3389/fmed.2024.1392555
19. Thornton, K., et al. (2024). Nutritional Data Integrity in Complex Language Model Applications: Harnessing the WikiFCD Knowledge Graph for AI Self-Verification across Multilingual International Food Composition Tables. JOWO 2024, CEUR Workshop Proceedings, Vol-3882. https://ceur-ws.org/Vol-3882/ifow-3.pdf
20. 中国营养学会. 中国居民膳食指南（2022）. 北京：人民卫生出版社, 2022.
