# nutri-rag W1 完成报告（2026-10-28）

## W1 数据准备阶段 — 全部完成

| 步骤 | 结果 | 产物 |
|---|---|---|
| W1-1 全量清单 | 1356 条（疾控官方平台 nlc.chinanutri.cn） | `data/foods_all_list.csv` + `data/fetch_foodlist.py` |
| W1-2 精选子集 | 307 条常见食物（关键词白名单+每类上限，剔除品牌变体） | `data/foods_selected_list.csv` + `data/fetch_foods_selected.py` |
| W1-3 营养详情 | 307×35 列（32 营养项，0 失败；缺失项为数据源本身未收录） | `data/foods_nutrition.csv` + `data/fetch_food_details.py` |
| W1-4 膳食指南 | 八准则核心推荐 + 准则六详细实践（中国营养学会官网） | `data/dietary_guidelines_2022.md`、`data/dietary_guidelines_rule6_detail.md` |
| W1-5 清洗切片 | 316 段（307 食物 + 9 指南），来源登记 | `data/kb_foods.txt`、`data/kb_guidelines.txt`、`data/SOURCES.md`、`data/build_kb_texts.py` |
| W1-6 向量库 | ChromaDB `nutri_kb` 316 chunks（阿里百炼 text-embedding-v3，1024 维，余弦距离） | `src/kb.py` + `data/chroma_db/`（备份 `data/chroma_db.tar.gz`） |

检索质量抽查（top-3 命中）：蔬菜水果量→准则三 ✓；鸡蛋营养→鸡蛋/蛋白/鹅蛋 ✓；喝水量→准则六 ✓；含铁食物→黄豆/鱿鱼/黑豆 ✓。

## 环境与密钥（不入库，重建时需要）
- 阿里百炼 API key：存于仓库根 `.env`（`DASHSCOPE_API_KEY=sk-...`），已 gitignore。**若沙箱清理，key 需用户从百炼控制台重新提供。**
- embedding 调用：OpenAI 兼容端点 `https://dashscope.aliyuncs.com/compatible-mode/v1`，模型 `text-embedding-v3`。
- 依赖：`pip install chromadb openai python-dotenv`。

## 明天从这里继续（W2 阶段）
1. **W2 RAG 管线**：src/retrieval.py（ChromaDB 检索 top-k，可加重排）→ src/generation.py（上下文组装→DeepSeek API→回答+引用溯源）→ src/evaluation.py（50 条评测集：成分20/膳食建议15/禁忌15；检索命中率、生成忠实度、消融对比 无RAG vs RAG）。
2. **待确认项（规划文档 12 项，未拍板）**：LLM 用 DeepSeek 还是统一切百炼 qwen 单 key；top-k/阈值；prompt 模板；README 语言与 License；Streamlit secrets 字段名等。
3. 数据文件过规范审查流程（任务①文件体检/②过程产物审查）后再提交属常态；W1 数据已按此入库（AGENTS.md 私有仓库名已脱敏）。

## 恢复向量库（如沙箱清理后 chroma_db 丢失）
```bash
tar -xzf data/chroma_db.tar.gz -C data/
# 或重建：python3 src/kb.py（需 .env 有 DASHSCOPE_API_KEY）
```
