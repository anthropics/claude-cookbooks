#!/usr/bin/env python3
"""Generate Codex skills from the steipete tooling catalog."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
from typing import Any

import yaml

DOMAIN_PACKS: dict[str, dict[str, str]] = {
    "mcp": {
        "title": "MCP",
        "short_description": "Route to steipete MCP-oriented skills.",
    },
    "cli": {
        "title": "CLI",
        "short_description": "Route to steipete CLI-focused skills.",
    },
    "voice": {
        "title": "Voice",
        "short_description": "Route to steipete voice and speech tooling skills.",
    },
    "macos-automation": {
        "title": "macOS Automation",
        "short_description": "Route to steipete macOS automation skills.",
    },
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


def normalize_tag(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


def title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_\s]+", value) if part)


def write_text(path: Path, content: str, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def safe_frontmatter(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False, width=1000).strip()


def project_tags(project: dict[str, Any]) -> list[str]:
    tags = []
    for raw_tag in project.get("tags", []):
        norm = normalize_tag(str(raw_tag))
        if norm:
            tags.append(norm)
    return tags


def project_in_domain(project: dict[str, Any], domain: str) -> bool:
    tags = set(project_tags(project))
    if domain == "mcp":
        return "mcp" in tags
    if domain == "cli":
        return "cli" in tags
    if domain == "voice":
        return bool(tags & {"voice", "speech", "elevenlabs"})
    if domain == "macos-automation":
        return (
            ("macos" in tags and "automation" in tags)
            or ("accessibility" in tags and "automation" in tags)
            or ("macos" in tags and "screenshots" in tags)
        )
    return False


def select_domain_map(
    projects: list[dict[str, Any]], domains: list[str]
) -> dict[str, list[dict[str, Any]]]:
    domain_map: dict[str, list[dict[str, Any]]] = {}
    for domain in domains:
        matched = [project for project in projects if project_in_domain(project, domain)]
        if matched:
            domain_map[domain] = matched
    return domain_map


def build_project_skill(
    project: dict[str, Any],
    dest_root: Path,
    prefix: str,
    overwrite: bool,
    catalog_path: Path,
) -> tuple[str, bool]:
    slug = project.get("slug") or slugify(project["name"])
    skill_name = f"{prefix}-{slug}"
    tags = project.get("tags", [])
    tags_csv = ", ".join(tags) if tags else "project-reference"
    summary = project.get("summary", "No summary provided.")
    status = project.get("status", "current")
    repo = project.get("repo", "")

    fm = safe_frontmatter(
        {
            "name": skill_name,
            "description": (
                f"Use when requests reference {project['name']} or related tooling patterns. "
                f"Tags: {tags_csv}."
            ),
        }
    )

    skill_md = f"""---
{fm}
---

# {project["name"]}

## Overview

This skill provides a fast project reference for **{project["name"]}** from the steipete tooling catalog.

## When To Use

- The user asks about `{project["name"]}` specifically.
- You need related implementation patterns in `{tags_csv}`.
- You want project-level context before writing code or recommendations.

## Workflow

1. Open `references/project.md`.
2. Extract only the details relevant to the user request.
3. Convert details into actionable implementation steps.
4. If the request spans multiple tools, use `steipete-tooling-index` to branch.

## Notes

- Source catalog: `{catalog_path}`.
- Keep responses focused on practical usage and integration.
"""

    reference_md = f"""# Project Reference

- Name: {project["name"]}
- Slug: {slug}
- Status: {status}
- Tags: {tags_csv}
- Summary: {summary}
"""
    if repo:
        reference_md += f"- Repository: {repo}\n"

    display_name = project["name"].replace("'", "''")
    short_description = summary[:120].replace("'", "''")
    openai_yaml = (
        "interface:\n"
        f"  display_name: '{display_name}'\n"
        f"  short_description: '{short_description}'\n"
    )

    skill_dir = dest_root / skill_name
    wrote_any = False
    wrote_any |= write_text(skill_dir / "SKILL.md", skill_md, overwrite=overwrite)
    wrote_any |= write_text(
        skill_dir / "references" / "project.md", reference_md, overwrite=overwrite
    )
    wrote_any |= write_text(skill_dir / "agents" / "openai.yaml", openai_yaml, overwrite=overwrite)
    return skill_name, wrote_any


def build_domain_pack_skill(
    *,
    domain: str,
    projects: list[dict[str, Any]],
    dest_root: Path,
    prefix: str,
    overwrite: bool,
    catalog_path: Path,
) -> bool:
    pack_meta = DOMAIN_PACKS[domain]
    pack_title = pack_meta["title"]
    skill_name = f"{prefix}-pack-{domain}"
    fm = safe_frontmatter(
        {
            "name": skill_name,
            "description": (
                f"Use for fast routing to steipete {pack_title} projects before loading per-project skills."
            ),
        }
    )

    skill_md = f"""---
{fm}
---

# Steipete {pack_title} Pack

## Overview

This router skill narrows context to steipete projects in the **{pack_title}** domain.

## Workflow

1. Open `references/index.md`.
2. Select the relevant project skills from this domain.
3. Load only those `{prefix}-<project-slug>` skills.
4. Synthesize recommendations from the selected skills.

## Notes

- Source catalog: `{catalog_path}`.
- This skill exists to keep context lean and routing predictable.
"""

    index_lines = [f"# Steipete {pack_title} Domain", ""]
    for project in sorted(projects, key=lambda item: item["name"].lower()):
        slug = project.get("slug") or slugify(project["name"])
        tags = ", ".join(project.get("tags", []))
        index_lines.append(f"- {project['name']} (`{prefix}-{slug}`): {project.get('summary', '')}")
        if tags:
            index_lines.append(f"  Tags: {tags}")

    openai_yaml = (
        "interface:\n"
        f"  display_name: 'Steipete {pack_title} Pack'\n"
        f"  short_description: '{pack_meta['short_description']}'\n"
    )

    skill_dir = dest_root / skill_name
    wrote_any = False
    wrote_any |= write_text(skill_dir / "SKILL.md", skill_md, overwrite=overwrite)
    wrote_any |= write_text(
        skill_dir / "references" / "index.md", "\n".join(index_lines), overwrite=overwrite
    )
    wrote_any |= write_text(skill_dir / "agents" / "openai.yaml", openai_yaml, overwrite=overwrite)
    return wrote_any


def build_index_skill(
    projects: list[dict[str, Any]],
    dest_root: Path,
    prefix: str,
    overwrite: bool,
    catalog_path: Path,
) -> bool:
    skill_name = f"{prefix}-tooling-index"
    fm = safe_frontmatter(
        {
            "name": skill_name,
            "description": (
                "Use for routing requests across steipete projects, MCP tools, CLI utilities, "
                "and automation references."
            ),
        }
    )

    skill_md = f"""---
{fm}
---

# Steipete Tooling Index

## Overview

This skill is a router over the steipete project catalog and points to focused per-project skills.

## Workflow

1. Open `references/index.md`.
2. Match user intent to one or more projects.
3. Load the corresponding `{prefix}-<project-slug>` skill(s).
4. Synthesize recommendations from the matched skills only.

## Notes

- Source catalog: `{catalog_path}`.
- Prefer loading one project skill at a time for lazy context usage.
"""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for project in projects:
        status = project.get("status", "current")
        grouped.setdefault(status, []).append(project)

    index_lines = ["# Steipete Project Index", "", "## Domain Packs", ""]
    for domain, meta in sorted(DOMAIN_PACKS.items()):
        index_lines.append(
            f"- {meta['title']} (`{prefix}-pack-{domain}`): {meta['short_description']}"
        )
    index_lines.extend(["", "## Projects by Status", ""])
    for status in sorted(grouped):
        index_lines.append(f"## {title_case(status)}")
        index_lines.append("")
        for project in sorted(grouped[status], key=lambda item: item["name"].lower()):
            slug = project.get("slug") or slugify(project["name"])
            tags = ", ".join(project.get("tags", []))
            skill = f"{prefix}-{slug}"
            index_lines.append(f"- {project['name']} (`{skill}`): {project.get('summary', '')}")
            if tags:
                index_lines.append(f"  Tags: {tags}")
        index_lines.append("")

    openai_yaml = (
        "interface:\n"
        "  display_name: 'Steipete Tooling Index'\n"
        "  short_description: 'Route requests to steipete project skills quickly.'\n"
    )

    skill_dir = dest_root / skill_name
    wrote_any = False
    wrote_any |= write_text(skill_dir / "SKILL.md", skill_md, overwrite=overwrite)
    wrote_any |= write_text(
        skill_dir / "references" / "index.md", "\n".join(index_lines), overwrite=overwrite
    )
    wrote_any |= write_text(skill_dir / "agents" / "openai.yaml", openai_yaml, overwrite=overwrite)
    return wrote_any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Codex skills from the steipete project catalog."
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path(__file__).with_name("projects.yaml"),
        help="Path to project catalog YAML.",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path("~/.codex/skills").expanduser(),
        help="Destination skills directory.",
    )
    parser.add_argument(
        "--prefix",
        default="steipete",
        help="Prefix for generated skill names (default: steipete).",
    )
    parser.add_argument(
        "--status",
        action="append",
        help="Filter by status (repeatable): current, pinned, legacy.",
    )
    parser.add_argument(
        "--tag",
        action="append",
        help="Include only projects matching any of these tags (repeatable).",
    )
    parser.add_argument(
        "--require-tag",
        action="append",
        help="Include only projects containing all required tags (repeatable).",
    )
    parser.add_argument(
        "--domain-pack",
        action="append",
        choices=sorted(DOMAIN_PACKS.keys()),
        help=(
            "Limit project set to one or more domains and generate only those domain pack router skills. "
            "Repeatable."
        ),
    )
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="Generate only the top-level tooling index skill.",
    )
    parser.add_argument(
        "--no-domain-packs",
        action="store_true",
        help="Skip generation of domain pack router skills.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing generated skill files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = yaml.safe_load(args.catalog.read_text(encoding="utf-8"))
    projects = payload.get("projects", [])
    if not projects:
        raise SystemExit("No projects found in catalog.")

    if args.status:
        allowed = {item.lower() for item in args.status}
        projects = [item for item in projects if item.get("status", "current").lower() in allowed]

    if args.tag:
        include_tags = {normalize_tag(tag) for tag in args.tag}
        projects = [
            item for item in projects if set(project_tags(item)).intersection(include_tags)
        ]
    else:
        include_tags = set()

    if args.require_tag:
        required_tags = {normalize_tag(tag) for tag in args.require_tag}
        projects = [item for item in projects if required_tags.issubset(set(project_tags(item)))]
    else:
        required_tags = set()

    selected_domains = list(dict.fromkeys(args.domain_pack or []))
    if selected_domains:
        projects = [
            item
            for item in projects
            if any(project_in_domain(item, domain) for domain in selected_domains)
        ]

    args.dest.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    wrote_index = build_index_skill(
        projects=projects,
        dest_root=args.dest,
        prefix=args.prefix,
        overwrite=args.overwrite,
        catalog_path=args.catalog.resolve(),
    )
    if wrote_index:
        created += 1
    else:
        skipped += 1

    if not args.index_only:
        for project in projects:
            _, wrote = build_project_skill(
                project=project,
                dest_root=args.dest,
                prefix=args.prefix,
                overwrite=args.overwrite,
                catalog_path=args.catalog.resolve(),
            )
            if wrote:
                created += 1
            else:
                skipped += 1

    domain_keys = selected_domains or sorted(DOMAIN_PACKS.keys())
    domain_map = select_domain_map(projects, domain_keys)
    domain_skill_count = 0
    if not args.no_domain_packs and not args.index_only:
        for domain, domain_projects in domain_map.items():
            wrote = build_domain_pack_skill(
                domain=domain,
                projects=domain_projects,
                dest_root=args.dest,
                prefix=args.prefix,
                overwrite=args.overwrite,
                catalog_path=args.catalog.resolve(),
            )
            domain_skill_count += 1
            if wrote:
                created += 1
            else:
                skipped += 1

    total = 1 if args.index_only else len(projects) + 1 + (
        0 if args.no_domain_packs else domain_skill_count
    )
    print(f"catalog={args.catalog.resolve()}")
    print(f"dest={args.dest.resolve()}")
    print(f"projects={len(projects)}")
    print(f"domain_packs={','.join(domain_map) if domain_map else 'none'}")
    print(f"filter_tag_any={','.join(sorted(include_tags)) if include_tags else 'none'}")
    print(f"filter_tag_all={','.join(sorted(required_tags)) if required_tags else 'none'}")
    print(f"skills_total={total}")
    print(f"skills_written={created}")
    print(f"skills_skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
