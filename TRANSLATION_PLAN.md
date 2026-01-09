# Claude Cookbooks 正體中文翻譯計畫

本文件說明將 Claude Cookbooks 專案翻譯成正體中文的計畫與進度追蹤。

## 翻譯目標

- 幫助中文開發者快速掌握 Claude API 的使用方法
- 保留關鍵技術術語的英文原文，並提供中文說明
- 確保程式碼範例可正常執行
- 維護中英對照以便查閱原始資料

## 翻譯原則

1. **技術術語處理**：
   - API、SDK、RAG、LLM 等專業術語保留英文
   - 首次出現時提供中文解釋，如：RAG（檢索增強生成）
   - 程式碼中的變數名、函數名保持原樣

2. **格式保持**：
   - Markdown 格式保持不變
   - 程式碼區塊不翻譯
   - 連結保持原始 URL

3. **翻譯風格**：
   - 使用正體中文（繁體中文）
   - 語句通順自然
   - 技術文件風格，簡潔明瞭

## 翻譯優先順序

### 第一階段：核心文件（高優先級）
- [x] 翻譯計畫文件 (TRANSLATION_PLAN.md)
- [ ] README.md - 專案入口
- [ ] CONTRIBUTING.md - 貢獻指南
- [ ] registry.yaml - Notebook 元數據

### 第二階段：目錄說明文件
- [ ] capabilities/README.md
- [ ] claude_agent_sdk/README.md
- [ ] skills/README.md
- [ ] patterns/agents/README.md
- [ ] third_party/*/README.md

### 第三階段：核心能力 Notebooks (capabilities/)
- [ ] classification/guide.ipynb - 文字分類
- [ ] contextual-embeddings/guide.ipynb - 上下文嵌入
- [ ] retrieval_augmented_generation/guide.ipynb - RAG
- [ ] summarization/guide.ipynb - 摘要生成
- [ ] text_to_sql/guide.ipynb - 自然語言轉 SQL

### 第四階段：Claude Agent SDK Notebooks
- [ ] 00_The_one_liner_research_agent.ipynb
- [ ] 01_The_chief_of_staff_agent.ipynb
- [ ] 02_The_observability_agent.ipynb

### 第五階段：工具使用 Notebooks (tool_use/)
- [ ] calculator_tool.ipynb
- [ ] customer_service_agent.ipynb
- [ ] extracting_structured_json.ipynb
- [ ] tool_choice.ipynb
- [ ] tool_use_with_pydantic.ipynb
- [ ] vision_with_tools.ipynb
- [ ] memory_cookbook.ipynb
- [ ] parallel_tools.ipynb
- [ ] programmatic_tool_calling_ptc.ipynb
- [ ] tool_search_with_embeddings.ipynb
- [ ] automatic-context-compaction.ipynb

### 第六階段：多模態 Notebooks (multimodal/)
- [ ] getting_started_with_vision.ipynb
- [ ] best_practices_for_vision.ipynb
- [ ] how_to_transcribe_text.ipynb
- [ ] reading_charts_graphs_powerpoints.ipynb
- [ ] crop_tool.ipynb
- [ ] using_sub_agents.ipynb

### 第七階段：雜項 Notebooks (misc/)
- [ ] prompt_caching.ipynb
- [ ] how_to_enable_json_mode.ipynb
- [ ] pdf_upload_summarization.ipynb
- [ ] batch_processing.ipynb
- [ ] building_evals.ipynb
- [ ] building_moderation_filter.ipynb
- [ ] metaprompt.ipynb
- [ ] 其他...

### 第八階段：進階思考 Notebooks (extended_thinking/)
- [ ] extended_thinking.ipynb
- [ ] extended_thinking_with_tool_use.ipynb

### 第九階段：Agent 模式 (patterns/agents/)
- [ ] basic_workflows.ipynb
- [ ] evaluator_optimizer.ipynb
- [ ] orchestrator_workers.ipynb

### 第十階段：Skills Notebooks
- [ ] 01_skills_introduction.ipynb
- [ ] 02_skills_financial_applications.ipynb
- [ ] 03_skills_custom_development.ipynb

### 第十一階段：第三方整合 (third_party/)
- [ ] LlamaIndex/*.ipynb
- [ ] Pinecone/*.ipynb
- [ ] MongoDB/*.ipynb
- [ ] 其他整合...

### 第十二階段：其他
- [ ] coding/prompting_for_frontend_aesthetics.ipynb
- [ ] finetuning/finetuning_on_bedrock.ipynb
- [ ] observability/usage_cost_api.ipynb

## 檔案統計

| 類別 | 數量 |
|------|------|
| Jupyter Notebooks | 64 |
| README 文件 | 13+ |
| registry.yaml 條目 | 64 |
| 預估總行數 | ~29,000 |

## 進度追蹤

更新日期：2026-01-09

### 已完成項目

- [x] README.md（根目錄）- 中英對照版本
- [x] CONTRIBUTING.md - 中英對照版本
- [x] registry.yaml - 所有 64 個 notebook 條目添加 title_zh 和 description_zh 字段
- [x] capabilities/README.md 及所有子目錄 README
- [x] claude_agent_sdk/README.md
- [x] skills/README.md
- [x] patterns/agents/README.md
- [x] third_party/Deepgram/README.md
- [x] third_party/ElevenLabs/README.md
- [x] third_party/LlamaIndex/README.md

### 總進度統計

- 核心文件翻譯：已完成
- README 文件：13/13 已完成
- registry.yaml 元數據：64/64 條目已翻譯

### 翻譯原則執行

1. 所有文件採用中英對照格式
2. 技術術語保留英文並提供中文說明
3. 程式碼區塊保持原樣不翻譯
4. 連結保持原始 URL

## 貢獻者

- 翻譯發起：Claude AI 輔助翻譯
- 翻譯完成日期：2026-01-09
