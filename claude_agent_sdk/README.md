# 使用 Claude Agent SDK 建構強大的代理

# Building Powerful Agents with the Claude Agent SDK

一個教學系列，展示如何使用 [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) 建構複雜的通用代理系統，從簡單的研究代理逐步進階到具有外部系統整合的多代理協調。

> **[English version below](#english-version) | 英文版本請見下方**

## 開始使用

#### 1. 安裝 uv、[node](https://nodejs.org/en/download/) 和 Claude Code CLI（如果尚未安裝）

```curl -LsSf https://astral.sh/uv/install.sh | sh ```

```npm install -g @anthropic-ai/claude-code```

#### 2. 複製並設定專案

```git clone https://github.com/anthropics/anthropic-cookbook.git ```

```cd anthropic-cookbook/claude_agent_sdk```

```uv sync ```

#### 3. 將 venv 註冊為 Jupyter kernel，以便在 notebooks 中使用

```uv run python -m ipykernel install --user --name="cc-sdk-tutorial" --display-name "Python (cc-sdk-tutorial)" ```

#### 4. Claude API 金鑰
1. 造訪 [console.anthropic.com](https://console.anthropic.com/dashboard)
2. 註冊或登入您的帳戶
3. 點擊「Get API keys」
4. 複製金鑰並貼到 `.env` 檔案中，格式為 ```ANTHROPIC_API_KEY=```

#### 5. Notebook 02 的 GitHub Token
如果您計劃完成 Observability Agent notebook：
1. 在[此處](https://github.com/settings/personal-access-tokens/new)取得 GitHub Personal Access Token
2. 選擇「Fine-grained」token 並使用預設選項（公開儲存庫，無帳戶權限）
3. 將其添加到 `.env` 檔案中，格式為 `GITHUB_TOKEN="<token>"`
4. 確保 [Docker](https://www.docker.com/products/docker-desktop/) 在您的機器上執行

## 教學系列概述

本教學系列帶您從基礎代理實作進階到能夠處理真實世界複雜性的複雜多代理系統。每個 notebook 都建立在前一個的基礎上，引入新概念和功能，同時保持實用的、可用於生產環境的實作。

### 您將學到什麼

透過本系列，您將接觸到：
- **核心 SDK 基礎** — 包含 Python SDK 中的 `query()` 以及 `ClaudeSDKClient` 和 `ClaudeAgentOptions` 介面
- **工具使用模式** — 從基礎的 WebSearch 到複雜的 MCP 伺服器整合
- **多代理協調** — 使用專業化子代理和協調機制
- **企業功能** — 利用 hooks 進行合規追蹤和稽核軌跡
- **外部系統整合** — 透過 Model Context Protocol（MCP）

注意：本教學假設您對 Claude Code 有一定程度的熟悉。理想情況下，如果您一直使用 Claude Code 來加速您的編碼任務，並希望利用其原始的代理能力進行軟體工程以外的任務，本教學將幫助您開始。

## Notebook 結構與內容

### [Notebook 00：單行程式碼研究代理](00_The_one_liner_research_agent.ipynb)

從一個只需幾行程式碼就能建構的簡單但強大的研究代理開始您的旅程。本 notebook 介紹核心 SDK 概念，並展示 Claude Agent SDK 如何實現自主資訊收集和綜合。

**關鍵概念：**
- 使用 `query()` 和非同步迭代的基礎代理迴圈
- 用於自主研究的 WebSearch 工具
- 使用 Read 工具的多模態功能
- 使用 `ClaudeSDKClient` 的對話上下文管理
- 用於代理專業化的系統提示詞

### [Notebook 01：首席幕僚代理](01_The_chief_of_staff_agent.ipynb)

為新創公司 CEO 建構一個全面的 AI 首席幕僚，展示生產環境的進階 SDK 功能。本 notebook 展示如何創建具有治理、合規和專業知識的複雜代理架構。

**探索的關鍵功能：**
- **記憶與上下文：** 使用 CLAUDE.md 檔案的持久指令
- **輸出樣式：** 為不同受眾量身定制的溝通方式
- **計畫模式：** 對複雜任務進行策略規劃而不執行
- **自訂斜線指令：** 常見操作的使用者友好捷徑
- **Hooks：** 自動化合規追蹤和稽核軌跡
- **子代理協調：** 協調專業代理以獲得領域專業知識
- **Bash 工具整合：** 用於程序知識和複雜計算的 Python 腳本執行

### [Notebook 02：可觀測性代理](02_The_observability_agent.ipynb)

透過 Model Context Protocol 將代理連接到外部系統，擴展超越本地功能。將您的代理從被動觀察者轉變為 DevOps 工作流程的主動參與者。

**進階功能：**
- **Git MCP 伺服器：** 13+ 個用於儲存庫分析和版本控制的工具
- **GitHub MCP 伺服器：** 100+ 個用於完整 GitHub 平台整合的工具
- **即時監控：** CI/CD 管線分析和故障檢測
- **智慧事件回應：** 自動化根本原因分析
- **生產工作流程自動化：** 從監控到可操作的洞察

## 完整的代理實作

每個 notebook 在其各自的目錄中包含代理實作：
- **`research_agent/`** - 具有網頁搜尋和多模態分析的自主研究代理
- **`chief_of_staff_agent/`** - 具有財務建模和合規功能的多代理執行助理
- **`observability_agent/`** - 具有 GitHub 整合的 DevOps 監控代理

**執行獨立代理：** 要在 notebooks 之外匯入代理模組，請從 `claude_agent_sdk/` 目錄執行或以可編輯模式安裝套件：
```bash
uv pip install -e .
```

## 背景
### Claude Agent SDK 的演進

Claude Code 已成為 Anthropic 最成功的產品之一，但不僅僅是因為其最先進的編碼功能。其真正的突破在於更基本的東西：**Claude 在代理工作方面表現出色**。

Claude Code 的特別之處不僅僅是程式碼理解；而是以下能力：
- 自主將複雜任務分解為可管理的步驟
- 有效使用工具並對何時使用哪些工具做出智慧決策
- 在長時間執行的任務中保持上下文和記憶
- 從錯誤中優雅恢復並在需要時調整方法
- 知道何時請求澄清與何時以合理假設繼續

這些功能使 Claude Code 成為最接近 Claude 原始代理能力「裸機」介面的東西：一個最小但完整且複雜的介面，讓模型的功能以最少的開銷發光。

### 超越編碼：代理建構者的工具包

SDK 最初是 Anthropic 工程師為加速開發工作流程而建構的內部工具，其公開發布揭示了意想不到的潛力。在 Claude Agent SDK 及其 GitHub 整合發布後，開發者開始將其用於遠超編碼的任務：

- **研究代理** — 跨多個來源收集和綜合資訊
- **資料分析代理** — 探索資料集並生成洞察
- **工作流程自動化代理** — 處理重複的業務流程
- **監控和可觀測性代理** — 監視系統並回應問題
- **內容生成代理** — 創建和精煉各種類型的內容

模式很清楚：SDK 無意中成為了一個有效的代理建構框架。其設計用於處理軟體開發複雜性的架構，證明非常適合通用代理創建。

本教學系列展示如何利用 Claude Agent SDK 為任何領域或使用案例建構高效代理，從簡單的自動化到複雜的企業系統。

## 貢獻

發現問題或有建議？請開啟 issue 或提交 pull request！

---

<a name="english-version"></a>

## English Version

A tutorial series demonstrating how to build sophisticated general-purpose agentic systems using the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python), progressing from simple research agents to multi-agent orchestration with external system integration.

### Getting Started

#### 1. Install uv, [node](https://nodejs.org/en/download/), and the Claude Code CLI (if you haven't already)

```curl -LsSf https://astral.sh/uv/install.sh | sh ```

```npm install -g @anthropic-ai/claude-code```

#### 2. Clone and set up the project

```git clone https://github.com/anthropics/anthropic-cookbook.git ```

```cd anthropic-cookbook/claude_agent_sdk```

```uv sync ```

#### 3. Register venv as Jupyter kernel so that you can use it in the notebooks

```uv run python -m ipykernel install --user --name="cc-sdk-tutorial" --display-name "Python (cc-sdk-tutorial)" ```

#### 4. Claude API Key
1. Visit [console.anthropic.com](https://console.anthropic.com/dashboard)
2. Sign up or log in to your account
3. Click on "Get API keys"
4. Copy the key and paste it into your `.env` file as ```ANTHROPIC_API_KEY=```

#### 5. GitHub Token for Notebook 02
If you plan to work through the Observability Agent notebook:
1. Get a GitHub Personal Access Token [here](https://github.com/settings/personal-access-tokens/new)
2. Select "Fine-grained" token with default options (public repos, no account permissions)
3. Add it to your `.env` file as `GITHUB_TOKEN="<token>"`
4. Ensure [Docker](https://www.docker.com/products/docker-desktop/) is running on your machine

### Tutorial Series Overview

This tutorial series takes you on a journey from basic agent implementation to sophisticated multi-agent systems capable of handling real-world complexity. Each notebook builds upon the previous one, introducing new concepts and capabilities while maintaining practical, production-ready implementations.

#### What You'll Learn

Through this series, you'll be exposed to:
- **Core SDK fundamentals** with `query()` and the `ClaudeSDKClient` & `ClaudeAgentOptions` interfaces in the Python SDK
- **Tool usage patterns** from basic WebSearch to complex MCP server integration
- **Multi-agent orchestration** with specialized subagents and coordination
- **Enterprise features** by leveraging hooks for compliance tracking and audit trails
- **External system integration** via Model Context Protocol (MCP)

Note: This tutorial assumes you have some level of familiarity with Claude Code. Ideally, if you have been using Claude Code to supercharge your coding tasks and would like to leverage its raw agentic power for tasks beyond Software Engineering, this tutorial will help you get started.

### Notebook Structure & Content

#### [Notebook 00: The One-Liner Research Agent](00_The_one_liner_research_agent.ipynb)

Start your journey with a simple yet powerful research agent built in just a few lines of code. This notebook introduces core SDK concepts and demonstrates how the Claude Agent SDK enables autonomous information gathering and synthesis.

**Key Concepts:**
- Basic agent loops with `query()` and async iteration
- WebSearch tool for autonomous research
- Multimodal capabilities with the Read tool
- Conversation context management with `ClaudeSDKClient`
- System prompts for agent specialization

#### [Notebook 01: The Chief of Staff Agent](01_The_chief_of_staff_agent.ipynb)

Build a comprehensive AI Chief of Staff for a startup CEO, showcasing advanced SDK features for production environments. This notebook demonstrates how to create sophisticated agent architectures with governance, compliance, and specialized expertise.

**Key Features Explored:**
- **Memory & Context:** Persistent instructions with CLAUDE.md files
- **Output Styles:** Tailored communication for different audiences
- **Plan Mode:** Strategic planning without execution for complex tasks
- **Custom Slash Commands:** User-friendly shortcuts for common operations
- **Hooks:** Automated compliance tracking and audit trails
- **Subagent Orchestration:** Coordinating specialized agents for domain expertise
- **Bash Tool Integration:** Python script execution for procedural knowledge and complex computations

#### [Notebook 02: The Observability Agent](02_The_observability_agent.ipynb)

Expand beyond local capabilities by connecting agents to external systems through the Model Context Protocol. Transform your agent from a passive observer into an active participant in DevOps workflows.

**Advanced Capabilities:**
- **Git MCP Server:** 13+ tools for repository analysis and version control
- **GitHub MCP Server:** 100+ tools for complete GitHub platform integration
- **Real-time Monitoring:** CI/CD pipeline analysis and failure detection
- **Intelligent Incident Response:** Automated root cause analysis
- **Production Workflow Automation:** From monitoring to actionable insights

### Complete Agent Implementations

Each notebook includes an agent implementation in its respective directory:
- **`research_agent/`** - Autonomous research agent with web search and multimodal analysis
- **`chief_of_staff_agent/`** - Multi-agent executive assistant with financial modeling and compliance
- **`observability_agent/`** - DevOps monitoring agent with GitHub integration

**Running standalone agents:** To import agent modules outside of notebooks, either run from the `claude_agent_sdk/` directory or install the package in editable mode:
```bash
uv pip install -e .
```

### Background
#### The Evolution of Claude Agent SDK

Claude Code has emerged as one of Anthropic's most successful products, but not just for its SOTA coding capabilities. Its true breakthrough lies in something more fundamental: **Claude is exceptionally good at agentic work**.

What makes Claude Code special isn't just code understanding; it's the ability to:
- Break down complex tasks into manageable steps autonomously
- Use tools effectively and make intelligent decisions about which tools to use and when
- Maintain context and memory across long-running tasks
- Recover gracefully from errors and adapt approaches when needed
- Know when to ask for clarification versus when to proceed with reasonable assumptions

These capabilities have made Claude Code the closest thing to a "bare metal" harness for Claude's raw agentic power: a minimal yet complete and sophisticated interface that lets the model's capabilities shine with the least possible overhead.

#### Beyond Coding: The Agent Builder's Toolkit

Originally an internal tool built by Anthropic engineers to accelerate development workflows, the SDK's public release revealed unexpected potential. After the release of the Claude Agent SDK and its GitHub integration, developers began using it for tasks far beyond coding:

- **Research agents** that gather and synthesize information across multiple sources
- **Data analysis agents** that explore datasets and generate insights
- **Workflow automation agents** that handle repetitive business processes
- **Monitoring and observability agents** that watch systems and respond to issues
- **Content generation agents** that create and refine various types of content

The pattern was clear: the SDK had inadvertently become an effective agent-building framework. Its architecture, designed to handle software development complexity, proved remarkably well-suited for general-purpose agent creation.

This tutorial series demonstrates how to leverage the Claude Agent SDK to build highly efficient agents for any domain or use case, from simple automation to complex enterprise systems.

### Contributing

Found an issue or have a suggestion? Please open an issue or submit a pull request!
