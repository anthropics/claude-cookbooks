# ElevenLabs <> Claude Cookbooks

[ElevenLabs](https://elevenlabs.io/) provides AI-powered speech-to-text and text-to-speech APIs for creating natural-sounding voice applications with advanced features like voice cloning and streaming synthesis.

This cookbook demonstrates how to build a low-latency voice assistant by combining ElevenLabs' speech processing with Claude's intelligent responses, progressively optimizing for real-time performance.

## What's Included

* **[Low Latency Voice Assistant Notebook](./low_latency_stt_claude_tts.ipynb)** - An interactive tutorial that walks you through building a voice assistant step-by-step, demonstrating various optimization techniques to minimize latency through streaming.

* **[WebSocket Streaming Script](./stream_voice_assistant_websocket.py)** - A production-ready conversational voice assistant featuring continuous microphone input, gapless audio playback, and the lowest possible latency using WebSocket streaming.

## How to Use This Cookbook

We recommend following this sequence to get the most out of this cookbook:

### Step 1: Set Up Your Environment

1. **Get your API keys:**
   - ElevenLabs API key: [elevenlabs.io/app/developers/api-keys](https://elevenlabs.io/app/developers/api-keys)
   - Anthropic API key: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

2. **Configure your environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Work Through the Notebook

Start with the **[Low Latency Voice Assistant Notebook](./low_latency_stt_claude_tts.ipynb)**. This interactive guide will teach you:

- How to use ElevenLabs for speech-to-text transcription
- How to generate Claude responses and measure latency
- How streaming reduces time-to-first-token
- How to stream text-to-speech for faster audio playback
- The tradeoffs between different streaming approaches
- Why WebSocket streaming provides the best balance of latency and quality

The notebook includes performance metrics and comparisons at each step, helping you understand the impact of each optimization.

### Step 3: Try the Production Script

After understanding the concepts from the notebook, run the **[WebSocket Streaming Script](./stream_voice_assistant_websocket.py)** to experience a fully functional voice assistant:

```bash
python stream_voice_assistant_websocket.py
```

**How it works:**
1. Press Enter to start recording
2. Speak your question into the microphone
3. Press Enter to stop recording
4. The assistant will respond with natural speech
5. Repeat or press Ctrl+C to exit

The script demonstrates production-ready implementations of:
- Real-time microphone recording with sounddevice
- Continuous conversation with context retention
- WebSocket-based streaming for minimal latency
- Custom audio queue for seamless playback

## More About ElevenLabs

Here are some helpful resources to deepen your understanding:

- [ElevenLabs Platform](https://elevenlabs.io/) - Official website
- [API Documentation](https://elevenlabs.io/docs/overview) - Complete API reference
- [Voice Library](https://elevenlabs.io/voice-library) - Explore available voices
- [API Playground](https://elevenlabs.io/app/speech-synthesis/text-to-speech) - Test voices interactively
- [Python SDK](https://github.com/elevenlabs/elevenlabs-python) - Official Python SDK