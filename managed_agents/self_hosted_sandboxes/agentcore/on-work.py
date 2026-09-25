"""
Host-side bridge invoked by `ant beta:worker poll --on-work` per work item.

Reads ANTHROPIC_{WORK_ID,ENVIRONMENT_ID,SESSION_ID,ENVIRONMENT_KEY} from the
poller's environment, drains the raw work JSON from stdin (kept opaque), and
calls invoke_agent_runtime with runtimeSessionId == ANTHROPIC_SESSION_ID. The
session affinity guarantee on AgentCore Runtime means the same microVM serves
all turns in one Anthropic session, mirroring the per-session container in
the docker variant.

The invoke is short — AgentCore Runtime returns when the in-microVM
`ant beta:worker run` exits (idle timeout after end_turn). The poller waits
for this script to exit before claiming the next item, so a long-running
session keeps this script alive for the whole session lifetime.
"""

import json
import os
import sys
import time

import boto3
from botocore.config import Config


def main() -> int:
    sys.stdin.read()  # drain the raw work JSON; we don't need its contents

    required = (
        "ANTHROPIC_SESSION_ID",
        "ANTHROPIC_WORK_ID",
        "ANTHROPIC_ENVIRONMENT_ID",
        "ANTHROPIC_ENVIRONMENT_KEY",
    )
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[on-work] missing env: {missing}", file=sys.stderr)
        return 2

    runtime_arn = os.environ["AGENTCORE_RUNTIME_ARN"]
    region = os.environ.get("AGENTCORE_REGION", "us-west-2")

    payload = {
        "session_id": os.environ["ANTHROPIC_SESSION_ID"],
        "work_id": os.environ["ANTHROPIC_WORK_ID"],
        "environment_id": os.environ["ANTHROPIC_ENVIRONMENT_ID"],
        "environment_key": os.environ["ANTHROPIC_ENVIRONMENT_KEY"],
        "base_url": os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    }

    # AgentCore runtimeSessionId must be >= 33 chars; pad if Anthropic ID is shorter.
    runtime_session_id = payload["session_id"]
    if len(runtime_session_id) < 33:
        runtime_session_id = runtime_session_id + "-" + "0" * (33 - len(runtime_session_id) - 1)

    client = boto3.client(
        "bedrock-agentcore",
        region_name=region,
        config=Config(read_timeout=900, retries={"max_attempts": 3}),
    )

    started = time.time()
    print(
        f"[on-work] session={payload['session_id']} work={payload['work_id']} -> invoke_agent_runtime",
        file=sys.stderr,
    )

    try:
        response = client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            runtimeSessionId=runtime_session_id,
            payload=json.dumps(payload).encode("utf-8"),
        )
    except Exception as exc:  # pragma: no cover
        print(f"[on-work] invoke failed: {exc}", file=sys.stderr)
        return 1

    body = response["response"].read()
    elapsed = time.time() - started
    print(
        f"[on-work] session={payload['session_id']} "
        f"done in {elapsed:.1f}s status={response.get('statusCode')} "
        f"body={body[:200]!r}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
