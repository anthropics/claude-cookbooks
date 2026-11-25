"""MongoDB Atlas setup helpers + shared document builders.

Setup boilerplate the cookbook notebook imports rather than teaches: seed the collection,
create the vector + Atlas Search indexes and wait until they are queryable *and* synced, and a
preflight check. Also the small ID/timestamp and decision/audit document shapers shared by the
notebook's `record_decision` handler and the AP2 module. The retrieval pipeline builders and the
custom-tool handlers themselves now live inline in the notebook (that is the teaching content);
`pymongo` still only ever runs on your side of the boundary.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta

from .config import (
    ANTHROPIC_AUTH_ENV,
    DEFAULT_MODEL,
    EMBED_DIM,
    REQUIRED_ENV,
    SEARCH_INDEX_NAME,
    VECTOR_INDEX_NAME,
    IndexTimeout,
)


def _new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _now():
    return datetime.now(UTC)


def build_decision_doc(
    transaction_id,
    decision,
    *,
    confidence,
    risk_factors,
    reasoning,
    reviewed_by,
    decision_id=None,
    created_at=None,
) -> dict:
    return {
        "decision_id": decision_id or _new_id("dec"),
        "transaction_id": transaction_id,
        "decision": decision,
        "confidence_score": confidence,
        "risk_factors": list(risk_factors),
        "reasoning": reasoning,
        "reviewed_by": reviewed_by,
        "created_at": created_at or _now(),
    }


def build_audit_event(
    event_type,
    transaction_id,
    *,
    decision_id=None,
    severity="info",
    event_data=None,
    event_id=None,
    timestamp=None,
) -> dict:
    return {
        "event_id": event_id or _new_id("evt"),
        "timestamp": timestamp or _now(),
        "event_type": event_type,
        "transaction_id": transaction_id,
        "decision_id": decision_id,
        "severity": severity,
        "event_data": event_data or {},
    }


def resolve_model(env=None) -> str:
    import os

    return (env if env is not None else os.environ).get("COOKBOOK_MODEL", DEFAULT_MODEL)


def missing_required_env(env=None) -> list[str]:
    import os

    source = env if env is not None else os.environ
    return [name for name in REQUIRED_ENV if not source.get(name)]


def has_anthropic_auth(env=None) -> bool:
    """True if any Anthropic auth signal is present (API key, auth token, or profile).

    Non-API-key auth (e.g. `ant` CLI workload-identity federation) is valid, so this is a soft
    check: a False result should warn, not block — the SDK still resolves credentials itself.
    """
    import os

    source = env if env is not None else os.environ
    return any(source.get(name) for name in ANTHROPIC_AUTH_ENV)


def server_version(coll) -> str:
    return str(coll.database.command("buildInfo").get("version", "0.0"))


def prepare_seed(docs, *, now) -> list[dict]:
    prepared = []
    for doc in docs:
        doc = dict(doc)
        days = doc.pop("created_days_ago", 0)
        doc["created_at"] = now - timedelta(days=days)
        prepared.append(doc)
    return prepared


def seed_collection(coll, docs) -> int:
    coll.delete_many({})
    if docs:
        coll.insert_many(list(docs))
    return coll.count_documents({})


def ensure_indexes(
    coll, *, dim=EMBED_DIM, poll_interval=2.0, timeout_s=180.0, sleep=None, monotonic=None
) -> None:
    sleep = sleep or time.sleep
    monotonic = monotonic or time.monotonic
    coll.create_index("transaction_id", unique=True)
    existing = {idx["name"] for idx in coll.list_search_indexes()}
    if VECTOR_INDEX_NAME not in existing:
        coll.create_search_index(vector_index_model(dim))
    if SEARCH_INDEX_NAME not in existing:
        coll.create_search_index(search_index_model())
    deadline = monotonic() + timeout_s
    names = (VECTOR_INDEX_NAME, SEARCH_INDEX_NAME)
    while True:
        status = {idx["name"]: idx for idx in coll.list_search_indexes()}
        if all(status.get(n, {}).get("queryable") is True for n in names):
            break
        if monotonic() >= deadline:
            pending = [n for n in names if status.get(n, {}).get("queryable") is not True]
            raise IndexTimeout(f"indexes not queryable within {timeout_s}s: {pending}")
        sleep(poll_interval)
    # `queryable` flips true before a freshly-seeded write is ingested, so a query here can
    # silently return nothing. Block until both indexes actually reflect the seeded docs.
    wait_for_index_sync(
        coll, deadline=deadline, poll_interval=poll_interval, sleep=sleep, monotonic=monotonic
    )


def wait_for_index_sync(
    coll, *, deadline=None, timeout_s=180.0, poll_interval=2.0, sleep=None, monotonic=None
) -> None:
    """Block until the Atlas Search indexes reflect the current documents.

    Atlas Search and Vector Search are eventually consistent: an index reports ``queryable``
    as soon as its definition is built, which can be *before* it has ingested the most recent
    writes. Querying in that window returns empty results even though the data is present.
    This polls a vector probe and a lexical ``exists`` probe until both return a hit (or the
    collection is genuinely empty), so callers never query a lagging index.
    """
    sleep = sleep or time.sleep
    monotonic = monotonic or time.monotonic
    if deadline is None:
        deadline = monotonic() + timeout_s
    probe = coll.find_one({}, {"embedding": 1})
    if probe is None:
        return  # nothing seeded; nothing to wait for
    qvec = probe["embedding"]
    vector_probe = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": qvec,
                "numCandidates": 100,
                "limit": 1,
            }
        },
        {"$limit": 1},
    ]
    lexical_probe = [
        {"$search": {"index": SEARCH_INDEX_NAME, "exists": {"path": "text"}}},
        {"$limit": 1},
    ]
    while True:
        vector_ready = bool(list(coll.aggregate(vector_probe)))
        lexical_ready = bool(list(coll.aggregate(lexical_probe)))
        if vector_ready and lexical_ready:
            return
        if monotonic() >= deadline:
            lagging = [
                name
                for name, ready in (
                    (VECTOR_INDEX_NAME, vector_ready),
                    (SEARCH_INDEX_NAME, lexical_ready),
                )
                if not ready
            ]
            raise IndexTimeout(f"indexes not reflecting seeded docs within timeout: {lagging}")
        sleep(poll_interval)


def vector_index_model(dim=EMBED_DIM) -> dict:
    return {
        "name": VECTOR_INDEX_NAME,
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": dim,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "status"},
            ]
        },
    }


def search_index_model() -> dict:
    return {
        "name": SEARCH_INDEX_NAME,
        "type": "search",
        "definition": {"mappings": {"dynamic": True}},
    }


def preflight(coll, *, expected_dim=EMBED_DIM) -> dict:
    issues: list[str] = []
    try:
        coll.database.command("ping")
    except Exception as exc:
        return {
            "ok": False,
            "issues": [f"cannot reach MongoDB (check MONGO_URI / IP allowlist): {exc}"],
        }
    indexes = {idx["name"]: idx for idx in coll.list_search_indexes()}
    for name in (VECTOR_INDEX_NAME, SEARCH_INDEX_NAME):
        index = indexes.get(name)
        if index is None:
            issues.append(
                f"missing MongoDB Atlas Search index '{name}' — create it, then wait until queryable"
            )
        elif index.get("queryable") is not True:
            issues.append(f"index '{name}' is still building — wait until it is queryable")
    vector_index = indexes.get(VECTOR_INDEX_NAME)
    if vector_index is not None:
        definition = vector_index.get("latestDefinition") or vector_index.get("definition") or {}
        if not any(
            f.get("type") == "filter" and f.get("path") == "status"
            for f in definition.get("fields", [])
        ):
            issues.append(
                "vector index is missing a `status` filter field — recreate from vector_index_model()"
            )
    return {"ok": not issues, "issues": issues}
