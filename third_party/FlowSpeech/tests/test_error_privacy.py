"""Untrusted API errors must not become credential-bearing diagnostics."""

import logging
import traceback

import httpx
import pytest
from flowspeech_v1 import ApiError, V1Client
from test_v1_contract import INPUT, JOB, REQUEST, job

KEY = "synthetic-private-api-key"
SIGNED = "https://storage.example.test/audio.wav?sig=synthetic-private-signature"


@pytest.mark.parametrize("boundary", ["api", "job"])
@pytest.mark.parametrize("kind", ["key", "embedded", "url", "dict", "list", "control"])
def test_untrusted_error_fields_are_not_public_diagnostics(boundary, kind, caplog):
    value = {
        "key": KEY,
        "embedded": "prefix_" + KEY + "_suffix",
        "url": SIGNED,
        "dict": {"secret": KEY},
        "list": [KEY],
        "control": "private\n" + KEY,
    }[kind]
    # The job schema requires a string code, but API errors can contain any JSON value.
    details = {
        "code": str(value) if boundary == "job" else value,
        "message": KEY + " " + SIGNED,
        "retryable": False,
    }
    payload = (
        {"error": details, "traceId": value}
        if boundary == "api"
        else job("failed", result=None, error=details)
    )
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(401 if boundary == "api" else 200, json=payload)
        )
    ) as http:
        speech = V1Client(api_key=KEY, http_client=http, download_client=http)
        try:
            with pytest.raises(ApiError) as caught:
                speech.generate(INPUT, request_id=REQUEST)
            error = caught.value
            logging.getLogger("flowspeech-test").error(
                "failure=%s code=%s trace=%s", error, error.code, error.trace_id
            )
            public = (
                str(error)
                + repr(vars(error))
                + caplog.text
                + "".join(traceback.format_exception(error))
            )
            assert KEY not in public and SIGNED not in public
            assert error.code == ("http_error" if boundary == "api" else "failed")
            assert error.trace_id is None
            assert error.request_id == REQUEST
            assert error.job_id == (JOB if boundary == "job" else None)
        finally:
            speech.close()


def test_safe_error_tokens_are_preserved():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                401,
                json={
                    "error": {
                        "code": "invalid_api_key",
                        "message": "untrusted prose",
                        "retryable": False,
                    },
                    "traceId": REQUEST,
                },
            )
        )
    ) as http:
        speech = V1Client(api_key=KEY, http_client=http, download_client=http)
        try:
            with pytest.raises(ApiError) as caught:
                speech.voices()
            assert caught.value.code == "invalid_api_key"
            assert caught.value.trace_id == REQUEST
            assert str(caught.value) == "FlowSpeech API returned HTTP 401"
        finally:
            speech.close()
