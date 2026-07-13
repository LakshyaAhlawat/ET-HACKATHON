"""Offline step: embeds every corpus chunk once and writes them into a local
on-disk Qdrant collection, so the request path (hybrid.py) never re-embeds
the corpus -- only the incoming query gets encoded live. Per CLAUDE.md's
"precompute everything": this runs once (`python -m retrieval.precompute`),
not on every API call.

Qdrant runs here in embedded/on-disk mode (`QdrantClient(path=...)`) rather
than against a live server -- consistent with how cascade/ and sld/ ship
precomputed JSON instead of depending on a running service at demo time. A
real deployment would point QDRANT_URL (see app/core/config.py) at a hosted
cluster instead; the collection schema is identical either way.
"""

import sys

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from retrieval.corpus import load_corpus_chunks
from retrieval.hybrid import COLLECTION_NAME, EMBED_DIM, EMBED_MODEL_NAME, QDRANT_PATH


def run() -> None:
    from sentence_transformers import SentenceTransformer

    chunks = load_corpus_chunks()
    print(f"Embedding {len(chunks)} chunks with {EMBED_MODEL_NAME}...", file=sys.stderr)
    model = SentenceTransformer(EMBED_MODEL_NAME)
    vectors = model.encode([c.text for c in chunks], normalize_embeddings=True)

    QDRANT_PATH.mkdir(parents=True, exist_ok=True)
    client = QdrantClient(path=str(QDRANT_PATH))
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=i,
                vector=vectors[i].tolist(),
                payload={
                    "chunk_id": chunk.chunk_id,
                    "source_doc": chunk.source_doc,
                    "heading": chunk.heading,
                    "text": chunk.text,
                },
            )
            for i, chunk in enumerate(chunks)
        ],
    )
    client.close()
    print(f"Wrote {len(chunks)} vectors to {QDRANT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    run()
