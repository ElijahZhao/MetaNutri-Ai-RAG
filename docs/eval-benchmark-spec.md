# NutriQA Evaluation Benchmark Specification

> Nutri-RAG 评测基准的构建规格（2026-10-30，S1 阶段产出）。
> 本文档定义评测集分类学、题量分配、gold 来源分级与判定口径，是 NutriQA 论文"评测协议"章节的可引用依据。数据与脚本见 `data/`（`build_eval_set.py`、`eval_questions.json`、`refusal_questions.json`）。

## 1. 目标

将 Nutri-RAG 评测从"自建 50 题 + 10 拒答"扩展为公开可复用的评测基准，满足以下约束：

- **gold 零虚构**：所有标准答案可溯源至官方数据源（中国食物成分表 / 膳食指南原文），禁止人工编造、LLM 生成与常识近似。
- **判定可自动化**：数值精确性、引用命中、拒答正确性均为机器可核验口径。
- **与现有管线无缝衔接**：字段格式、脚本约定与既有 `data/eval_questions.json` 一致。

## 2. 分类学（四类）

| 类别 | 标识 | 定义 | 判定维度 |
|---|---|---|---|
| 数值型 | `composition` | "每 100g X 含多少 Y"型，gold 为成分表精确值 | 数值精确性 |
| 指南型 | `guideline` | 膳食指南规范 / 建议，gold 为指南原文 | 忠实度 + 引用命中 |
| 禁忌型 | `special` | 疾病 / 特殊人群 × 食物宜忌，gold 为指南条款组合 | 立场正确性 + 引用命中 |
| 拒答型 | `refusal` | 资料外 / 越界 / 伪精确问题 | 拒答正确性 |

## 3. 题量分配（总计 200 题）

| 类别 | 现有 | 目标 | 素材来源 | 可行性 |
|---|---|---|---|---|
| composition | 20 | **60** | 325 食物 × 32 营养项（CSV） | 充裕 |
| guideline | 15 | **50** | 八准则 + rule6 细节 | 可行 |
| special | 15 | **50** | 指南特殊人群章节 | 可行 |
| refusal | 10 | **40** | offtopic 15 / not_in_kb 15 / boundary 10 | 可行 |

## 4. Gold 来源分级

| 级别 | 定义 | 适用类别 | 示例 |
|---|---|---|---|
| 1 级 | 成分表 CSV 官方精确值 / 指南原文逐字 | composition、guideline | "每 100 克可食部含 1530kJ" |
| 2 级 | 指南条款组合 / 推导（如"高血压人群" = 准则 × 食物成分交集） | special | 高血压人群限制钠摄入（准则）+ 高钠食物清单（成分表） |
| 禁止 | 人工编造、LLM 生成、常识近似（"大约""通常"） | — | 不得进入 gold |

## 5. 判定口径

### 5.1 数值题（composition）

- gold 精确匹配；单位换算后数值容差 ±1（如 kJ 与 kcal 换算后比对）。
- **语义近似不给分**：模型给出"约 100mg"而 gold 为精确值时，视为不通过（数值精确性是本基准的核心维度）。

### 5.2 引用核验（guideline / special）

- `source_keyword` 必须命中 top-k 检索切片（沿用现有机制，见 `src/evaluation.py`）。
- 答案引用的 `[n]` 编号必须对应实际被检索到的切片。

### 5.3 拒答判定（refusal）

- 回答包含"未收录 / 超出资料范围"标记 **且未给出具体数值** = 拒答正确。
- 回答给出任何具体数值或营养建议 = 拒答失败（幻觉）。

## 6. 拒答分类学（子类）

| 子类 | 标识 | 定义 | 示例 | 目标数 |
|---|---|---|---|---|
| 无关 | `offtopic` | 与营养领域无关 | 天气、体育 | 15 |
| 库外 | `not_in_kb` | 属营养领域但库内无此食物 / 概念 | 进口保健品、新式饮品 | 15 |
| 边界 | `boundary` | 库外食物问精确数值（伪精确诱饵） | "每 100 克魔芋爽的钠含量" | 10 |

> boundary 类是领域特定的拒答场景：库外食物 × 精确数值问题是中文营养问答中最常见的幻觉诱因，也是本基准区别于通用不可问答评测框架（如 UAEval4RAG）的差异化点。

## 7. 构建标准

- 字段格式：`{id, category, question, gold, source_keyword}`（拒答题为 `{id, category, question}`）。
- 出题脚本：`data/build_eval_set.py` 模式——数值题经 `food_value()` 从 CSV 提取真实值、指南题经 `guide_snippet()` 从指南原文提取逐字片段；提取失败即报错，禁止静默降级。
- 题量目标按类别分批落地，每批落地后运行全量校验（gold 可提取、id 唯一、类别合法）。

## 8. 与论文的关系

本规格是 NutriQA 论文"评测协议"贡献的支撑文档；评测集扩展完成并经过 S2 的 judge-人工一致性校验后，数字进入 `docs/tech-report.md`（H-6 单一源约定）。

## 9. 落地状态（S2 完成，2026-10-30）

### 9.1 评测集与数据

| 类别 | 目标 | 已落地 | 数据文件 | 说明 |
|---|---|---|---|---|
| composition | 60 | 60 | `data/eval_questions.json` | 数值精确值（±1 容差） |
| guideline | 50 | 50 | `data/eval_questions.json` | 指南原文逐字 |
| special | 50 | 50 | `data/eval_questions.json` | 特殊人群/实践 |
| refusal | 40 | 40 | `data/refusal_questions.json` | offtopic 15 / not_in_kb 15 / boundary 10 |
| **合计** | **200** | **200** | — | S1d 溯源抽查 8/8 + 5/5 通过 |

### 9.2 三模型最终基线（混合检索 BM25+向量 RRF，新 KB 344 chunks，top_k=8）

**160 题生成评测：**

| 指标 | qwen-plus | deepseek-chat | glm-5.3-flash |
|---|---|---|---|
| retrieval_hit_rate | 1.0 | 1.0 | 1.0 |
| faithfulness | 0.9625 | **0.9938** | 0.9875 |
| rag_citation_rate | 1.0 | 1.0 | 1.0 |
| gold_cover_rag | 0.9625 | 0.9938 | 0.9875 |
| gold_cover_norag | 0.7625 | 0.7688 | 0.7625 |
| ablation_gain | 0.20 | **0.225** | 0.225 |

- by_category：qwen guideline 0.92 / special 0.96；deepseek guideline 1.0 / special 0.98；glm guideline 0.96 / special 1.0（composition 三模型均 1.0）
- 检索优化前（纯向量 k=5 + 旧 KB）：qwen 0.9187/0.9187/0.1688；**混合检索 + 分块修复后检索命中 1.0，RAG 增益升至 0.20-0.225**
- 检索方法 > 分块粒度：切分修复对纯向量有扰动（13→15 miss），混合检索稳定修复至 0 miss

**40 题拒答评测：**

| 口径 | qwen-plus | deepseek-chat | glm-5.3-flash |
|---|---|---|---|
| refusal_rate_rag | 1.0 | 1.0 | 0.975 |
| refusal_rate_norag | 0.0 | 0.0 | 0.025 |
| refusal_rate_strict | 0.675 | 0.925 | 0.925 |

- RAG 拒答率三模型均 ≥0.975：检索到边界/库外信息即拒答（boundary 子类 10/10 全拒）
- strict（去资料+拒答指令）：deepseek = glm 0.925 > qwen 0.675——"资料边界控制 vs 模型指令约束"的实证
- GLM 是唯一裸 LLM 主动拒答的模型（norag 0.025）

### 9.3 judge-人工一致性闸门（S2-2）

| 对比 | 比例 | 判定 |
|---|---|---|
| LLM judge vs 人工（39 条） | **0.846** | ✅ ≥0.8 通过 |
| 规则口径 vs 人工 | **0.949** | 规则判定为低成本强代理 |

- 规则口径（±1 容差 + 要点覆盖 + 编造检测）比通用 LLM judge 更贴人工——论文主口径用规则（可审计、可复现）
- judge 系统性偏严：6 条分歧中 4 条 judge 判不忠、人工判忠（±1 容差与部分要点覆盖）

### 9.4 工程与可复现性

- 检索：`src/hybrid.py` HybridRetriever（BM25 字 bigram + 向量 RRF，候选池 max(k*4,20)）；评测 top_k=8，demo 保持向量检索
- 分块修复：`data/build_kb_texts.py` 正则覆盖（一）~（十），guideline 17→19 chunks（（八）1549→360 字）
- 台账：`data/SOURCES.md` 325 食物 / 19 段 / 344 chunks；chroma_db 344 docs，备份 tar.gz 同步
- 守卫测试：26/26 通过（19 chunks / 344 docs / 325 foods 断言）
- API 超时修复：`src/generation.py` timeout=60.0（评测可复现）
- 密钥管理：API key 只进 `.env`（gitignored），`src/config.py` 仅存环境变量名

## 10. 下一步（S2+）## 10. 下一步（S2+）

1. judge-人工一致性校验（≥0.8 闸门）
2. 检索优化（top_k / 混合检索 / 分块），复测 13 题未命中
3. 跨模型实验（qwen-plus + DeepSeek + 火山引擎第三模型，用户选定）
