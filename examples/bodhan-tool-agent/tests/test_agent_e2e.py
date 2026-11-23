"""End-to-end test of a multi-step task, with the LLM and the Bodhan models faked.

This exercises the real agent loop: planning, tool dispatch, trace writing,
budget enforcement and the output layout. Only the two network boundaries are
stubbed, so the orchestration under test is the orchestration that ships.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from bodhan_agent import loop
from bodhan_mcp import tools


# --- fakes for the LLM's response shape ------------------------------------

@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction
    type: str = "function"


@dataclass
class FakeMessage:
    content: str | None = None
    tool_calls: list | None = None


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeResponse:
    choices: list


class ScriptedLLM:
    """Replays a fixed sequence of planner turns."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.calls = 0
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        if self.calls < len(self.turns):
            turn = self.turns[self.calls]
        else:
            turn = FakeMessage(content="Done.")
        self.calls += 1
        return FakeResponse(choices=[FakeChoice(message=turn)])


@pytest.fixture
def fake_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_BASE_URL", "http://fake")
    monkeypatch.setenv("LLM_MODEL", "fake-model")
    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    monkeypatch.setattr(loop.config, "llm_config",
                        lambda: loop.config.LLMConfig("http://fake", "fake-model", "k"))
    return tmp_path


def test_multi_step_task_writes_the_full_output_layout(fake_env, monkeypatch):
    """Transcribe, then translate: two tools, one run, complete outputs."""
    inputs = fake_env / "inputs"
    inputs.mkdir()
    (inputs / "note.txt").write_text("placeholder", encoding="utf-8")
    out = fake_env / "out"

    monkeypatch.setattr(tools, "transcribe_audio", lambda path, language_hint=None: {
        "ok": True, "text": "यह एक परीक्षण है", "language": "hi",
        "duration_seconds": 12.0, "segments": [], "windows": 1,
    })
    monkeypatch.setattr(tools, "translate_text", lambda **kw: {
        "ok": True, "text": "This is a test", "target_lang": "en",
        "verification": {"coverage_ok": True, "numerals_ok": True},
    })
    monkeypatch.setitem(tools.TOOLS, "transcribe_audio", tools.transcribe_audio)
    monkeypatch.setitem(tools.TOOLS, "translate_text", tools.translate_text)

    turns = [
        FakeMessage(tool_calls=[FakeToolCall(
            id="1", function=FakeFunction("transcribe_audio",
                                          json.dumps({"path": str(inputs / "note.txt")})))]),
        FakeMessage(tool_calls=[FakeToolCall(
            id="2", function=FakeFunction("translate_text",
                                          json.dumps({"text": "यह एक परीक्षण है",
                                                      "target_lang": "en"})))]),
        FakeMessage(content="Transcribed the Hindi note and translated it to English."),
    ]
    monkeypatch.setattr(loop, "OpenAI", lambda **kw: ScriptedLLM(turns))

    report = loop.run_task("Transcribe this note and translate to English",
                           str(inputs), str(out), max_steps=10, max_cost_inr=5.0)

    assert report["status"] == "completed"
    assert report["tool_calls"] == 2
    assert (out / "result.md").exists()
    assert (out / "report.json").exists()
    assert (out / "trace.jsonl").exists()
    assert (out / "artifacts").is_dir()

    lines = [json.loads(line) for line in
             (out / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(e["type"] == "plan" for e in lines)
    assert [e["tool"] for e in lines if e["type"] == "tool_result"] == [
        "transcribe_audio", "translate_text"]
    assert "English" in (out / "result.md").read_text(encoding="utf-8")


def test_impossible_task_fails_honestly_without_artifacts(fake_env, monkeypatch):
    """An unsupported language must end in an explanation, not invented output."""
    inputs = fake_env / "inputs"
    inputs.mkdir()
    (inputs / "clip.txt").write_text("hello", encoding="utf-8")
    out = fake_env / "out"

    turns = [
        FakeMessage(tool_calls=[FakeToolCall(
            id="1", function=FakeFunction("translate_text",
                                          json.dumps({"text": "hello",
                                                      "target_lang": "fr"})))]),
        FakeMessage(content=("French is not supported by Indic-Translate, which covers "
                             "English and the 22 scheduled Indian languages. No "
                             "translation was produced.")),
    ]
    monkeypatch.setattr(loop, "OpenAI", lambda **kw: ScriptedLLM(turns))

    report = loop.run_task("Translate this into French", str(inputs), str(out),
                           max_steps=10, max_cost_inr=5.0)

    assert report["artifacts"] == []
    result = (out / "result.md").read_text(encoding="utf-8")
    assert "not supported" in result.lower()

    lines = [json.loads(line) for line in
             (out / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
    failed = [e for e in lines if e["type"] == "tool_result" and not e["ok"]]
    assert failed and "unsupported_language" in failed[0]["result_summary"]


def test_step_limit_stops_the_run(fake_env, monkeypatch):
    """A planner that never finishes is stopped by the step guard."""
    inputs = fake_env / "inputs"
    inputs.mkdir()
    (inputs / "a.txt").write_text("x", encoding="utf-8")
    out = fake_env / "out"

    looping = FakeMessage(tool_calls=[FakeToolCall(
        id="x", function=FakeFunction("inspect_media",
                                      json.dumps({"path": str(inputs / "a.txt")})))])
    monkeypatch.setattr(loop, "OpenAI", lambda **kw: ScriptedLLM([looping] * 20))

    report = loop.run_task("Go forever", str(inputs), str(out),
                           max_steps=3, max_cost_inr=5.0)

    assert report["status"] == "stopped_on_steps"
    assert report["stop_reason"] == "max_steps_reached"
    assert report["steps"] == 3
