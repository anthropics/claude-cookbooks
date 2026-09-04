"""Seed-data loader for the MongoDB-on-CMA cookbook.

The fixture is 20 fraud-review transactions with precomputed 1024-dim Voyage embeddings,
stored as plaintext JSON-per-line under ``example_data/mongodb_on_cma/``. Shipping it as
plaintext (rather than an inline gzip+base64 blob) keeps the notebook readable and avoids
tripping secret scanners on a long base64 string.
"""

from __future__ import annotations

import json
from pathlib import Path

# example_data/mongodb_on_cma/seed_transactions.jsonl, resolved relative to this file so the
# loader works regardless of the caller's working directory.
SEED_PATH = (
    Path(__file__).resolve().parent.parent
    / "example_data"
    / "mongodb_on_cma"
    / "seed_transactions.jsonl"
)


def load_seed(path: Path | str | None = None) -> list[dict]:
    """Return the seed transactions as a list of dicts (one per JSONL line)."""
    p = Path(path) if path is not None else SEED_PATH
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
