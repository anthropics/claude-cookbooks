# ElevenLabs <> Claude 實用指南

# ElevenLabs <> Claude Cookbooks

[ElevenLabs](https://elevenlabs.io/) 提供 AI 驅動的語音轉文字和文字轉語音 API，用於創建具有語音克隆和串流合成等進階功能的自然語音應用程式。

> **[English version below](#english-version) | 英文版本請見下方**

本指南展示如何透過結合 ElevenLabs 的語音處理與 Claude 的智慧回應來建構低延遲語音助手，逐步優化以達到即時效能。

## 包含內容

* **[低延遲語音助手 Notebook](./low_latency_stt_claude_tts.ipynb)** - 一個互動式教學，逐步引導您建構語音助手，展示各種優化技術以透過串流最小化延遲。

* **[WebSocket 串流腳本](./stream_voice_assistant_websocket.py)** - 一個生產就緒的對話式語音助手，具有連續麥克風輸入、無縫音檔播放，以及使用 WebSocket 串流實現的最低延遲。

## 如何使用本指南

我們建議按照以下順序來充分利用本指南：

### 步驟 1：設定您的環境

1. **創建虛擬環境：**
   ```bash
   # 導航到 ElevenLabs 目錄
   cd /path/to/claude-cookbooks/third_party/ElevenLabs

   # 創建虛擬環境
   python -m venv venv

   # 啟用它
   source venv/bin/activate  # macOS/Linux
   # 或
   venv\Scripts\activate     # Windows
   ```

2. **取得您的 API 金鑰：**
   - **ElevenLabs API 金鑰：** [elevenlabs.io/app/developers/api-keys](https://elevenlabs.io/app/developers/api-keys)

     創建 API 金鑰時，確保它具有以下最低權限：
     - 文字轉語音
     - 語音轉文字
     - 語音的讀取權限
     - 模型的讀取權限

   - **Anthropic API 金鑰：** [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

3. **設定您的環境：**
   ```bash
   cp .env.example .env
   ```

   編輯 `.env` 並添加您的 API 金鑰：
   ```
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

4. **安裝依賴項：**
   ```bash
   # 啟用 venv 後
   pip install -r requirements.txt
   ```

### 步驟 2：完成 Notebook

從 **[低延遲語音助手 Notebook](./low_latency_stt_claude_tts.ipynb)** 開始。這個互動式指南將教您：

- 如何使用 ElevenLabs 進行語音轉文字轉錄
- 如何生成 Claude 回應並測量延遲
- 串流如何減少首個 token 的回應時間
- 如何串流文字轉語音以加快音檔播放
- 不同串流方法之間的權衡
- 為什麼 WebSocket 串流提供最佳的延遲和品質平衡

Notebook 在每個步驟都包含效能指標和比較，幫助您理解每個優化的影響。

### 步驟 3：嘗試生產腳本

在理解 Notebook 中的概念後，執行 **[WebSocket 串流腳本](./stream_voice_assistant_websocket.py)** 來體驗功能完整的語音助手：

```bash
python stream_voice_assistant_websocket.py
```

**運作方式：**
1. 按 Enter 開始錄音
2. 對著麥克風說出您的問題
3. 按 Enter 停止錄音
4. 助手將以自然語音回應
5. 重複或按 Ctrl+C 退出

## 疑難排解

### 音檔爆音或雜訊

**症狀：** 您可能偶爾在播放期間聽到短暫的爆音、咔嗒聲或音檔中斷。

**解釋：**
這是因為腳本使用 MP3 格式音檔，這是 ElevenLabs 免費層所需的。當即時串流 MP3 資料區塊時，FFmpeg 偶爾會收到無法解碼的不完整幀。

**解決方案：**
如果您想完全消除音檔爆音：
1. 升級到付費 ElevenLabs 層級
2. 修改腳本使用 `pcm_44100` 格式而非 MP3
3. PCM 格式提供更乾淨的串流，沒有解碼問題

### API 金鑰問題

**症狀：** `AssertionError: ELEVENLABS_API_KEY is not set` 或 `AssertionError: ANTHROPIC_API_KEY is not set`

**解決方案：**
1. 確認您已將 `.env.example` 複製到 `.env`：`cp .env.example .env`
2. 編輯 `.env` 並確保兩個 API 金鑰都正確設定
3. 檢查 API 金鑰中是否有錯字或多餘空格

### 依賴項問題

**症狀：** 錯誤如 `ImportError: PortAudio library not found` 或音檔播放失敗

**解決方案：**

**macOS：**
```bash
brew install portaudio ffmpeg
```

**Ubuntu/Debian：**
```bash
sudo apt-get install portaudio19-dev ffmpeg
```

**Windows：**
- 從 [ffmpeg.org](https://ffmpeg.org/download.html) 安裝 FFmpeg
- 將 FFmpeg 添加到系統 PATH

## 專案創意

一旦您熟悉語音助手，以下是一些您可以建構的啟發性專案：

- **會議記錄器** - 即時錄製和轉錄會議，然後使用 Claude 從對話中生成摘要、行動項目和關鍵要點。

- **語言學習家教** - 以任何語言練習對話並獲得即時回饋。Claude 可以糾正發音、建議更好的措辭，並根據您的技能水平調整難度。

- **互動式說故事者** - 創建選擇自己冒險的遊戲，Claude 講述故事並回應您的口語選擇，每個角色都有不同的語音。

- **免手動編碼助手** - 在保持雙手放在鍵盤上的同時口頭描述程式碼變更、錯誤或功能。非常適合橡皮鴨除錯或獨自結對程式設計。

## 更多關於 ElevenLabs

以下是一些有用的資源來加深您的理解：

- [ElevenLabs 平台](https://elevenlabs.io/) - 官方網站
- [API 文件](https://elevenlabs.io/docs/overview) - 完整 API 參考
- [語音庫](https://elevenlabs.io/voice-library) - 探索可用語音
- [API Playground](https://elevenlabs.io/app/speech-synthesis/text-to-speech) - 互動測試語音
- [Python SDK](https://github.com/elevenlabs/elevenlabs-python) - 官方 Python SDK

---

<a name="english-version"></a>

## English Version

[ElevenLabs](https://elevenlabs.io/) provides AI-powered speech-to-text and text-to-speech APIs for creating natural-sounding voice applications with advanced features like voice cloning and streaming synthesis.

This cookbook demonstrates how to build a low-latency voice assistant by combining ElevenLabs' speech processing with Claude's intelligent responses, progressively optimizing for real-time performance.

### What's Included

* **[Low Latency Voice Assistant Notebook](./low_latency_stt_claude_tts.ipynb)** - An interactive tutorial that walks you through building a voice assistant step-by-step, demonstrating various optimization techniques to minimize latency through streaming.

* **[WebSocket Streaming Script](./stream_voice_assistant_websocket.py)** - A production-ready conversational voice assistant featuring continuous microphone input, gapless audio playback, and the lowest possible latency using WebSocket streaming.

### How to Use This Cookbook

See the Chinese version above for detailed setup instructions and troubleshooting.

### More About ElevenLabs

Here are some helpful resources to deepen your understanding:

- [ElevenLabs Platform](https://elevenlabs.io/) - Official website
- [API Documentation](https://elevenlabs.io/docs/overview) - Complete API reference
- [Voice Library](https://elevenlabs.io/voice-library) - Explore available voices
- [API Playground](https://elevenlabs.io/app/speech-synthesis/text-to-speech) - Test voices interactively
- [Python SDK](https://github.com/elevenlabs/elevenlabs-python) - Official Python SDK
