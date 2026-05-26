"""
Interactive PTY into the per-session microVM via
InvokeAgentRuntimeCommandWithWebSocketStream.

Connects the local terminal to a remote bash PTY in the microVM that owns
the given Anthropic session id. Same session id => same microVM (session
affinity), so you can attach a shell to a session that the agent is
actively using and watch /workspace change in real time.

Wire protocol:
    [1 byte channel id][payload bytes]   MAX_FRAME_SIZE = 65536

    0x00 STDIN   client -> server  raw bytes (keystrokes)
    0x01 STDOUT  server -> client  raw bytes
    0x02 STDERR  server -> client  raw bytes
    0x03 STATUS  server -> client  metav1.Status JSON, one per WS frame
    0x04 RESIZE  client -> server  JSON {"width":N,"height":N}
    0xFF CLOSE   either           empty

Subprotocol header: v1.command.agentcore.aws.dev (sent as a regular
header so botocore SigV4 signs it; kwarg `subprotocols=` is rejected by
the endpoint because it does not echo Sec-WebSocket-Protocol back).

Usage:
    python3 tui_shell.py --runtime-session-id sesn_...
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import select
import signal
import struct
import sys
import termios
import threading
import tty
import uuid
from urllib.parse import quote, urlparse

import boto3
import websocket
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

DEFAULT_REGION = "us-west-2"
SUBPROTOCOL = "v1.command.agentcore.aws.dev"

CH_STDIN = 0x00
CH_STDOUT = 0x01
CH_STDERR = 0x02
CH_STATUS = 0x03
CH_RESIZE = 0x04
CH_CLOSE = 0xFF


def default_endpoint(region: str) -> str:
    return f"https://bedrock-agentcore.{region}.amazonaws.com"


def sign_ws_url(
    endpoint: str,
    agent_arn: str,
    region: str,
    runtime_session_id: str,
    command_session_id: str,
    qualifier: str = "DEFAULT",
) -> tuple[str, list[str]]:
    creds = boto3.Session(region_name=region).get_credentials().get_frozen_credentials()
    host = urlparse(endpoint).hostname
    encoded_arn = quote(agent_arn, safe="")
    path = f"/runtimes/{encoded_arn}/ws/commands"

    params = {"qualifier": qualifier, "commandSessionId": command_session_id}
    qs = "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in sorted(params.items()))
    url = f"https://{host}{path}?{qs}"

    headers = {
        "Host": host,
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": runtime_session_id,
        "Sec-WebSocket-Protocol": SUBPROTOCOL,
    }
    req = AWSRequest(method="GET", url=url, headers=headers)
    SigV4Auth(creds, "bedrock-agentcore", region).add_auth(req)

    ws_url = url.replace("https://", "wss://")
    header_list = [f"{k}: {v}" for k, v in req.headers.items()]
    return ws_url, header_list


def get_term_size() -> tuple[int, int]:
    try:
        s = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, b"\0" * 8)
        rows, cols, _, _ = struct.unpack("HHHH", s)
        return cols or 80, rows or 24
    except Exception:
        return 80, 24


def send_resize(ws: websocket.WebSocket, cols: int, rows: int) -> None:
    payload = json.dumps({"width": cols, "height": rows}).encode()
    ws.send_binary(bytes([CH_RESIZE]) + payload)


def reader_thread(ws: websocket.WebSocket, stop: threading.Event, exit_status: dict) -> None:
    try:
        while not stop.is_set():
            try:
                opcode, data = ws.recv_data()
            except websocket.WebSocketConnectionClosedException:
                break
            except websocket.WebSocketTimeoutException:
                continue

            if opcode == 0x8:  # CLOSE control
                break
            if opcode != 0x2 or not data:
                continue

            channel = data[0]
            payload = data[1:]
            if channel == CH_STDOUT:
                os.write(sys.stdout.fileno(), payload)
            elif channel == CH_STDERR:
                os.write(sys.stderr.fileno(), payload)
            elif channel == CH_STATUS:
                try:
                    st = json.loads(payload.decode("utf-8", "replace"))
                except json.JSONDecodeError:
                    st = {"raw": payload.decode("utf-8", "replace")}
                meta = st.get("metadata") or {}
                exit_status["status"] = st
                if st.get("status") == "Failure" or "code" in st or "exitCode" in meta:
                    break
            elif channel == CH_CLOSE:
                break
    finally:
        stop.set()


def run_shell(ws_url: str, headers: list[str]) -> int:
    ws = websocket.create_connection(ws_url, header=headers, timeout=60)
    ws.settimeout(0.5)

    cols, rows = get_term_size()
    send_resize(ws, cols, rows)

    in_fd = sys.stdin.fileno()
    is_tty = os.isatty(in_fd)
    old_attrs = termios.tcgetattr(in_fd) if is_tty else None
    if is_tty:
        tty.setraw(in_fd)

    stop = threading.Event()
    exit_status: dict = {}

    def handle_winch(_signum, _frame):
        try:
            c, r = get_term_size()
            send_resize(ws, c, r)
        except Exception:  # noqa: BLE001, S110 - resize is best-effort
            pass

    prev_winch = signal.signal(signal.SIGWINCH, handle_winch) if is_tty else None
    reader = threading.Thread(target=reader_thread, args=(ws, stop, exit_status), daemon=True)
    reader.start()

    try:
        while not stop.is_set():
            r, _, _ = select.select([in_fd], [], [], 0.1)
            if in_fd in r:
                try:
                    chunk = os.read(in_fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                try:
                    ws.send_binary(bytes([CH_STDIN]) + chunk)
                except websocket.WebSocketConnectionClosedException:
                    break
    finally:
        stop.set()
        if is_tty and old_attrs is not None:
            termios.tcsetattr(in_fd, termios.TCSADRAIN, old_attrs)
        if prev_winch is not None:
            signal.signal(signal.SIGWINCH, prev_winch)
        try:
            ws.send_binary(bytes([CH_CLOSE]))
        except Exception:  # noqa: BLE001, S110 - best-effort close
            pass
        try:
            ws.close()
        except Exception:  # noqa: BLE001, S110 - best-effort close
            pass
        reader.join(timeout=1.0)

    if exit_status.get("status"):
        st = exit_status["status"]
        sys.stderr.write(f"\n[exit] {json.dumps(st)}\n")
        return int(st.get("code") or 0) if st.get("status") == "Failure" else 0
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--agent-arn", default=os.environ.get("AGENTCORE_RUNTIME_ARN"))
    p.add_argument(
        "--runtime-session-id",
        required=True,
        help="Anthropic session id (sesn_...); reused as runtimeSessionId",
    )
    p.add_argument("--region", default=os.environ.get("AGENTCORE_REGION", DEFAULT_REGION))
    p.add_argument("--qualifier", default="DEFAULT")
    p.add_argument(
        "--command-session-id",
        default=None,
        help="reuse to reconnect to an existing PTY",
    )
    args = p.parse_args()

    if not args.agent_arn:
        print("--agent-arn or AGENTCORE_RUNTIME_ARN required", file=sys.stderr)
        return 2

    rsid = args.runtime_session_id
    if len(rsid) < 33:
        rsid = rsid + "-" + "0" * (33 - len(rsid) - 1)

    csid = args.command_session_id or str(uuid.uuid4())

    ws_url, headers = sign_ws_url(
        endpoint=default_endpoint(args.region),
        agent_arn=args.agent_arn,
        region=args.region,
        runtime_session_id=rsid,
        command_session_id=csid,
        qualifier=args.qualifier,
    )

    sys.stderr.write(f"[runtimeSessionId] {rsid}\n")
    sys.stderr.write(f"[commandSessionId] {csid}\n")
    sys.stderr.write("[connecting...]\n")

    try:
        return run_shell(ws_url, headers)
    except websocket.WebSocketBadStatusException as e:
        sys.stderr.write(f"[upgrade failed] HTTP {e.status_code}\n")
        rid = None
        if getattr(e, "resp_headers", None):
            rid = e.resp_headers.get("x-amz-request-id") or e.resp_headers.get("X-Amz-Request-Id")
        if rid:
            sys.stderr.write(f"[request-id] {rid}\n")
        if getattr(e, "resp_body", None):
            sys.stderr.write(f"[body] {e.resp_body!r}\n")
        return 2
    except Exception as e:
        sys.stderr.write(f"[error] {type(e).__name__}: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
