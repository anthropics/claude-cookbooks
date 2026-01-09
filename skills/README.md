# Claude Skills 實用指南

# Claude Skills Cookbook

一個使用 Claude Skills 功能進行文件生成、資料分析和業務自動化的完整指南。本指南展示如何利用 Claude 內建的 Excel、PowerPoint 和 PDF 創建技能，以及如何為專業工作流程建構自訂技能。

> **[English version below](#english-version) | 英文版本請見下方**

> **查看 Skills 實際應用：** 請查看 **[Claude Creates Files](https://www.anthropic.com/news/create-files)** 了解這些 Skills 如何為 Claude 在 Claude.ai 和桌面應用程式中直接創建和編輯文件的能力提供支援！

## 什麼是 Skills？

Skills 是組織化的指令、可執行程式碼和資源套件，為 Claude 提供針對特定任務的專業能力。可以將它們視為「專業知識套件」，Claude 可以動態發現和載入，用於：

- 創建專業文件（Excel、PowerPoint、PDF、Word）
- 執行複雜的資料分析和視覺化
- 應用公司特定的工作流程和品牌規範
- 使用領域專業知識自動化業務流程

📖 閱讀我們的工程部落格文章 [為代理配備真實世界的 Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

## 主要功能

- ✨ **漸進式揭露架構** - Skills 僅在需要時載入，優化 token 使用
- 📊 **金融聚焦** - 金融和業務分析的真實世界範例
- 🔧 **自訂 Skills 開發** - 學習建構和部署您自己的技能
- 🎯 **生產就緒範例** - 可立即適用的程式碼

## 指南結構

### 📚 [Notebook 1：Skills 簡介](notebooks/01_skills_introduction.ipynb)

透過快速入門範例學習 Claude Skills 功能的基礎。

- 理解 Skills 架構
- 使用 beta headers 設定 API
- 創建您的第一個 Excel 試算表
- 生成 PowerPoint 簡報
- 匯出為 PDF 格式

### 💼 [Notebook 2：金融應用](notebooks/02_skills_financial_applications.ipynb)

使用真實財務資料探索強大的業務使用案例。

- 建構帶有圖表和樞紐分析表的財務儀表板
- 投資組合分析和投資報告
- 跨格式工作流程：CSV → Excel → PowerPoint → PDF
- Token 優化策略

### 🔧 [Notebook 3：自訂 Skills 開發](notebooks/03_skills_custom_development.ipynb)

掌握創建您自己的專業技能的藝術。

- 建構財務比率計算器
- 創建公司品牌規範技能
- 進階：財務建模套件
- [最佳實踐](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)和安全考量

## 快速開始

### 先決條件

- Python 3.8 或更高版本
- Anthropic API 金鑰（[在此取得](https://console.anthropic.com/)）
- Jupyter Notebook 或 JupyterLab

### 安裝

1. **複製儲存庫**

```bash
git clone https://github.com/anthropics/claude-cookbooks.git
cd claude-cookbooks/skills
```

2. **創建虛擬環境**（建議）

```bash
python -m venv venv
source venv/bin/activate  # Windows 上：venv\Scripts\activate
```

3. **安裝依賴項**

```bash
pip install -r requirements.txt
```

4. **設定 API 金鑰**

```bash
cp .env.example .env
# 編輯 .env 並添加您的 ANTHROPIC_API_KEY
```

5. **啟動 Jupyter**

```bash
jupyter notebook
```

6. **從 Notebook 1 開始**
   開啟 `notebooks/01_skills_introduction.ipynb` 並跟著做！

## 範例資料

本指南在 `sample_data/` 中包含真實的財務資料集：

- 📊 **financial_statements.csv** - 季度損益表、資產負債表和現金流量資料
- 💰 **portfolio_holdings.json** - 含績效指標的投資組合
- 📋 **budget_template.csv** - 含差異分析的部門預算
- 📈 **quarterly_metrics.json** - KPIs 和營運指標

## 專案結構

```
skills/
├── notebooks/                    # Jupyter notebooks
│   ├── 01_skills_introduction.ipynb
│   ├── 02_skills_financial_applications.ipynb
│   └── 03_skills_custom_development.ipynb
├── sample_data/                  # 財務資料集
│   ├── financial_statements.csv
│   ├── portfolio_holdings.json
│   ├── budget_template.csv
│   └── quarterly_metrics.json
├── custom_skills/                # 您的自訂技能
│   ├── financial_analyzer/
│   ├── brand_guidelines/
│   └── report_generator/
├── outputs/                      # 生成的檔案
├── docs/                         # 文件
├── requirements.txt             # Python 依賴項
├── .env.example                 # 環境範本
└── README.md                    # 本檔案
```

## API 設定

Skills 需要特定的 beta headers。notebooks 會自動處理這些，但這是幕後發生的事情：

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="your-api-key",
    default_headers={
        "anthropic-beta": "code-execution-2025-08-25,files-api-2025-04-14,skills-2025-10-02"
    }
)
```

**必要的 Beta Headers：**

- `code-execution-2025-08-25` - 啟用 Skills 的程式碼執行
- `files-api-2025-04-14` - 下載生成的檔案所需
- `skills-2025-10-02` - 啟用 Skills 功能

## 使用生成的檔案

當 Skills 創建文件（Excel、PowerPoint、PDF 等）時，它們會在回應中返回 `file_id` 屬性。您必須使用 **Files API** 來下載這些檔案。

### 運作方式

1. **Skills 創建檔案** — 在程式碼執行期間
2. **回應包含 file_ids** — 每個創建的檔案
3. **使用 Files API** — 下載實際檔案內容
4. **本地儲存** — 或根據需要處理

### 範例：創建和下載 Excel 檔案

```python
from anthropic import Anthropic

client = Anthropic(api_key="your-api-key")

# 步驟 1：使用技能創建檔案
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
    messages=[{
        "role": "user",
        "content": "Create an Excel file with a simple budget spreadsheet"
    }]
)

# 步驟 2：從回應中提取 file_id
file_id = None
for block in response.content:
    if block.type == "tool_result" and hasattr(block, 'output'):
        # 在工具輸出中尋找 file_id
        if 'file_id' in str(block.output):
            file_id = extract_file_id(block.output)  # 解析 file_id
            break

# 步驟 3：使用 Files API 下載檔案
if file_id:
    file_content = client.beta.files.download(file_id=file_id)

    # 步驟 4：儲存到磁碟
    with open("outputs/budget.xlsx", "wb") as f:
        f.write(file_content.read())

    print(f"✅ 檔案已下載：budget.xlsx")
```

## 內建 Skills 參考

Claude 提供這些預建技能：

| Skill      | ID     | 說明                                                         |
| ---------- | ------ | ------------------------------------------------------------ |
| Excel      | `xlsx` | 創建和操作含公式、圖表和格式化的 Excel 工作簿                  |
| PowerPoint | `pptx` | 生成含投影片、圖表和轉場效果的專業簡報                        |
| PDF        | `pdf`  | 創建含文字、表格和圖片的格式化 PDF 文件                       |
| Word       | `docx` | 生成含豐富格式和結構的 Word 文件                              |

## 創建自訂 Skills

自訂技能遵循此結構：

```
my_skill/
├── SKILL.md           # 必要：給 Claude 的指令
├── scripts/           # 可選：Python/JS 程式碼
│   └── processor.py
└── resources/         # 可選：範本、資料
    └── template.xlsx
```

在 [Notebook 3](notebooks/03_skills_custom_development.ipynb) 中了解更多。

## 常見使用案例

### 財務報告

- 自動化季度報告
- 預算差異分析
- 投資績效儀表板

### 資料分析

- 含複雜公式的 Excel 分析
- 樞紐分析表生成
- 統計分析和視覺化

### 文件自動化

- 品牌簡報生成
- 多來源報告編譯
- 跨格式文件轉換

## 資源

### 文件

- 📖 [Claude API 文件](https://docs.anthropic.com/en/api/messages)
- 🔧 [Skills 文件](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)

### 支援文章

- 📚 [使用 Skills 教 Claude 您的工作方式](https://support.claude.com/en/articles/12580051-teach-claude-your-way-of-working-using-skills)
- 🛠️ [如何透過對話與 Claude 創建技能](https://support.claude.com/en/articles/12599426-how-to-create-a-skill-with-claude-through-conversation)

### 社群與支援

- 💬 [Claude 支援](https://support.claude.com)
- 🐙 [GitHub Issues](https://github.com/anthropics/claude-cookbooks/issues)

## 貢獻

我們歡迎貢獻！請參閱 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解指南。

## 授權

本指南在 MIT 授權下提供。詳見 [LICENSE](../LICENSE)。

---

**有問題？** 查看 [FAQ](docs/FAQ.md) 或開啟 issue。

**準備開始了嗎？** 開啟 [Notebook 1](notebooks/01_skills_introduction.ipynb)，讓我們建構一些精彩的東西！

---

<a name="english-version"></a>

## English Version

A comprehensive guide to using Claude's Skills feature for document generation, data analysis, and business automation. This cookbook demonstrates how to leverage Claude's built-in skills for Excel, PowerPoint, and PDF creation, as well as how to build custom skills for specialized workflows.

> **See Skills in Action:** Check out **[Claude Creates Files](https://www.anthropic.com/news/create-files)** to see how these Skills power Claude's ability to create and edit documents directly in Claude.ai and the desktop app!

### What are Skills?

Skills are organized packages of instructions, executable code, and resources that give Claude specialized capabilities for specific tasks. Think of them as "expertise packages" that Claude can discover and load dynamically to:

- Create professional documents (Excel, PowerPoint, PDF, Word)
- Perform complex data analysis and visualization
- Apply company-specific workflows and branding
- Automate business processes with domain expertise

📖 Read our engineering blog post on [Equipping agents for the real world with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### Key Features

- ✨ **Progressive Disclosure Architecture** - Skills load only when needed, optimizing token usage
- 📊 **Financial Focus** - Real-world examples for finance and business analytics
- 🔧 **Custom Skills Development** - Learn to build and deploy your own skills
- 🎯 **Production-Ready Examples** - Code you can adapt for immediate use

### Cookbook Structure

#### 📚 [Notebook 1: Introduction to Skills](notebooks/01_skills_introduction.ipynb)

Learn the fundamentals of Claude's Skills feature with quick-start examples.

#### 💼 [Notebook 2: Financial Applications](notebooks/02_skills_financial_applications.ipynb)

Explore powerful business use cases with real financial data.

#### 🔧 [Notebook 3: Custom Skills Development](notebooks/03_skills_custom_development.ipynb)

Master the art of creating your own specialized skills.

### Quick Start

See the Chinese version above for detailed installation instructions.

### Built-in Skills Reference

| Skill      | ID     | Description                                                                 |
| ---------- | ------ | --------------------------------------------------------------------------- |
| Excel      | `xlsx` | Create and manipulate Excel workbooks with formulas, charts, and formatting |
| PowerPoint | `pptx` | Generate professional presentations with slides, charts, and transitions    |
| PDF        | `pdf`  | Create formatted PDF documents with text, tables, and images                |
| Word       | `docx` | Generate Word documents with rich formatting and structure                  |

### Resources

- 📖 [Claude API Documentation](https://docs.anthropic.com/en/api/messages)
- 🔧 [Skills Documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- 💬 [Claude Support](https://support.claude.com)
- 🐙 [GitHub Issues](https://github.com/anthropics/claude-cookbooks/issues)

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### License

This cookbook is provided under the MIT License. See [LICENSE](../LICENSE) for details.

---

**Questions?** Check the [FAQ](docs/FAQ.md) or open an issue.

**Ready to start?** Open [Notebook 1](notebooks/01_skills_introduction.ipynb) and let's build something amazing!
