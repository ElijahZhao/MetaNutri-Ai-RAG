# NutriQA 技术报告（可复现性说明）

> 面向论文读者的复现文档。所有数字与主仓 `data/eval_report*.json` / `data/refusal_report*.json` 逐一一致（数字单一来源，见 §7）。论文正文见 `docs/paper/NutriQA-paper.md`（英文投稿稿）与 `docs/paper/NutriQA-paper.pdf`。

## 1. 项目定位

NutriQA 是面向中文官方营养数据的可溯源 RAG 问答评测基准与实证研究。系统以中国疾控中心营养与健康所「食物营养成分查询平台」与中国营养学会《中国居民膳食指南（2022）》为数据源，构建 344 切片封闭知识库，在三个商用 LLM（qwen-plus、deepseek-chat、glm-5.3-flash）上完成 200 题评测（160 生成 + 40 拒答）。

## 2. 实验配置

### 2.1 模型与 API

| 模型 | 服务商 | 评测用途 |
|---|---|---|
| qwen-plus | 阿里云百炼（DashScope） | 生成评测、拒答评测、LLM judge（temperature=0） |
| deepseek-chat | DeepSeek | 生成评测、拒答评测 |
| glm-5.3-flash（Model ID `glm-5-3-flash-260828`） | 智谱 AI，经火山引擎（Volcano Engine）提供 | 生成评测、拒答评测 |

所有模型零样本调用（zero-shot），temperature 与超时（60 s）统一。API 密钥仅存 `.env`（已被 .gitignore 排除），`src/config.py` 只保存环境变量名。

### 2.2 嵌入与检索

| 组件 | 配置 |
|---|---|
| 嵌入模型 | `text-embedding-v3`（DashScope，`EMB_MODEL`，默认值） |
| 检索器 | `HybridRetriever`（`src/hybrid.py`）：BM25（中文二字词元 bigram）+ 稠密向量双通道，RRF（Reciprocal Rank Fusion）融合，候选池 max(k×4, 20) |
| 评测 top_k | 8 |
| 公开 demo | 保持纯向量检索（`src/retrieval.py`） |

### 2.3 数据管线

| 步骤 | 脚本 | 输出 |
|---|---|---|
| 食物列表抓取 | `data/fetch_foodlist.py` | 全量清单（1,356 条） |
| 精选子集抓取 | `data/fetch_foods_selected.py` / `data/fetch_food_details.py` | 325 食物 × 32 营养属性（`foods_nutrition.csv`） |
| 指南文本抓取 | 八准则 + 准则六详细实践 | `dietary_guidelines_2022.md` / `dietary_guidelines_rule6_detail.md` |
| 清洗切片 | `data/build_kb_texts.py` | 325 食物块 + 19 指南块（切分正则覆盖（一）–（十）），合计 344 切片 |
| 入库 | `src/kb.py` | ChromaDB（`data/chroma_db.tar.gz` 备份） |
| 来源登记 | — | `data/SOURCES.md`（325 食物 / 19 指南块 / 344 切片） |

数据清洗纪律：缺失列标记为"数据源未收录"，不估算、不补值；缺失率如实登记（总膳食纤维 298/325、维生素 A 231/325、碘 297/325）。

## 3. 基准（NutriQA）

### 3.1 题集结构

| 类别 | 题数 | 能力维度 |
|---|---|---|
| composition | 60 | 数值精确回忆（±1 容差） |
| guideline | 50 | 指南要点覆盖 |
| special | 50 | 特殊人群/场景营养推理 |
| refusal | 40 | 拒答（R31–R40 为 boundary 子类：库外食物 × 数值诱饵） |

题集文件：`data/eval_questions.json`（160）、`data/refusal_questions.json`（40）。

### 3.2 Gold 三级溯源与判定口径

- composition/guideline/special：gold 为官方数据（成分表数值 ±1 容差 / 指南原文摘录子句级命中）。
- refusal：无 gold，按"是否拒答"判定。
- 判定规则（`src/evaluation.py` / `src/eval_refusal.py`）：答案数值 ⊆ 检索来源数值（±1）+ gold 要点覆盖 + 无来源外编造检测；语义近似不给分。

## 4. 评测协议

1. **生成评测**：160 题（composition/guideline/special）在 RAG 与 NoRAG 两种模式运行；报告含 `retrieval_hit_rate / faithfulness / rag_citation_rate / gold_cover_rag / gold_cover_norag / ablation_gain`。
2. **拒答评测**：40 题三协议——RAG（带检索上下文）、NoRAG（不带）、Strict（无上下文 + 显式"不知道就拒答"指令）。
3. **判官一致性**：40 题分层样本（含 6 条已知不忠实案例）由 qwen-plus（temperature=0）以通用 judge prompt 独立判定，与人工标注对照；C15 标注留白，39 条有效。

## 5. 复现步骤

```bash
git clone https://github.com/ElijahZhao/MetaNutri-Ai-RAG.git
cd MetaNutri-Ai-RAG
pip install -r requirements.txt
# 配置 .env（DASHSCOPE_API_KEY / DEEPSEEK_API_KEY / ARK_API_KEY）
python3 src/kb.py --rebuild            # 重建向量库（可选，缺失时自动从 tar.gz 恢复）

python3 data/build_kb_texts.py         # 清洗切片（344 切片）
python3 src/eval_hybrid.py             # 生成评测（160 题 × 三模型 × RAG/NoRAG）
python3 src/eval_refusal.py            # 拒答评测（40 题 × 三模型 × 三协议）
python3 src/evaluation.py              # 单模型评测入口（HybridRetriever, top_k=8）

python3 docs/figures/make_figures.py   # 重生成论文 Figure 1-6
streamlit run app.py                   # 本地 demo（聊天 + 引用 + 评测看板）
```

守卫测试：`pytest tests/`（数据守卫 26/26）。

## 6. 与论文章节对应

| 论文章节 | 本仓工件 |
|---|---|
| 3.1 基准构建 | `data/build_eval_set.py`、`data/build_refusal_set.py`、`data/eval_questions.json`、`data/refusal_questions.json`、`docs/eval-benchmark-spec.md` |
| 3.2 系统实现 | `src/hybrid.py`、`src/kb.py`、`src/config.py`、`src/generation.py` |
| 3.3 评测协议 | `src/evaluation.py`、`src/eval_refusal.py` |
| 4.1–4.5 结果 | `data/eval_report*.json`、`data/refusal_report*.json`、`docs/figures/fig1-6.png` |

## 7. 数字单一来源（权威工件）

| 工件 | 内容 |
|---|---|
| `data/eval_report.json` | qwen-plus 160 题生成评测 |
| `data/eval_report_deepseek.json` | deepseek-chat 160 题生成评测 |
| `data/eval_report_glm.json` | glm-5.3-flash 160 题生成评测 |
| `data/refusal_report.json` | qwen-plus 40 题拒答评测 |
| `data/refusal_report_deepseek.json` | deepseek-chat 40 题拒答评测 |
| `data/refusal_report_glm.json` | glm-5.3-flash 40 题拒答评测 |
| `docs/eval-benchmark-spec.md` | §9.2 三模型最终基线 / §9.3 judge 闸门 |

权威结果（v1.0.0，与论文一致）：eval 160 题三模型 retrieval_hit_rate 均 1.0；faithfulness qwen 0.9625 / deepseek 0.9938 / glm 0.9875；ablation_gain 0.20 / 0.225 / 0.225。拒答 40 题：refusal_rate_rag 1.0 / 1.0 / 0.975；refusal_rate_norag 0.0 / 0.0 / 0.025；strict 0.675 / 0.925 / 0.925。boundary 子类（R31–R40）裸 LLM 编造率三模型均 100%，RAG 拒答率三模型均 100%。判官一致性：规则 vs 人工 37/39 = 0.949，LLM judge vs 人工 33/39 = 0.846，规则 vs judge 34/40 = 0.850。

历史消融工件（论文未引用，仅供审计）：`data/hybrid_report.json`、`data/sweep_report.json`、`src/eval_sweep.py`。

## 8. 已知限制（与论文 Limitations 对应）

- L1 规模与覆盖：200 题，KB 覆盖 325 常见食物；boundary 子类 10 题统计功效有限（v1.1 扩至 30+）。
- L2 泛化食物名歧义（C50 首行匹配瑕疵）：gold 首行匹配"虾→虾皮"等；已限定范围不改变总体结论。
- L3 top-k 边界敏感性：RRF 在 k=5 边界抖动（G45/S40）；结论依赖 top_k=8 配置；k ∈ {3,…,12} 网格为后续工作。
- L4 官方源数据稀疏性：SOURCES 台账初版 307 与 CSV 325 行不一致已修正；维生素 A / 碘等缺失率为官方原始状态。
- L5 判官残余误差：规则-人工 0.949 非 1.0，G35/G36 为规则编造检测过严。
- L6 模型快照：三个商用模型为 2026 年 10 月 API 快照，迭代会改变绝对数值。

## 9. 工件清单（git tag v1.0.0）

代码：`src/`（hybrid、evaluation、eval_refusal、kb、generation、retrieval、config）；数据：`data/`（报告 JSON、题集、KB 文本、SOURCES、chroma_db.tar.gz）；文档：`docs/`（eval-benchmark-spec、figures、paper、tech-report）；测试：`tests/`。
