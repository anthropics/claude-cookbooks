"""MongoDB-on-CMA: setup boilerplate for the Fraud Review Agent cookbook.

The notebook holds the teaching code — the retrieval pipeline builders, the custom-tool
handlers, and the `requires_action` gate loop are all defined inline there. This package keeps
only the legitimately-boilerplate pieces the notebook imports rather than teaches:

- ``config``       — tunables, index names, the server-version check
- ``embeddings``   — Atlas AI / Voyage embedding + rerank client
- ``tools``        — Atlas setup (seed, indexes, preflight) + shared decision/audit doc shapers
- ``ap2_mandates`` — AP2 (Agent Payments Protocol) mandate signing/verification (crypto black box)
- ``seed``         — loads the plaintext example-data fixture
"""

from __future__ import annotations

from .config import (
    DEFAULT_MODEL,
    EMBED_DIM,
    EMBED_MODEL,
    RERANK_MODEL,
    EmbeddingDimensionMismatch,
    IndexTimeout,
    supports_rank_fusion,
)
from .embeddings import (
    AtlasEmbeddingClient,
    embed_documents,
    embed_query,
    make_embedding_client,
    rerank,
)
from .seed import load_seed
from .tools import (
    build_audit_event,
    build_decision_doc,
    ensure_indexes,
    has_anthropic_auth,
    missing_required_env,
    preflight,
    prepare_seed,
    resolve_model,
    search_index_model,
    seed_collection,
    server_version,
    vector_index_model,
    wait_for_index_sync,
)

__all__ = [
    "AtlasEmbeddingClient",
    "DEFAULT_MODEL",
    "EMBED_DIM",
    "EMBED_MODEL",
    "EmbeddingDimensionMismatch",
    "IndexTimeout",
    "RERANK_MODEL",
    "build_audit_event",
    "build_decision_doc",
    "embed_documents",
    "embed_query",
    "ensure_indexes",
    "has_anthropic_auth",
    "load_seed",
    "make_embedding_client",
    "missing_required_env",
    "preflight",
    "prepare_seed",
    "rerank",
    "resolve_model",
    "search_index_model",
    "seed_collection",
    "server_version",
    "supports_rank_fusion",
    "vector_index_model",
    "wait_for_index_sync",
]
