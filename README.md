# Claude Cookbooks

# Claude 實用指南

Claude Cookbooks 提供專為幫助開發者使用 Claude 建構應用程式所設計的程式碼與指南，提供可直接複製使用的程式碼片段，讓您輕鬆整合到自己的專案中。

> **[English version below](#english-version) | 英文版本請見下方**

## 先決條件

要充分運用本指南中的範例，您需要一個 Claude API 金鑰（可在[此處](https://www.anthropic.com)免費註冊）。

雖然程式碼範例主要以 Python 撰寫，但概念可以適用於任何支援 Claude API 互動的程式語言。

如果您是第一次使用 Claude API，我們建議先從 [Claude API 基礎課程](https://github.com/anthropics/courses/tree/master/anthropic_api_fundamentals) 開始，建立穩固的基礎。

## 更多資源

想要更多資源來增強您使用 Claude 和 AI 助手的體驗？請查看以下實用連結：

- [Anthropic 開發者文件](https://docs.claude.com/claude/docs/guide-to-anthropics-prompt-engineering-resources)
- [Anthropic 支援文件](https://support.anthropic.com)
- [Anthropic Discord 社群](https://www.anthropic.com/discord)

## 參與貢獻

Claude Cookbooks 靠開發者社群的貢獻而蓬勃發展。我們重視您的意見，無論是提交想法、修正錯字、新增指南，或改進現有內容。透過貢獻，您幫助讓這個資源對每個人都更有價值。

為避免重複工作，請在貢獻前先查看現有的 issues 和 pull requests。

如果您有新範例或指南的想法，請在 [issues 頁面](https://github.com/anthropics/anthropic-cookbook/issues)分享。

## 實用指南目錄

### 核心能力 (Capabilities)
- [分類 (Classification)](https://github.com/anthropics/anthropic-cookbook/tree/main/capabilities/classification)：探索使用 Claude 進行文字與資料分類的技術。
- [檢索增強生成 (RAG)](https://github.com/anthropics/anthropic-cookbook/tree/main/capabilities/retrieval_augmented_generation)：學習如何使用外部知識增強 Claude 的回應。
- [摘要生成 (Summarization)](https://github.com/anthropics/anthropic-cookbook/tree/main/capabilities/summarization)：探索使用 Claude 進行有效文字摘要的技術。

### 工具使用與整合 (Tool Use and Integration)
- [工具使用 (Tool use)](https://github.com/anthropics/anthropic-cookbook/tree/main/tool_use)：學習如何將 Claude 與外部工具和函數整合以擴展其功能。
  - [客服代理 (Customer service agent)](https://github.com/anthropics/anthropic-cookbook/blob/main/tool_use/customer_service_agent.ipynb)
  - [計算機整合 (Calculator integration)](https://github.com/anthropics/anthropic-cookbook/blob/main/tool_use/calculator_tool.ipynb)
  - [SQL 查詢 (SQL queries)](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/how_to_make_sql_queries.ipynb)

### 第三方整合 (Third-Party Integrations)
- [檢索增強生成](https://github.com/anthropics/anthropic-cookbook/tree/main/third_party)：使用外部資料來源補充 Claude 的知識。
  - [向量資料庫 (Pinecone)](https://github.com/anthropics/anthropic-cookbook/blob/main/third_party/Pinecone/rag_using_pinecone.ipynb)
  - [維基百科 (Wikipedia)](https://github.com/anthropics/anthropic-cookbook/blob/main/third_party/Wikipedia/wikipedia-search-cookbook.ipynb/)
  - [網頁內容 (Web pages)](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/read_web_pages_with_haiku.ipynb)
- [使用 Voyage AI 建立嵌入向量](https://github.com/anthropics/anthropic-cookbook/blob/main/third_party/VoyageAI/how_to_create_embeddings.md)

### 多模態能力 (Multimodal Capabilities)
- [Claude 視覺功能](https://github.com/anthropics/anthropic-cookbook/tree/main/multimodal)：
  - [圖片入門指南](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/getting_started_with_vision.ipynb)
  - [視覺功能最佳實踐](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/best_practices_for_vision.ipynb)
  - [解讀圖表與數據](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/reading_charts_graphs_powerpoints.ipynb)
  - [從表單提取內容](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/how_to_transcribe_text.ipynb)
- [使用 Claude 生成圖片](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/illustrated_responses.ipynb)：搭配 Stable Diffusion 使用 Claude 生成圖片。

### 進階技術 (Advanced Techniques)
- [子代理 (Sub-agents)](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/using_sub_agents.ipynb)：學習如何將 Haiku 作為子代理與 Opus 搭配使用。
- [上傳 PDF 到 Claude](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/pdf_upload_summarization.ipynb)：解析並將 PDF 以文字形式傳送給 Claude。
- [自動化評估 (Automated evaluations)](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/building_evals.ipynb)：使用 Claude 自動化提示詞評估流程。
- [啟用 JSON 模式](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/how_to_enable_json_mode.ipynb)：確保 Claude 輸出一致的 JSON 格式。
- [建立內容審核過濾器](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/building_moderation_filter.ipynb)：使用 Claude 為您的應用程式建立內容審核過濾器。
- [提示詞快取 (Prompt caching)](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/prompt_caching.ipynb)：學習使用 Claude 進行高效提示詞快取的技術。

## 其他資源

- [Anthropic on AWS](https://github.com/aws-samples/anthropic-on-aws)：探索在 AWS 基礎架構上使用 Claude 的範例和解決方案。
- [AWS Samples](https://github.com/aws-samples/)：來自 AWS 的程式碼範例集合，可適用於 Claude。請注意，某些範例可能需要修改才能與 Claude 最佳配合。

---

<a name="english-version"></a>

## English Version

The Claude Cookbooks provide code and guides designed to help developers build with Claude, offering copy-able code snippets that you can easily integrate into your own projects.

### Prerequisites

To make the most of the examples in this cookbook, you'll need a Claude API key (sign up for free [here](https://www.anthropic.com)).

While the code examples are primarily written in Python, the concepts can be adapted to any programming language that supports interaction with the Claude API.

If you're new to working with the Claude API, we recommend starting with our [Claude API Fundamentals course](https://github.com/anthropics/courses/tree/master/anthropic_api_fundamentals) to get a solid foundation.

### Explore Further

Looking for more resources to enhance your experience with Claude and AI assistants? Check out these helpful links:

- [Anthropic developer documentation](https://docs.claude.com/claude/docs/guide-to-anthropics-prompt-engineering-resources)
- [Anthropic support docs](https://support.anthropic.com)
- [Anthropic Discord community](https://www.anthropic.com/discord)

### Contributing

The Claude Cookbooks thrives on the contributions of the developer community. We value your input, whether it's submitting an idea, fixing a typo, adding a new guide, or improving an existing one. By contributing, you help make this resource even more valuable for everyone.

To avoid duplication of efforts, please review the existing issues and pull requests before contributing.

If you have ideas for new examples or guides, share them on the [issues page](https://github.com/anthropics/anthropic-cookbook/issues).

### Table of recipes

#### Capabilities
- [Classification](https://github.com/anthropics/anthropic-cookbook/tree/main/capabilities/classification): Explore techniques for text and data classification using Claude.
- [Retrieval Augmented Generation](https://github.com/anthropics/anthropic-cookbook/tree/main/capabilities/retrieval_augmented_generation): Learn how to enhance Claude's responses with external knowledge.
- [Summarization](https://github.com/anthropics/anthropic-cookbook/tree/main/capabilities/summarization): Discover techniques for effective text summarization with Claude.

#### Tool Use and Integration
- [Tool use](https://github.com/anthropics/anthropic-cookbook/tree/main/tool_use): Learn how to integrate Claude with external tools and functions to extend its capabilities.
  - [Customer service agent](https://github.com/anthropics/anthropic-cookbook/blob/main/tool_use/customer_service_agent.ipynb)
  - [Calculator integration](https://github.com/anthropics/anthropic-cookbook/blob/main/tool_use/calculator_tool.ipynb)
  - [SQL queries](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/how_to_make_sql_queries.ipynb)

#### Third-Party Integrations
- [Retrieval augmented generation](https://github.com/anthropics/anthropic-cookbook/tree/main/third_party): Supplement Claude's knowledge with external data sources.
  - [Vector databases (Pinecone)](https://github.com/anthropics/anthropic-cookbook/blob/main/third_party/Pinecone/rag_using_pinecone.ipynb)
  - [Wikipedia](https://github.com/anthropics/anthropic-cookbook/blob/main/third_party/Wikipedia/wikipedia-search-cookbook.ipynb/)
  - [Web pages](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/read_web_pages_with_haiku.ipynb)
- [Embeddings with Voyage AI](https://github.com/anthropics/anthropic-cookbook/blob/main/third_party/VoyageAI/how_to_create_embeddings.md)

#### Multimodal Capabilities
- [Vision with Claude](https://github.com/anthropics/anthropic-cookbook/tree/main/multimodal):
  - [Getting started with images](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/getting_started_with_vision.ipynb)
  - [Best practices for vision](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/best_practices_for_vision.ipynb)
  - [Interpreting charts and graphs](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/reading_charts_graphs_powerpoints.ipynb)
  - [Extracting content from forms](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/how_to_transcribe_text.ipynb)
- [Generate images with Claude](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/illustrated_responses.ipynb): Use Claude with Stable Diffusion for image generation.

#### Advanced Techniques
- [Sub-agents](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/using_sub_agents.ipynb): Learn how to use Haiku as a sub-agent in combination with Opus.
- [Upload PDFs to Claude](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/pdf_upload_summarization.ipynb): Parse and pass PDFs as text to Claude.
- [Automated evaluations](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/building_evals.ipynb): Use Claude to automate the prompt evaluation process.
- [Enable JSON mode](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/how_to_enable_json_mode.ipynb): Ensure consistent JSON output from Claude.
- [Create a moderation filter](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/building_moderation_filter.ipynb): Use Claude to create a content moderation filter for your application.
- [Prompt caching](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/prompt_caching.ipynb): Learn techniques for efficient prompt caching with Claude.

### Additional Resources

- [Anthropic on AWS](https://github.com/aws-samples/anthropic-on-aws): Explore examples and solutions for using Claude on AWS infrastructure.
- [AWS Samples](https://github.com/aws-samples/): A collection of code samples from AWS which can be adapted for use with Claude. Note that some samples may require modification to work optimally with Claude.
