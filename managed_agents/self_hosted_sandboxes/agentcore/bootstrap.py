"""
One-time bootstrap: create the self-hosted environment and an agent.

Anthropic does not (currently) expose environment-key generation through the
Python SDK — it lives only in the Console. This script creates the
environment + agent and then asks you to paste the env key it prints. The
result lands in bootstrap.config so subsequent steps never need
ANTHROPIC_API_KEY again.

The API key only lives on the host running this script. The host poller and
the AgentCore microVM run on the environment key alone.

Usage:
    pip install -r requirements-host.txt
    export ANTHROPIC_API_KEY=sk-ant-api03-...
    python3 bootstrap.py

Idempotent: an existing bootstrap.config short-circuits.
"""

import os
import sys
import webbrowser
from pathlib import Path

import anthropic

CONFIG_PATH = Path(__file__).parent / "bootstrap.config"


def short_circuit_if_exists() -> None:
    if CONFIG_PATH.exists():
        print(f"[bootstrap] {CONFIG_PATH} already exists; nothing to do")
        print("[bootstrap] delete it (and Console resources) to recreate")
        sys.exit(0)


def write_config(values: dict) -> None:
    body = "".join(f"export {k}={v}\n" for k, v in values.items())
    CONFIG_PATH.write_text(body)
    CONFIG_PATH.chmod(0o600)
    print(f"\n[bootstrap] wrote {CONFIG_PATH} (chmod 600)")


def prompt_for_env_key(environment_id: str) -> str:
    url = f"https://console.anthropic.com/workspaces/-/environments/{environment_id}"
    print()
    print("[bootstrap] open the environment in Console and click")
    print("            'Generate environment key':")
    print(f"            {url}")
    try:
        webbrowser.open(url)
    except Exception:  # noqa: S110, BLE001 - browser opening is a nicety, not required
        pass
    print()
    while True:
        key = input("[bootstrap] paste environment key (sk-ant-oat01-...): ").strip()
        if key.startswith("sk-ant-oat") and len(key) > 30:
            return key
        print("[bootstrap]   that doesn't look like an environment key, try again")


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[bootstrap] ANTHROPIC_API_KEY is required", file=sys.stderr)
        return 2

    short_circuit_if_exists()

    client = anthropic.Anthropic(api_key=api_key)

    print("[bootstrap] creating self-hosted environment ...")
    environment = client.beta.environments.create(
        name="agentcore-self-hosted-sandbox",
        config={"type": "self_hosted"},
    )
    environment_id = environment.id
    print(f"[bootstrap]   environment_id = {environment_id}")

    environment_key = prompt_for_env_key(environment_id)
    print(f"[bootstrap]   environment_key = {environment_key[:14]}…")

    model = os.environ.get("ANTHROPIC_AGENT_MODEL", "claude-haiku-4-5")
    print(f"[bootstrap] creating agent (model={model}) ...")
    agent = client.beta.agents.create(
        name="agentcore-coding-agent",
        model=model,
        system=(
            "You are a coding agent running inside an AgentCore Runtime "
            "microVM. Files in /workspace persist for the session. Use the "
            "bash, read, write, edit, glob, and grep tools to make changes."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )
    print(f"[bootstrap]   agent_id = {agent.id}")

    write_config(
        {
            "ANTHROPIC_ENVIRONMENT_ID": environment_id,
            "ANTHROPIC_ENVIRONMENT_KEY": environment_key,
            "ANTHROPIC_AGENT_ID": agent.id,
        }
    )

    print("\n[bootstrap] next steps:")
    print(f"  source {CONFIG_PATH.name}")
    print("  export AGENTCORE_RUNTIME_ARN=arn:aws:bedrock-agentcore:...")
    print("  ./start.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
