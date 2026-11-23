"""The only place in the codebase that talks to Bodhan.

Every speech-recognition, translation, speech-synthesis and OCR call goes
through one of the four functions here. Nothing else in the project may call
another provider for those jobs -- that is the assignment's hard ground rule,
and keeping the surface to one file is how it stays auditable.

Around each call this module provides:
  * content-addressed caching, so an identical input is never paid for twice
  * retry with exponential backoff on transient failures
  * cost metering and pre-flight budget checks
  * a hard character guard on synthesis, the most expensive model per unit

-------------------------------------------------------------------------------
ADAPTER NOTE -- read this before your first real run
-------------------------------------------------------------------------------
The request/response shapes below follow the OpenAI-compatible conventions the
hosted API documents (`/audio/transcriptions`, `/audio/speech`,
`/chat/completions`). If your curl tests show different field names or routes,
this is the ONLY file you need to change: fix the four `_call_*` functions and
everything above them keeps working unchanged. That is the entire reason the
adapter is isolated here.
-------------------------------------------------------------------------------
"""

from __future__ import annotations

import base64
import random
import time
from pathlib import Path
from typing import Any

import httpx

from . import config
from .cache import CACHE, key_for
from .cost import (
    METER,
    BudgetExceeded,
    estimate_tokens,
    price_ocr,
    price_speak,
    price_transcribe,
    price_translate,
)
from .media import probe

RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


class BodhanError(RuntimeError):
    """A Bodhan API failure, surfaced with an actionable message."""


class UnsupportedLanguage(BodhanError):
    """The requested language is not served by the model. Never fabricate output."""


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _request(method: str, path: str, api_key: str, **kwargs: Any) -> httpx.Response:
    """One HTTP call with retry and exponential backoff."""
    url = f"{config.BODHAN_BASE_URL}{path}"
    last_error: Exception | None = None

    for attempt in range(config.MAX_RETRIES):
        try:
            with httpx.Client(timeout=config.REQUEST_TIMEOUT_SECONDS) as client:
                response = client.request(method, url, headers=_headers(api_key), **kwargs)
            if response.status_code in RETRYABLE_STATUS:
                raise httpx.HTTPStatusError(
                    f"retryable status {response.status_code}",
                    request=response.request, response=response,
                )
            if response.status_code >= 400:
                raise BodhanError(
                    f"{method} {path} failed with {response.status_code}: "
                    f"{response.text[:300]}"
                )
            return response
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            last_error = exc
            if attempt == config.MAX_RETRIES - 1:
                break
            backoff = (2 ** attempt) + random.uniform(0, 0.4)
            time.sleep(backoff)

    raise BodhanError(
        f"{method} {path} failed after {config.MAX_RETRIES} attempts: {last_error}"
    )


# ---------------------------------------------------------------------------
# Indic-Transcribe  --  all speech to text
# ---------------------------------------------------------------------------

def _call_transcribe(audio_path: Path, language_hint: str | None) -> dict:
    api_key = config.require_key("BODHAN_TRANSCRIBE_KEY")
    data: dict[str, Any] = {"model": config.MODEL_TRANSCRIBE, "response_format": "json"}
    if language_hint:
        data["language"] = language_hint
    with audio_path.open("rb") as fh:
        files = {"file": (audio_path.name, fh, "application/octet-stream")}
        response = _request("POST", "/audio/transcriptions", api_key, data=data, files=files)
    return response.json()


def transcribe(audio_path: str | Path, language_hint: str | None = None) -> dict:
    """Transcribe one audio file that is already inside the model's window.

    Callers should use tools.transcribe_audio, which handles windowing. Returns
    {"text": str, "language": str | None, "cached": bool}.
    """
    path = Path(audio_path)
    if not path.exists():
        raise BodhanError(f"Audio file not found: {path}")

    params = {"model": config.MODEL_TRANSCRIBE, "language_hint": language_hint}
    cache_key = key_for(config.MODEL_TRANSCRIBE, params, file_path=path)

    cached = CACHE.get_json(cache_key)
    duration = probe(path).duration_seconds or 0.0
    cost = price_transcribe(duration)

    if cached is not None:
        METER.record(config.MODEL_TRANSCRIBE, duration, "audio_seconds", cost, cached=True)
        return {**cached, "cached": True}

    METER.check(cost)
    payload = _call_transcribe(path, language_hint)
    text = payload.get("text", "")
    result = {"text": text, "language": payload.get("language") or language_hint}
    CACHE.put_json(cache_key, result)
    METER.record(config.MODEL_TRANSCRIBE, duration, "audio_seconds", cost)
    return {**result, "cached": False}


# ---------------------------------------------------------------------------
# Indic-Translate  --  all translation
# ---------------------------------------------------------------------------

def _call_translate(text: str, target_lang: str, source_lang: str | None) -> str:
    api_key = config.require_key("BODHAN_TRANSLATE_KEY")
    source_clause = f" from {source_lang}" if source_lang else ""
    instruction = (
        f"Translate the following text{source_clause} into {target_lang}. "
        "Preserve Markdown structure, tables, LaTeX and all numerals exactly. "
        "Return only the translation."
    )
    body = {
        "model": config.MODEL_TRANSLATE,
        "messages": [
            {"role": "system", "content": instruction},
            {"role": "user", "content": text},
        ],
        "temperature": 0.0,
    }
    response = _request("POST", "/chat/completions", api_key, json=body)
    payload = response.json()
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise BodhanError(f"Unexpected translate response shape: {payload}") from exc


def translate(text: str, target_lang: str, source_lang: str | None = None) -> dict:
    """Translate one chunk that already fits the context window.

    Callers should use tools.translate_text, which handles chunking.
    """
    if target_lang not in config.TRANSLATE_LANGUAGES:
        raise UnsupportedLanguage(
            f"Indic-Translate does not support '{target_lang}'. "
            f"Supported: {', '.join(sorted(config.TRANSLATE_LANGUAGES))}."
        )
    if not text.strip():
        return {"text": "", "cached": True}

    params = {"model": config.MODEL_TRANSLATE, "target": target_lang, "source": source_lang}
    cache_key = key_for(config.MODEL_TRANSLATE, params, text=text)

    cached = CACHE.get_json(cache_key)
    estimated_tokens = estimate_tokens(text)
    cost = price_translate(estimated_tokens)

    if cached is not None:
        METER.record(config.MODEL_TRANSLATE, estimated_tokens, "output_tokens", cost, cached=True)
        return {**cached, "cached": True}

    METER.check(cost)
    translated = _call_translate(text, target_lang, source_lang)
    result = {"text": translated}
    CACHE.put_json(cache_key, result)
    METER.record(config.MODEL_TRANSLATE, estimate_tokens(translated), "output_tokens",
                 price_translate(estimate_tokens(translated)))
    return {**result, "cached": False}


# ---------------------------------------------------------------------------
# Indic-Speak  --  all speech synthesis
# ---------------------------------------------------------------------------

def _call_speak(text: str, language: str, voice: str | None) -> bytes:
    api_key = config.require_key("BODHAN_SPEAK_KEY")
    body: dict[str, Any] = {
        "model": config.MODEL_SPEAK,
        "input": text,
        "language": language,
        "response_format": "mp3",
    }
    if voice:
        body["voice"] = voice
    response = _request("POST", "/audio/speech", api_key, json=body)

    ctype = response.headers.get("content-type", "")
    if "application/json" in ctype:
        payload = response.json()
        for field in ("audio", "audio_base64", "b64_audio", "data"):
            if field in payload:
                return base64.b64decode(payload[field])
        raise BodhanError(f"No audio field in speech response: {list(payload)}")
    return response.content


def speak(text: str, language: str, out_path: str | Path, voice: str | None = None,
          allow_long: bool = False) -> dict:
    """Synthesise one short chunk of text to an audio file.

    Callers should use tools.synthesize_speech, which splits long text.

    The character guard is deliberate: synthesis is the most expensive model per
    unit by a wide margin, and a single runaway call can consume an entire run's
    budget before any other guard fires.
    """
    if language not in config.SPEAK_LANGUAGES:
        raise UnsupportedLanguage(
            f"Indic-Speak does not support '{language}'. "
            f"Supported: {', '.join(sorted(config.SPEAK_LANGUAGES))}. "
            "No audio was produced."
        )
    if not text.strip():
        raise BodhanError("Refusing to synthesise empty text.")
    if len(text) > config.SPEAK_RECOMMENDED_MAX_CHARS and not allow_long:
        raise BodhanError(
            f"Refusing to synthesise {len(text)} characters in one call "
            f"(guard is {config.SPEAK_RECOMMENDED_MAX_CHARS}). "
            "Use tools.synthesize_speech, which splits text on sentence boundaries."
        )

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    params = {"model": config.MODEL_SPEAK, "language": language, "voice": voice}
    cache_key = key_for(config.MODEL_SPEAK, params, text=text)
    cost = price_speak(len(text))

    cached = CACHE.get_blob(cache_key, ".mp3")
    if cached is not None:
        out.write_bytes(cached)
        METER.record(config.MODEL_SPEAK, len(text), "input_chars", cost, cached=True)
        return {"path": str(out), "chars": len(text), "cached": True}

    METER.check(cost)
    audio = _call_speak(text, language, voice)
    CACHE.put_blob(cache_key, ".mp3", audio)
    out.write_bytes(audio)
    METER.record(config.MODEL_SPEAK, len(text), "input_chars", cost)
    return {"path": str(out), "chars": len(text), "cached": False}


# ---------------------------------------------------------------------------
# Indic-OCR  --  all text extraction from images
# ---------------------------------------------------------------------------

def _call_ocr(image_path: Path) -> str:
    api_key = config.require_key("BODHAN_OCR_KEY")
    encoded = base64.b64encode(image_path.read_bytes()).decode()
    suffix = image_path.suffix.lower().lstrip(".") or "png"
    mime = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix}"
    body = {
        "model": config.MODEL_OCR,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "Extract all text from this page as Markdown. Preserve headings, "
                         "lists, tables and equations. Keep reading order."},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
            ],
        }],
        "temperature": 0.0,
    }
    response = _request("POST", "/chat/completions", api_key, json=body)
    payload = response.json()
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise BodhanError(f"Unexpected OCR response shape: {payload}") from exc


def ocr_image(image_path: str | Path) -> dict:
    """Run Indic-OCR on a single page image.

    Note: the image is base64-encoded only on the wire to Bodhan. It is never
    placed in the agent's LLM context -- the agent sees file paths and text.
    """
    path = Path(image_path)
    if not path.exists():
        raise BodhanError(f"Image not found: {path}")

    params = {"model": config.MODEL_OCR}
    cache_key = key_for(config.MODEL_OCR, params, file_path=path)
    cost = price_ocr(1)

    cached = CACHE.get_json(cache_key)
    if cached is not None:
        METER.record(config.MODEL_OCR, 1, "images", cost, cached=True)
        return {**cached, "cached": True}

    METER.check(cost)
    text = _call_ocr(path)
    result = {"text": text, "source_image": str(path)}
    CACHE.put_json(cache_key, result)
    METER.record(config.MODEL_OCR, 1, "images", cost)
    return {**result, "cached": False}


__all__ = [
    "BodhanError",
    "UnsupportedLanguage",
    "BudgetExceeded",
    "transcribe",
    "translate",
    "speak",
    "ocr_image",
]
