# Claude 核心能力

# Claude Capabilities

歡迎來到 Claude Cookbooks 的核心能力章節！此目錄包含一系列展示 Claude 擅長的特定能力的指南。每個指南深入探索特定能力，討論潛在使用案例、優化結果的提示詞工程技術，以及評估 Claude 效能的方法。

> **[English version below](#english-version) | 英文版本請見下方**

## 指南

- **[使用 Claude 進行分類](./classification/guide.ipynb)**：了解 Claude 如何革新分類任務，特別是在具有複雜業務規則和有限訓練資料的場景中。本指南引導您完成資料準備、結合檢索增強生成（RAG）的提示詞工程、測試和評估。

- **[使用 Claude 進行檢索增強生成](./retrieval_augmented_generation/guide.ipynb)**：學習如何使用 RAG 以領域特定知識增強 Claude 的能力。本指南展示如何從頭建構 RAG 系統、優化其效能，並創建評估套件。您將學習摘要索引和重新排序等技術如何顯著提高問答任務的精確度、召回率和整體準確度。

- **[使用上下文嵌入的檢索增強生成](./contextual-embeddings/guide.ipynb)**：學習使用新技術來提高 RAG 系統的效能。在傳統 RAG 中，文件通常被分割成較小的區塊以便有效檢索。雖然這種方法對許多應用程式效果很好，但當單個區塊缺乏足夠上下文時可能會導致問題。上下文嵌入透過在嵌入前為每個區塊添加相關上下文來解決此問題。您將學習如何將上下文嵌入與語義搜尋、BM25 搜尋和重新排序結合使用來提高效能。

- **[使用 Claude 進行摘要](./summarization/guide.ipynb)**：探索 Claude 從多個來源摘要和綜合資訊的能力。本指南涵蓋各種摘要技術，包括多樣本、基於領域和分塊方法，以及處理長篇內容和多個文件的策略。我們還探索評估摘要，這可能是藝術、主觀性和正確方法的平衡！

- **[使用 Claude 進行自然語言轉 SQL](./text_to_sql/guide.ipynb)**：本指南涵蓋如何使用提示詞技術、自我改進和 RAG 從自然語言生成複雜的 SQL 查詢。我們還將探索如何評估和改進生成的 SQL 查詢的準確性，包括測試語法、資料正確性、行數等的評估。

## 開始使用

要開始使用這些指南，只需導航到所需指南的目錄並遵循 `guide.ipynb` 檔案中提供的說明。每個指南都是獨立的，包含重現範例和實驗所需的所有程式碼、資料和評估腳本。

---

<a name="english-version"></a>

## English Version

Welcome to the Capabilities section of the Claude Cookbooks! This directory contains a collection of guides that showcase specific capabilities where Claude excels. Each guide provides an in-depth exploration of a particular capability, discussing potential use cases, prompt engineering techniques to optimize results, and approaches for evaluating Claude's performance.

### Guides

- **[Classification with Claude](./classification/guide.ipynb)**: Discover how Claude can revolutionize classification tasks, especially in scenarios with complex business rules and limited training data. This guide walks you through data preparation, prompt engineering with retrieval-augmented generation (RAG), testing, and evaluation.

- **[Retrieval Augmented Generation with Claude](./retrieval_augmented_generation/guide.ipynb)**: Learn how to enhance Claude's capabilities with domain-specific knowledge using RAG. This guide demonstrates how to build a RAG system from scratch, optimize its performance, and create an evaluation suite. You'll learn how techniques like summary indexing and re-ranking can significantly improve precision, recall, and overall accuracy in question-answering tasks.

- **[Retrieval Augmented Generation with Contextual Embeddings](./contextual-embeddings/guide.ipynb)**: Learn how to use a new technique to improve the performance of your RAG system. In traditional RAG, documents are typically split into smaller chunks for efficient retrieval. While this approach works well for many applications, it can lead to problems when individual chunks lack sufficient context. Contextual Embeddings solve this problem by adding relevant context to each chunk before embedding. You'll learn how to use contextual embeddings with semantic search, BM25 search, and reranking to improve performance.

- **[Summarization with Claude](./summarization/guide.ipynb)**: Explore Claude's ability to summarize and synthesize information from multiple sources. This guide covers a variety of summarization techniques, including multi-shot, domain-based, and chunking methods, as well as strategies for handling long-form content and multiple documents. We also explore evaluating summaries, which can be a balance of art, subjectivity, and the right approach!

- **[Text-to-SQL with Claude](./text_to_sql/guide.ipynb)**: This guide covers how to generate complex SQL queries from natural language using prompting techniques, self-improvement, and RAG. We'll also explore how to evaluate and improve the accuracy of generated SQL queries, with evals that test for syntax, data correctness, row count, and more.

### Getting Started

To get started with these guides, simply navigate to the desired guide's directory and follow the instructions provided in the `guide.ipynb` file. Each guide is self-contained and includes all the necessary code, data, and evaluation scripts to reproduce the examples and experiments.
