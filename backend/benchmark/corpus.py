"""Re-exports the production corpus loader (backend/retrieval/corpus.py) so
the benchmark harness always scores the same chunking the real retrieval
router uses -- Session 7 moved the canonical implementation to retrieval/
now that a production consumer exists; this module is kept so existing
`from benchmark.corpus import ...` call sites don't need to change."""

from retrieval.corpus import Chunk as Chunk
from retrieval.corpus import load_corpus_chunks as load_corpus_chunks
from retrieval.corpus import load_corpus_raw_text as load_corpus_raw_text
