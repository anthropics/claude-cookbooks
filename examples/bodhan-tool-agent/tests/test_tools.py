"""Tool validation, structured errors and budget enforcement.

Bad input must produce a structured error, never an exception that would crash
an MCP client. These run offline.
"""

from __future__ import annotations

import pytest

from bodhan_mcp import tools
from bodhan_mcp.cost import BudgetExceeded, CostMeter, price_ocr, price_speak, price_transcribe


class TestStructuredErrors:
    def test_missing_file_is_an_error_not_a_crash(self):
        result = tools.inspect_media("definitely/not/a/real/file.wav")
        assert result["ok"] is False
        assert result["error"]["code"] == "file_not_found"

    def test_transcribe_rejects_an_image(self, tmp_path):
        image = tmp_path / "page.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n")
        result = tools.transcribe_audio(str(image))
        assert result["ok"] is False
        assert result["error"]["code"] == "wrong_file_kind"
        assert "ocr_document" in result["error"]["message"]

    def test_ocr_rejects_audio(self, tmp_path):
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF")
        result = tools.ocr_document(str(audio))
        assert result["ok"] is False
        assert result["error"]["code"] == "wrong_file_kind"

    def test_translate_without_input_errors(self):
        result = tools.translate_text(target_lang="hi")
        assert result["ok"] is False
        assert result["error"]["code"] == "missing_input"

    def test_translate_empty_text_errors(self):
        result = tools.translate_text(text="   ", target_lang="hi")
        assert result["ok"] is False
        assert result["error"]["code"] == "empty_input"


class TestHonestFailure:
    """Unsupported languages must fail clearly and produce nothing."""

    def test_translation_into_french_is_refused(self):
        result = tools.translate_text(text="Hello", target_lang="fr")
        assert result["ok"] is False
        assert result["error"]["code"] == "unsupported_language"
        assert "fr" in result["error"]["message"]
        assert "text" not in result

    def test_synthesis_into_french_is_refused(self, tmp_path):
        result = tools.synthesize_speech("Bonjour", "fr", str(tmp_path / "out.mp3"))
        assert result["ok"] is False
        assert result["error"]["code"] == "unsupported_language"
        assert not (tmp_path / "out.mp3").exists()

    def test_synthesis_of_empty_text_is_refused(self, tmp_path):
        result = tools.synthesize_speech("", "hi", str(tmp_path / "out.mp3"))
        assert result["ok"] is False
        assert result["error"]["code"] == "empty_input"


class TestBudget:
    def test_meter_totals_line_items(self):
        meter = CostMeter(budget_inr=10.0)
        meter.record("indic-ocr", 5, "images", price_ocr(5))
        assert meter.total_inr == pytest.approx(1.0)

    def test_cached_calls_cost_nothing(self):
        meter = CostMeter(budget_inr=10.0)
        meter.record("indic-ocr", 1, "images", price_ocr(1), cached=True)
        assert meter.total_inr == 0.0

    def test_check_raises_before_spending(self):
        meter = CostMeter(budget_inr=1.0)
        meter.record("indic-speak", 1000, "input_chars", price_speak(1000))
        with pytest.raises(BudgetExceeded):
            meter.check(price_speak(10_000))

    def test_budget_error_reports_the_numbers(self):
        meter = CostMeter(budget_inr=0.5)
        with pytest.raises(BudgetExceeded) as excinfo:
            meter.check(price_transcribe(600))
        assert excinfo.value.budget_inr == 0.5

    def test_no_budget_means_no_limit(self):
        meter = CostMeter(budget_inr=None)
        meter.check(999.0)  # must not raise


class TestPricing:
    def test_transcribe_priced_per_audio_minute(self):
        assert price_transcribe(60) == pytest.approx(0.10)

    def test_speak_priced_per_10k_characters(self):
        assert price_speak(10_000) == pytest.approx(6.00)

    def test_ocr_priced_per_image(self):
        assert price_ocr(3) == pytest.approx(0.60)
