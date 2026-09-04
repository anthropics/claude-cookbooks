"""Embedding + rerank client for the MongoDB-on-CMA cookbook.

`AtlasEmbeddingClient` adapts the MongoDB Atlas AI endpoint (`/v1/embeddings`, `/v1/rerank`)
to the same `.embed()` / `.rerank()` surface as the `voyageai` SDK, so the rest of the
cookbook is provider-agnostic. `make_embedding_client()` picks Atlas, Voyage, or neither
(the seed ships precomputed vectors, so retrieval works with no provider at all).
"""

from __future__ import annotations

from .config import (
    ATLAS_EMBEDDINGS_URL,
    ATLAS_RERANK_URL,
    EMBED_DIM,
    EMBED_MODEL,
    RERANK_MODEL,
    EmbeddingDimensionMismatch,
)


class _EmbedResponse:
    def __init__(self, embeddings):
        self.embeddings = embeddings


class _RerankResult:
    def __init__(self, index, relevance_score):
        self.index = index
        self.relevance_score = relevance_score


class _RerankResponse:
    def __init__(self, results):
        self.results = results


class AtlasEmbeddingClient:
    # Adapts the MongoDB Atlas AI endpoint to the voyageai .embed()/.rerank() interface.
    def __init__(
        self,
        api_key,
        *,
        url=ATLAS_EMBEDDINGS_URL,
        rerank_url=ATLAS_RERANK_URL,
        output_dimension=EMBED_DIM,
        transport=None,
    ):
        self._api_key = api_key
        self._url = url
        self._rerank_url = rerank_url
        self._dim = output_dimension
        self._transport = transport

    def _post(self, url, payload):
        if self._transport is not None:
            return self._transport(url, payload, self._api_key)
        import requests

        resp = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def embed(self, texts, model=None, input_type=None):
        body = self._post(
            self._url,
            {
                "model": model or EMBED_MODEL,
                "input": list(texts),
                "input_type": input_type,
                "output_dimension": self._dim,
            },
        )
        return _EmbedResponse([item["embedding"] for item in body["data"]])

    def rerank(self, query, documents, model=None, top_k=None):
        body = self._post(
            self._rerank_url,
            {
                "model": model or RERANK_MODEL,
                "query": query,
                "documents": list(documents),
                "top_k": top_k,
            },
        )
        return _RerankResponse(
            [_RerankResult(d["index"], d["relevance_score"]) for d in body["data"]]
        )


def check_embedding_dim(vec, expected):
    if len(vec) != expected:
        raise EmbeddingDimensionMismatch(
            f"embedding has {len(vec)} dimensions, expected {expected}"
        )
    return vec


def embed_query(text, *, client, model=EMBED_MODEL, dim=EMBED_DIM) -> list[float]:
    result = client.embed([text], model=model, input_type="query")
    return check_embedding_dim(list(result.embeddings[0]), dim)


def embed_documents(texts, *, client, model=EMBED_MODEL, dim=EMBED_DIM) -> list[list[float]]:
    result = client.embed(list(texts), model=model, input_type="document")
    return [check_embedding_dim(list(v), dim) for v in result.embeddings]


def rerank(query, documents, *, client, model=RERANK_MODEL, top_k):
    return client.rerank(query, documents, model=model, top_k=top_k).results


def make_embedding_client(env=None):
    import os

    source = env if env is not None else os.environ
    if source.get("MDB_ATLAS_API_KEY"):
        return AtlasEmbeddingClient(source["MDB_ATLAS_API_KEY"])
    if source.get("VOYAGE_API_KEY"):
        import voyageai

        return voyageai.Client()
    return None
