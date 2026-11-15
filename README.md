# AI Panel Studio — 多智能体自主圆桌辩论演播室

> **AI Panel Studio** 是一套端到端、工程化交付的多智能体（Multi-Agent）自主圆桌辩论演播平台 Web App MVP。项目基于 **事件驱动状态机** 与 **8 因子动态发言仲裁引擎**，彻底打破传统的机械轮流发言模式，实现真正的专家自主意图判定、抢答反驳、共识收敛看板与实时演播厅打字机流式呈现。

[![Tests](https://img.shields.io/badge/tests-156%2F156%20passing-brightgreen)](docs/TEST_PLAN.md)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org)
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20Async-003B57.svg)](https://www.sqlite.org)

---

## 🌟 核心特性与技术亮点

1. **非机械式 8 因子动态发言仲裁引擎 (`SpeakerArbitrator`)**
   - 绝非固定 A → B → C → D 轮流模式。
   - 所有专家并行生成结构化发言意图（`wants_floor`、`action_type`、`priority`、`reason`、`target_speaker_id`）。
   - 仲裁器基于 8 因子归一化评分公式判定发言权：
     $$S_i = 0.20 \cdot U_i + 0.25 \cdot C_i + 0.15 \cdot T_i + 0.15 \cdot E_i + 0.10 \cdot N_i + 0.15 \cdot \frac{1}{1 + \ln(1 + \text{turns}_i)}$$
   - 内置发言冷却期（`cooldown`）与对数机会公平性阻尼，严密防止单专家无限霸麦。

2. **多讨论完全并发隔离（P0 级架构准入）**
   - 每个讨论具备全局唯一 `discussion_id`。
   - 独立协程锁（`asyncio.Lock`）、独立事件序列号（`seq_id`）、独立会话状态机与独立 SSE 广播订阅。
   - 暂停、恢复或结题任意单场讨论，绝不影响其他并发运行的圆桌会话。

3. **高可靠 SSE 实时事件流与断线恢复**
   - 500 容量事件环形缓冲区（`EventRingBuffer`）。
   - 支持 `Last-Event-ID` 机制：客户端意外断网或重连后，自动拉取失步期间的所有事件并平滑追回。
   - 支持首包即时刷新（Handshake Comment）与打字机抖动流（Typing Jitter Stream）。

4. **零凭证泄露安全防御体系**
   - 严格禁止在前端代码中暴露任何大模型密钥（无 `VITE_` 前缀密钥）。
   - 后端统一自 `.env` 读取 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。
   - **离线高保真 Mock 引擎平滑回退**：未配置 Key 或网络故障时，系统自动切入内建的 5 大辩论领域高仿真 Mock 引擎，在 Web 界面明显披露当前运行模式，杜绝虚假输出。

5. **演播厅暗色沉浸式产品设计**
   - **话题创建页**：议题输入、预设案例一键载入、2-6 位专家席位自主生成、历史研讨库复盘。
   - **辩论直播间**：主持人仲裁席、专家状态卡片（带举手动画 ✋ 与激活发光边框）、实况 Teleprompter 打字流、共识与分歧收敛看板。
   - **总结审计页**：主持人自然语言综合评述长文、共识列表、分歧焦点、专家心智演变审计表、一键导出 JSON / Markdown 结题报告。

---

## 🛠️ 技术栈清单

- **后端 (Backend)**：Python 3.11+ / FastAPI / SQLAlchemy 2.0 (Async) / SQLite (WAL 模式) / Pydantic 2 / asyncio / sse-starlette
- **前端 (Frontend)**：React 19 / TypeScript / Vite / Tailwind CSS / Lucide React
- **测试体系 (Testing)**：Pytest / pytest-asyncio / pytest-cov / httpx (156 项全自动化测试套件)

---

## 🚀 Windows 11 本地快速上手指南

### 1. 环境准备
确保本机已安装：
- **Python 3.11 或更高版本**（推荐 Python 3.11 / 3.12 / 3.13）
- **Node.js 18 或更高版本**（推荐 LTS）
- **Git**

### 2. 克隆项目与配置环境变量
```powershell
# 进入项目根目录
cd G:\实习\ai-panel-studio

# 复制环境变量模板
Copy-Item .env.example .env
```

> **提示**：若有 DeepSeek 或 OpenAI API Key，可在 `.env` 中填入：
> ```env
> LLM_API_KEY=your_deepseek_or_openai_key_here
> LLM_BASE_URL=https://api.deepseek.com/v1
> LLM_MODEL=deepseek-chat
> ```
> 若未填写密钥，系统将**自动启用离线高仿真 Mock 引擎**，完全支持离线演播与测试验证！

### 3. 后端环境配置与依赖安装
```powershell
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 升级 pip 并安装依赖
pip install -r requirements.txt
```

### 4. 数据库初始化与注入 5 组预设讨论数据
项目提供预置的 5 大经典圆桌讨论（覆盖初级程序员替代、大学生就业读研、自动驾驶普及、AI Agent 对 SaaS 重构、本科创业）：
```powershell
# 在根目录运行种子脚本 (确保已激活虚拟环境)
cd G:\实习\ai-panel-studio
python seed.py
```
> 输出显示 `✅ Seeding successfully completed! 5 full discussions ready.` 即表示 5 组圆桌、31 轮实录、25 位专家及对应共识与分歧已注入 SQLite 数据库。

### 5. 启动后端服务
```powershell
cd G:\实习\ai-panel-studio\backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
后端服务启动于：`http://127.0.0.1:8000`  
API 文档（Swagger UI）：`http://127.0.0.1:8000/docs`  
健康检查：`http://127.0.0.1:8000/api/health`

### 6. 启动前端开发服务器
打开新的 PowerShell 终端窗口：
```powershell
cd G:\实习\ai-panel-studio\frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```
前端界面就绪于：`http://localhost:5174`（或 Vite 提示的具体端口）。打开浏览器即可开始使用！

---

## 🧪 运行自动化测试套件

在 `G:\实习\ai-panel-studio` 目录下执行全套 156 项测试：
```powershell
pytest backend/tests -v
```

### 分级测试执行：
```powershell
# 运行 Tier 1 核心功能与基础生命周期 (36 tests)
pytest backend/tests/e2e/test_tier1_features.py -q

# 运行 Tier 2 边界条件与安全异常防御 (51 tests)
pytest backend/tests/e2e/test_tier2_boundaries.py -q

# 运行 Tier 3 并发隔离与 SSE 断线重连 (12 tests)
pytest backend/tests/e2e/test_tier3_concurrency.py -q

# 运行 Tier 4 现实全真业务链路 (5 tests)
pytest backend/tests/e2e/test_tier4_scenarios.py -q
```
**实测通过率**：**156 / 156 passed (100% 通过率)**

---

## 📚 完整工程文档导航

详细技术规格与开发全记录收录于 `docs/` 目录：

- 📋 [**需求规格说明书 (PRD.md)**](docs/PRD.md)：核心场景、用户故事、状态机定义与验收指标。
- 🏛️ [**领域驱动设计白皮书 (DDD.md)**](docs/DDD.md)：统一语言、实体聚合根、值对象、领域事件与防腐层。
- 📐 [**系统架构设计书 (ARCHITECTURE.md)**](docs/ARCHITECTURE.md)：前后端分离、SSE 流式管道、8 因子仲裁拓扑。
- 🗄️ [**数据库实体关系模型 (ER_DIAGRAM.md)**](docs/ER_DIAGRAM.md)：SQLite 关系范式、级联外键、Mermaid 架构图。
- 🔌 [**OpenAPI 接口契约说明书 (API.md)**](docs/API.md)：10 大 RESTful 端点与 SSE 流式事件协议定义。
- 🧪 [**测试全景计划与质量报告 (TEST_PLAN.md)**](docs/TEST_PLAN.md)：Tiers 1-4 分层测试矩阵与 156 项用例执行报告。
- 💬 [**核心 Prompt 真实资产库 (PROMPTS.md)**](docs/PROMPTS.md)：记录涵盖 SDD、DDD、TDD、Engine、E2E 的 5 段实际开发 Prompt。
- 🛠️ [**开发工作流与排障报告 (WORKFLOW.md)**](docs/WORKFLOW.md)：真实复盘 Claude Code 结合 DeepSeek V4 Pro 的协同开发与 3 个典型难题定位。
- 🏆 [**最终综合验收报告 (FINAL_ACCEPTANCE_REPORT.md)**](docs/FINAL_ACCEPTANCE_REPORT.md)：对照 Items A~Q 全部门禁项的逐项核验结果。

---

## 📦 发布打包

运行独立的打包脚本，生成剔除 `node_modules`、`.venv`、`.git`、缓存及本地数据库的干净源码发布压缩包：
```powershell
python scripts/package_release.py
```
生成包文件位于：`ai-panel-studio-release.zip`。
