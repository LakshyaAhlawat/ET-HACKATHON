# ET AI Hackathon 2026 — PS4: Data Centre EPC Project Intelligence

## What we are building
An AI platform that reads EPC construction project documents and catches
mistakes before they become schedule disasters. Three core capabilities:

1. **Compliance Verifier** — reads the spec, reads the vendor submittal,
   and flags deviations (e.g. spec demands >=500 TR chiller, vendor offers 480 TR).
2. **Cascade Simulator** — models how a 3-week supply delay amplifies into a
   7-week handover slip via critical-path propagation + Monte Carlo.
3. **SLD Redundancy Analyser** — computer vision on single-line electrical
   diagrams; derives whether 2N redundancy actually holds by graph reachability.

## THE ARCHITECTURAL RULE — never violate this
**The LLM perceives. Deterministic code judges.**

- LLM job: extract structured data from documents (values, units, constraints).
- Pure Python job: compare 480 vs 500 and emit PASS / FAIL / INSUFFICIENT_DATA.
- An LLM must NEVER decide compliance. A verifier that hallucinates a "pass"
  is worse than no verifier. If you catch yourself writing
  `llm.ask("is this compliant?")` — stop, and write a constraint evaluator.

Three outcomes, not two. `INSUFFICIENT_DATA` is mandatory: if the submittal
doesn't state ambient temperature, we cannot evaluate a constraint conditioned
on ambient temperature, and we say so. We never guess.

## Tech stack (do not substitute without asking)
- Backend: FastAPI (Python 3.11), Docker
- LLM: Groq (llama-3.3-70b-versatile) via `instructor` + Pydantic for
  schema-enforced structured output. Gemini 2.0 Flash as VLM fallback for
  image-only datasheets.
- Units: `pint` — NEVER regex for unit conversion. TR vs kW vs BTU/hr is
  where real errors hide.
- PDF parsing: `docling` (layout-aware). NOT pypdf — it shreds spec tables.
  `camelot` for vendor cut-sheet tables. `paddleocr` for scans.
- Vector: Qdrant. Keyword: BM25 (`rank_bm25`). Fuse with Reciprocal Rank Fusion.
- Rerank: `bge-reranker-v2-m3` cross-encoder.
- Graph: Neo4j (AuraDB free tier).
- Relational: Postgres (Supabase).
- Schedule: NetworkX (CPM/DAG) + NumPy (Monte Carlo). NEVER an LLM for arithmetic.
- CV: YOLOv8 (ultralytics) + OpenCV Hough transform.
- Agents: LangGraph (explicit state machines, visualisable traces).
- Frontend: Next.js 14 App Router, TypeScript, Tailwind, `react-pdf`,
  `recharts`, `react-force-graph`, `framer-motion`.

## Non-negotiable engineering rules
1. **Precompute everything.** YOLO detections, Monte Carlo sweeps, embeddings,
   requirement extraction — all run OFFLINE and ship as JSON. Live inference on
   hackathon wifi is how good projects die at 3:00 in a 4:00 pitch.
2. **Capture source bounding boxes at extraction time.** Every extracted fact
   carries `source_page` + `source_bbox`. Without it we cannot draw the red box
   on the PDF, and the red box IS the demo.
3. **The `condition` field is load-bearing.** A spec saying "not less than 500 TR
   at 35C ambient" is a CONDITIONAL constraint. A chiller rated 500 TR at 25C
   FAILS it. Miss this and we produce confident false passes.
4. Every commit must leave the app runnable. `docker compose up` always works.
5. Type hints everywhere. `ruff` + `mypy` clean.

## PDF coordinate space — a recurring gotcha
PDF user space has a **bottom-left origin** (`source_bbox` = `(x0, y0, x1, y1)`
in points, y increasing upward). CSS/DOM overlays have a **top-left origin**.
Converting one to the other requires flipping the y-axis against the page
height, not just scaling. See `frontend/src/lib/pdfOverlay.ts` for the pure
function that does this — it is unit-tested precisely because this is where
off-by-one-axis bugs hide silently (the box renders, just in the wrong place).

## Core schema (the crux of the whole project)
```python
class Requirement(BaseModel):
    req_id: str                      # "MECH-3.4.2"
    equipment_class: str             # "chiller"
    parameter: str                   # "cooling_capacity"
    operator: Literal[">=", "<=", "==", "in", "!="]
    value: float
    unit: str                        # "TR"
    condition: str | None            # "@35C ambient"  <- LOAD-BEARING
    source_doc: str
    source_page: int
    source_bbox: tuple[float, float, float, float]

class ExtractedValue(BaseModel):
    equipment_class: str
    parameter: str
    value: float
    unit: str
    condition: str | None
    source_doc: str
    source_page: int
    source_bbox: tuple[float, float, float, float]
    extraction_confidence: float

class Verdict(BaseModel):
    req_id: str
    status: Literal["PASS", "NON_CONFORMANCE", "INSUFFICIENT_DATA"]
    required: str                    # human-readable: ">= 500 TR @ 35C"
    submitted: str | None            # "480 TR @ 35C"
    delta_pct: float | None          # -4.0
    reason: str                      # why INSUFFICIENT_DATA, if applicable
    spec_evidence: SourceRegion
    submittal_evidence: SourceRegion | None
```
Implemented at `backend/app/models/schema.py`. The deterministic evaluator
that produces `Verdict`s from `Requirement` + `ExtractedValue` lives at
`backend/app/services/compliance/evaluator.py` — tests were written before
the implementation and must keep passing (`backend/tests/`).

## Repo layout
```
backend/    FastAPI app, pydantic schema, evaluator, cascade/SLD stubs
frontend/   Next.js 14 App Router, TS, Tailwind
data/       fixtures/ (hand-authored + generated demo assets), raw/, processed/,
            embeddings/, yolo_detections/, monte_carlo/, ground_truth/, benchmark/
scripts/    one-off/reproducible generation scripts (e.g. fixture PDFs)
```

## Design system (control-room aesthetic)
- Near-black background `#0A0C10`, panels `#131720`
- Signal amber `#F5A623` (spec/attention highlight)
- Compliant `#34D399`, deviation `#EF4444`
- Inter for UI text, JetBrains Mono for every number, tag, and clause reference
- Dense layout — real ops tools are dense, not spacious marketing pages

## Judging weights (build to these)
Innovation 25% | Business Impact 25% | Technical Excellence 20% |
Scalability 15% | User Experience 15%

## Priority order — cut from the bottom, never the top
1. Compliance verifier + split-pane PDF highlighting  [NON-NEGOTIABLE]
2. Cascade simulator + slider                          [NON-NEGOTIABLE]
3. Benchmark harness + results table                   [NON-NEGOTIABLE]
4. SLD redundancy analyser        [timebox 4 days; kill if YOLO not detecting]
5. Knowledge graph + query router
6. RFI deduplicator
7. Commissioning mobile view
8. Geospatial shipment tracker                         [first to go]

## Data provenance (state this honestly on a slide)
- REAL + PUBLIC: TIA-942 / BICSI excerpts, vendor datasheets (Vertiv, Schneider,
  Caterpillar, Kirloskar), CPWD spec formats, public tender technical specs.
- SYNTHESISED + DISCLOSED: project schedule, RFI log, planted deviations,
  demo fixtures (`data/fixtures/`). Seeded, reproducible, with a ground-truth
  key the model never sees.

## Working style
- Ask before adding a dependency not listed above.
- Write the test before the implementation for anything in the verifier.
- If something is ambiguous, ask — do not invent requirements.
