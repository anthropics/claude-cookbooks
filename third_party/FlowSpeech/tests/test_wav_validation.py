"""Structural WAV regressions run unchanged against source and installed artifacts."""

import importlib
import struct

import httpx
import pytest
from test_v1_contract import INPUT, JOB, REQUEST, URL, ApiError, V1Client, job, response, wav_bytes

validate_wav = importlib.import_module(V1Client.__module__).validate_wav
PCM = struct.pack("<HHIIHH", 1, 1, 24000, 48000, 2, 16)
SAMPLES = b"\x00\x00\x01\x00"


def chunk(name, data, *, declared=None, pad=True):
    return (
        name
        + struct.pack("<I", len(data) if declared is None else declared)
        + data
        + (b"\0" if pad and len(data) % 2 else b"")
    )


def riff(*chunks):
    body = b"WAVE" + b"".join(chunks)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def formatted(fmt=PCM, data=SAMPLES):
    return riff(chunk(b"fmt ", fmt), chunk(b"data", data))


def replace_u32(data, offset, value):
    result = bytearray(data)
    struct.pack_into("<I", result, offset, value)
    return bytes(result)


BAD_WAVS = [
    pytest.param(b"", id="empty"),
    pytest.param(b"RIFF", id="truncated-riff"),
    pytest.param(b"RIFX" + formatted()[4:], id="big-endian-container"),
    pytest.param(formatted()[:8] + b"OTHER" + formatted()[12:], id="not-wave"),
    pytest.param(replace_u32(formatted(), 4, 4), id="riff-too-small"),
    pytest.param(replace_u32(formatted(), 4, 0xFFFFFFFF), id="riff-too-large"),
    pytest.param(formatted() + b"trailer", id="outside-riff-trailer"),
    pytest.param(
        riff(b"JUNK" + struct.pack("<I", 100)), id="oversized-junk-runtimeerror-regression"
    ),
    pytest.param(
        riff(chunk(b"fmt ", PCM), chunk(b"data", SAMPLES), b"cut"), id="truncated-chunk-header"
    ),
    pytest.param(
        riff(chunk(b"fmt ", PCM), chunk(b"data", SAMPLES), chunk(b"JUNK", b"x", pad=False)),
        id="missing-alignment-pad",
    ),
    pytest.param(riff(chunk(b"fmt ", PCM, declared=0xFFFFFFFF)), id="format-bounds-overflow"),
    pytest.param(
        riff(chunk(b"fmt ", PCM), chunk(b"data", SAMPLES, declared=0xFFFFFFFF)),
        id="data-bounds-overflow",
    ),
    pytest.param(riff(chunk(b"data", SAMPLES)), id="missing-format"),
    pytest.param(riff(chunk(b"fmt ", PCM)), id="missing-data"),
    pytest.param(riff(chunk(b"data", SAMPLES), chunk(b"fmt ", PCM)), id="data-before-format"),
    pytest.param(
        riff(chunk(b"fmt ", PCM), chunk(b"fmt ", PCM), chunk(b"data", SAMPLES)),
        id="duplicate-format",
    ),
    pytest.param(
        riff(chunk(b"fmt ", PCM), chunk(b"data", SAMPLES), chunk(b"data", SAMPLES)),
        id="duplicate-data",
    ),
    pytest.param(formatted(data=b""), id="empty-pcm"),
    pytest.param(formatted(data=SAMPLES + b"x"), id="odd-pcm-size-flooring-regression"),
    pytest.param(formatted()[:-1], id="truncated-sample"),
    pytest.param(formatted(fmt=PCM[:-1]), id="short-format"),
    pytest.param(formatted(fmt=PCM + b"\0"), id="partial-format-extension"),
    pytest.param(formatted(fmt=PCM + b"\x01\0"), id="nonzero-pcm-extension"),
    pytest.param(formatted(fmt=PCM + b"\0\0xx"), id="oversized-format"),
]
for name, fields in [
    ("not-pcm", (3, 1, 24000, 48000, 2, 16)),
    ("stereo", (1, 2, 24000, 48000, 2, 16)),
    ("sample-rate", (1, 1, 48000, 48000, 2, 16)),
    ("byte-rate", (1, 1, 24000, 96000, 2, 16)),
    ("block-align", (1, 1, 24000, 48000, 4, 16)),
    ("sample-width", (1, 1, 24000, 48000, 2, 8)),
]:
    BAD_WAVS.append(pytest.param(formatted(fmt=struct.pack("<HHIIHH", *fields)), id=name))


@pytest.mark.parametrize("data", BAD_WAVS)
def test_malformed_wav_is_typed_and_preserves_recovery(factory, data):
    client, calls, downloads, _ = factory([response(job())], [httpx.Response(200, content=data)])
    with pytest.raises(ApiError) as caught:
        client.generate(INPUT, request_id=REQUEST)
    error = caught.value
    assert error.code == "invalid_audio" and error.retryable is False
    assert (error.request_id, error.job_id, error.result_url) == (REQUEST, JOB, URL)
    assert len(calls) == len(downloads) == 1


@pytest.mark.parametrize(
    "data",
    [
        wav_bytes(),
        formatted(fmt=PCM + b"\0\0"),
        riff(chunk(b"JUNK", b"odd"), chunk(b"fmt ", PCM), chunk(b"data", SAMPLES)),
        riff(chunk(b"fmt ", PCM), chunk(b"data", SAMPLES), chunk(b"LIST", b"odd")),
    ],
)
def test_valid_pcm_and_padded_ancillary_chunks_are_preserved(factory, data):
    client, _, _, _ = factory([response(job())], [httpx.Response(200, content=data)])
    assert client.generate(INPUT, request_id=REQUEST)[1] == data


def test_every_truncation_is_a_normalized_parse_failure():
    data = wav_bytes()
    for length in range(len(data)):
        with pytest.raises(ApiError) as caught:
            validate_wav(data[:length], result_url=URL)
        assert caught.value.code == "invalid_audio" and caught.value.result_url == URL


def test_riff_size_cannot_hide_an_incomplete_chunk():
    data = formatted()
    for length in range(12, len(data)):
        truncated = replace_u32(data[:length], 4, length - 8)
        with pytest.raises(ApiError, match="WAV"):
            validate_wav(truncated)


def test_container_validation_honors_the_remaining_operation_deadline():
    checks = 0

    def expired():
        nonlocal checks
        checks += 1
        if checks == 2:
            raise ApiError("deadline", code="deadline_exceeded")

    with pytest.raises(ApiError) as caught:
        validate_wav(formatted(), check_deadline=expired)
    assert caught.value.code == "deadline_exceeded" and checks == 2
