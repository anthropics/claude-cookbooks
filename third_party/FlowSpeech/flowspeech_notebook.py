"""Local request persistence and notebook helpers; no requests at import time."""

import json
import os
import uuid
from pathlib import Path

from flowspeech_v1 import ApiError, identifier, make_input


def dialogue_input(script, voices):
    if not isinstance(script, str) or not script.strip() or not isinstance(voices, dict):
        raise ValueError("A labelled script and speaker-to-voice mapping are required")
    turns = []
    for line in script.splitlines():
        if not line.strip():
            continue
        speaker, separator, text = line.partition(":")
        speaker = speaker.strip()
        if not separator or speaker not in voices:
            raise ValueError("Every script line must start with a configured speaker label")
        turns.append({"speaker": speaker, "text": text.strip(), "voiceName": voices[speaker]})
    return make_input(segments=turns)


def load_request(file):
    path = Path(file)
    if path.is_symlink() or path.stat().st_size > 1024 * 1024:
        raise ValueError("Invalid saved request file")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or set(record) != {"request_id", "input", "script"}:
        raise ValueError("Invalid saved request fields")
    identifier(record["request_id"])
    if not isinstance(record["script"], str) or not record["script"].strip():
        raise ValueError("Invalid saved script")
    return record


def prepare_request(script, voices, file):
    """Persist a caller-known UUID and immutable input before starting paid work."""
    speech_input = dialogue_input(script, voices)
    path = Path(file)
    if os.path.lexists(path):
        record = load_request(path)
        if record["input"] != speech_input or record["script"] != script:
            raise ValueError(
                "Saved request differs; keep it for recovery and use a new file for new input"
            )
        return record
    record = {"request_id": str(uuid.uuid4()), "input": speech_input, "script": script}
    encoded = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
    if len(encoded) > 1024 * 1024:
        raise ValueError("Saved request exceeds 1 MiB")
    with open(
        path, "x", encoding="utf-8", opener=lambda p, flags: os.open(p, flags, 0o600)
    ) as output:
        output.write(encoded.decode("utf-8"))
        output.flush()
        os.fsync(output.fileno())
    return record


def generate_recording(client, record, file):
    path = Path(file)
    if (
        any(ord(c) < 32 or ord(c) == 127 for c in str(path))
        or os.path.lexists(path)
        or not path.parent.is_dir()
        or not os.access(path.parent, os.W_OK)
    ):
        raise ValueError("Choose an unused output file in an existing writable directory")
    job, audio, request_id = client.generate(record["input"], request_id=record["request_id"])
    try:
        with open(path, "xb", opener=lambda p, flags: os.open(p, flags, 0o600)) as output:
            output.write(audio)
    except OSError:
        raise ApiError(
            "Audio could not be saved; recover the existing recording",
            request_id=request_id,
            job_id=job["id"],
            result_url=job["result"]["url"],
        ) from None
    return job
