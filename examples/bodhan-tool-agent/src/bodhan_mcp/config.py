"""Configuration, loaded from the environment only. No secrets live in code."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BODHAN_BASE_URL = os.getenv("BODHAN_BASE_URL", "https://api.bodhan.ai/v1").rstrip("/")
CACHE_DIR = Path(os.getenv("BODHAN_CACHE_DIR", ".cache"))

# Model identifiers as sent to the hosted API.
MODEL_TRANSCRIBE = os.getenv("BODHAN_TRANSCRIBE_MODEL", "indic-transcribe-core")
MODEL_TRANSLATE = os.getenv("BODHAN_TRANSLATE_MODEL", "indic-translate")
MODEL_SPEAK = os.getenv("BODHAN_SPEAK_MODEL", "indic-speak")
MODEL_OCR = os.getenv("BODHAN_OCR_MODEL", "indic-ocr")

# Hosted prices, in rupees. Used by the cost meter and the budget guard.
PRICE_TRANSCRIBE_PER_AUDIO_MINUTE = 0.10
PRICE_TRANSLATE_PER_10K_OUTPUT_TOKENS = 0.20
PRICE_SPEAK_PER_10K_INPUT_CHARS = 6.00
PRICE_OCR_PER_IMAGE = 0.20

# Model limits the tools hide from their callers.
TRANSCRIBE_WINDOW_SECONDS = 30
TRANSLATE_CONTEXT_TOKENS = 32_000
SPEAK_RECOMMENDED_MAX_CHARS = 600

# Networking.
REQUEST_TIMEOUT_SECONDS = float(os.getenv("BODHAN_TIMEOUT", "120"))
MAX_RETRIES = 4
MAX_CONCURRENCY = 4

# The 13 production-tier languages Indic-Speak supports.
# Anything outside this set must fail honestly rather than produce invented output.
SPEAK_LANGUAGES = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "en": "English",
}

# Indic-Translate covers English plus the 22 scheduled Indian languages.
TRANSLATE_LANGUAGES = set(SPEAK_LANGUAGES) | {
    "sa", "ne", "sd", "ks", "kok", "mni", "bho", "doi", "mai", "sat",
}


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    model: str
    api_key: str


def require_key(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(
            f"{name} is not set. Copy .env.example to .env and fill in your Bodhan keys."
        )
    return value


def llm_config() -> LLMConfig:
    base = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    key = os.getenv("LLM_API_KEY")
    missing = [n for n, v in
               (("LLM_BASE_URL", base), ("LLM_MODEL", model), ("LLM_API_KEY", key)) if not v]
    if missing:
        raise ConfigError(f"Missing LLM settings: {', '.join(missing)}")
    return LLMConfig(base_url=base.rstrip("/"), model=model, api_key=key)
