from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

SERVER_PATH = (
    Path(__file__).resolve().parent.parent
    / "claude_agent_sdk"
    / "site_reliability_agent"
    / "sre_mcp_server.py"
)
_SPEC = importlib.util.spec_from_file_location("sre_mcp_server", SERVER_PATH)
assert _SPEC and _SPEC.loader
sre_mcp_server = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sre_mcp_server)


def _mock_proc(stdout: bytes = b"ok\n", stderr: bytes = b"", returncode: int = 0) -> AsyncMock:
    proc = AsyncMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    return proc


@pytest.mark.parametrize(
    ("command", "expected_args"),
    [
        (
            "docker-compose -f config/docker-compose.yml up -d api-server",
            ["docker-compose", "-f", "config/docker-compose.yml", "up", "-d", "api-server"],
        ),
        (
            "docker-compose -f config/docker-compose.yml ps",
            ["docker-compose", "-f", "config/docker-compose.yml", "ps"],
        ),
        (
            "docker-compose -f config/docker-compose.yml logs api-server --tail=50",
            [
                "docker-compose",
                "-f",
                "config/docker-compose.yml",
                "logs",
                "api-server",
                "--tail=50",
            ],
        ),
        (
            "docker-compose --file=config/docker-compose.yml -p sre restart api-server",
            [
                "docker-compose",
                "--file=config/docker-compose.yml",
                "-p",
                "sre",
                "restart",
                "api-server",
            ],
        ),
        (
            "docker-compose -fconfig/docker-compose.yml down",
            ["docker-compose", "-fconfig/docker-compose.yml", "down"],
        ),
        (
            "docker compose -f config/docker-compose.yml up -d api-server",
            ["docker", "compose", "-f", "config/docker-compose.yml", "up", "-d", "api-server"],
        ),
        (
            "docker ps",
            ["docker", "ps"],
        ),
        (
            "docker logs api-server --tail=20",
            ["docker", "logs", "api-server", "--tail=20"],
        ),
    ],
)
def test_run_shell_command_allows_documented_commands(
    command: str, expected_args: list[str]
) -> None:
    proc = _mock_proc()
    with patch.object(asyncio, "create_subprocess_exec", AsyncMock(return_value=proc)) as mock_exec:
        result = asyncio.run(sre_mcp_server.run_shell_command(command))

    assert result["isError"] is False
    mock_exec.assert_called_once()
    assert list(mock_exec.call_args.args) == expected_args


@pytest.mark.parametrize(
    "command",
    [
        "docker compose exec api-server sh",
        "docker compose -f config/docker-compose.yml run --rm api-server sh",
        "docker compose -f ../docker-compose.yml up -d",
        "docker compose",
        "docker-compose",
        "docker-compose -f config/docker-compose.yml exec api-server sh",
        "docker-compose -f ../docker-compose.yml up -d",
        "docker-compose --file=/tmp/evil.yml up -d",
        "docker-compose -f",
        "docker -H tcp://127.0.0.1:2375 ps",
        "docker run --rm alpine sh",
        "kubectl rollout restart deployment/api-server",
    ],
)
def test_run_shell_command_rejects_disallowed_commands(command: str) -> None:
    with patch.object(asyncio, "create_subprocess_exec", AsyncMock()) as mock_exec:
        result = asyncio.run(sre_mcp_server.run_shell_command(command))

    assert result["isError"] is True
    mock_exec.assert_not_called()
