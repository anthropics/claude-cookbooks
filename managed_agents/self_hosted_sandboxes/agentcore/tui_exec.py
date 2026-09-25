"""
One-shot exec into the per-session microVM via InvokeAgentRuntimeCommand.

Streams stdout/stderr/exit deltas back over HTTP. Targets the same microVM
as the running Anthropic session by passing the session id as
runtimeSessionId. Useful for ad-hoc inspection of /workspace while the
agent is running, without touching the agent loop itself.

Usage:
    python3 tui_exec.py --runtime-session-id sesn_... -- "ls -la /workspace"
"""

import argparse
import os
import sys

import boto3


def main() -> int:
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--agent-arn", default=os.environ.get("AGENTCORE_RUNTIME_ARN"))
    p.add_argument(
        "--runtime-session-id", required=True, help="Anthropic session id (sesn_...) to attach to"
    )
    p.add_argument("--region", default=os.environ.get("AGENTCORE_REGION", "us-west-2"))
    p.add_argument("--qualifier", default="DEFAULT")
    p.add_argument("--timeout", type=int, default=15, help="server-side command timeout in seconds")
    p.add_argument("command", nargs="+", help="shell command to run")
    args = p.parse_args()

    if not args.agent_arn:
        print("--agent-arn or AGENTCORE_RUNTIME_ARN required", file=sys.stderr)
        return 2

    cmd = " ".join(args.command)

    # AgentCore runtimeSessionId must be >= 33 chars; pad if Anthropic ID is shorter.
    rsid = args.runtime_session_id
    if len(rsid) < 33:
        rsid = rsid + "-" + "0" * (33 - len(rsid) - 1)

    client = boto3.client("bedrock-agentcore", region_name=args.region)

    print(f"[exec] runtimeSessionId={rsid}", file=sys.stderr)
    print(f"[exec] command={cmd!r}", file=sys.stderr)

    resp = client.invoke_agent_runtime_command(
        agentRuntimeArn=args.agent_arn,
        qualifier=args.qualifier,
        runtimeSessionId=rsid,
        contentType="application/json",
        accept="application/json",
        body={"command": cmd, "timeout": args.timeout},
    )
    print(
        f"[exec] http={resp['ResponseMetadata']['HTTPStatusCode']} rid={resp['ResponseMetadata'].get('RequestId')}",
        file=sys.stderr,
    )

    exit_code = 0
    for ev in resp["stream"]:
        chunk = ev.get("chunk")
        if not chunk:
            continue
        if "contentDelta" in chunk:
            d = chunk["contentDelta"]
            if "stdout" in d:
                sys.stdout.write(d["stdout"])
                sys.stdout.flush()
            if "stderr" in d:
                sys.stderr.write(d["stderr"])
                sys.stderr.flush()
        elif "contentStop" in chunk:
            stop = chunk["contentStop"]
            exit_code = stop.get("exitCode", 0)
            print(
                f"\n[exec] exit={exit_code} status={stop.get('status')}",
                file=sys.stderr,
            )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
