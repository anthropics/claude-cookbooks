# Claude Cookbooks 貢獻指南

感謝您有興趣為 Claude Cookbooks 做出貢獻！本指南將幫助您開始開發，並確保您的貢獻符合我們的品質標準。

> **[English version below](#english-version) | 英文版本請見下方**

## 開發環境設定

### 先決條件

- Python 3.11 或更高版本
- [uv](https://docs.astral.sh/uv/) 套件管理器（推薦）或 pip

### 快速開始

1. **安裝 uv**（推薦的套件管理器）：
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   或使用 Homebrew：
   ```bash
   brew install uv
   ```

2. **複製儲存庫**：
   ```bash
   git clone https://github.com/anthropics/anthropic-cookbook.git
   cd anthropic-cookbook
   ```

3. **設定開發環境**：
   ```bash
   # 建立虛擬環境並安裝依賴項
   uv sync --all-extras

   # 或使用 pip：
   pip install -e ".[dev]"
   ```

4. **安裝 pre-commit hooks**：
   ```bash
   uv run pre-commit install
   # 或：pre-commit install
   ```

5. **設定您的 API 金鑰**：
   ```bash
   cp .env.example .env
   # 編輯 .env 並添加您的 Claude API 金鑰
   ```

## 品質標準

本儲存庫使用自動化工具來維護程式碼品質：

### Notebook 驗證工具組

- **[nbconvert](https://nbconvert.readthedocs.io/)**：用於測試的 Notebook 執行工具
- **[ruff](https://docs.astral.sh/ruff/)**：具有原生 Jupyter 支援的快速 Python linter 和格式化工具
- **Claude AI 審查**：使用 Claude 進行智慧程式碼審查

**注意**：本儲存庫刻意保留 Notebook 輸出，因為它們展示了使用者預期的結果。

### Claude Code 斜線指令

本儲存庫包含可在 Claude Code（用於本機開發）和 GitHub Actions CI 中使用的斜線指令。當您在本儲存庫中使用 Claude Code 時，這些指令會自動可用。

**可用指令**：
- `/link-review` - 驗證 markdown 和 notebooks 中的連結
- `/model-check` - 確認 Claude 模型使用是否為最新版本
- `/notebook-review` - 全面的 notebook 品質檢查

**在 Claude Code 中使用**：
```bash
# 執行與 CI 相同的驗證
/notebook-review skills/my-notebook.ipynb
/model-check
/link-review README.md
```

這些指令使用與 CI 流程完全相同的驗證邏輯，幫助您在推送前發現問題。指令定義儲存在 `.claude/commands/` 中，供本機和 CI 使用。

### 提交前

1. **執行品質檢查**：
   ```bash
   uv run ruff check skills/ --fix
   uv run ruff format skills/

   uv run python scripts/validate_notebooks.py
   ```

2. **測試 notebook 執行**（可選，需要 API 金鑰）：
   ```bash
   uv run jupyter nbconvert --to notebook \
     --execute skills/classification/guide.ipynb \
     --ExecutePreprocessor.kernel_name=python3 \
     --output test_output.ipynb
   ```

### Pre-commit Hooks

Pre-commit hooks 會在每次提交前自動執行，以確保程式碼品質：

- 使用 ruff 格式化程式碼
- 驗證 notebook 結構

如果 hook 失敗，請修復問題後再次嘗試提交。

## 貢獻指南

### Notebook 最佳實踐

1. **使用環境變數來儲存 API 金鑰**：
   ```python
   import os
   api_key = os.environ.get("ANTHROPIC_API_KEY")
   ```

2. **使用最新的 Claude 模型**：
   - 可用時使用模型別名以獲得更好的可維護性
   - 最新 Haiku 模型：`claude-haiku-4-5-20251001` (Haiku 4.5)
   - 在此查看最新模型：https://docs.claude.com/en/docs/about-claude/models/overview
   - Claude 會在 PR 審查中自動驗證模型使用

3. **保持 notebooks 專注**：
   - 每個 notebook 一個概念
   - 清晰的說明和註解
   - 將預期輸出包含在 markdown cells 中

4. **測試您的 notebooks**：
   - 確保它們可以從頭到尾執行而不出錯
   - 對範例 API 呼叫使用最少的 tokens
   - 包含錯誤處理

### Git 工作流程

1. **建立功能分支**：
   ```bash
   git checkout -b <您的名字>/<功能描述>
   # 範例：git checkout -b alice/add-rag-example
   ```

2. **使用約定式提交**：
   ```bash
   # 格式：<類型>(<範圍>): <主題>

   # 類型：
   feat     # 新功能
   fix      # 錯誤修復
   docs     # 文件
   style    # 格式化
   refactor # 程式碼重構
   test     # 測試
   chore    # 維護
   ci       # CI/CD 變更

   # 範例：
   git commit -m "feat(skills): add text-to-sql notebook"
   git commit -m "fix(api): use environment variable for API key"
   git commit -m "docs(readme): update installation instructions"
   ```

3. **保持提交原子性**：
   - 每次提交一個邏輯變更
   - 撰寫清晰、描述性的訊息
   - 適時引用相關 issues

4. **推送並建立 PR**：
   ```bash
   git push -u origin your-branch-name
   gh pr create  # 或使用 GitHub 網頁介面
   ```

### Pull Request 指南

1. **PR 標題**：使用約定式提交格式
2. **描述**：包含：
   - 您做了什麼變更
   - 為什麼做這些變更
   - 如何測試它們
   - 相關的 issue 編號
3. **保持 PRs 專注**：每個 PR 一個功能/修復
4. **回應回饋**：及時處理審查意見

## 測試

### 本機測試

執行驗證套件：

```bash
# 檢查所有 notebooks
uv run python scripts/validate_notebooks.py

# 對所有檔案執行 pre-commit
uv run pre-commit run --all-files
```

### CI/CD

我們的 GitHub Actions 工作流程會自動：

- 驗證 notebook 結構
- 使用 ruff 進行程式碼檢查
- 測試 notebook 執行（僅限維護者）
- 檢查連結
- Claude 審查程式碼和模型使用

外部貢獻者的 API 測試將受到限制以節省資源。

## 取得幫助

- **Issues**：[GitHub Issues](https://github.com/anthropics/anthropic-cookbook/issues)
- **Discussions**：[GitHub Discussions](https://github.com/anthropics/anthropic-cookbook/discussions)
- **Discord**：[Anthropic Discord](https://www.anthropic.com/discord)

## 安全性

- 絕不提交 API 金鑰或機密資訊
- 使用環境變數儲存敏感資料
- 私下向 security@anthropic.com 報告安全問題

## 授權

透過貢獻，您同意您的貢獻將以與專案相同的授權（MIT 授權）發布。

---

<a name="english-version"></a>

## English Version

# Contributing to Claude Cookbooks

Thank you for your interest in contributing to the Claude Cookbooks! This guide will help you get started with development and ensure your contributions meet our quality standards.

### Development Setup

#### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

#### Quick Start

1. **Install uv** (recommended package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Or with Homebrew:
   ```bash
   brew install uv
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/anthropics/anthropic-cookbook.git
   cd anthropic-cookbook
   ```

3. **Set up the development environment**:
   ```bash
   # Create virtual environment and install dependencies
   uv sync --all-extras

   # Or with pip:
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**:
   ```bash
   uv run pre-commit install
   # Or: pre-commit install
   ```

5. **Set up your API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Claude API key
   ```

### Quality Standards

This repository uses automated tools to maintain code quality:

#### The Notebook Validation Stack

- **[nbconvert](https://nbconvert.readthedocs.io/)**: Notebook execution for testing
- **[ruff](https://docs.astral.sh/ruff/)**: Fast Python linter and formatter with native Jupyter support
- **Claude AI Review**: Intelligent code review using Claude

**Note**: Notebook outputs are intentionally kept in this repository as they demonstrate expected results for users.

#### Claude Code Slash Commands

This repository includes slash commands that work in both Claude Code (for local development) and GitHub Actions CI. These commands are automatically available when you work in this repository with Claude Code.

**Available Commands**:
- `/link-review` - Validate links in markdown and notebooks
- `/model-check` - Verify Claude model usage is current
- `/notebook-review` - Comprehensive notebook quality check

**Usage in Claude Code**:
```bash
# Run the same validations that CI will run
/notebook-review skills/my-notebook.ipynb
/model-check
/link-review README.md
```

These commands use the exact same validation logic as our CI pipeline, helping you catch issues before pushing. The command definitions are stored in `.claude/commands/` for both local and CI use.

#### Before Committing

1. **Run quality checks**:
   ```bash
   uv run ruff check skills/ --fix
   uv run ruff format skills/

   uv run python scripts/validate_notebooks.py
   ```

2. **Test notebook execution** (optional, requires API key):
   ```bash
   uv run jupyter nbconvert --to notebook \
     --execute skills/classification/guide.ipynb \
     --ExecutePreprocessor.kernel_name=python3 \
     --output test_output.ipynb
   ```

#### Pre-commit Hooks

Pre-commit hooks will automatically run before each commit to ensure code quality:

- Format code with ruff
- Validate notebook structure

If a hook fails, fix the issues and try committing again.

### Contribution Guidelines

#### Notebook Best Practices

1. **Use environment variables for API keys**:
   ```python
   import os
   api_key = os.environ.get("ANTHROPIC_API_KEY")
   ```

2. **Use current Claude models**:
   - Use model aliases for better maintainability when available
   - Latest Haiku model: `claude-haiku-4-5-20251001` (Haiku 4.5)
   - Check current models at: https://docs.claude.com/en/docs/about-claude/models/overview
   - Claude will automatically validate model usage in PR reviews

3. **Keep notebooks focused**:
   - One concept per notebook
   - Clear explanations and comments
   - Include expected outputs as markdown cells

4. **Test your notebooks**:
   - Ensure they run from top to bottom without errors
   - Use minimal tokens for example API calls
   - Include error handling

#### Git Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b <your-name>/<feature-description>
   # Example: git checkout -b alice/add-rag-example
   ```

2. **Use conventional commits**:
   ```bash
   # Format: <type>(<scope>): <subject>

   # Types:
   feat     # New feature
   fix      # Bug fix
   docs     # Documentation
   style    # Formatting
   refactor # Code restructuring
   test     # Tests
   chore    # Maintenance
   ci       # CI/CD changes

   # Examples:
   git commit -m "feat(skills): add text-to-sql notebook"
   git commit -m "fix(api): use environment variable for API key"
   git commit -m "docs(readme): update installation instructions"
   ```

3. **Keep commits atomic**:
   - One logical change per commit
   - Write clear, descriptive messages
   - Reference issues when applicable

4. **Push and create PR**:
   ```bash
   git push -u origin your-branch-name
   gh pr create  # Or use GitHub web interface
   ```

#### Pull Request Guidelines

1. **PR Title**: Use conventional commit format
2. **Description**: Include:
   - What changes you made
   - Why you made them
   - How to test them
   - Related issue numbers
3. **Keep PRs focused**: One feature/fix per PR
4. **Respond to feedback**: Address review comments promptly

### Testing

#### Local Testing

Run the validation suite:

```bash
# Check all notebooks
uv run python scripts/validate_notebooks.py

# Run pre-commit on all files
uv run pre-commit run --all-files
```

#### CI/CD

Our GitHub Actions workflows will automatically:

- Validate notebook structure
- Lint code with ruff
- Test notebook execution (for maintainers)
- Check links
- Claude reviews code and model usage

External contributors will have limited API testing to conserve resources.

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/anthropics/anthropic-cookbook/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anthropics/anthropic-cookbook/discussions)
- **Discord**: [Anthropic Discord](https://www.anthropic.com/discord)

### Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Report security issues privately to security@anthropic.com

### License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).
