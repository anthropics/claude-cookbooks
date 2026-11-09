"""Shared required-ID and case-insensitive UUID contract regressions."""

import pytest
from test_v1_contract import INPUT, ApiError, V1Client, job, response, wav_bytes

JOB = "abcdefab-1234-4abc-8def-abcdef012345"
REQUEST = "fedcbafe-5678-4def-8abc-fedcba987654"
OTHER = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"


def identified_job(status="success", *, uppercase=False):
    return job(
        status,
        id=JOB.upper() if uppercase else JOB,
        requestId=REQUEST.upper() if uppercase else REQUEST,
    )


@pytest.mark.parametrize("stage", ["submit", "poll"])
@pytest.mark.parametrize("bad_request", ["missing", None, "not-a-uuid", OTHER])
def test_generate_rejects_missing_malformed_or_mismatched_request_id(factory, stage, bad_request):
    payload = identified_job()
    if bad_request == "missing":
        del payload["requestId"]
    else:
        payload["requestId"] = bad_request
    responses = [response(payload)]
    if stage == "poll":
        responses.insert(0, response(identified_job("queued")))
    client, calls, downloads, _ = factory(responses)
    with pytest.raises(ApiError) as error:
        client.generate(INPUT, request_id=REQUEST.upper())
    assert error.value.code == "invalid_response"
    assert error.value.request_id == REQUEST
    if stage == "poll":
        assert error.value.job_id == JOB
    assert not downloads and sum(call.method == "POST" for call in calls) == 1


@pytest.mark.parametrize("method", ["get_job", "find_job", "cancel_job"])
@pytest.mark.parametrize("bad_request", ["missing", None, "not-a-uuid"])
def test_every_job_endpoint_requires_a_valid_request_id(factory, method, bad_request):
    payload = identified_job()
    if bad_request == "missing":
        del payload["requestId"]
    else:
        payload["requestId"] = bad_request
    client, calls, downloads, _ = factory([response(payload)])
    with pytest.raises(ApiError) as error:
        getattr(client, method)(REQUEST if method == "find_job" else JOB)
    assert error.value.code == "invalid_response"
    assert len(calls) == 1 and not downloads


@pytest.mark.parametrize("method", ["get_job", "find_job", "cancel_job"])
def test_lookup_and_cancellation_reject_mismatched_identifiers(factory, method):
    payload = identified_job()
    payload["requestId" if method == "find_job" else "id"] = OTHER
    client, calls, downloads, _ = factory([response(payload)])
    with pytest.raises(ApiError) as error:
        getattr(client, method)(REQUEST if method == "find_job" else JOB)
    assert error.value.code == "invalid_response"
    assert len(calls) == 1 and not downloads


@pytest.mark.parametrize("submit_uppercase", [False, True])
@pytest.mark.parametrize("poll_uppercase", [False, True])
def test_generation_normalizes_identifiers_through_polling(
    factory, submit_uppercase, poll_uppercase
):
    client, calls, downloads, _ = factory(
        [
            response(identified_job("queued", uppercase=submit_uppercase)),
            response(identified_job(uppercase=poll_uppercase)),
        ]
    )
    result, audio, request_id = client.generate(INPUT, request_id=REQUEST.upper())
    assert result["id"] == JOB and result["requestId"] == request_id == REQUEST
    assert audio == wav_bytes() and len(downloads) == 1
    assert calls[0].headers["Idempotency-Key"] == REQUEST
    assert calls[1].url.path == "/api/v1/tts/jobs/" + JOB


@pytest.mark.parametrize("method", ["get_job", "find_job", "cancel_job"])
@pytest.mark.parametrize("uppercase_input", [False, True])
def test_job_endpoints_accept_uppercase_response_uuids(factory, method, uppercase_input):
    client, calls, _, _ = factory([response(identified_job(uppercase=True))])
    expected = REQUEST if method == "find_job" else JOB
    result = getattr(client, method)(expected.upper() if uppercase_input else expected)
    assert result["id"] == JOB and result["requestId"] == REQUEST
    if method == "find_job":
        assert calls[0].url.params["requestId"] == REQUEST
    else:
        assert JOB in calls[0].url.path


def test_job_validator_normalizes_expected_ids_too():
    result = V1Client._job(identified_job(), job_id=JOB.upper(), request_id=REQUEST.upper())
    assert result["id"] == JOB and result["requestId"] == REQUEST
