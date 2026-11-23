"""Content-addressed cache for every paid model call.

Keyed by sha256(model + sorted params + input bytes), so an identical input is
never sent to the same model twice -- within a run or across runs. This is what
makes development affordable on a small credit balance, and it makes reruns
deterministic and free.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import CACHE_DIR


def _digest(model: str, params: dict[str, Any], payload: bytes = b"") -> str:
    h = hashlib.sha256()
    h.update(model.encode())
    h.update(json.dumps(params, sort_keys=True, ensure_ascii=False).encode())
    h.update(payload)
    return h.hexdigest()


def key_for(model: str, params: dict[str, Any], file_path: str | Path | None = None,
            text: str | None = None) -> str:
    """Build a cache key from a model name, its parameters and its input."""
    payload = b""
    if file_path is not None:
        payload = Path(file_path).read_bytes()
    elif text is not None:
        payload = text.encode("utf-8")
    return _digest(model, params, payload)


class Cache:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or CACHE_DIR)
        self.root.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def _json_path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def _blob_path(self, key: str, suffix: str) -> Path:
        return self.root / f"{key}{suffix}"

    def get_json(self, key: str) -> Any | None:
        p = self._json_path(key)
        if p.exists():
            self.hits += 1
            return json.loads(p.read_text(encoding="utf-8"))
        self.misses += 1
        return None

    def put_json(self, key: str, value: Any) -> None:
        self._json_path(key).write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_blob(self, key: str, suffix: str) -> bytes | None:
        p = self._blob_path(key, suffix)
        if p.exists():
            self.hits += 1
            return p.read_bytes()
        self.misses += 1
        return None

    def put_blob(self, key: str, suffix: str, data: bytes) -> Path:
        p = self._blob_path(key, suffix)
        p.write_bytes(data)
        return p

    def stats(self) -> dict[str, int]:
        return {"hits": self.hits, "misses": self.misses}


CACHE = Cache()
