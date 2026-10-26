# FlowSpeech <> Claude Cookbook

[FlowSpeech](https://flowspeech.io/) is a context-aware text-to-speech service for generating human-like narration with emotion, pause, voice, and multi-speaker controls.

This integration shows how to use Claude to turn a creative brief into a directed two-speaker script, then synthesize the result with the FlowSpeech API.

## What's Included

- **[Create directed narration with Claude and FlowSpeech](./claude_directed_narration.ipynb)** - Generate a concise dialogue with Claude, send it to FlowSpeech, save the returned audio as a WAV file, and play it in Jupyter.

## Setup

1. Create a virtual environment and activate it.
2. Install the notebook dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment template and add your keys:

   ```bash
   cp .env.example .env
   ```

4. Create the required API keys:
   - [Anthropic API key](https://console.anthropic.com/settings/keys)
   - [FlowSpeech API key](https://flowspeech.io/settings/apikeys/create)

5. Start Jupyter and open `claude_directed_narration.ipynb`.

The example never stores credentials in the notebook. Both keys are loaded from environment variables.

## Public API v1

An active FlowSpeech API subscription and sufficient credits are required. Keep
this notebook and its two helper modules together, and start Jupyter in this
directory. The notebook uses ordered multi-speaker segments, asynchronous jobs,
and downloaded WAV audio; the API does not return base64 PCM.

Before submission, the notebook saves `flowspeech-request.json` with the UUID,
script, and voices. This private file contains text but no API key. Re-running
loads the saved script instead of requesting a new one and reuses the same UUID
and body. Changed text or voices require a new request file and UUID. Existing
WAV files are validated and reused, never overwritten.

The helper enforces a 300-second total deadline, bounded retries, at least
five seconds between status queries, and longer Retry-After cooldowns, including
body-read failures. Cancelling the notebook stops the caller; it does not cancel
the paid server job. Keep the saved request file even after a timeout.

For read-only recovery, use `speech.find_job(request_id)` or
`speech.get_job(job_id)` inside a `V1Client` context. A success result can be
downloaded with `speech.download_audio(job["result"]["url"])`, without another
submission. Failed/cancelled jobs and deleted results are reported explicitly.
Only a 404 lookup permits replaying the unchanged input with its original UUID.

Downloads never carry API authorization, cookies, or injected client defaults.
HTTPS redirects are bounded and validated. Result metadata and the entire RIFF
container must match nonempty, aligned PCM WAV at 24 kHz, mono, 16 bit.
Unsupported model, source, speed, format, and legacy speaker fields are rejected.
`speech.quota()` preserves the current `subscription` field;
`speech.voices()` reads the current voice catalog.

## Offline Validation

From this directory:

```bash
python -m pip install "httpx==0.28.1" "pytest==8.4.2"
python -m pytest tests --confcutdir=tests -q
python verify_bundle.py
```

Tests use fake HTTP and extracted notebook cells, with network connections
blocked. They do not run paid writing or speech generation. The review bundle
contains only the listed runtime/documentation files and is retested after
extraction; it is not a separately published package.
