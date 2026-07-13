# Benchmark corpus — provenance disclosure

Per `CLAUDE.md`'s data provenance policy ("SYNTHESISED + DISCLOSED: project
schedule, RFI log, planted deviations, demo fixtures"), the documents in this
folder are **synthesized, not sourced** — they were authored to give the
50-question benchmark (`data/benchmark/ground_truth_50.json`) real prose to
retrieve against, since the official ground-truth key references far more
equipment types and RFI threads than the two-document `data/fixtures/spec.pdf`
/ `submittal.pdf` pair from Session 1 covers.

**How they were written:** every fact in these documents is transcribed
directly from the `evidence` / `reasoning` / `evidence_pointers` fields already
present in `ground_truth_50.json` — nothing here invents a fact beyond what
the ground-truth key itself already specifies. The key's `expected_answer`
and `reason` fields are never copied into these documents; only the
underlying facts (clause text, submitted values, RFI question/response pairs)
are.

**The `[FACT ...]` tags:** each requirement/submittal fact carries an inline
machine-parseable annotation, e.g.

```
[FACT equipment_class=chiller parameter=cooling_capacity operator=>= value=500 unit=TR condition="@35C ambient"]
```

This lets `benchmark/systems/ours_extractor.py` reproduce `Requirement` /
`ExtractedValue` objects deterministically and reproducibly, without a live
Groq API call in the scoring loop (the benchmark must not depend on token
quota to reproduce a score). The production extraction path
(`backend/ingestion/extract.py`) performs the equivalent extraction via
Groq + instructor against real, unannotated vendor PDFs — the tag is a
benchmark-harness convenience, not a claim about how the production system
reads documents.

**Reused, not synthesized:** `data/fixtures/spec.pdf` + `submittal.pdf`
(the real DEV_001 chiller trap), `data/cascade_tasks.json` (the real 111-task
DAG), and `data/sld_results.json` + `frontend/public/sld/sld-0{1..5}.png`
(the real YOLO+NetworkX topology results) are the actual system artifacts —
this corpus supplements them, it does not replace them.
