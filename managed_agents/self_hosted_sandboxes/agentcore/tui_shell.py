"""
Interactive PTY into the per-session microVM via the AgentCore
``InvokeAgentRuntimeCommandShell`` API (GA).

Connects the local terminal to a remote bash PTY in the microVM that owns
the given Anthropic session id. Same session id => same microVM (session
affinity), so you can attach a shell to a session the agent is actively
using and watch /workspace change in real time.

This uses the official ``bedrock-agentcore`` SDK's
``AgentCoreRuntimeClient.open_shell()`` instead of hand-rolling the
WebSocket + SigV4 + binary framing. The SDK speaks the same wire protocol
(1-byte channel prefix per frame: STDIN/STDOUT/STDERR/STATUS/RESIZE/
HEARTBEAT/CLOSE) and adds reconnection with output replay.

``open_shell`` returns an *async* context manager, so the client runs on
asyncio: one task pumps local stdin into the shell, the main loop async-
iterates output frames onto the local terminal.

Reconnect: pass the same ``--runtime-session-id`` AND ``--shell-id`` to
re-attach to the same PTY after a disconnect (the service replays up to
256 KB of recent output). ``shell_id`` names the PTY; ``session_id`` routes
to the VM that hosts it - you need both.

Usage:
    python3 tui_shell.py --runtime-session-id sesn_...
    python3 tui_shell.py --runtime-session-id sesn_... --shell-id my-shell   # reconnect
"""

from __future__ import annotations

import argparse
import asyncio
import fcntl
import os
import signal
import struct
import sys
import termios
import tty

import boto3
from bedrock_agentcore.runtime import (
    AgentCoreRuntimeClient,
    ReconnectConfig,
    ShellChannel,
)

DEFAULT_REGION = "us-west-2"


def get_term_size() -> tuple[int, int]:
    try:
        s = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, b"\0" * 8)
        rows, cols, _, _ = struct.unpack("HHHH", s)
        return cols or 80, rows or 24
    except Exception:  # noqa: BLE001 - fall back to a sane default
        return 80, 24


async def pump_stdin(shell, stop: asyncio.Event) -> None:
    """Forward local stdin bytes to the remote shell until ``stop`` is set.

    Reads the raw tty fd via the event loop so keystrokes (including Ctrl+C,
    arrow keys, pastes) stream straight through to the PTY.
    """
    loop = asyncio.get_running_loop()
    in_fd = sys.stdin.fileno()
    queue: asyncio.Queue[bytes] = asyncio.Queue()

    def on_readable() -> None:
        try:
            chunk = os.read(in_fd, 4096)
        except OSError:
            chunk = b""
        queue.put_nowait(chunk)

    loop.add_reader(in_fd, on_readable)
    try:
        while not stop.is_set():
            chunk = await queue.get()
            if not chunk:
                break
            await shell.send_bytes(chunk)
    finally:
        loop.remove_reader(in_fd)
        stop.set()


async def run_shell(
    runtime_arn: str,
    region: str,
    runtime_session_id: str,
    shell_id: str | None,
    qualifier: str,
) -> int:
    client = AgentCoreRuntimeClient(region=region, session=boto3.Session(region_name=region))
    reconnect = ReconnectConfig(max_retries=5, base_delay=0.5)

    in_fd = sys.stdin.fileno()
    is_tty = os.isatty(in_fd)
    old_attrs = termios.tcgetattr(in_fd) if is_tty else None

    async with client.open_shell(
        runtime_arn,
        session_id=runtime_session_id,
        shell_id=shell_id,
        endpoint_name=qualifier,
        reconnect_config=reconnect,
    ) as shell:
        sys.stderr.write(f"[shellId] {shell.shell_id}\n")
        sys.stderr.write(f"[reconnected] {shell.reconnected}\n")
        sys.stderr.write("[connected] type `exit` to end the shell\n")

        # Raw-mode the local tty so keystrokes pass through unbuffered, and
        # mirror the local window size to the remote PTY now + on SIGWINCH.
        if is_tty:
            tty.setraw(in_fd)
        cols, rows = get_term_size()
        await shell.resize(cols, rows)

        loop = asyncio.get_running_loop()
        if is_tty:

            def on_winch() -> None:
                c, r = get_term_size()
                loop.create_task(shell.resize(c, r))

            loop.add_signal_handler(signal.SIGWINCH, on_winch)

        stop = asyncio.Event()
        stdin_task = asyncio.create_task(pump_stdin(shell, stop))

        # The SDK iterator surfaces only STDOUT/STDERR/STATUS frames: it
        # swallows HEARTBEAT, auto-reconnects on transient drops, parses the
        # exit code into shell.exit_code, and raises StopAsyncIteration when
        # the shell exits (CLOSE / terminal STATUS). So we just render output
        # and read shell.exit_code after the loop.
        try:
            async for frame in shell:
                if frame.channel == ShellChannel.STDOUT:
                    os.write(sys.stdout.fileno(), frame.payload)
                elif frame.channel == ShellChannel.STDERR:
                    os.write(sys.stderr.fileno(), frame.payload)
        finally:
            stop.set()
            stdin_task.cancel()
            if is_tty:
                try:
                    loop.remove_signal_handler(signal.SIGWINCH)
                except (ValueError, NotImplementedError):
                    pass
                if old_attrs is not None:
                    termios.tcsetattr(in_fd, termios.TCSADRAIN, old_attrs)

        if shell.kicked:
            sys.stderr.write("\n[kicked] another client attached to this shell_id\n")
        return shell.exit_code or 0


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
        "--shell-id",
        default=None,
        help="reuse with the same --runtime-session-id to reconnect to an existing PTY",
    )
    args = p.parse_args()

    if not args.agent_arn:
        print("--agent-arn or AGENTCORE_RUNTIME_ARN required", file=sys.stderr)
        return 2

    # AgentCore runtimeSessionId must be >= 33 chars; pad if the Anthropic id
    # is shorter (matches tui_exec.py).
    rsid = args.runtime_session_id
    if len(rsid) < 33:
        rsid = rsid + "-" + "0" * (33 - len(rsid) - 1)

    sys.stderr.write(f"[runtimeSessionId] {rsid}\n")
    sys.stderr.write("[connecting...]\n")

    try:
        return asyncio.run(
            run_shell(
                runtime_arn=args.agent_arn,
                region=args.region,
                runtime_session_id=rsid,
                shell_id=args.shell_id,
                qualifier=args.qualifier,
            )
        )
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # noqa: BLE001 - surface a clean operator error
        sys.stderr.write(f"\n[error] {type(e).__name__}: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
