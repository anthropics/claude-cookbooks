"""Deploy the research agent to Modal via ``modal.Sandbox``.

This reuses ``hosting/Dockerfile`` unchanged — the same image that tier 1 runs
locally — so the only thing that changes between tiers is the operational
machinery, not the agent or its interface.

Run from ``claude_agent_sdk/``::

    python hosting/modal/modal_app.py

Prereqs: ``pip install modal && modal setup`` and a Modal secret named
``anthropic`` containing ``ANTHROPIC_API_KEY``.

.. note::
   Session transcripts persist on a ``modal.Volume`` mounted at ``/data``.
   Volumes have explicit commit semantics; if you run many sandboxes writing
   many sessions concurrently and see lost writes, switch persistence to a
   ``SessionStore`` adapter (https://code.claude.com/docs/en/agent-sdk/session-storage).
"""

from __future__ import annotations

import secrets
from pathlib import Path

import modal

APP_NAME = "research-agent-hosting"
VOLUME_NAME = "research-agent-sessions"

# Build context must be claude_agent_sdk/ (the grandparent of this file) so the
# image can COPY research_agent/ and utils/ alongside hosting/.
BUILD_CONTEXT = Path(__file__).resolve().parents[2]
DOCKERFILE = BUILD_CONTEXT / "hosting" / "Dockerfile"

# Sandboxes created from a driver script need a *registered* app, not a local
# ``modal.App(...)`` object — ``lookup`` registers it server-side on first run.
app = modal.App.lookup(APP_NAME, create_if_missing=True)

image = modal.Image.from_dockerfile(
    str(DOCKERFILE),
    context_dir=str(BUILD_CONTEXT),
)

sessions_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


def deploy() -> None:
    # The Modal tunnel is a public HTTPS URL with nothing in front of it.
    # server.py refuses requests without this token when AGENT_AUTH_TOKEN is
    # set — the minimal stand-in for the gateway tiers 1 and 3 assume exists.
    auth_token = secrets.token_urlsafe(32)

    with modal.enable_output():
        # The image's ENTRYPOINT is ./hosting/entrypoint.sh; like compose's
        # `command: ["serve"]`, this arg is appended to it, not run in place
        # of it.
        sandbox = modal.Sandbox.create(
            "serve",
            app=app,
            image=image,
            secrets=[
                modal.Secret.from_name("anthropic"),
                modal.Secret.from_dict({"AGENT_AUTH_TOKEN": auth_token}),
            ],
            volumes={"/data": sessions_volume},
            encrypted_ports=[8000],
            timeout=60 * 60,  # orchestrator-side idle kill; the server never self-terminates
        )

    tunnel = sandbox.tunnels()[8000]
    print(f"sandbox: {sandbox.object_id}")
    print(f"url:     {tunnel.url}")
    print(f"token:   {auth_token}")
    print()
    print("⚠️  The URL is public. The token is the only thing gating it — don't share both.")
    print()
    print("Try it:")
    print(
        f"  curl -N -X POST {tunnel.url}/sessions/demo-1/messages \\\n"
        f"    -H 'Authorization: Bearer {auth_token}' \\\n"
        "    -H 'Content-Type: application/json' \\\n"
        '    -d \'{"prompt":"What are the latest AI agent trends?"}\''
    )


if __name__ == "__main__":
    deploy()
