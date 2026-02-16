# Redundancy Bridge (claude-cookbooks ↔ todo-exec)

This directory is mirrored into `todo-exec` so Claude can access steipete cookbook ingestion assets directly from the active workspace.

## Mirror Target

- `/Users/hidemiasakura/projects/todo-exec/skills/steipete-cookbook-pack`

## Mirrored Artifacts

- `projects.yaml`
- `ingest_projects_as_skills.py`
- `steipete_projects_landscape.ipynb`
- Generated steipete skills (`steipete-*`)

## Refresh Command

```bash
/Users/hidemiasakura/projects/todo-exec/skills/steipete-cookbook-pack/sync_from_cookbook.sh
```

This command regenerates steipete skills to `~/.codex/skills` and updates the todo-exec mirror copy.
