"""Chunking and limit handling -- the logic each tool uses to hide model limits.

These run offline: no API key, no network, no cost.
"""

from __future__ import annotations

import pytest

from bodhan_mcp.config import SPEAK_RECOMMENDED_MAX_CHARS
from bodhan_mcp.media import split_sentences
from bodhan_mcp.tools import _chunk_for_context, _cer, _numerals, _script_guess


class TestSplitSentences:
    def test_short_text_is_one_piece(self):
        assert split_sentences("Hello there.", 600) == ["Hello there."]

    def test_empty_text_yields_nothing(self):
        assert split_sentences("   ", 600) == []

    def test_every_piece_respects_the_limit(self):
        text = " ".join(f"This is sentence number {i}." for i in range(200))
        pieces = split_sentences(text, 200)
        assert pieces
        assert all(len(p) <= 200 for p in pieces)

    def test_no_content_is_lost(self):
        text = "First sentence. Second sentence. Third sentence."
        joined = " ".join(split_sentences(text, 20))
        for word in ("First", "Second", "Third"):
            assert word in joined

    def test_splits_on_devanagari_danda(self):
        text = "यह पहला वाक्य है। यह दूसरा वाक्य है। यह तीसरा वाक्य है।"
        pieces = split_sentences(text, 25)
        assert len(pieces) > 1
        assert all(len(p) <= 25 for p in pieces)

    def test_a_single_overlong_sentence_is_broken_on_words(self):
        text = "word " * 500
        pieces = split_sentences(text, 100)
        assert all(len(p) <= 100 for p in pieces)

    def test_default_speak_limit_is_respected(self):
        text = "A sentence that repeats. " * 100
        assert all(len(p) <= SPEAK_RECOMMENDED_MAX_CHARS
                   for p in split_sentences(text, SPEAK_RECOMMENDED_MAX_CHARS))


class TestContextChunking:
    def test_short_text_is_not_chunked(self):
        assert _chunk_for_context("short", 6000) == ["short"]

    def test_long_text_splits_on_paragraphs(self):
        text = "\n\n".join(["paragraph " * 100] * 10)
        chunks = _chunk_for_context(text, 2000)
        assert len(chunks) > 1
        assert all(len(c) <= 2500 for c in chunks)


class TestNumerals:
    def test_finds_plain_and_decimal_numbers(self):
        found = _numerals("Water boils at 100 °C, or 212.5 °F, in 1 atm.")
        assert "100" in found and "212.5" in found and "1" in found

    def test_no_numbers_found_in_prose(self):
        assert _numerals("No digits here at all.") == []


class TestCER:
    def test_identical_strings_score_zero(self):
        assert _cer("hello world", "hello world") == 0.0

    def test_classic_kitten_sitting_distance(self):
        assert _cer("kitten", "sitting") == pytest.approx(0.5, abs=0.01)

    def test_whitespace_is_normalised_before_comparison(self):
        assert _cer("hello   world", "hello world") == 0.0

    def test_completely_missing_output_scores_one(self):
        assert _cer("some text", "") == 1.0


class TestScriptGuess:
    @pytest.mark.parametrize("text,expected", [
        ("यह हिंदी में लिखा है", "hi"),
        ("এটি বাংলায় লেখা", "bn"),
        ("இது தமிழில் எழுதப்பட்டது", "ta"),
        ("This is written in English", "en"),
    ])
    def test_detects_major_scripts(self, text, expected):
        assert _script_guess(text)[0] == expected

    def test_empty_text_has_no_language(self):
        assert _script_guess("")[0] is None
