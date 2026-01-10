# 專案結構說明

# Project Structure Guide

本文詳細說明 Claude Cookbooks 專案的目錄結構和各部分的用途，幫助您快速找到所需的資源。

> **[English version below](#english-version) | 英文版本請見下方**

---

## 目錄總覽

```
claude-cookbooks/
├── capabilities/          # 核心能力教學
├── tool_use/              # 工具使用範例
├── multimodal/            # 多模態（視覺）功能
├── extended_thinking/     # 延伸思考模式
├── patterns/              # 代理設計模式
├── claude_agent_sdk/      # Claude Agent SDK 範例
├── skills/                # Claude Skills 系統
├── misc/                  # 其他實用範例
├── third_party/           # 第三方整合
├── coding/                # 程式開發相關
├── finetuning/            # 模型微調
├── observability/         # 可觀測性
├── tool_evaluation/       # 工具評估
├── tests/                 # 測試檔案
├── scripts/               # 輔助腳本
├── docs/                  # 文件說明
└── .github/               # GitHub 設定
```

---

## 核心目錄說明

### `capabilities/` - 核心能力

Claude 的核心能力教學和評估框架：

| 子目錄 | 說明 | 適合對象 |
|--------|------|----------|
| `classification/` | 文字分類技術 | 需要建立分類系統的開發者 |
| `contextual-embeddings/` | 上下文嵌入和檢索 | RAG 系統開發者 |
| `retrieval_augmented_generation/` | RAG 完整教學 | 想增強 Claude 知識的開發者 |
| `summarization/` | 摘要生成技術 | 需要自動摘要功能的開發者 |
| `text_to_sql/` | 自然語言轉 SQL | 資料庫應用開發者 |

每個能力目錄通常包含：
- `guide.ipynb` - 主要教學 notebook
- `evals/` - 評估腳本和設定

---

### `tool_use/` - 工具使用

教導 Claude 如何使用外部工具：

| Notebook | 說明 | 難度 |
|----------|------|------|
| `calculator_tool.ipynb` | 基礎計算機工具範例 | 入門 |
| `extracting_structured_json.ipynb` | 提取結構化 JSON | 入門 |
| `customer_service_agent.ipynb` | 客服代理完整實作 | 中級 |
| `memory_cookbook.ipynb` | 記憶管理系統 | 中級 |
| `automatic-context-compaction.ipynb` | 上下文壓縮技術 | 進階 |
| `tool_search_with_embeddings.ipynb` | 工具搜尋優化 | 進階 |

---

### `multimodal/` - 多模態功能

處理圖片和視覺輸入：

| Notebook | 說明 |
|----------|------|
| `getting_started_with_vision.ipynb` | 視覺功能入門 |
| `best_practices_for_vision.ipynb` | 視覺最佳實踐 |
| `reading_charts_graphs_powerpoints.ipynb` | 解讀圖表和簡報 |
| `how_to_transcribe_text.ipynb` | 圖片文字轉錄 |
| `crop_tool.ipynb` | 圖片裁切工具 |
| `using_sub_agents.ipynb` | 子代理協作 |

---

### `extended_thinking/` - 延伸思考

Claude 的深度推理模式：

| Notebook | 說明 |
|----------|------|
| `extended_thinking.ipynb` | 延伸思考基礎 |
| `extended_thinking_with_tool_use.ipynb` | 延伸思考 + 工具使用 |

---

### `patterns/` - 設計模式

可重複使用的代理設計模式：

```
patterns/
└── agents/
    ├── basic_workflows.ipynb      # 基礎工作流程
    ├── evaluator_optimizer.ipynb  # 評估器-優化器模式
    ├── orchestrator_workers.ipynb # 協調器-工作者模式
    └── prompt_templates/          # 提示詞範本
```

---

### `claude_agent_sdk/` - Agent SDK

企業級代理實作範例：

| Notebook | 說明 |
|----------|------|
| `00_The_one_liner_research_agent.ipynb` | 一行程式碼研究代理 |
| `01_The_chief_of_staff_agent.ipynb` | 首席幕僚代理 |
| `02_The_observability_agent.ipynb` | 可觀測性代理 |

---

### `skills/` - Skills 系統

Claude 自訂技能開發：

```
skills/
├── README.md               # Skills 系統說明
├── CLAUDE.md               # 實作指南
└── custom_skills/          # 自訂技能範例
    ├── analyzing-financial-statements/
    ├── applying-brand-guidelines/
    └── creating-financial-models/
```

---

### `misc/` - 其他範例

各種實用的獨立範例：

| Notebook | 說明 | 推薦程度 |
|----------|------|----------|
| `how_to_enable_json_mode.ipynb` | 啟用 JSON 模式 | ⭐⭐⭐ |
| `prompt_caching.ipynb` | 提示詞快取 | ⭐⭐⭐ |
| `batch_processing.ipynb` | 批次處理 | ⭐⭐ |
| `building_evals.ipynb` | 建立評估系統 | ⭐⭐ |
| `building_moderation_filter.ipynb` | 內容審核過濾 | ⭐⭐ |
| `using_citations.ipynb` | 引用功能 | ⭐⭐ |
| `pdf_upload_summarization.ipynb` | PDF 摘要 | ⭐ |

---

### `third_party/` - 第三方整合

與外部服務的整合範例：

| 目錄 | 服務 | 用途 |
|------|------|------|
| `Pinecone/` | Pinecone | 向量資料庫 |
| `VoyageAI/` | Voyage AI | 嵌入向量 |
| `Wikipedia/` | Wikipedia | 知識檢索 |
| `MongoDB/` | MongoDB | 資料庫整合 |
| `LlamaIndex/` | LlamaIndex | RAG 框架 |
| `Deepgram/` | Deepgram | 語音轉文字 |
| `ElevenLabs/` | ElevenLabs | 文字轉語音 |
| `WolframAlpha/` | Wolfram Alpha | 計算知識 |

---

## 設定檔說明

### 專案根目錄

| 檔案 | 用途 |
|------|------|
| `pyproject.toml` | Python 專案設定（依賴、工具配置） |
| `uv.toml` | uv 套件管理器設定 |
| `uv.lock` | 鎖定的依賴版本 |
| `Makefile` | 開發指令（`make check`, `make test` 等） |
| `tox.ini` | 測試環境設定 |
| `.pre-commit-config.yaml` | Git pre-commit hooks |
| `registry.yaml` | 所有 notebook 的中央註冊表 |
| `authors.yaml` | 貢獻者資訊 |

### `.github/` 目錄

```
.github/
├── workflows/              # CI/CD 工作流程
│   ├── lint-format.yml     # 程式碼格式檢查
│   ├── notebook-quality.yml # Notebook 品質檢查
│   ├── notebook-tests.yml   # Notebook 測試
│   └── links.yml            # 連結檢查
├── ISSUE_TEMPLATE/         # Issue 範本
└── PULL_REQUEST_TEMPLATE.md # PR 範本
```

### `.claude/` 目錄

Claude Code 整合設定：

```
.claude/
├── commands/               # Slash 指令
│   ├── notebook-review.md  # /notebook-review
│   ├── model-check.md      # /model-check
│   └── link-review.md      # /link-review
├── agents/                 # 代理設定
└── skills/                 # 技能設定
```

---

## 如何找到您需要的內容

### 依目的查找

| 我想要... | 請看... |
|----------|---------|
| 開始使用 Claude API | `misc/how_to_enable_json_mode.ipynb` |
| 處理圖片 | `multimodal/getting_started_with_vision.ipynb` |
| 建立 RAG 系統 | `capabilities/retrieval_augmented_generation/` |
| 建立聊天機器人 | `tool_use/customer_service_agent.ipynb` |
| 優化 token 用量 | `misc/prompt_caching.ipynb` |
| 整合向量資料庫 | `third_party/Pinecone/` |
| 學習進階代理 | `claude_agent_sdk/` |

### 依難度查找

**入門級**
- `tool_use/calculator_tool.ipynb`
- `misc/how_to_enable_json_mode.ipynb`
- `multimodal/getting_started_with_vision.ipynb`

**中級**
- `tool_use/customer_service_agent.ipynb`
- `capabilities/classification/guide.ipynb`
- `misc/building_evals.ipynb`

**進階**
- `extended_thinking/`
- `claude_agent_sdk/`
- `patterns/agents/`

---

## registry.yaml 說明

`registry.yaml` 是專案的中央註冊表，記錄所有 notebook 的元資料：

```yaml
- title: Calculator tool
  description: Learn how to integrate a simple calculator tool with Claude
  path: tool_use/calculator_tool.ipynb
  authors:
    - anthropic
  categories:
    - tool_use
  date_created: 2024-01-15
```

如果您要新增 notebook，請務必在此檔案中註冊。

---

<a name="english-version"></a>

## English Version

This document provides a detailed explanation of the Claude Cookbooks project directory structure and the purpose of each section.

---

### Directory Overview

```
claude-cookbooks/
├── capabilities/          # Core capability tutorials
├── tool_use/              # Tool usage examples
├── multimodal/            # Multimodal (vision) features
├── extended_thinking/     # Extended thinking mode
├── patterns/              # Agent design patterns
├── claude_agent_sdk/      # Claude Agent SDK examples
├── skills/                # Claude Skills system
├── misc/                  # Other practical examples
├── third_party/           # Third-party integrations
├── coding/                # Code development related
├── finetuning/            # Model fine-tuning
├── observability/         # Observability
├── tool_evaluation/       # Tool evaluation
├── tests/                 # Test files
├── scripts/               # Helper scripts
├── docs/                  # Documentation
└── .github/               # GitHub configuration
```

---

### Core Directory Descriptions

#### `capabilities/` - Core Capabilities

Claude's core capability tutorials and evaluation frameworks:

| Subdirectory | Description | Target Audience |
|--------------|-------------|-----------------|
| `classification/` | Text classification techniques | Developers building classification systems |
| `contextual-embeddings/` | Contextual embeddings and retrieval | RAG system developers |
| `retrieval_augmented_generation/` | Complete RAG tutorials | Developers enhancing Claude's knowledge |
| `summarization/` | Summarization techniques | Developers needing auto-summarization |
| `text_to_sql/` | Natural language to SQL | Database application developers |

---

#### `tool_use/` - Tool Usage

Teaching Claude how to use external tools:

| Notebook | Description | Difficulty |
|----------|-------------|------------|
| `calculator_tool.ipynb` | Basic calculator tool example | Beginner |
| `extracting_structured_json.ipynb` | Extract structured JSON | Beginner |
| `customer_service_agent.ipynb` | Complete customer service agent | Intermediate |
| `memory_cookbook.ipynb` | Memory management system | Intermediate |
| `automatic-context-compaction.ipynb` | Context compression techniques | Advanced |

---

#### `multimodal/` - Multimodal Features

Processing images and visual inputs:

| Notebook | Description |
|----------|-------------|
| `getting_started_with_vision.ipynb` | Getting started with vision |
| `best_practices_for_vision.ipynb` | Vision best practices |
| `reading_charts_graphs_powerpoints.ipynb` | Interpreting charts and presentations |
| `how_to_transcribe_text.ipynb` | Image text transcription |

---

#### `misc/` - Other Examples

Various standalone practical examples:

| Notebook | Description | Recommended |
|----------|-------------|-------------|
| `how_to_enable_json_mode.ipynb` | Enable JSON mode | ⭐⭐⭐ |
| `prompt_caching.ipynb` | Prompt caching | ⭐⭐⭐ |
| `batch_processing.ipynb` | Batch processing | ⭐⭐ |
| `building_evals.ipynb` | Building evaluation systems | ⭐⭐ |

---

#### `third_party/` - Third-Party Integrations

Integration examples with external services:

| Directory | Service | Purpose |
|-----------|---------|---------|
| `Pinecone/` | Pinecone | Vector database |
| `VoyageAI/` | Voyage AI | Embeddings |
| `Wikipedia/` | Wikipedia | Knowledge retrieval |
| `MongoDB/` | MongoDB | Database integration |

---

### How to Find What You Need

#### By Purpose

| I want to... | Look at... |
|--------------|------------|
| Start using Claude API | `misc/how_to_enable_json_mode.ipynb` |
| Process images | `multimodal/getting_started_with_vision.ipynb` |
| Build a RAG system | `capabilities/retrieval_augmented_generation/` |
| Build a chatbot | `tool_use/customer_service_agent.ipynb` |
| Optimize token usage | `misc/prompt_caching.ipynb` |

#### By Difficulty

**Beginner**
- `tool_use/calculator_tool.ipynb`
- `misc/how_to_enable_json_mode.ipynb`
- `multimodal/getting_started_with_vision.ipynb`

**Intermediate**
- `tool_use/customer_service_agent.ipynb`
- `capabilities/classification/guide.ipynb`
- `misc/building_evals.ipynb`

**Advanced**
- `extended_thinking/`
- `claude_agent_sdk/`
- `patterns/agents/`

---

### registry.yaml

`registry.yaml` is the project's central registry recording metadata for all notebooks:

```yaml
- title: Calculator tool
  description: Learn how to integrate a simple calculator tool with Claude
  path: tool_use/calculator_tool.ipynb
  authors:
    - anthropic
  categories:
    - tool_use
  date_created: 2024-01-15
```

If you're adding a new notebook, make sure to register it in this file.
