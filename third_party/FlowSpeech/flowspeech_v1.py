"""FlowSpeech public API v1 jobs, recovery, and bounded credential-free WAV downloads."""

from __future__ import annotations

import json
import math
import os
import re
import struct
import threading
import time
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit

import httpx

PENDING = {"queued", "running", "merging", "settling"}
TERMINAL = {"success", "failed", "cancelled"}
MAX_HTTP_WORKERS = 8
_HTTP_WORKERS = threading.BoundedSemaphore(MAX_HTTP_WORKERS)


class ApiError(RuntimeError):
    def __init__(
        self,
        message,
        *,
        status_code=None,
        code=None,
        retryable=False,
        trace_id=None,
        request_id=None,
        job_id=None,
        result_url=None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.retryable = retryable
        self.trace_id = trace_id
        self.request_id = request_id
        self.job_id = job_id
        self.result_url = result_url

    def __str__(self):
        recovery = []
        if self.request_id:
            recovery.append(f"request_id={self.request_id}")
        if self.job_id:
            recovery.append(f"job_id={self.job_id}")
        return super().__str__() + (" (" + ", ".join(recovery) + ")" if recovery else "")


class _BodyReadError(httpx.TransportError):
    def __init__(self, status, headers):
        super().__init__("Response body transport failed")
        self.status = status
        self.headers = headers


def identifier(value):
    import uuid

    if not isinstance(value, str):
        raise ValueError("ID must be a UUID")
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        raise ValueError("ID must be a UUID") from None
    if str(parsed) != value.lower():
        raise ValueError("ID must be a canonical UUID")
    return str(parsed)


def safe_url(value, *, base=False):
    if not isinstance(value, str) or any(ord(c) < 33 or ord(c) == 127 for c in value):
        raise ValueError("URL must be a valid HTTPS URL")
    try:
        parts = urlsplit(value)
        _ = parts.port
    except ValueError:
        raise ValueError("URL must be a valid HTTPS URL") from None
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
        or "\\" in value
        or (base and (parts.path not in ("", "/") or parts.query))
    ):
        raise ValueError(
            "URL must be HTTPS without credentials or fragments; base URL must be an origin"
        )
    return value.rstrip("/") if base else value


def positive(value, name):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a finite positive number")
    return value


def make_input(text=None, voice_name="Kore", segments=None):
    def nonempty(value, name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        if (
            name in ("speaker", "voice_name", "voiceName")
            and len(value.encode("utf-16-le")) // 2 > 100
        ):
            raise ValueError(f"{name} must be at most 100 UTF-16 code units")
        return value

    if segments is None:
        result = {
            "mode": "single",
            "text": nonempty(text, "text"),
            "voiceName": nonempty(voice_name, "voice_name"),
        }
        texts = [text]
    else:
        if text not in (None, ""):
            raise ValueError("Use either text or segments, not both")
        if not isinstance(segments, list) or not 1 <= len(segments) <= 1000:
            raise ValueError("segments must contain 1 to 1000 turns")
        turns, assignments = [], {}
        for segment in segments:
            if not isinstance(segment, dict) or set(segment) != {"speaker", "text", "voiceName"}:
                raise ValueError("Each segment requires only speaker, text and voiceName")
            turn = {key: nonempty(segment[key], key) for key in ("speaker", "text", "voiceName")}
            if len(turn["speaker"]) > 100:
                raise ValueError("speaker must be at most 100 characters")
            if turn["speaker"] in assignments and assignments[turn["speaker"]] != turn["voiceName"]:
                raise ValueError("Each speaker must use a consistent voiceName")
            assignments[turn["speaker"]] = turn["voiceName"]
            turns.append(turn)
        result = {"mode": "multi", "segments": turns}
        texts = [turn["text"] for turn in turns]
    if sum(len(text.encode("utf-16-le")) // 2 for text in texts) > 100_000:
        raise ValueError("Text must be 100,000 UTF-16 code units or fewer")
    if len(json.dumps({"input": result}, ensure_ascii=False).encode()) > 1024 * 1024:
        raise ValueError("Request body exceeds 1 MiB")
    return result


def retry_after(value, wall_clock=time.time):
    if not value:
        return 0.0
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            seconds = parsedate_to_datetime(value).timestamp() - wall_clock()
        except (TypeError, ValueError, OverflowError):
            return 0.0
    return max(0.0, seconds) if math.isfinite(seconds) else 0.0


def validate_wav(content, *, result_url=None, check_deadline=None):
    """Validate the complete RIFF container, not just frames understood by wave."""
    try:
        if not isinstance(content, bytes) or len(content) < 12:
            raise ValueError("Truncated RIFF header")
        if content[:4] != b"RIFF" or content[8:12] != b"WAVE":
            raise ValueError("Not a RIFF/WAVE file")
        end = struct.unpack_from("<I", content, 4)[0] + 8
        if end != len(content):
            raise ValueError("RIFF size does not match the downloaded bytes")
        offset, have_format, have_data = 12, False, False
        while offset < end:
            if check_deadline is not None:
                check_deadline()
            if end - offset < 8:
                raise ValueError("Truncated chunk header")
            name = content[offset : offset + 4]
            size = struct.unpack_from("<I", content, offset + 4)[0]
            start = offset + 8
            chunk_end = start + size
            next_chunk = chunk_end + (size & 1)
            if next_chunk > end:
                raise ValueError("Chunk or alignment pad exceeds RIFF bounds")
            if name == b"fmt ":
                if have_format or have_data or size not in (16, 18):
                    raise ValueError("Invalid or duplicate PCM format chunk")
                if struct.unpack_from("<HHIIHH", content, start) != (1, 1, 24000, 48000, 2, 16):
                    raise ValueError("Expected PCM 24000 Hz mono 16-bit audio")
                if size == 18 and struct.unpack_from("<H", content, start + 16)[0] != 0:
                    raise ValueError("Unexpected PCM format extension")
                have_format = True
            elif name == b"data":
                if not have_format or have_data or not size or size % 2:
                    raise ValueError("Invalid, empty or partial PCM data frames")
                have_data = True
            offset = next_chunk
        if not have_format or not have_data:
            raise ValueError("Missing format or data chunk")
        if check_deadline is not None:
            check_deadline()
    except (TypeError, ValueError, struct.error, OverflowError):
        raise ApiError(
            "Invalid or truncated WAV audio", code="invalid_audio", result_url=result_url
        ) from None


class V1Client:
    def __init__(
        self,
        *,
        api_key=None,
        base_url="https://flowspeech.io",
        timeout=300.0,
        http_client=None,
        download_client=None,
        poll_interval=5.0,
        max_retries=2,
        max_download_bytes=64 * 1024 * 1024,
        clock=time.monotonic,
        sleep=time.sleep,
        user_agent="flowspeech/0.2.0",
    ):
        key = api_key if api_key is not None else os.getenv("FLOWSPEECH_API_KEY")
        if not isinstance(key, str) or not key or any(ord(c) < 33 or ord(c) > 126 for c in key):
            raise ApiError(
                "FlowSpeech API key is required and must contain no whitespace",
                code="configuration",
            )
        self.api_key = key
        self.base_url = safe_url(base_url, base=True)
        self.timeout = positive(timeout, "timeout")
        self.poll_interval = max(5.0, positive(poll_interval, "poll_interval"))
        if type(max_retries) is not int or not 0 <= max_retries <= 10:
            raise ValueError("max_retries must be an integer between 0 and 10")
        if type(max_download_bytes) is not int or max_download_bytes <= 0:
            raise ValueError("max_download_bytes must be a positive integer")
        self.max_retries, self.max_download_bytes = max_retries, max_download_bytes
        self.clock, self.sleep = clock, sleep
        self._client = http_client or httpx.Client(trust_env=False)
        self._download = download_client or httpx.Client(trust_env=False)
        self._owns_client, self._owns_download = http_client is None, download_client is None
        self.user_agent = user_agent
        self._worker_lock = threading.Lock()
        self._workers = set()
        self._closed = False
        self._clients_closed = False

    def close(self):
        with self._worker_lock:
            self._closed = True
            for cancelled in self._workers:
                cancelled.set()
            cleanup = not self._workers and not self._clients_closed
            if cleanup:
                self._clients_closed = True
        if cleanup:
            self._close_owned_clients()

    def _close_owned_clients(self):
        try:
            if self._owns_client:
                self._client.close()
        finally:
            if self._owns_download:
                self._download.close()

    def _finish_worker(self, cancelled, slots):
        try:
            with self._worker_lock:
                self._workers.remove(cancelled)
                cleanup = self._closed and not self._workers and not self._clients_closed
                if cleanup:
                    self._clients_closed = True
            if cleanup:
                self._close_owned_clients()
        finally:
            slots.release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _remaining(self, deadline):
        remaining = deadline - self.clock()
        if remaining <= 0:
            raise ApiError(
                "FlowSpeech total deadline exceeded; recover using request_id or job_id",
                code="deadline_exceeded",
                retryable=True,
            )
        return remaining

    def _wait(self, seconds, deadline):
        if seconds >= self._remaining(deadline):
            raise ApiError(
                "Retry/poll wait exceeds total deadline", code="deadline_exceeded", retryable=True
            )
        self.sleep(seconds)
        self._remaining(deadline)

    def _http(self, method, url, deadline, *, body=None, request_id=None, download=False):
        # No executor queue: timed-out calls cannot leave a later POST waiting for a slot.
        completed = threading.Event()
        cancelled = threading.Event()
        outcome = []
        with self._worker_lock:
            if self._closed:
                raise ApiError("FlowSpeech client is closed", code="client_closed")
            if any(worker.is_set() for worker in self._workers):
                raise ApiError(
                    "A timed-out HTTP request is still finishing; recover with the original IDs",
                    code="client_busy",
                    retryable=True,
                )
            remaining = self._remaining(deadline)
            slots = _HTTP_WORKERS
            if not slots.acquire(blocking=False):
                raise ApiError(
                    "FlowSpeech HTTP worker limit reached; no request was queued",
                    code="client_busy",
                    retryable=True,
                )
            self._workers.add(cancelled)

        def perform():
            try:
                outcome.append(
                    self._http_once(
                        method,
                        url,
                        deadline,
                        body=body,
                        request_id=request_id,
                        download=download,
                        cancelled=cancelled,
                    )
                )
            except BaseException as exc:
                outcome.append(exc)
            finally:
                try:
                    self._finish_worker(cancelled, slots)
                except BaseException:
                    outcome[:] = [
                        ApiError("FlowSpeech HTTP cleanup failed", code="transport_error")
                    ]
                finally:
                    completed.set()

        try:
            worker = threading.Thread(target=perform, daemon=True, name="flowspeech-http")
            worker.start()
        except BaseException:
            self._finish_worker(cancelled, slots)
            raise
        try:
            if not completed.wait(min(remaining, self._remaining(deadline))):
                raise ApiError(
                    "FlowSpeech total deadline exceeded during HTTP request",
                    code="deadline_exceeded",
                    retryable=True,
                )
        except BaseException:
            cancelled.set()
            raise
        if isinstance(outcome[0], BaseException):
            raise outcome[0]
        self._remaining(deadline)
        return outcome[0]

    def _http_once(
        self, method, url, deadline, *, body=None, request_id=None, download=False, cancelled
    ):
        def check():
            if cancelled.is_set():
                raise ApiError("FlowSpeech HTTP request was stopped", code="deadline_exceeded")
            return self._remaining(deadline)

        headers = {
            "Accept": "audio/wav" if download else "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": self.user_agent,
        }
        if not download:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if body is not None:
            headers["Content-Type"] = "application/json"
        if request_id:
            headers["Idempotency-Key"] = request_id
        # Explicit Request bypasses injected client defaults, cookies and auth.
        budget = min(30.0, check())
        request = httpx.Request(
            method,
            url,
            headers=headers,
            content=body,
            extensions={"timeout": dict.fromkeys(("connect", "read", "write", "pool"), budget)},
        )
        client = self._download if download else self._client
        check()
        response = client.send(request, stream=True, follow_redirects=False, auth=None)
        limit = self.max_download_bytes if download else 2 * 1024 * 1024
        try:
            check()
            if 300 <= response.status_code < 400:
                return response.status_code, response.headers, b""
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise ApiError("Unexpected compressed response refused", code="invalid_response")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > limit):
                raise ApiError(
                    "Response exceeds size limit or has invalid Content-Length",
                    code="response_too_large",
                )
            data = bytearray()
            chunks = iter(response.iter_bytes())
            while True:
                check()
                try:
                    chunk = next(chunks)
                except StopIteration:
                    break
                check()
                if len(data) + len(chunk) > limit:
                    raise ApiError("Response exceeds size limit", code="response_too_large")
                data.extend(chunk)
            check()
            return response.status_code, response.headers, bytes(data)
        except httpx.TransportError as exc:
            raise _BodyReadError(response.status_code, response.headers) from exc
        finally:
            try:
                response.close()
            except httpx.TransportError:
                raise _BodyReadError(response.status_code, response.headers) from None

    def _error_token(self, value):
        if (
            isinstance(value, str)
            and self.api_key not in value
            and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value, flags=re.ASCII)
        ):
            return value
        return None

    def _api(self, method, path, deadline, *, body=None, request_id=None):
        for attempt in range(self.max_retries + 1):
            try:
                status, headers, content = self._http(
                    method, self.base_url + path, deadline, body=body, request_id=request_id
                )
            except httpx.TransportError as exc:
                status = exc.status if isinstance(exc, _BodyReadError) else None
                error = ApiError(
                    "FlowSpeech transport failed",
                    code="transport_error",
                    status_code=status,
                    retryable=status is None
                    or 200 <= status < 300
                    or status in (429, 500, 502, 503, 504),
                )
                delay = max(
                    self.poll_interval,
                    retry_after(
                        exc.headers.get("Retry-After") if isinstance(exc, _BodyReadError) else None
                    ),
                )
            else:
                if 300 <= status < 400:
                    raise ApiError(
                        "Unexpected API redirect refused",
                        status_code=status,
                        code="redirect_refused",
                    )
                try:
                    payload = json.loads(content)
                except (ValueError, UnicodeError):
                    payload = None
                if 200 <= status < 300:
                    if not isinstance(payload, dict):
                        raise ApiError(
                            "FlowSpeech returned invalid JSON object",
                            status_code=status,
                            code="invalid_response",
                        )
                    if "error" not in payload or "status" in payload:
                        return payload, max(
                            self.poll_interval, retry_after(headers.get("Retry-After"))
                        )
                details = payload.get("error", {}) if isinstance(payload, dict) else {}
                details = details if isinstance(details, dict) else {}
                error = ApiError(
                    f"FlowSpeech API returned HTTP {status}",
                    status_code=status,
                    code=self._error_token(details.get("code")) or "http_error",
                    retryable=(status == 429 and details.get("retryable") is not False)
                    or (status >= 500 and details.get("retryable") is True),
                    trace_id=self._error_token(payload.get("traceId"))
                    if isinstance(payload, dict)
                    else None,
                )
                delay = max(self.poll_interval, retry_after(headers.get("Retry-After")))
            if not error.retryable or attempt == self.max_retries:
                raise error
            self._wait(delay, deadline)

    def quota(self):
        payload, _ = self._api("GET", "/api/v1/quota", self.clock() + self.timeout)
        quota = payload.get("quota")
        if not isinstance(quota, dict) or any(
            type(quota.get(k)) not in (int, float) or not math.isfinite(quota[k]) or quota[k] < 0
            for k in ("remaining", "reserved", "available")
        ):
            raise ApiError("Malformed quota response", code="invalid_response")
        return payload

    def voices(self):
        payload, _ = self._api("GET", "/api/v1/voices", self.clock() + self.timeout)
        voices = payload.get("voices")
        if not isinstance(voices, list) or any(
            not isinstance(v, dict) or not isinstance(v.get("name"), str) or not v["name"]
            for v in voices
        ):
            raise ApiError("Malformed voices response", code="invalid_response")
        return voices

    @staticmethod
    def _job(job, *, job_id=None, request_id=None):
        try:
            actual_job_id = identifier(job.get("id"))
            actual_request_id = identifier(job.get("requestId"))
            if job_id is not None and actual_job_id != identifier(job_id):
                raise ValueError("Job ID mismatch")
            if request_id is not None and actual_request_id != identifier(request_id):
                raise ValueError("Request ID mismatch")
        except (ValueError, AttributeError):
            raise ApiError("Malformed or mismatched job ID", code="invalid_response") from None
        job["id"], job["requestId"] = actual_job_id, actual_request_id
        try:
            if not isinstance(job.get("status"), str) or job["status"] not in PENDING | TERMINAL:
                raise ApiError("Unknown job status", code="invalid_response", job_id=job["id"])
            usage = job.get("usage")
            if not isinstance(usage, dict) or any(
                type(usage.get(k)) is not int or usage[k] < 0
                for k in ("billableCharacters", "reservedCredits", "chargedCredits")
            ):
                raise ApiError("Malformed job usage", code="invalid_result")
            if "resultDeleted" in job and type(job["resultDeleted"]) is not bool:
                raise ApiError("Malformed resultDeleted flag", code="invalid_result")
            if job.get("error") is not None and (
                not isinstance(job["error"], dict)
                or not isinstance(job["error"].get("code"), str)
                or not job["error"]["code"]
            ):
                raise ApiError("Malformed job error", code="invalid_response")
            if job["status"] == "success":
                if job.get("resultDeleted") is True:
                    if job.get("result") is not None:
                        raise ApiError(
                            "Deleted recording has an unexpected result", code="invalid_result"
                        )
                else:
                    V1Client._result(job)
            return job
        except ApiError as exc:
            exc.job_id, exc.request_id = actual_job_id, actual_request_id
            raise

    def get_job(self, job_id, *, deadline=None):
        job_id = identifier(job_id)
        deadline = self.clock() + self.timeout if deadline is None else deadline
        job, _ = self._api("GET", "/api/v1/tts/jobs/" + job_id, deadline)
        return self._job(job, job_id=job_id)

    def find_job(self, request_id):
        request_id = identifier(request_id)
        job, _ = self._api(
            "GET", "/api/v1/tts/jobs?requestId=" + request_id, self.clock() + self.timeout
        )
        return self._job(job, request_id=request_id)

    def cancel_job(self, job_id):
        job_id = identifier(job_id)
        job, _ = self._api(
            "POST", "/api/v1/tts/jobs/" + job_id + "/cancel", self.clock() + self.timeout
        )
        return self._job(job, job_id=job_id)

    @staticmethod
    def _result(job):
        if job.get("resultDeleted") is True:
            raise ApiError("Recording was deleted; result is unavailable", code="result_deleted")
        result = job.get("result")
        if not isinstance(result, dict):
            raise ApiError("Successful job is missing its result", code="invalid_result")
        if (
            result.get("mimeType") != "audio/wav"
            or type(result.get("sampleRate")) is not int
            or result.get("sampleRate") != 24000
            or result.get("access") != "link"
            or type(result.get("channels")) is not int
            or result["channels"] != 1
            or type(result.get("bitsPerSample")) is not int
            or result.get("bitsPerSample") != 16
            or not isinstance(job.get("usage"), dict)
            or any(
                type(job["usage"].get(k)) is not int
                or not math.isfinite(job["usage"][k])
                or job["usage"][k] < 0
                for k in ("billableCharacters", "reservedCredits", "chargedCredits")
            )
        ):
            raise ApiError("Malformed WAV result metadata or usage", code="invalid_result")
        try:
            safe_url(result.get("url"))
        except ValueError:
            raise ApiError("Unsafe result URL refused", code="invalid_result") from None
        return result

    def download_audio(self, url, *, deadline=None):
        deadline = self.clock() + self.timeout if deadline is None else deadline
        safe_url(url)
        for attempt in range(self.max_retries + 1):
            current = url
            try:
                for redirect in range(6):
                    status, headers, content = self._http("GET", current, deadline, download=True)
                    if status in (301, 302, 303, 307, 308):
                        if redirect == 5 or not headers.get("Location"):
                            raise ApiError(
                                "Audio redirect limit or missing Location", code="download_failed"
                            )
                        try:
                            current = safe_url(urljoin(current, headers["Location"]))
                        except ValueError:
                            raise ApiError(
                                "Unsafe audio redirect refused",
                                code="download_failed",
                                result_url=url,
                            ) from None
                        continue
                    break
                if status != 200:
                    error = ApiError(
                        f"Audio download returned HTTP {status}; retry the existing URL",
                        status_code=status,
                        code="download_failed",
                        retryable=status == 429 or status >= 500,
                        result_url=url,
                    )
                else:
                    validate_wav(
                        content, result_url=url, check_deadline=lambda: self._remaining(deadline)
                    )
                    return content
                delay = max(self.poll_interval, retry_after(headers.get("Retry-After")))
            except httpx.TransportError as exc:
                error = ApiError(
                    "Audio transport failed; retry the existing URL",
                    code="download_failed",
                    retryable=not isinstance(exc, _BodyReadError)
                    or 200 <= exc.status < 300
                    or exc.status in (429, 500, 502, 503, 504),
                    result_url=url,
                )
                delay = max(
                    self.poll_interval,
                    retry_after(
                        exc.headers.get("Retry-After") if isinstance(exc, _BodyReadError) else None
                    ),
                )
            if not error.retryable or attempt == self.max_retries:
                raise error
            self._wait(delay, deadline)

    def generate(self, input_data, *, request_id):
        if not isinstance(input_data, dict):
            raise ValueError("input must be an object")
        if input_data.get("mode") == "single" and set(input_data) == {"mode", "text", "voiceName"}:
            input_data = make_input(input_data["text"], input_data["voiceName"])
        elif input_data.get("mode") == "multi" and set(input_data) == {"mode", "segments"}:
            input_data = make_input(segments=input_data["segments"])
        else:
            raise ValueError("Unsupported input fields or mode")
        request_id = identifier(request_id)
        deadline, job_id, result_url = self.clock() + self.timeout, None, None
        body = json.dumps({"input": input_data}, ensure_ascii=False, separators=(",", ":")).encode()
        try:
            job, delay = self._api(
                "POST", "/api/v1/tts/jobs", deadline, body=body, request_id=request_id
            )
            self._job(job, request_id=request_id)
            job_id = job["id"]
            while job["status"] in PENDING:
                self._wait(delay, deadline)
                job, delay = self._api("GET", "/api/v1/tts/jobs/" + job_id, deadline)
                self._job(job, job_id=job_id, request_id=request_id)
            if job["status"] != "success":
                details = job.get("error") or {}
                raise ApiError(
                    f"FlowSpeech job {job['status']}",
                    code=(
                        self._error_token(details.get("code"))
                        if isinstance(details, dict)
                        else None
                    )
                    or job["status"],
                )
            result = self._result(job)
            result_url = result["url"]
            audio = self.download_audio(result_url, deadline=deadline)
            return job, audio, request_id
        except ApiError as exc:
            exc.request_id, exc.job_id = request_id, job_id or exc.job_id
            exc.result_url = result_url or exc.result_url
            raise
