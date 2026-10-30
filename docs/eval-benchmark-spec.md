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

## 9. 落地状态（S1 完成，2026-10-30）

| 类别 | 目标 | 已落地 | 数据文件 | 基线（qwen-plus，S1b/S1c 实测） |
|---|---|---|---|---|
| composition | 60 | 60 | `data/eval_questions.json` | retrieval_hit 1.0 / faithfulness 1.0 |
| guideline | 50 | 50 | `data/eval_questions.json` | retrieval_hit 0.90 / faithfulness 0.88 |
| special | 50 | 50 | `data/eval_questions.json` | retrieval_hit 0.84 / faithfulness 0.86 |
| refusal | 40 | 40 | `data/refusal_questions.json` | refusal_rate_rag 0.975 / norag 0.0 / strict 0.775 |
| **合计** | **200** | **200** | — | 整体 retrieval_hit 0.9187 / faithfulness 0.9187 / gold_cover_rag 0.9313 / gold_cover_norag 0.7625 / ablation_gain 0.1688 |

- gold 溯源：composition 全部来自成分表 CSV 精确值（脚本提取，失败即报错）；guideline/special 来自指南原文逐字（抽查 5/5 命中原文）；拒答为无 gold 判定口径。
- 可复现性修复：`src/generation.py` 与 `src/eval_refusal.py` 均加 `timeout=60.0`（评测可完成、可复现）。
- 守卫测试：26/26 通过；报告与评测集动态对齐断言。
- 已知缺口：guideline/special 13 题检索未命中（长短语关键词，S2 优化方向）；boundary 类跨模型数据留 S3。

## 10. 下一步（S2+）

1. judge-人工一致性校验（≥0.8 闸门）
2. 检索优化（top_k / 混合检索 / 分块），复测 13 题未命中
3. 跨模型实验（qwen-plus + DeepSeek + 火山引擎第三模型，用户选定）
