import copy
import time
from email.utils import formatdate

import httpx
import pytest
from test_v1_contract import INPUT, JOB, REQUEST, ApiError, job, response, wav_bytes


class BrokenStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b"x"
        raise httpx.ReadError("interrupted body")


@pytest.mark.parametrize("status", [200, 202, 429, 503])
@pytest.mark.parametrize("download", [False, True])
def test_body_read_failure_preserves_long_cooldown(factory, status, download):
    broken = httpx.Response(status, headers={"Retry-After": "17"}, stream=BrokenStream())
    api = [response(job())] if download else [broken, response(job())]
    audio = [broken, httpx.Response(200, content=wav_bytes())] if download else None
    client, calls, downloads, clock = factory(api, audio)
    client.generate(INPUT, request_id=REQUEST)
    assert clock.waits == [17]
    assert len(calls) == (1 if download else 2)
    if not download:
        assert calls[0].content == calls[1].content
        assert calls[0].headers["Idempotency-Key"] == calls[1].headers["Idempotency-Key"]
    else:
        assert len(downloads) == 2


def test_body_error_retains_date_cooldown(factory):
    broken = httpx.Response(
        503,
        headers={"Retry-After": formatdate(time.time() + 30, usegmt=True)},
        stream=BrokenStream(),
    )
    client, _, _, clock = factory([broken, response(job())])
    client.generate(INPUT, request_id=REQUEST)
    assert 28 <= clock.waits[0] <= 30


@pytest.mark.parametrize(
    "first",
    [
        httpx.ConnectError("offline"),
        httpx.Response(200, stream=BrokenStream()),
        response({"error": {"retryable": True}}, 429, **{"Retry-After": "1"}),
    ],
)
def test_status_retries_keep_minimum_five_seconds(factory, first):
    client, _, _, clock = factory(
        [response(job("queued")), first, response(job())], poll_interval=0.1
    )
    client.generate(INPUT, request_id=REQUEST)
    assert clock.waits == [5, 5]


def test_body_error_cooldown_exceeds_remaining_deadline(factory):
    client, calls, _, clock = factory(
        [httpx.Response(503, headers={"Retry-After": "90"}, stream=BrokenStream())], timeout=10
    )
    with pytest.raises(ApiError) as caught:
        client.generate(INPUT, request_id=REQUEST)
    assert caught.value.code == "deadline_exceeded"
    assert caught.value.request_id == REQUEST and len(calls) == 1 and not clock.waits


def test_nonretryable_status_body_failure_does_not_retry(factory):
    client, calls, _, _ = factory([httpx.Response(401, stream=BrokenStream())])
    with pytest.raises(ApiError):
        client.generate(INPUT, request_id=REQUEST)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "field", ["url", "mimeType", "sampleRate", "channels", "bitsPerSample", "access"]
)
@pytest.mark.parametrize("method", ["generate", "get_job", "find_job"])
def test_every_success_endpoint_requires_all_result_metadata(factory, field, method):
    payload = copy.deepcopy(job())
    del payload["result"][field]
    client, _, downloads, _ = factory([response(payload)])
    with pytest.raises(ApiError):
        if method == "generate":
            client.generate(INPUT, request_id=REQUEST)
        else:
            getattr(client, method)(JOB if method == "get_job" else REQUEST)
    assert not downloads


@pytest.mark.parametrize(
    "field,value",
    [
        ("sampleRate", 24000.0),
        ("channels", True),
        ("bitsPerSample", 16.0),
        ("access", "private"),
    ],
)
def test_result_types_are_strict(factory, field, value):
    payload = job()
    payload["result"][field] = value
    client, _, _, _ = factory([response(payload)])
    with pytest.raises(ApiError):
        client.generate(INPUT, request_id=REQUEST)


@pytest.mark.parametrize(
    "usage", [None, {}, {"billableCharacters": True, "reservedCredits": 0, "chargedCredits": 0}]
)
def test_pending_usage_is_required(factory, usage):
    client, _, _, _ = factory([response(job("queued", usage=usage))])
    with pytest.raises(ApiError):
        client.generate(INPUT, request_id=REQUEST)


def test_deleted_success_is_readable_but_cannot_generate(factory):
    client, calls, downloads, _ = factory([response(job(result=None, resultDeleted=True))])
    assert client.find_job(REQUEST)["resultDeleted"] is True
    assert len(calls) == 1 and not downloads


@pytest.mark.parametrize("request_id", [None, "", 123, "../path"])
def test_caller_known_uuid_required_before_submission(factory, request_id):
    client, calls, _, _ = factory([])
    with pytest.raises(ValueError):
        client.generate(INPUT, request_id=request_id)
    assert not calls


def test_quota_preserves_current_subscription(factory):
    payload = {
        "quota": {"remaining": 12, "reserved": 2, "available": 10},
        "subscription": {"status": "active"},
        "limits": {"maxCharacters": 100000},
    }
    client, _, _, _ = factory([response(payload)])
    assert client.quota() == payload


def test_error_string_includes_known_ids(factory):
    client, _, _, _ = factory([response(job("queued"))], timeout=1)
    with pytest.raises(ApiError) as caught:
        client.generate(INPUT, request_id=REQUEST)
    assert JOB in str(caught.value) and REQUEST in str(caught.value)


def test_explicit_nonretryable_rate_limit_is_not_replayed(factory):
    client, calls, _, clock = factory([response({"error": {"retryable": False}}, 429)])
    with pytest.raises(ApiError):
        client.generate(INPUT, request_id=REQUEST)
    assert len(calls) == 1 and not clock.waits


def test_invalid_metadata_retains_valid_correlated_ids(factory):
    client, _, _, _ = factory([response(job(result=None))])
    with pytest.raises(ApiError) as caught:
        client.generate(INPUT, request_id=REQUEST)
    assert caught.value.job_id == JOB and caught.value.request_id == REQUEST
