"""
Tear down the resources created by setup.sh and deploy.py:
  - AgentCore Runtime + endpoints
  - IAM execution role
  - ECR images (the repo itself is kept; pass --delete-repo to drop it)

The local bootstrap.config (Anthropic environment + agent IDs) is intentionally
not touched here — those are control-plane resources, archive them with
`ant beta:agents archive` / `ant beta:environments archive` separately.
"""

import json
import sys
import time
from pathlib import Path

import boto3


def load_runtime_config():
    path = Path(__file__).parent / "runtime_config.json"
    if not path.exists():
        print("runtime_config.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def main() -> int:
    delete_repo = "--delete-repo" in sys.argv

    cfg = load_runtime_config()
    region = cfg["region"]
    agent_name = cfg["agent_name"]
    runtime_id = cfg["runtime_id"]
    ecr_repo = cfg["ecr_repo"]

    session = boto3.Session(region_name=region)
    control = session.client("bedrock-agentcore-control", region_name=region)
    iam = session.client("iam")
    ecr = session.client("ecr")

    print(f"cleaning up {agent_name} in {region}\n")

    # 1) endpoints
    try:
        eps = control.list_agent_runtime_endpoints(agentRuntimeId=runtime_id)
        for ep in eps.get("runtimeEndpoints", []):
            if ep["name"] == "DEFAULT":
                continue
            print(f"  deleting endpoint: {ep['name']}")
            control.delete_agent_runtime_endpoint(
                agentRuntimeId=runtime_id, endpointName=ep["name"]
            )
        if eps.get("runtimeEndpoints"):
            time.sleep(15)
    except Exception as exc:
        print(f"  warn (endpoints): {exc}")

    # 2) runtime
    try:
        print(f"  deleting runtime: {runtime_id}")
        control.delete_agent_runtime(agentRuntimeId=runtime_id)
        time.sleep(20)
    except Exception as exc:
        print(f"  warn (runtime): {exc}")

    # 3) IAM
    role_name = f"agentcore-{agent_name}-role"
    try:
        for p in iam.list_role_policies(RoleName=role_name).get("PolicyNames", []):
            iam.delete_role_policy(RoleName=role_name, PolicyName=p)
        iam.delete_role(RoleName=role_name)
        print(f"  deleted IAM role: {role_name}")
    except iam.exceptions.NoSuchEntityException:
        print(f"  IAM role not found: {role_name}")
    except Exception as exc:
        print(f"  warn (iam): {exc}")

    # 4) ECR images / repo
    try:
        if delete_repo:
            print(f"  deleting ECR repo (force): {ecr_repo}")
            ecr.delete_repository(repositoryName=ecr_repo, force=True)
        else:
            imgs = ecr.list_images(repositoryName=ecr_repo).get("imageIds", [])
            if imgs:
                print(f"  deleting {len(imgs)} ECR images in {ecr_repo}")
                ecr.batch_delete_image(repositoryName=ecr_repo, imageIds=imgs)
    except ecr.exceptions.RepositoryNotFoundException:
        print(f"  ECR repo not found: {ecr_repo}")
    except Exception as exc:
        print(f"  warn (ecr): {exc}")

    # 5) local config
    for f in ("runtime_config.json", "envvars.config"):
        p = Path(__file__).parent / f
        if p.exists():
            p.unlink()
            print(f"  removed local: {f}")

    print(f"\ncleanup complete{' (repo deleted)' if delete_repo else ' (repo kept)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
