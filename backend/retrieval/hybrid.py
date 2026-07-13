"""Hybrid retrieval: BM25 (keyword) + Qdrant (vector), fused with Reciprocal
Rank Fusion, then reranked with a bge cross-encoder -- exactly the retrieval
stack CLAUDE.md names for this project.

BM25 is not a fallback here, it's load-bearing: vector similarity alone
cannot reliably distinguish "TX-01" from "TX-10" (they're nearly identical
in embedding space but mean completely different pieces of equipment) --
only exact keyword overlap does. Fusing both, then reranking, gets the
precision of keyword match and the recall of semantic search.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from rank_bm25 import BM25Okapi

from retrieval.corpus import Chunk, load_corpus_chunks

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder, SentenceTransformer

REPO_ROOT = Path(__file__).resolve().parents[2]
QDRANT_PATH = REPO_ROOT / "data" / "qdrant_local"
COLLECTION_NAME = "epc_corpus"

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384

# CLAUDE.md's named cross-encoder; it is a ~1.1GB multilingual model. Falls
# back to a much smaller cross-encoder (same CrossEncoder API) if the
# download is unavailable, so the router still works offline.
_PREFERRED_RERANKER = "BAAI/bge-reranker-v2-m3"
_FALLBACK_RERANKER = "cross-encoder/ms-marco-MiniLM-L-6-v2"

RRF_K = 60


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source_doc: str
    heading: str
    score: float


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9.]+", text.lower())


@lru_cache(maxsize=1)
def _bm25_index() -> tuple[BM25Okapi, tuple[Chunk, ...]]:
    chunks = load_corpus_chunks()
    return BM25Okapi([_tokenize(c.text) for c in chunks]), chunks


def _bm25_ranked_ids(query: str, top_k: int) -> list[str]:
    bm25, chunks = _bm25_index()
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [chunks[i].chunk_id for i in ranked]


@lru_cache(maxsize=1)
def _embed_model() -> "SentenceTransformer":
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBED_MODEL_NAME)  # type: ignore[no-any-return]


@lru_cache(maxsize=1)
def _qdrant_client() -> object:
    from qdrant_client import QdrantClient

    return QdrantClient(path=str(QDRANT_PATH))


def _vector_ranked_ids(query: str, top_k: int) -> list[str]:
    client = _qdrant_client()
    query_vector = _embed_model().encode(query, normalize_embeddings=True).tolist()
    hits = client.query_points(  # type: ignore[attr-defined]
        collection_name=COLLECTION_NAME, query=query_vector, limit=top_k
    ).points
    return [hit.payload["chunk_id"] for hit in hits]


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = RRF_K
) -> list[tuple[str, float]]:
    """Standard RRF: score(doc) = sum over lists of 1 / (k + rank + 1). Pure
    function, no I/O, so it's unit-testable independent of BM25/Qdrant."""
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


@lru_cache(maxsize=1)
def _reranker() -> tuple["CrossEncoder", str]:
    from sentence_transformers import CrossEncoder

    try:
        return CrossEncoder(_PREFERRED_RERANKER), _PREFERRED_RERANKER
    except Exception:
        return CrossEncoder(_FALLBACK_RERANKER), _FALLBACK_RERANKER


def retrieve(query: str, top_k: int = 8, rerank_top_n: int = 4) -> list[RetrievedChunk]:
    """BM25 + vector search, fused with RRF, reranked with a cross-encoder.
    Returns the top rerank_top_n chunks with their source for citation."""
    chunks_by_id = {c.chunk_id: c for c in load_corpus_chunks()}

    bm25_ids = _bm25_ranked_ids(query, top_k)
    vector_ids = _vector_ranked_ids(query, top_k)
    fused = reciprocal_rank_fusion([bm25_ids, vector_ids])
    fused_ids = [doc_id for doc_id, _score in fused[:top_k] if doc_id in chunks_by_id]

    if not fused_ids:
        return []

    try:
        model, _name = _reranker()
        pairs = [(query, chunks_by_id[doc_id].text) for doc_id in fused_ids]
        cross_scores = model.predict(pairs)  # type: ignore[arg-type]
        ranked_ids = [
            doc_id
            for _score, doc_id in sorted(
                zip(cross_scores, fused_ids, strict=True), key=lambda t: t[0], reverse=True
            )
        ]
    except Exception:
        ranked_ids = fused_ids

    return [
        RetrievedChunk(
            text=chunks_by_id[doc_id].text,
            source_doc=chunks_by_id[doc_id].source_doc,
            heading=chunks_by_id[doc_id].heading,
            score=dict(fused).get(doc_id, 0.0),
        )
        for doc_id in ranked_ids[:rerank_top_n]
    ]
