# Sentinel AI - Safety Guardrails for Claude

This cookbook demonstrates how to add real-time safety guardrails to Claude API calls using [Sentinel AI](https://github.com/MaxwellCalkin/sentinel-ai), an open-source safety scanning library.

## What you'll learn

- Scanning user inputs for prompt injection before sending to Claude
- Detecting and redacting PII in messages
- Scanning Claude's responses for harmful content
- Multilingual injection detection (12 languages)
- Protecting agentic tool calls from dangerous commands
- Streaming protection with mid-stream blocking

## Requirements

```bash
pip install -r requirements.txt
```

Set your `ANTHROPIC_API_KEY` environment variable.
