# AGENTS.md — nutri-rag 智能体指南

## 本仓库是什么
MetaNutri 生态的 RAG 研究应用模块：健康饮食问答系统。
公开营养数据 → ChromaDB 向量库 → Python RAG 管线（检索→组装→DeepSeek→回答+引用）→ Streamlit demo + 内置评测。
独立子仓库（与 ppgr 同构），README 首行声明 "RAG research & app module of the MetaNutri ecosystem"。
**本项目不涉及论文**：不加载《论文模式.md》；若场景变化，需用户重新决策后再开启。

## 三仓库架构
| | 仓库 | 可见性 | 用途 |
|---|---|---|---|
| 主仓库 | ElijahZhao/nutri-rag | Public | 展示面：README、代码、docs/ |
| 错题本 | ElijahZhao/project-archive | Private | 本项目一切过程材料 → `nutri-rag/` 子目录（01-过程证据/02-审查产物/03-诊断书/05-AI使用记录） |
| 学习笔记 | ElijahZhao/learning-notes | Private | 仅跨项目通用心得，同样写在 `nutri-rag/` 下 |

硬规则：
- 只允许新增/修改 `project-archive/nutri-rag/` 与 `learning-notes/nutri-rag/` 下的内容；其他项目内容只读不动
- 不得用 submodule/subtree 关联私人仓库；主仓库任何文件、README、commit、CI 中不得出现两个私人仓库的名称或 URL
- `[项目名]` = `nutri-rag`，与主仓库大小写、连字符完全一致

## 常用命令
- 安装依赖：`uv sync`
- 构建向量库：`python -m src.scripts.build_kb`
- 运行评测：`pytest tests/`（检索命中率、生成忠实度）
- 启动 demo：`streamlit run app.py`
- 可选 API：`uvicorn src.api:app --reload`

## 开发与审查流程（权威规范仓库）
- 规范源：`ElijahZhao/List-of-open-source-projects-for-AI-coding-agent-specification`
- 审查类任务（审查/收尾/README/去味）必须先加载该仓库《项目审查提示词库.md》全文，按任务编号执行：
  ① 文件体检 → ② 过程产物审查 → ③ 竣工评审 → ④ 修缮审查 → ⑤ README 重写 → ⑥ 去 AI 味
- **一任务一确认**：每任务产出清单/报告后停下等用户拍板，禁止连跑
- 每次回复开头声明：当前任务编号 / 覆盖率 / 是否涉及涉密模块
- 报告遵循该库附录 F 统一模板

## 铁律（任何时候直接生效）
1. 绝不编数据：缺失标 `[待补测]`，禁止估算与"合理推测"
2. 结论必有证据：数字对照实验输出、API 行为对照代码、文献对照原文；无法取证写"未确认"
3. 剥离环境信息：环境标识/绝对路径剥离后进公开仓库；**失败与异常的技术事实必须保留**
4. 提交话术中性：commit 只描述"改了什么"，不写"为什么/按什么流程改"
5. 披露义务 > 任何保密偏好

## 架构边界（禁改路径）
- `data/`：数据源与清洗脚本，历史文件只增不改；新数据必须记录来源
- `src/`：管线代码（retrieval / generation / evaluation 分模块）
- `tests/`：评测与单元测试，任何管线改动必须跑通
- `app.py`：Streamlit 前端，保持轻量
- 禁止提交：API key、绝对路径、个人信息
