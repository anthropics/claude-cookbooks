"""
Deploy the AgentCore Runtime for the CMA self-hosted sandbox.

Reads envvars.config (created by setup.sh) and creates:
  - IAM execution role (Bedrock + ECR + CloudWatch + X-Ray)
  - AgentCore Runtime (PUBLIC network mode, container image from ECR)

Writes runtime_config.json with the runtime ARN. The host poller's start.sh
sources that to set AGENTCORE_RUNTIME_ARN.

PUBLIC mode keeps the demo lean: no VPC, no NAT, no S3 Files mount. Each
session's /workspace is ephemeral inside its microVM, same as the docker/
variant. For persistent /workspace across sessions, see the
01-claude-code-with-s3-files cookbook.
"""

import json
import os
import sys
import time
from pathlib import Path

import boto3


def load_envvars() -> dict:
    path = Path(__file__).parent / "envvars.config"
    if not path.exists():
        print("envvars.config not found. Run ./setup.sh first.", file=sys.stderr)
        sys.exit(1)
    cfg = {}
    for line in path.read_text().splitlines():
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def cfg_get(env: dict, key: str, default=None):
    return env.get(key) or os.environ.get(key) or default


def trust_policy(account_id: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {"StringEquals": {"aws:SourceAccount": account_id}},
            }
        ],
    }


def execution_policy(region: str, account_id: str, ecr_repo: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Logs",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                    "logs:PutLogEvents",
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*",
                    f"arn:aws:logs:{region}:{account_id}:log-group:*",
                ],
            },
            {
                "Sid": "XRay",
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                ],
                "Resource": "*",
            },
            {
                "Sid": "CloudWatchMetrics",
                "Effect": "Allow",
                "Action": "cloudwatch:PutMetricData",
                "Resource": "*",
                "Condition": {"StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}},
            },
            {
                "Sid": "ECRAuth",
                "Effect": "Allow",
                "Action": ["ecr:GetAuthorizationToken"],
                "Resource": "*",
            },
            {
                "Sid": "ECRImage",
                "Effect": "Allow",
                "Action": ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
                "Resource": [f"arn:aws:ecr:{region}:{account_id}:repository/{ecr_repo}"],
            },
        ],
    }


def ensure_execution_role(iam, agent_name: str, region: str, account_id: str, ecr_repo: str) -> str:
    role_name = f"agentcore-{agent_name}-role"
    try:
        resp = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy(account_id)),
            Description=f"Execution role for {agent_name}",
        )
        role_arn = resp["Role"]["Arn"]
        print(f"  created IAM role: {role_arn}")
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"  IAM role exists: {role_arn}")

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName=f"{agent_name}-policy",
        PolicyDocument=json.dumps(execution_policy(region, account_id, ecr_repo)),
    )
    print("  waiting 10s for IAM propagation ...")
    time.sleep(10)
    return role_arn


def create_runtime(control, agent_name: str, ecr_uri: str, role_arn: str) -> dict:
    print(f"  creating runtime '{agent_name}' (PUBLIC network) ...")
    resp = control.create_agent_runtime(
        agentRuntimeName=agent_name,
        agentRuntimeArtifact={"containerConfiguration": {"containerUri": ecr_uri}},
        roleArn=role_arn,
        networkConfiguration={"networkMode": "PUBLIC"},
        protocolConfiguration={"serverProtocol": "HTTP"},
        description="Anthropic CMA self-hosted sandbox on AgentCore Runtime",
    )
    runtime_id = resp["agentRuntimeId"]
    runtime_arn = resp["agentRuntimeArn"]
    print(f"  runtime created: {runtime_id}")

    print("  waiting for runtime READY ...")
    while True:
        status_resp = control.get_agent_runtime(agentRuntimeId=runtime_id)
        status = status_resp["status"]
        print(f"    status: {status}")
        if status == "READY":
            return {"runtime_id": runtime_id, "runtime_arn": runtime_arn}
        if status in ("CREATE_FAILED", "UPDATE_FAILED"):
            print(f"  failed: {status_resp.get('failureReason', '?')}", file=sys.stderr)
            sys.exit(1)
        time.sleep(15)


def main() -> int:
    env = load_envvars()
    region = cfg_get(env, "AGENTCORE_REGION", "us-west-2")
    agent_name = cfg_get(env, "AGENTCORE_AGENT_NAME")
    ecr_repo = cfg_get(env, "AGENTCORE_ECR_REPO")
    ecr_uri = cfg_get(env, "AGENTCORE_ECR_URI")
    if not all([agent_name, ecr_repo, ecr_uri]):
        print("envvars.config missing required fields", file=sys.stderr)
        return 1

    session = boto3.Session(region_name=region)
    account_id = session.client("sts").get_caller_identity()["Account"]

    print(f"region:      {region}")
    print(f"account:     {account_id}")
    print(f"agent name:  {agent_name}")
    print(f"image:       {ecr_uri}")
    print()

    print("[deploy] ensuring IAM execution role ...")
    role_arn = ensure_execution_role(
        session.client("iam"), agent_name, region, account_id, ecr_repo
    )

    print("[deploy] creating AgentCore runtime ...")
    runtime = create_runtime(
        session.client("bedrock-agentcore-control", region_name=region),
        agent_name,
        ecr_uri,
        role_arn,
    )

    config = {
        "agent_name": agent_name,
        "region": region,
        "runtime_id": runtime["runtime_id"],
        "runtime_arn": runtime["runtime_arn"],
        "ecr_uri": ecr_uri,
        "ecr_repo": ecr_repo,
    }
    Path(__file__).parent.joinpath("runtime_config.json").write_text(json.dumps(config, indent=2))

    print()
    print(f"[deploy] runtime ARN: {runtime['runtime_arn']}")
    print("[deploy] wrote runtime_config.json")
    print()
    print("Next:")
    print(f"  export AGENTCORE_RUNTIME_ARN={runtime['runtime_arn']}")
    print(f"  export AGENTCORE_REGION={region}")
    print("  source bootstrap.config && ./start.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
