import json
import os
import sys
import types
import uuid
from pathlib import Path

import pytest
from flowspeech_notebook import dialogue_input, generate_recording, load_request, prepare_request
from flowspeech_v1 import validate_wav
from test_v1_contract import JOB, REQUEST, ApiError, job, response, wav_bytes

SCRIPT = "Guide: Welcome.[pause:0.6s]\nVisitor: [excited] A hidden room!"
VOICES = {"Guide": "Kore", "Visitor": "Puck"}
ROOT = Path(os.environ.get("FLOWSPEECH_TEST_ROOT", Path(__file__).resolve().parents[1]))


def test_dialogue_mapping_preserves_order_and_pause_cues():
    assert dialogue_input(SCRIPT, VOICES) == {
        "mode": "multi",
        "segments": [
            {"speaker": "Guide", "text": "Welcome.[pause:0.6s]", "voiceName": "Kore"},
            {"speaker": "Visitor", "text": "[excited] A hidden room!", "voiceName": "Puck"},
        ],
    }


@pytest.mark.parametrize("script", ["", "Unknown: Hello", "No label", "Guide: "])
def test_invalid_dialogue_rejected(script):
    with pytest.raises(ValueError):
        dialogue_input(script, VOICES)


def test_request_is_saved_privately_before_submission_and_reused(tmp_path):
    path = tmp_path / "request.json"
    first = prepare_request(SCRIPT, VOICES, path)
    assert str(uuid.UUID(first["request_id"])) == first["request_id"]
    assert path.stat().st_mode & 0o777 == 0o600
    assert prepare_request(SCRIPT, VOICES, path) == first == load_request(path)
    with pytest.raises(ValueError, match="differs"):
        prepare_request(SCRIPT + "\nGuide: Different", VOICES, path)
    assert load_request(path) == first


@pytest.mark.parametrize("output", ["already.wav", "missing/recording.wav", "bad\0.wav"])
def test_bad_output_fails_before_any_submission(factory, tmp_path, output):
    client, calls, _, _ = factory([])
    (tmp_path / "already.wav").write_bytes(wav_bytes())
    record = {"request_id": REQUEST, "input": dialogue_input(SCRIPT, VOICES)}
    with pytest.raises(ValueError):
        generate_recording(client, record, tmp_path / output)
    assert not calls


def test_save_race_preserves_original_and_recovery_ids(factory, tmp_path, monkeypatch):
    client, calls, _, _ = factory([response(job())])
    path = tmp_path / "race.wav"
    original = client.generate

    def generate(*args, **kwargs):
        result = original(*args, **kwargs)
        path.write_bytes(b"other-writer")
        return result

    monkeypatch.setattr(client, "generate", generate)
    record = {"request_id": REQUEST, "input": dialogue_input(SCRIPT, VOICES)}
    with pytest.raises(ApiError) as caught:
        generate_recording(client, record, path)
    assert caught.value.job_id == JOB and caught.value.request_id == REQUEST
    assert path.read_bytes() == b"other-writer" and len(calls) == 1


def test_actual_notebook_code_executes_offline_and_resumes_without_new_calls(
    factory, tmp_path, monkeypatch
):
    client, calls, downloads, _ = factory([response(job())])
    writing_calls, displays = [], []

    def create(**kwargs):
        writing_calls.append(kwargs)
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=SCRIPT)])

    def module(name, **attributes):
        value = types.ModuleType(name)
        value.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, value)

    module(
        "anthropic",
        Anthropic=lambda **_: types.SimpleNamespace(messages=types.SimpleNamespace(create=create)),
    )
    module("dotenv", load_dotenv=lambda: None)
    module("IPython.display", Audio=lambda **kwargs: kwargs, display=displays.append)
    module("flowspeech_v1", V1Client=lambda **_: client, validate_wav=validate_wav)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "offline-writing-key")
    monkeypatch.setenv("FLOWSPEECH_API_KEY", "offline-speech-key")
    monkeypatch.setattr(uuid, "uuid4", lambda: uuid.UUID(REQUEST))
    monkeypatch.chdir(tmp_path)
    notebook = json.loads((ROOT / "claude_directed_narration.ipynb").read_text())
    assert notebook["nbformat"] == 4
    assert len({cell["id"] for cell in notebook["cells"]}) == len(notebook["cells"])
    code = [
        ("".join(cell["source"]), i)
        for i, cell in enumerate(notebook["cells"])
        if cell["cell_type"] == "code" and not "".join(cell["source"]).startswith("%")
    ]
    for _ in range(2):
        namespace = {}
        for source, index in code:
            exec(compile(source, f"notebook-cell-{index}", "exec"), namespace)  # noqa: S102
    assert len(writing_calls) == len(calls) == len(downloads) == 1
    assert len(displays) == 2
    assert json.loads(calls[0].content)["input"] == dialogue_input(SCRIPT, VOICES)
    assert namespace["output_path"].read_bytes() == wav_bytes()
    assert namespace["output_path"].stat().st_mode & 0o777 == 0o600
    assert namespace["request_id"] == REQUEST


def test_persistence_rejects_symlinks_and_extra_fields(tmp_path):
    path = tmp_path / "request.json"
    record = prepare_request(SCRIPT, VOICES, path)
    link = tmp_path / "link.json"
    link.symlink_to(path)
    with pytest.raises(ValueError):
        load_request(link)
    path.write_text(json.dumps({**record, "speed": 2}))
    with pytest.raises(ValueError):
        load_request(path)
