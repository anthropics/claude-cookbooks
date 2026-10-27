import io
import json
import uuid
import wave
from email.utils import formatdate

import httpx
import pytest
from flowspeech_v1 import ApiError, V1Client, make_input, retry_after

JOB = "11111111-1111-4111-8111-111111111111"
REQUEST = "22222222-2222-4222-8222-222222222222"
URL = "https://audio.example.test/speech.wav"
INPUT = {"mode": "single", "text": "Hello", "voiceName": "Kore"}


def wav_bytes():
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(b"\x00\x00" * 24)
    return output.getvalue()


def job(status="success", **kwargs):
    return {
        "id": JOB,
        "requestId": REQUEST,
        "status": status,
        "result": {
            "url": URL,
            "mimeType": "audio/wav",
            "sampleRate": 24000,
            "channels": 1,
            "bitsPerSample": 16,
            "access": "link",
        },
        "usage": {"billableCharacters": 5, "reservedCredits": 0, "chargedCredits": 5},
        **kwargs,
    }


class Clock:
    now = 0.0

    def __init__(self):
        self.waits = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds


@pytest.fixture
def factory():
    clients = []

    def create(api_responses, audio_responses=None, **kwargs):
        calls, downloads = [], []
        responses = iter(api_responses)
        audio_responses = iter(audio_responses or [httpx.Response(200, content=wav_bytes())])

        def handle(request, queue, captured):
            captured.append(request)
            response = next(queue)
            if isinstance(response, Exception):
                raise response
            return response

        api = httpx.Client(transport=httpx.MockTransport(lambda r: handle(r, responses, calls)))
        # Deliberately polluted injected client: downloads must ignore all these defaults.
        audio = httpx.Client(
            transport=httpx.MockTransport(lambda r: handle(r, audio_responses, downloads)),
            auth=("ignored", "ignored"),
            headers={"Authorization": "ignored", "X-Api-Key": "ignored"},
            cookies={"session": "ignored"},
            follow_redirects=True,
        )
        clock = Clock()
        client = V1Client(
            api_key="test-only",
            http_client=api,
            download_client=audio,
            clock=clock,
            sleep=clock.sleep,
            **kwargs,
        )
        clients.extend([api, audio, client])
        return client, calls, downloads, clock

    yield create
    for client in clients:
        client.close()


def response(payload, status=200, **headers):
    return httpx.Response(status, json=payload, headers=headers)


def test_single_polling_and_download_credentials(factory):
    states = ["queued", "running", "merging", "settling", "success"]
    client, calls, downloads, clock = factory(
        [response(job(state), **{"Retry-After": "7"}) for state in states]
    )
    completed, audio, request_id = client.generate(INPUT, request_id=REQUEST)
    assert completed["status"] == "success" and audio == wav_bytes() and request_id == REQUEST
    assert json.loads(calls[0].content) == {"input": INPUT}
    assert calls[0].headers["Idempotency-Key"] == REQUEST
    assert all(r.headers["Authorization"] == "Bearer test-only" for r in calls)
    assert [r.method for r in calls] == ["POST", "GET", "GET", "GET", "GET"]
    assert clock.waits == [7, 7, 7, 7]
    for request in downloads:
        assert not (
            {"authorization", "cookie", "x-api-key", "proxy-authorization"} & set(request.headers)
        )


def test_multi_input(factory):
    turns = [
        {"speaker": "Alice", "text": "Hello", "voiceName": "Kore"},
        {"speaker": "Bob", "text": "Welcome", "voiceName": "Puck"},
    ]
    client, calls, _, _ = factory([response(job(), 202)])
    client.generate(make_input(segments=turns), request_id=REQUEST)
    assert json.loads(calls[0].content) == {"input": {"mode": "multi", "segments": turns}}


@pytest.mark.parametrize(
    "first",
    [
        httpx.ConnectError("network"),
        httpx.ReadTimeout("network"),
        response(
            {"error": {"code": "busy", "message": "busy", "retryable": True}},
            503,
            **{"Retry-After": "9"},
        ),
        response({"error": {"code": "limited", "retryable": True}}, 429, **{"Retry-After": "9"}),
    ],
)
def test_create_retries_preserve_uuid_body(factory, first):
    client, calls, _, clock = factory([first, response(job())])
    client.generate(INPUT, request_id=REQUEST)
    assert calls[0].content == calls[1].content
    assert calls[0].headers["Idempotency-Key"] == calls[1].headers["Idempotency-Key"] == REQUEST
    assert clock.waits == ([9] if isinstance(first, httpx.Response) else [5])


def test_caller_uuid_is_recoverable_on_transport_failure(factory):
    client, calls, _, _ = factory([httpx.ConnectError("network")] * 3)
    with pytest.raises(ApiError) as error:
        client.generate(INPUT, request_id=REQUEST)
    assert str(uuid.UUID(error.value.request_id)) == error.value.request_id
    assert len(calls) == 3
    assert len({r.content for r in calls}) == 1
    assert len({r.headers["Idempotency-Key"] for r in calls}) == 1


@pytest.mark.parametrize("status", ["failed", "cancelled"])
def test_terminal_failure_is_not_http_success(factory, status):
    client, calls, downloads, _ = factory([response(job(status, error={"code": "stopped"}))])
    with pytest.raises(ApiError) as error:
        client.generate(INPUT, request_id=REQUEST)
    assert error.value.code == "stopped" and error.value.job_id == JOB
    assert error.value.request_id == REQUEST
    assert len(calls) == 1 and downloads == []


@pytest.mark.parametrize(
    "payload,expected",
    [
        (job(result=None, resultDeleted=True), "result_deleted"),
        (job(result=None), "invalid_result"),
        (job(status="unknown"), "invalid_response"),
        (job(id=None), "invalid_response"),
        (job(id="../escape"), "invalid_response"),
        (job(requestId=JOB), "invalid_response"),
        (job(usage=None), "invalid_result"),
        ([], "invalid_response"),
    ],
)
def test_malformed_jobs(factory, payload, expected):
    client, _, downloads, _ = factory([response(payload)])
    with pytest.raises(ApiError) as error:
        client.generate(INPUT, request_id=REQUEST)
    assert error.value.code == expected and not downloads


@pytest.mark.parametrize(
    "url",
    [
        "http://audio.test/a.wav",
        "file:///tmp/a",
        "https://name:password@audio.test/a",
        "https://audio.test/a#fragment",
        "https://audio.test/\nhello",
    ],
)
def test_unsafe_result_urls(factory, url):
    payload = job()
    payload["result"]["url"] = url
    client, _, downloads, _ = factory([response(payload)])
    with pytest.raises(ApiError, match="Unsafe"):
        client.generate(INPUT, request_id=REQUEST)
    assert not downloads


@pytest.mark.parametrize(
    "field,value",
    [
        ("mimeType", "audio/mpeg"),
        ("sampleRate", 48000),
        ("channels", True),
        ("bitsPerSample", 8),
        ("url", None),
    ],
)
def test_bad_metadata(factory, field, value):
    payload = job()
    payload["result"][field] = value
    client, _, downloads, _ = factory([response(payload)])
    with pytest.raises(ApiError):
        client.generate(INPUT, request_id=REQUEST)
    assert not downloads


def test_api_redirect_never_followed(factory):
    client, calls, downloads, _ = factory(
        [httpx.Response(302, headers={"Location": "https://other.test"})]
    )
    with pytest.raises(ApiError, match="redirect"):
        client.generate(INPUT, request_id=REQUEST)
    assert len(calls) == 1 and not downloads


def test_audio_redirects_have_no_credentials(factory):
    client, _, downloads, _ = factory(
        [response(job())],
        [
            httpx.Response(302, headers={"Location": "https://second.test/next"}),
            httpx.Response(307, headers={"Location": "/final"}),
            httpx.Response(200, content=wav_bytes()),
        ],
    )
    client.generate(INPUT, request_id=REQUEST)
    assert len(downloads) == 3
    assert all(not ({"authorization", "cookie", "x-api-key"} & set(r.headers)) for r in downloads)


def test_download_failure_does_not_recreate_job(factory):
    client, calls, downloads, _ = factory([response(job())], [httpx.Response(503)] * 3)
    with pytest.raises(ApiError) as error:
        client.generate(INPUT, request_id=REQUEST)
    assert len(calls) == 1 and len(downloads) == 3
    assert error.value.result_url == URL and error.value.job_id == JOB
    assert error.value.request_id == REQUEST


@pytest.mark.parametrize("audio", [b"not wav", b"", wav_bytes()[:-3]])
def test_invalid_downloads(factory, audio):
    client, _, _, _ = factory([response(job())], [httpx.Response(200, content=audio)])
    with pytest.raises(ApiError, match="WAV"):
        client.generate(INPUT, request_id=REQUEST)


def test_bounded_download(factory):
    client, _, _, _ = factory([response(job())], max_download_bytes=40)
    with pytest.raises(ApiError, match="size"):
        client.generate(INPUT, request_id=REQUEST)


def test_deadline_prevents_long_retry_after(factory):
    client, calls, _, clock = factory(
        [response(job("queued"), **{"Retry-After": "20"})], timeout=10
    )
    with pytest.raises(ApiError) as error:
        client.generate(INPUT, request_id=REQUEST)
    assert error.value.code == "deadline_exceeded" and error.value.job_id == JOB
    assert len(calls) == 1 and clock.waits == []


def test_deadline_bounds_request_timeout(factory):
    client, calls, _, _ = factory([response(job("queued")), response(job())], timeout=8)
    client.generate(INPUT, request_id=REQUEST)
    assert calls[0].extensions["timeout"]["read"] == 8
    assert calls[1].extensions["timeout"]["read"] == 3


def test_retry_after_formats():
    assert retry_after("8") == 8
    assert retry_after(formatdate(1010, usegmt=True), lambda: 1000) == 10
    assert retry_after("bad") == 0
    assert retry_after("nan") == 0
    assert retry_after("-1") == 0


def test_quota_voices_recovery_cancel(factory):
    quota = {"remaining": 100, "reserved": 10, "available": 90}
    client, calls, _, _ = factory(
        [
            response({"quota": quota, "subscription": {"plan": "basic"}, "limits": {}}),
            response({"voices": [{"name": "Kore"}]}),
            response(job()),
            response(job()),
            response(job("cancelled")),
        ]
    )
    assert client.quota()["quota"] == quota
    assert client.voices() == [{"name": "Kore"}]
    assert client.get_job(JOB)["id"] == JOB
    assert client.find_job(REQUEST)["id"] == JOB
    assert client.cancel_job(JOB)["status"] == "cancelled"
    assert [r.url.path for r in calls] == [
        "/api/v1/quota",
        "/api/v1/voices",
        f"/api/v1/tts/jobs/{JOB}",
        "/api/v1/tts/jobs",
        f"/api/v1/tts/jobs/{JOB}/cancel",
    ]
    assert calls[3].url.params["requestId"] == REQUEST


@pytest.mark.parametrize("method", ["get_job", "find_job", "cancel_job"])
def test_bad_ids_rejected_before_io(factory, method):
    client, calls, _, _ = factory([])
    with pytest.raises(ValueError):
        getattr(client, method)("../traversal")
    assert not calls


@pytest.mark.parametrize("status", [400, 401, 402, 403, 404, 409, 413, 415, 500])
def test_structured_nonretryable_errors(factory, status):
    client, calls, _, _ = factory(
        [
            response(
                {
                    "error": {
                        "code": "rejected",
                        "message": "test-only was rejected",
                        "retryable": False,
                    },
                    "traceId": "trace",
                },
                status,
            )
        ]
    )
    with pytest.raises(ApiError) as error:
        client.generate(INPUT, request_id=REQUEST)
    assert error.value.status_code == status and error.value.code == "rejected"
    assert error.value.trace_id == "trace"
    assert "test-only" not in str(error.value) and len(calls) == 1


@pytest.mark.parametrize(
    "payload", [{}, {"quota": {}}, {"quota": {"remaining": -1, "reserved": 0, "available": 0}}]
)
def test_bad_quota(factory, payload):
    client, _, _, _ = factory([response(payload)])
    with pytest.raises(ApiError, match="quota"):
        client.quota()


@pytest.mark.parametrize("payload", [{}, {"voices": "not list"}, {"voices": [{}]}])
def test_bad_voices(factory, payload):
    client, _, _, _ = factory([response(payload)])
    with pytest.raises(ApiError, match="voices"):
        client.voices()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"api_key": ""},
        {"api_key": "bad\nkey"},
        {"api_key": " spaces "},
        {"api_key": "ok", "base_url": "http://example.test"},
        {"api_key": "ok", "timeout": 0},
        {"api_key": "ok", "timeout": float("nan")},
        {"api_key": "ok", "max_retries": -1},
    ],
)
def test_bad_configuration(kwargs):
    with pytest.raises((ApiError, ValueError)):
        V1Client(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"text": ""},
        {"text": "x" * 100001},
        {"segments": []},
        {"segments": [{"speaker": "A", "text": "Hi", "voiceName": "Kore", "speed": 2}]},
        {"text": "x", "segments": [{"speaker": "A", "text": "Hi", "voiceName": "Kore"}]},
    ],
)
def test_bad_inputs(kwargs):
    with pytest.raises(ValueError):
        make_input(**kwargs)


@pytest.mark.parametrize("option", ["model", "source", "speed", "format", "speakers"])
def test_obsolete_options_rejected(factory, option):
    client, calls, _, _ = factory([])
    with pytest.raises(ValueError):
        client.generate({**INPUT, option: "unsupported"}, request_id=REQUEST)
    assert not calls


def test_stream_without_length_is_bounded(factory):
    class Stream(httpx.SyncByteStream):
        def __iter__(self):
            yield b"X" * 30
            yield b"Y" * 30

    client, _, _, _ = factory(
        [response(job())], [httpx.Response(200, stream=Stream())], max_download_bytes=40
    )
    with pytest.raises(ApiError, match="size"):
        client.generate(INPUT, request_id=REQUEST)


def test_non_json_response(factory):
    client, _, _, _ = factory([httpx.Response(200, content=b"not JSON")])
    with pytest.raises(ApiError, match="JSON"):
        client.generate(INPUT, request_id=REQUEST)


def test_mismatched_polled_id(factory):
    client, _, _, _ = factory([response(job("queued")), response(job(id=REQUEST))])
    with pytest.raises(ApiError, match="mismatched"):
        client.generate(INPUT, request_id=REQUEST)


@pytest.mark.parametrize(
    "location", ["http://other.test/a", "https://name:pass@other.test/a", "file:///tmp/a"]
)
def test_unsafe_audio_redirect_preserves_recovery_ids(factory, location):
    client, calls, downloads, _ = factory(
        [response(job())], [httpx.Response(302, headers={"Location": location})]
    )
    with pytest.raises(ApiError) as error:
        client.generate(INPUT, request_id=REQUEST)
    assert error.value.code == "download_failed"
    assert error.value.job_id == JOB and error.value.request_id == REQUEST
    assert len(calls) == len(downloads) == 1


def test_redirect_loop_is_bounded(factory):
    client, _, downloads, _ = factory(
        [response(job())], [httpx.Response(302, headers={"Location": URL}) for _ in range(6)]
    )
    with pytest.raises(ApiError, match="redirect"):
        client.generate(INPUT, request_id=REQUEST)
    assert len(downloads) == 6


def test_absolute_deadline_during_slow_request():
    import threading
    import time

    finished = threading.Event()
    calls = []

    def slow(request):
        calls.append(request)
        try:
            time.sleep(0.2)
            return response(job())
        finally:
            finished.set()

    with httpx.Client(transport=httpx.MockTransport(slow)) as transport:
        with V1Client(api_key="test-only", timeout=0.04, http_client=transport) as client:
            start = time.monotonic()
            with pytest.raises(ApiError) as error:
                client.generate(INPUT, request_id=REQUEST)
            elapsed = time.monotonic() - start
            assert elapsed < 0.15 and error.value.code == "deadline_exceeded"
            assert error.value.request_id == REQUEST
            assert finished.wait(1)
            assert len(calls) == 1


def test_absolute_deadline_during_slow_download():
    import threading
    import time

    finished = threading.Event()

    class SlowStream(httpx.SyncByteStream):
        def __iter__(self):
            yield wav_bytes()[:44]
            time.sleep(0.2)
            yield wav_bytes()[44:]

        def close(self):
            finished.set()

    api = httpx.Client(transport=httpx.MockTransport(lambda _: response(job())))
    audio = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, stream=SlowStream()))
    )
    with (
        api,
        audio,
        V1Client(
            api_key="test-only", timeout=0.04, http_client=api, download_client=audio
        ) as client,
    ):
        start = time.monotonic()
        with pytest.raises(ApiError) as error:
            client.generate(INPUT, request_id=REQUEST)
        assert time.monotonic() - start < 0.15
        assert error.value.code == "deadline_exceeded" and error.value.job_id == JOB
        assert error.value.result_url == URL
        assert finished.wait(1)


def test_poll_429_respects_retry_after(factory):
    client, calls, _, clock = factory(
        [
            response(job("queued")),
            response(
                {"error": {"code": "limited", "retryable": True}}, 429, **{"Retry-After": "13"}
            ),
            response(job()),
        ]
    )
    client.generate(INPUT, request_id=REQUEST)
    assert clock.waits == [5, 13] and len(calls) == 3


def test_same_body_replay_200(factory):
    client, calls, _, _ = factory([response(job(), 200)])
    result, _, _ = client.generate(INPUT, request_id=REQUEST)
    assert result["status"] == "success" and len(calls) == 1


def test_missing_key(monkeypatch):
    monkeypatch.delenv("FLOWSPEECH_API_KEY", raising=False)
    with pytest.raises(ApiError, match="key"):
        V1Client()
