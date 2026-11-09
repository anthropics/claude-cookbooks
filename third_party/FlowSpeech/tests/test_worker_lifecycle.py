"""Bounded synchronous HTTP workers: offline, finite gates, no queued paid work."""

import threading

import flowspeech_v1 as module
import httpx
import pytest
from test_v1_contract import INPUT, JOB, REQUEST, job, response, wav_bytes


def test_worker_releases_original_semaphore_after_global_replacement(held, monkeypatch):
    transport, http = held
    original = threading.BoundedSemaphore(1)
    replacement = threading.BoundedSemaphore(1)
    monkeypatch.setattr(module, "_HTTP_WORKERS", original)
    speech = client(http)
    try:
        with pytest.raises(module.ApiError):
            speech.voices()
        assert not original.acquire(blocking=False)
        monkeypatch.setattr(module, "_HTTP_WORKERS", replacement)
        transport.finish()
        for slots in (original, replacement):
            assert slots.acquire(blocking=False)
            assert not slots.acquire(blocking=False)
            slots.release()
        assert not speech._workers
    finally:
        transport.finish()
        speech.close()


def test_interrupted_wait_marks_worker_abandoned_and_blocks_reentry(held, monkeypatch):
    transport, http = held
    real_event = threading.Event
    entered = real_event()
    original_handle = transport.handle_request

    def handle(request):
        entered.set()
        return original_handle(request)

    transport.handle_request = handle

    class InterruptedWait(threading.Event):
        def wait(self, timeout=None):
            assert entered.wait(1)
            raise KeyboardInterrupt

    events = [InterruptedWait()]

    def event():
        return events.pop() if events else real_event()

    speech = client(http)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(module.threading, "Event", event)
            with pytest.raises(KeyboardInterrupt):
                speech.generate(INPUT, request_id=REQUEST)
        with pytest.raises(module.ApiError) as busy:
            speech.generate(INPUT, request_id=REQUEST)
        assert busy.value.code == "client_busy" and busy.value.request_id == REQUEST
        assert len(transport.calls) == 1
    finally:
        transport.finish()
        speech.close()


def test_owned_cleanup_failure_still_closes_other_client(monkeypatch):
    class BrokenClose(httpx.MockTransport):
        def close(self):
            raise httpx.ReadError("synthetic cleanup failure")

    api = httpx.Client(transport=BrokenClose(lambda _: response(job())))
    audio = httpx.Client(transport=httpx.MockTransport(lambda _: response(job())))
    clients = iter([api, audio])
    monkeypatch.setattr(module.httpx, "Client", lambda **kwargs: next(clients))
    speech = module.V1Client(api_key="test-only")
    with pytest.raises(httpx.ReadError):
        speech.close()
    assert api.is_closed and audio.is_closed
    assert speech._clients_closed and not speech._workers


class HeldTransport(httpx.BaseTransport):
    def __init__(self):
        self.release = threading.Event()
        self.calls = []
        self.threads = []
        self.responses = []
        self.closed_while_active = False
        self.closed = False
        self.active = 0

    def handle_request(self, request):
        self.calls.append(request)
        self.threads.append(threading.current_thread())
        self.active += 1
        try:
            assert self.release.wait(2), "Test gate must be released"
            result = (
                response({"voices": []})
                if request.url.path.endswith("/voices")
                else response(job())
            )
            self.responses.append(result)
            return result
        finally:
            self.active -= 1

    def close(self):
        self.closed_while_active |= bool(self.active)
        self.closed = True

    def finish(self):
        self.release.set()
        for worker in self.threads:
            worker.join(2)
            assert not worker.is_alive()


@pytest.fixture
def held():
    transport = HeldTransport()
    http = httpx.Client(transport=transport)
    yield transport, http
    transport.finish()
    http.close()


def client(http, **kwargs):
    return module.V1Client(
        api_key="test-only",
        http_client=http,
        download_client=http,
        timeout=0.04,
        **kwargs,
    )


def test_timeout_blocks_reentry_until_worker_cleanup_and_retains_request_id(held):
    transport, http = held
    speech = client(http)
    try:
        with pytest.raises(module.ApiError) as first:
            speech.generate(INPUT, request_id=REQUEST)
        assert first.value.code == "deadline_exceeded" and first.value.request_id == REQUEST
        assert len(transport.calls) == 1
        for _ in range(3):
            with pytest.raises(module.ApiError) as busy:
                speech.generate(INPUT, request_id=REQUEST)
            assert busy.value.code == "client_busy" and busy.value.request_id == REQUEST
        assert len(transport.calls) == 1
        transport.finish()
        assert transport.responses[0].is_closed
        assert not speech._workers
        assert speech.voices() == []
        assert [r.method for r in transport.calls] == ["POST", "GET"]
        assert not http.is_closed
    finally:
        transport.finish()
        speech.close()
    assert not http.is_closed and not transport.closed_while_active


def test_module_capacity_bounds_workers_across_new_clients_without_queue(held, monkeypatch):
    transport, http = held
    monkeypatch.setattr(module, "_HTTP_WORKERS", threading.BoundedSemaphore(2))
    clients = [client(http) for _ in range(5)]
    try:
        for speech in clients[:2]:
            with pytest.raises(module.ApiError) as timed_out:
                speech.generate(INPUT, request_id=REQUEST)
            assert timed_out.value.code == "deadline_exceeded"
        for speech in clients[2:]:
            with pytest.raises(module.ApiError) as busy:
                speech.generate(INPUT, request_id=REQUEST)
            assert busy.value.code == "client_busy"
        assert len(transport.calls) == 2
        transport.finish()
        assert len(transport.calls) == 2
        assert clients[-1].voices() == []
        assert len(transport.calls) == 3
    finally:
        transport.finish()
        for speech in clients:
            speech.close()


def test_healthy_concurrent_calls_remain_supported(held):
    from concurrent.futures import ThreadPoolExecutor

    transport, http = held
    entered = threading.Barrier(3)
    original = transport.handle_request

    def synchronized(request):
        entered.wait(timeout=2)
        return original(request)

    transport.handle_request = synchronized
    speech = module.V1Client(api_key="test-only", http_client=http, download_client=http, timeout=1)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            calls = [pool.submit(speech.voices) for _ in range(2)]
            try:
                entered.wait(timeout=2)
            finally:
                transport.release.set()
            assert [call.result(timeout=2) for call in calls] == [[], []]
        assert len(transport.calls) == 2 and not speech._workers
    finally:
        transport.finish()
        speech.close()
    assert not http.is_closed


def test_close_defers_owned_clients_and_never_closes_borrowed_clients(held, monkeypatch):
    transport, borrowed = held
    owned_download = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    monkeypatch.setattr(module.httpx, "Client", lambda **kwargs: owned_download)
    speech = module.V1Client(api_key="test-only", http_client=borrowed, timeout=0.04)
    try:
        with pytest.raises(module.ApiError):
            speech.generate(INPUT, request_id=REQUEST)
        speech.close()
        assert not owned_download.is_closed and not borrowed.is_closed
        with pytest.raises(module.ApiError) as closed:
            speech.voices()
        assert closed.value.code == "client_closed" and len(transport.calls) == 1
        transport.finish()
        assert owned_download.is_closed and not borrowed.is_closed
        assert not transport.closed_while_active
    finally:
        transport.finish()
        speech.close()


def test_owned_http_transport_is_not_closed_under_inflight_request(held, monkeypatch):
    transport, http = held
    monkeypatch.setattr(module.httpx, "Client", lambda **kwargs: http)
    speech = module.V1Client(api_key="test-only", timeout=0.04)
    try:
        with pytest.raises(module.ApiError):
            speech.generate(INPUT, request_id=REQUEST)
        speech.close()
        assert not http.is_closed and transport.active == 1
        transport.finish()
        assert http.is_closed and not transport.closed_while_active
    finally:
        transport.finish()
        speech.close()


def test_delayed_worker_start_after_timeout_cannot_send_a_post(held, monkeypatch):
    transport, http = held
    real_thread = threading.Thread
    start_gate = threading.Event()
    workers = []

    def delayed_thread(*, target, **kwargs):
        def delayed():
            assert start_gate.wait(2)
            target()

        worker = real_thread(target=delayed, **kwargs)
        workers.append(worker)
        return worker

    monkeypatch.setattr(module.threading, "Thread", delayed_thread)
    speech = client(http)
    try:
        with pytest.raises(module.ApiError) as caught:
            speech.generate(INPUT, request_id=REQUEST)
        assert caught.value.code == "deadline_exceeded" and caught.value.request_id == REQUEST
        assert transport.calls == []
    finally:
        start_gate.set()
        for worker in workers:
            worker.join(2)
            assert not worker.is_alive()
        speech.close()
    assert transport.calls == [] and not speech._workers and not http.is_closed


@pytest.mark.parametrize("failure", ["construct", "start"])
def test_worker_start_failure_releases_both_admission_slots(held, monkeypatch, failure):
    transport, http = held
    semaphore = threading.BoundedSemaphore(1)
    monkeypatch.setattr(module, "_HTTP_WORKERS", semaphore)
    speech = client(http)

    class CannotStart:
        def __init__(self, **kwargs):
            if failure == "construct":
                raise RuntimeError("synthetic thread construction failure")

        def start(self):
            raise RuntimeError("synthetic thread start failure")

    with monkeypatch.context() as patch:
        patch.setattr(module.threading, "Thread", CannotStart)
        with pytest.raises(RuntimeError):
            speech.voices()
    assert not speech._workers and transport.calls == []
    assert semaphore.acquire(blocking=False)
    semaphore.release()
    transport.release.set()
    assert speech.voices() == []
    speech.close()


def test_slow_download_timeout_retains_recovery_and_rejects_reentry():
    gate = threading.Event()
    workers = []
    responses = []
    calls = []

    class SlowAudio(httpx.SyncByteStream):
        def __iter__(self):
            workers.append(threading.current_thread())
            yield wav_bytes()[:44]
            assert gate.wait(2)
            yield wav_bytes()[44:]

    def handle(request):
        calls.append(request)
        result = (
            response(job()) if request.method == "POST" else httpx.Response(200, stream=SlowAudio())
        )
        responses.append(result)
        return result

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        speech = client(http)
        try:
            with pytest.raises(module.ApiError) as timed_out:
                speech.generate(INPUT, request_id=REQUEST)
            assert timed_out.value.request_id == REQUEST and timed_out.value.job_id == JOB
            assert timed_out.value.result_url
            with pytest.raises(module.ApiError) as busy:
                speech.download_audio(timed_out.value.result_url)
            assert busy.value.code == "client_busy"
            assert [r.method for r in calls] == ["POST", "GET"]
        finally:
            gate.set()
            for worker in workers:
                worker.join(2)
                assert not worker.is_alive()
            speech.close()
        assert all(result.is_closed for result in responses)
        assert not http.is_closed


@pytest.mark.parametrize("status", [200, 401, 403, 429, 503])
def test_close_transport_failure_preserves_status_and_cooldown(factory, status):
    class BrokenClose(httpx.SyncByteStream):
        def __iter__(self):
            yield b"{}"

        def close(self):
            raise httpx.ReadError("synthetic close failure")

    first = httpx.Response(status, headers={"Retry-After": "17"}, stream=BrokenClose())
    speech, calls, _, clock = factory([first, response(job())])
    if status in (401, 403):
        with pytest.raises(module.ApiError) as error:
            speech.generate(INPUT, request_id=REQUEST)
        assert error.value.status_code == status and error.value.request_id == REQUEST
        assert len(calls) == 1 and clock.waits == []
    else:
        speech.generate(INPUT, request_id=REQUEST)
        assert clock.waits == [17]
        assert calls[0].content == calls[1].content
        assert calls[0].headers["Idempotency-Key"] == calls[1].headers["Idempotency-Key"] == REQUEST
