# ElevenLabs <> Claude Cookbooks

[ElevenLabs](https://elevenlabs.io/) provides AI-powered speech-to-text and text-to-speech APIs for creating natural-sounding voice applications with advanced features like voice cloning and streaming synthesis.

This cookbook demonstrates how to build a low-latency voice assistant by combining ElevenLabs' speech processing with Claude's intelligent responses, progressively optimizing for real-time performance.

## What's Included

* **[Low Latency Voice Assistant Notebook](./low_latency_stt_claude_tts.ipynb)** - An interactive tutorial that walks you through building a voice assistant step-by-step, demonstrating various optimization techniques to minimize latency through streaming.

* **[WebSocket Streaming Script](./stream_voice_assistant_websocket.py)** - A production-ready conversational voice assistant featuring continuous microphone input, gapless audio playback, and the lowest possible latency using WebSocket streaming.

## How to Use This Cookbook

We recommend following this sequence to get the most out of this cookbook:

### Step 1: Set Up Your Environment

1. **Create a virtual environment:**
   ```bash
   # Navigate to the ElevenLabs directory
   cd /path/to/claude-cookbooks/third_party/ElevenLabs

   # Create virtual environment
   python -m venv venv

   # Activate it
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\Scripts\activate     # On Windows
   ```

2. **Get your API keys:**
   - **ElevenLabs API key:** [elevenlabs.io/app/developers/api-keys](https://elevenlabs.io/app/developers/api-keys)

     When creating your API key, ensure it has the following minimum permissions:
     - Text to speech
     - Speech to text
     - Read access on voices
     - Read access on models

   - **Anthropic API key:** [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

3. **Configure your environment:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

4. **Install dependencies:**
   ```bash
   # With venv activated
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

## Troubleshooting

### Audio Popping or Crackling

**Symptom:** You may occasionally hear brief pops, clicks, or audio dropouts during playback.

**Explanation:**

This occurs because the script uses MP3 format audio, which is required for the ElevenLabs free tier. When streaming MP3 data in real-time chunks, FFmpeg occasionally receives incomplete frames that cannot be decoded. This typically happens:
- At the start of streaming (first chunk may be too small)
- During brief network delays
- At the end of audio generation (final chunk may be partial)

The script automatically handles these failed chunks by skipping them (using a try-except pattern in the audio decoding logic), which prevents errors from appearing in the console but may result in brief audio gaps that manifest as pops or clicks.

**Impact:**
- Audio playback continues normally
- Brief pops or clicks are usually imperceptible or minor
- The WebSocket connection remains stable
- No functionality is lost

**Solution:**

This is expected behavior when using MP3 format on the free tier. If you want to eliminate audio popping entirely:
1. Upgrade to a paid ElevenLabs tier
2. Modify the script to use `pcm_44100` format instead of MP3
3. PCM format provides cleaner streaming without decoding issues

### API Key Issues

**Symptom:** `AssertionError: ELEVENLABS_API_KEY is not set` or `AssertionError: ANTHROPIC_API_KEY is not set`

**Solution:**
1. Verify you've copied `.env.example` to `.env`: `cp .env.example .env`
2. Edit `.env` and ensure both API keys are set correctly
3. Check for typos or extra spaces in your API keys
4. Confirm your ElevenLabs key has the required permissions (see Step 1)

### Dependency Issues

**Symptom:** Errors like `ImportError: PortAudio library not found` or audio playback failures

**Solution:**

**macOS:**
```bash
brew install portaudio ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev ffmpeg
```

**Windows:**
- Install FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add FFmpeg to your system PATH
- PortAudio typically installs automatically with sounddevice on Windows

Then reinstall Python dependencies:
```bash
pip install -r requirements.txt
```

### Microphone Permissions

**Symptom:** `OSError: [Errno -9999] Unanticipated host error` or microphone not accessible

**Solution:**
- **macOS:** Go to System Preferences → Security & Privacy → Privacy → Microphone, and enable Terminal (or your Python IDE)
- **Windows:** Go to Settings → Privacy → Microphone, and enable microphone access for Python/Terminal
- **Linux:** Check your user is in the `audio` group: `sudo usermod -a -G audio $USER` (then log out and back in)

Test your microphone setup:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### WebSocket Connection Failures

**Symptom:** Connection errors, timeouts, or stream interruptions

**Solution:**
1. Check your internet connection is stable
2. Verify firewall isn't blocking WebSocket connections (port 443)
3. Try disabling VPN or proxy temporarily
4. Ensure you're not exceeding API rate limits (see ElevenLabs dashboard for usage)

If you continue to experience issues, check [ElevenLabs Status](https://status.elevenlabs.io/) for service updates.

## Project Ideas

Once you're comfortable with the voice assistant, here are some inspiring projects you can build:

- **Meeting Note-Taker** - Record and transcribe meetings in real-time, then use Claude to generate summaries, action items, and key takeaways from the conversation.

- **Language Learning Tutor** - Practice conversations in any language with real-time feedback. Claude can correct pronunciation, suggest better phrasing, and adapt difficulty to your skill level.

- **Interactive Storyteller** - Create choose-your-own-adventure games where Claude narrates the story and responds to your spoken choices, with different voice characters for each role.

- **Hands-Free Coding Assistant** - Describe code changes, bugs, or features verbally while keeping your hands on the keyboard. Perfect for rubber duck debugging or pair programming solo.

- **Voice-Activated Smart Home** - Build natural conversation interfaces for controlling home devices. Ask complex questions like "Is it cold enough to turn on the heater?" instead of simple on/off commands.

- **Personal Voice Journal** - Keep a daily journal by speaking your thoughts. Claude can organize entries by theme, track your mood over time, and surface relevant past entries when you need them.

## More About ElevenLabs

Here are some helpful resources to deepen your understanding:

- [ElevenLabs Platform](https://elevenlabs.io/) - Official website
- [API Documentation](https://elevenlabs.io/docs/overview) - Complete API reference
- [Voice Library](https://elevenlabs.io/voice-library) - Explore available voices
- [API Playground](https://elevenlabs.io/app/speech-synthesis/text-to-speech) - Test voices interactively
- [Python SDK](https://github.com/elevenlabs/elevenlabs-python) - Official Python SDK