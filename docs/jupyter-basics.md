# Jupyter Notebook 基礎教學

# Jupyter Notebook Basics

本文將介紹 Jupyter Notebook 的基本概念和操作方式，幫助您快速上手閱讀和執行本專案中的範例。

> **[English version below](#english-version) | 英文版本請見下方**

---

## 什麼是 Jupyter Notebook？

Jupyter Notebook 是一個開源的互動式運算環境，讓您可以在同一個文件中結合：

- **程式碼**：可執行的 Python（或其他語言）程式碼
- **Markdown 文字**：格式化的說明文字、標題、列表等
- **輸出結果**：程式執行的輸出，包括文字、表格、圖表等
- **多媒體**：圖片、影片、互動式視覺化元件

### .ipynb 檔案格式

Notebook 檔案的副檔名是 `.ipynb`（**I**nteractive **Py**thon **N**ote**b**ook 的縮寫）。它實際上是一個 JSON 格式的文件，包含了所有的程式碼、文字和輸出。

---

## 核心概念：Cell（儲存格）

Notebook 由多個 **Cell（儲存格）** 組成，每個 cell 可以是：

### 1. Code Cell（程式碼儲存格）

用於撰寫和執行程式碼：

```python
# 這是一個 code cell 的範例
import anthropic

client = anthropic.Anthropic()
print("Hello, Claude!")
```

### 2. Markdown Cell（文字儲存格）

用於撰寫說明文字，支援 Markdown 語法：

```markdown
## 這是標題

這是一段說明文字，可以包含：
- **粗體**
- *斜體*
- `程式碼片段`
- [連結](https://anthropic.com)
```

---

## 基本操作

### 執行 Cell

| 操作 | 快捷鍵 |
|------|--------|
| 執行當前 cell 並移到下一個 | `Shift + Enter` |
| 執行當前 cell 並保持選取 | `Ctrl + Enter` |
| 執行當前 cell 並在下方新增 cell | `Alt + Enter` |

### 編輯模式

Notebook 有兩種模式：

1. **命令模式（Command Mode）**
   - Cell 外框為藍色
   - 按 `Esc` 進入
   - 用於導航和操作 cell

2. **編輯模式（Edit Mode）**
   - Cell 外框為綠色
   - 按 `Enter` 或點擊 cell 進入
   - 用於編輯 cell 內容

### 常用快捷鍵

#### 命令模式（按 Esc 後）

| 操作 | 快捷鍵 |
|------|--------|
| 在上方新增 cell | `A` |
| 在下方新增 cell | `B` |
| 刪除 cell | `D D`（按兩次 D） |
| 複製 cell | `C` |
| 貼上 cell | `V` |
| 撤銷刪除 | `Z` |
| 切換為 Markdown | `M` |
| 切換為 Code | `Y` |
| 儲存 notebook | `Ctrl + S` |

#### 編輯模式（編輯 cell 時）

| 操作 | 快捷鍵 |
|------|--------|
| 程式碼自動完成 | `Tab` |
| 顯示文件說明 | `Shift + Tab` |
| 註解/取消註解 | `Ctrl + /` |
| 縮排 | `Tab` |
| 取消縮排 | `Shift + Tab` |

---

## 執行順序的重要性

### 執行順序很重要！

Notebook 中的 cell 可以按**任意順序**執行，但變數和函數的定義**取決於執行順序**，而非在文件中的位置。

```python
# Cell 1
x = 10

# Cell 2
y = x + 5  # 如果先執行 Cell 2，會出錯，因為 x 還沒定義

# Cell 3
print(y)  # 輸出: 15（假設按順序執行）
```

### 最佳實踐

1. **從頭到尾依序執行**：使用 `Kernel > Restart & Run All` 確保所有 cell 按順序執行
2. **注意 cell 旁邊的數字**：`In [1]:` 表示這是第一個執行的 cell，數字越大表示越晚執行
3. **如果出錯**：嘗試重新啟動 Kernel 並從頭執行

---

## Kernel（核心）

Kernel 是執行程式碼的後端引擎。對於 Python notebook，就是一個 Python 解釋器進程。

### Kernel 操作

| 操作 | 說明 |
|------|------|
| Restart | 重新啟動 Kernel，清除所有變數 |
| Restart & Clear Output | 重新啟動並清除所有輸出 |
| Restart & Run All | 重新啟動並從頭執行所有 cell |
| Interrupt | 中斷正在執行的程式碼 |

### 何時需要重新啟動 Kernel？

- 程式碼卡住或無限迴圈
- 變數狀態混亂
- 想要確保 notebook 可以從頭到尾順利執行
- 安裝了新的套件

---

## 閱讀本專案的 Notebook

### Notebook 結構

本專案的 notebook 通常包含以下結構：

1. **標題和介紹**：說明 notebook 的目的
2. **環境設置**：安裝依賴、導入套件、設置 API 金鑰
3. **主要內容**：分步驟的教學和範例程式碼
4. **總結**：重點回顧和延伸閱讀

### 範例：典型的 notebook 開頭

```python
# Cell 1: 導入必要套件
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Cell 2: 載入環境變數
load_dotenv()

# Cell 3: 初始化客戶端
client = Anthropic()

# Cell 4: 發送請求
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)
print(message.content[0].text)
```

### 執行建議

1. **先閱讀 Markdown 說明**：了解每個步驟的目的
2. **依序執行 code cell**：使用 `Shift + Enter`
3. **觀察輸出**：比對預期結果和實際輸出
4. **實驗修改**：嘗試修改參數，觀察變化

---

## 常見問題

### Q: Cell 卡住不動怎麼辦？

點擊 `Kernel > Interrupt` 或按 `I I`（在命令模式下按兩次 I）中斷執行。

### Q: 為什麼變數找不到？

可能是因為定義該變數的 cell 還沒執行。請確保按順序執行所有 cell，或使用 `Kernel > Restart & Run All`。

### Q: 輸出太長怎麼辦？

點擊輸出區域左側可以折疊輸出，或右鍵選擇 `Clear Outputs` 清除輸出。

### Q: 如何分享 Notebook？

- 直接分享 `.ipynb` 檔案
- 使用 GitHub（會自動渲染 notebook）
- 匯出為 HTML 或 PDF：`File > Export Notebook As`

---

## 進階功能

### Magic Commands（魔法命令）

Jupyter 提供特殊的魔法命令，以 `%` 或 `%%` 開頭：

```python
# 計算 cell 執行時間
%time result = expensive_function()

# 計算整個 cell 的執行時間
%%time
for i in range(1000):
    process(i)

# 列出所有變數
%who

# 查看變數詳細資訊
%whos

# 執行 shell 命令
!pip install some-package
```

### 顯示圖片和圖表

```python
# Matplotlib 圖表自動顯示
import matplotlib.pyplot as plt
%matplotlib inline

plt.plot([1, 2, 3, 4])
plt.show()

# 顯示圖片
from IPython.display import Image
Image('path/to/image.png')
```

---

## 延伸資源

- [Jupyter 官方文件](https://jupyter.org/documentation)
- [Jupyter Notebook 快捷鍵完整列表](https://jupyter-notebook.readthedocs.io/en/stable/notebook.html#keyboard-shortcuts)
- [JupyterLab 使用指南](https://jupyterlab.readthedocs.io/en/stable/)

---

<a name="english-version"></a>

## English Version

This document introduces the basic concepts and operations of Jupyter Notebook to help you quickly get started with reading and running examples in this project.

---

### What is Jupyter Notebook?

Jupyter Notebook is an open-source interactive computing environment that allows you to combine in a single document:

- **Code**: Executable Python (or other language) code
- **Markdown text**: Formatted explanatory text, headings, lists, etc.
- **Output**: Program execution output, including text, tables, charts, etc.
- **Media**: Images, videos, interactive visualizations

#### The .ipynb File Format

Notebook files have the extension `.ipynb` (short for **I**nteractive **Py**thon **N**ote**b**ook). It's actually a JSON format file containing all the code, text, and output.

---

### Core Concept: Cells

A Notebook consists of multiple **Cells**, each of which can be:

#### 1. Code Cell

Used for writing and executing code:

```python
# This is an example of a code cell
import anthropic

client = anthropic.Anthropic()
print("Hello, Claude!")
```

#### 2. Markdown Cell

Used for writing explanatory text with Markdown syntax:

```markdown
## This is a Heading

This is explanatory text that can include:
- **Bold**
- *Italic*
- `code snippets`
- [Links](https://anthropic.com)
```

---

### Basic Operations

#### Running Cells

| Action | Shortcut |
|--------|----------|
| Run current cell and move to next | `Shift + Enter` |
| Run current cell and stay | `Ctrl + Enter` |
| Run current cell and insert below | `Alt + Enter` |

#### Edit Modes

Notebooks have two modes:

1. **Command Mode**
   - Cell border is blue
   - Press `Esc` to enter
   - Used for navigation and cell operations

2. **Edit Mode**
   - Cell border is green
   - Press `Enter` or click cell to enter
   - Used for editing cell content

#### Common Shortcuts

##### Command Mode (after pressing Esc)

| Action | Shortcut |
|--------|----------|
| Insert cell above | `A` |
| Insert cell below | `B` |
| Delete cell | `D D` (press D twice) |
| Copy cell | `C` |
| Paste cell | `V` |
| Undo delete | `Z` |
| Change to Markdown | `M` |
| Change to Code | `Y` |
| Save notebook | `Ctrl + S` |

##### Edit Mode (while editing a cell)

| Action | Shortcut |
|--------|----------|
| Code completion | `Tab` |
| Show documentation | `Shift + Tab` |
| Comment/Uncomment | `Ctrl + /` |
| Indent | `Tab` |
| Dedent | `Shift + Tab` |

---

### Importance of Execution Order

#### Execution order matters!

Cells in a notebook can be executed in **any order**, but variable and function definitions **depend on execution order**, not their position in the file.

```python
# Cell 1
x = 10

# Cell 2
y = x + 5  # If Cell 2 runs first, error occurs because x is not defined

# Cell 3
print(y)  # Output: 15 (assuming sequential execution)
```

#### Best Practices

1. **Execute from top to bottom**: Use `Kernel > Restart & Run All` to ensure all cells run in order
2. **Note the numbers next to cells**: `In [1]:` means this was the first executed cell
3. **If errors occur**: Try restarting the Kernel and running from the beginning

---

### Kernel

The Kernel is the backend engine that executes code. For Python notebooks, it's a Python interpreter process.

#### Kernel Operations

| Operation | Description |
|-----------|-------------|
| Restart | Restart the Kernel, clearing all variables |
| Restart & Clear Output | Restart and clear all outputs |
| Restart & Run All | Restart and run all cells from beginning |
| Interrupt | Stop currently running code |

#### When to Restart the Kernel?

- Code is stuck or in an infinite loop
- Variable state is confused
- Want to ensure notebook runs from start to finish
- Installed a new package

---

### Reading Notebooks in This Project

#### Notebook Structure

Notebooks in this project typically contain:

1. **Title and Introduction**: Purpose of the notebook
2. **Environment Setup**: Install dependencies, import packages, set API keys
3. **Main Content**: Step-by-step tutorials and example code
4. **Summary**: Key takeaways and further reading

#### Tips for Running

1. **Read Markdown explanations first**: Understand the purpose of each step
2. **Run code cells in order**: Use `Shift + Enter`
3. **Observe output**: Compare expected results with actual output
4. **Experiment**: Try modifying parameters and observe changes

---

### FAQ

#### Q: Cell is stuck, what do I do?

Click `Kernel > Interrupt` or press `I I` (press I twice in command mode) to interrupt execution.

#### Q: Why can't I find the variable?

The cell defining that variable may not have been executed yet. Make sure to run all cells in order, or use `Kernel > Restart & Run All`.

#### Q: Output is too long?

Click the left side of the output area to collapse it, or right-click and select `Clear Outputs`.

#### Q: How to share a Notebook?

- Share the `.ipynb` file directly
- Use GitHub (automatically renders notebooks)
- Export as HTML or PDF: `File > Export Notebook As`

---

### Advanced Features

#### Magic Commands

Jupyter provides special magic commands starting with `%` or `%%`:

```python
# Time a single statement
%time result = expensive_function()

# Time an entire cell
%%time
for i in range(1000):
    process(i)

# List all variables
%who

# View variable details
%whos

# Run shell commands
!pip install some-package
```

---

### Additional Resources

- [Jupyter Official Documentation](https://jupyter.org/documentation)
- [Jupyter Notebook Keyboard Shortcuts](https://jupyter-notebook.readthedocs.io/en/stable/notebook.html#keyboard-shortcuts)
- [JupyterLab User Guide](https://jupyterlab.readthedocs.io/en/stable/)
