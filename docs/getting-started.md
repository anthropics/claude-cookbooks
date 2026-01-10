# 新手入門指南

# Getting Started Guide

本指南將幫助您從零開始設置並使用 Claude Cookbooks 專案。

> **[English version below](#english-version) | 英文版本請見下方**

---

## 什麼是 Claude Cookbooks？

Claude Cookbooks 是一個由 Anthropic 維護的開源專案，提供了大量使用 Claude API 的實用範例和教學。這些範例以 **Jupyter Notebook** 格式呈現，讓您可以互動式地學習和實驗。

### 為什麼使用 Jupyter Notebook？

- **互動式執行**：可以逐步執行程式碼，即時看到結果
- **圖文並茂**：可以在程式碼旁邊加入說明文字、圖片和圖表
- **易於學習**：適合教學和實驗，方便修改和嘗試
- **保留輸出**：執行結果會保存在 notebook 中，方便日後參考

---

## 環境設置

### 步驟 1：安裝 Python

確保您的系統已安裝 Python 3.11 或更高版本。

```bash
# 檢查 Python 版本
python --version
# 或
python3 --version
```

如果尚未安裝，請從 [python.org](https://www.python.org/downloads/) 下載安裝。

### 步驟 2：安裝 uv 套件管理工具

本專案使用 [uv](https://docs.astral.sh/uv/) 作為套件管理工具，它比傳統的 pip 更快速且更可靠。

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip 安裝
pip install uv
```

### 步驟 3：克隆專案

```bash
git clone https://github.com/anthropics/anthropic-cookbook.git
cd anthropic-cookbook
```

### 步驟 4：安裝專案依賴

```bash
# 安裝所有依賴項
uv sync --all-extras

# 安裝 pre-commit hooks（可選，但推薦）
uv run pre-commit install
```

### 步驟 5：設置 API 金鑰

1. 前往 [Anthropic Console](https://console.anthropic.com/) 註冊並取得 API 金鑰
2. 設置環境變數：

```bash
# 複製範例設定檔
cp .env.example .env

# 編輯 .env 檔案，加入您的 API 金鑰
# ANTHROPIC_API_KEY=your-api-key-here
```

---

## 執行 Notebook

### 方法 1：使用 Jupyter Lab（推薦）

```bash
# 啟動 Jupyter Lab
uv run jupyter lab
```

這會在瀏覽器中開啟 Jupyter Lab 介面，您可以瀏覽並執行任何 notebook。

### 方法 2：使用 VS Code

1. 安裝 [VS Code](https://code.visualstudio.com/)
2. 安裝 [Jupyter 擴充套件](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)
3. 開啟專案資料夾
4. 點擊任意 `.ipynb` 檔案即可開啟並執行

### 方法 3：使用傳統 Jupyter Notebook

```bash
# 啟動 Jupyter Notebook
uv run jupyter notebook
```

---

## 推薦的學習路徑

### 初學者

如果您是第一次接觸 Claude API，建議按以下順序學習：

1. **[Claude API 基礎課程](https://github.com/anthropics/courses/tree/master/anthropic_api_fundamentals)** - 先完成這個線上課程
2. **[計算機工具範例](tool_use/calculator_tool.ipynb)** - 了解基本的工具使用
3. **[JSON 模式](misc/how_to_enable_json_mode.ipynb)** - 學習如何獲得結構化輸出

### 中級使用者

已有基礎後，可以探索：

1. **[RAG 檢索增強生成](capabilities/retrieval_augmented_generation/)** - 使用外部資料增強回應
2. **[客服代理](tool_use/customer_service_agent.ipynb)** - 建立實用的對話代理
3. **[視覺功能](multimodal/getting_started_with_vision.ipynb)** - 處理圖片輸入

### 進階使用者

深入探索進階主題：

1. **[Extended Thinking](extended_thinking/)** - 延伸思考模式
2. **[Claude Agent SDK](claude_agent_sdk/)** - 企業級代理實作
3. **[Skills 技能系統](skills/)** - 自訂技能開發

---

## 常見問題

### Q: 為什麼執行 notebook 時出現 API 金鑰錯誤？

確保您已正確設置環境變數：

```bash
# 檢查環境變數是否設置
echo $ANTHROPIC_API_KEY
```

如果使用 `.env` 檔案，確保 notebook 中有載入：

```python
from dotenv import load_dotenv
load_dotenv()
```

### Q: 如何更新到最新版本的依賴？

```bash
uv sync --all-extras --upgrade
```

### Q: 執行 notebook 時出現套件找不到的錯誤？

某些 notebook 可能需要額外的套件，請查看 notebook 開頭的安裝說明，或執行：

```bash
uv add <package-name>
```

### Q: 如何驗證我的環境設置是否正確？

```bash
# 執行測試
make test

# 或檢查格式和 linting
make check
```

---

## 下一步

- 閱讀 [Jupyter Notebook 基礎教學](jupyter-basics.md) 了解如何操作 notebook
- 查看 [專案結構說明](project-structure.md) 了解各目錄的用途
- 閱讀 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解如何貢獻程式碼

---

<a name="english-version"></a>

## English Version

This guide will help you set up and use the Claude Cookbooks project from scratch.

### What is Claude Cookbooks?

Claude Cookbooks is an open-source project maintained by Anthropic that provides practical examples and tutorials for using the Claude API. These examples are presented in **Jupyter Notebook** format, allowing you to learn and experiment interactively.

#### Why Jupyter Notebook?

- **Interactive execution**: Run code step by step and see results immediately
- **Rich content**: Add explanatory text, images, and charts alongside code
- **Easy to learn**: Great for teaching and experimentation
- **Preserved output**: Execution results are saved in the notebook for future reference

---

### Environment Setup

#### Step 1: Install Python

Ensure your system has Python 3.11 or higher installed.

```bash
# Check Python version
python --version
# or
python3 --version
```

If not installed, download from [python.org](https://www.python.org/downloads/).

#### Step 2: Install uv Package Manager

This project uses [uv](https://docs.astral.sh/uv/) as the package manager, which is faster and more reliable than traditional pip.

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or install via pip
pip install uv
```

#### Step 3: Clone the Project

```bash
git clone https://github.com/anthropics/anthropic-cookbook.git
cd anthropic-cookbook
```

#### Step 4: Install Project Dependencies

```bash
# Install all dependencies
uv sync --all-extras

# Install pre-commit hooks (optional but recommended)
uv run pre-commit install
```

#### Step 5: Set Up API Key

1. Go to [Anthropic Console](https://console.anthropic.com/) to register and obtain an API key
2. Set up environment variables:

```bash
# Copy the example config file
cp .env.example .env

# Edit .env file and add your API key
# ANTHROPIC_API_KEY=your-api-key-here
```

---

### Running Notebooks

#### Method 1: Using Jupyter Lab (Recommended)

```bash
# Start Jupyter Lab
uv run jupyter lab
```

This opens the Jupyter Lab interface in your browser where you can browse and run any notebook.

#### Method 2: Using VS Code

1. Install [VS Code](https://code.visualstudio.com/)
2. Install the [Jupyter Extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)
3. Open the project folder
4. Click any `.ipynb` file to open and run it

#### Method 3: Using Classic Jupyter Notebook

```bash
# Start Jupyter Notebook
uv run jupyter notebook
```

---

### Recommended Learning Path

#### Beginners

If you're new to the Claude API, we recommend the following order:

1. **[Claude API Fundamentals Course](https://github.com/anthropics/courses/tree/master/anthropic_api_fundamentals)** - Complete this online course first
2. **[Calculator Tool Example](tool_use/calculator_tool.ipynb)** - Understand basic tool usage
3. **[JSON Mode](misc/how_to_enable_json_mode.ipynb)** - Learn how to get structured output

#### Intermediate Users

After building a foundation, explore:

1. **[RAG - Retrieval Augmented Generation](capabilities/retrieval_augmented_generation/)** - Enhance responses with external data
2. **[Customer Service Agent](tool_use/customer_service_agent.ipynb)** - Build practical conversational agents
3. **[Vision Features](multimodal/getting_started_with_vision.ipynb)** - Handle image inputs

#### Advanced Users

Dive into advanced topics:

1. **[Extended Thinking](extended_thinking/)** - Extended thinking mode
2. **[Claude Agent SDK](claude_agent_sdk/)** - Enterprise-grade agent implementation
3. **[Skills System](skills/)** - Custom skill development

---

### FAQ

#### Q: Why am I getting API key errors when running notebooks?

Make sure you have set up environment variables correctly:

```bash
# Check if environment variable is set
echo $ANTHROPIC_API_KEY
```

If using a `.env` file, ensure it's loaded in the notebook:

```python
from dotenv import load_dotenv
load_dotenv()
```

#### Q: How do I update to the latest version of dependencies?

```bash
uv sync --all-extras --upgrade
```

#### Q: Getting "package not found" errors when running a notebook?

Some notebooks may require additional packages. Check the installation instructions at the beginning of the notebook, or run:

```bash
uv add <package-name>
```

#### Q: How do I verify my environment setup is correct?

```bash
# Run tests
make test

# Or check formatting and linting
make check
```

---

### Next Steps

- Read [Jupyter Notebook Basics](jupyter-basics.md) to learn how to operate notebooks
- Check [Project Structure Guide](project-structure.md) to understand directory purposes
- Read [CONTRIBUTING.md](../CONTRIBUTING.md) to learn how to contribute code
