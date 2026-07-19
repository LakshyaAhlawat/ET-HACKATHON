# Q&A prep — anticipated judge questions

Every answer here is grounded in a number or file already in this repo
(`data/benchmark/results/`, `docs/DECK_OUTLINE.md`, `ARCHITECTURE.md`) —
re-run `cd backend && .venv/Scripts/python.exe -m benchmark.run` before the
pitch if anything upstream changed, and update the numbers below to match.

What this document does **not** cover: literally rehearsing delivery. That's
a you-on-camera task — 10 timed run-throughs against `docs/DEMO_SCRIPT.md`'s
90-second cut list. This is ammunition for what happens after you stop
talking.

---

### "Your benchmark — did you tune the system to the 50 questions?"

No, and this is worth saying before they ask it a second way. The ground
truth's own metadata says so: *"Do not adjust this key based on system
output. This is the ground truth. If the system gets a question wrong,
that's the system's fault, not the key's fault."* The scoring code
(`backend/benchmark/scoring.py`) is generic precision/recall/F1 and a
keyword-recall proxy — nothing category-specific to these 50 questions.
The honest tell: **`ours` doesn't score 1.00 on everything** —
`sld_topology` is 0.42, *lower* than bm25's 0.57. A tuned system wouldn't
have a category it loses on.

### "Why is `sld_topology` your worst category?"

Because we're disclosing a real bug, not hiding it. `ours` answers
SLD_001–005 from the actual YOLOv8+Hough+NetworkX pipeline
(`data/sld_results.json`), and 3 of 5 test topologies currently come back
with zero detected source-to-load paths — a wire-connectivity gap in the
Hough transform stage, not a redundancy judgment being wrong. It's a
known, timeboxed limitation (SLD was priority #4, "kill if YOLO not
detecting" per the project's own priority order), not a surprise you're
finding for us.

### "The 'other categories' table — multi_hop, rfi_dedup — those numbers look mediocre. Why?"

Because that table is measuring something different and weaker than the
deviation table, and we say so on the slide instead of burying it. It's
keyword overlap against reference text, not correctness — a system that
returns a short, *correct* computed number (e.g. an actual simulated
handover date for `cascade_scenarios`) can score lower on this metric than
a baseline that pads its answer with reference-adjacent prose. The
deviation-detection table (precision/recall/F1, exact match) is the rigorous
one; this one is a coverage signal. If pressed: "we'd replace this with a
human-graded rubric given more runway — RAGAS (`ragas_eval.py`) is wired in
as a richer alternative but needs a live Groq key to run."

### "Is the Ctrl+F row real data?"

No, and the results table says so in its own reading notes: it's a
*modeled estimate* (`data/benchmark/ctrl_f_baseline.json`'s `note` field),
not a stopwatch trial. If asked directly: "we'd run a real timed trial
before citing it as measured — right now it's there to show the shape of
the comparison, not to claim a precise number."

### "How does your unit-conversion catch actually work? Give me the trap."

`DEV_001`: spec requires ≥500 TR at 35°C ambient. Submittal states
1688 kW. 1688 kW ÷ 3.517 kW/TR ≈ 480 TR — a real 4% shortfall, invisible
unless you convert units before comparing. `DEV_007` is the sharper trap:
spec wants 250 kW at 0.9 power factor; submittal states 250 **kVA**. kVA
(apparent power) and kW (real power) share the same physical dimension, so
a naive unit library converts them 1:1 and calls it a pass. We special-cased
this (`app/core/units.py::is_power_factor_pair`) to refuse the comparison
without an explicit power factor rather than silently treating kVA as kW —
that's why `ours` answers `INSUFFICIENT_DATA` there, and why `bm25` (which
does raw number comparison with no unit conversion at all) fails this one
outright.

### "What's the actual architecture? One sentence."

"The LLM perceives, deterministic code judges" — an LLM (or in the demo
path, a regex-based FACT-tag extractor standing in for it, see
`corpus_extractor.py`) turns a document into structured numbers; a plain
Python function with a real unit-conversion library (`pint`) compares those
numbers and decides PASS / NON_CONFORMANCE / INSUFFICIENT_DATA. No LLM ever
renders a compliance verdict.

### "What happens when the data just isn't there — a missing condition, an unstated power factor?"

We say so, we don't guess. `INSUFFICIENT_DATA` isn't an error state, it's a
first-class answer — the whole reason it exists as a third option is that
"spec wants 20 min runtime at 25°C, submittal says 20 min, ambient not
stated" is a *real* gap, and guessing "close enough, PASS" is the failure
mode that costs three weeks downstream. `DEV_003`, `006`, `007`, `009` in
the benchmark are exactly this case, and `ours` catches all four — its
`INSUFFICIENT_DATA accuracy` is 1.00, vanilla RAG's is 0.00. That's not a
rounding difference, that's a chatbot that never says "I don't know."

### "This all runs on synthetic/fake documents. Why should I trust the numbers?"

Because we disclose the provenance instead of blurring it (see
`CLAUDE.md`'s data-provenance section, stated on a slide, not a footnote):
the spec formats, standard citations (TIA-942, BICSI, IEC, ISO 10816), and
vendor-datasheet *style* are real; the specific project's 15 planted
deviations and demo fixtures are synthesized, seeded, and reproducible,
with a ground-truth key the model never saw during development. That's a
standard, defensible eval methodology — the alternative (hand-picking real
documents with unknown, unlabeled defects) would make the benchmark *less*
trustworthy, not more, because you couldn't verify our grading against
anything.

### "What's not real yet — what would break if we deployed this tomorrow?"

Answer this before they ask (`docs/DECK_OUTLINE.md` slide 7 says the same):
Postgres/Qdrant run as hosted services in the target deployment but as
embedded/local instances in the demo; Neo4j AuraDB sync
(`graph/neo4j_sync.py`) is written but untested against real credentials;
the SLD wire-detection gap above. Nothing in the *judged capability* is
fake — the compliance verifier, cascade simulator, and query router all run
against real precomputed data with zero network dependency
(`scripts/verify_offline.py` proves this) — but infrastructure-hosting and
one CV pipeline stage are not production-hardened.

---

## Numbers to have cold (pull fresh before presenting)

- Deviation detection: **1.00 / 1.00 / 1.00** (precision/recall/F1), vs.
  bm25 **0.80/0.73/0.76**, vanilla RAG **0.42/0.45/0.43**.
- `INSUFFICIENT_DATA` accuracy: ours **1.00**, vanilla RAG **0.00**.
- Known gap: `sld_topology` **0.42** (worst category, disclosed cause above).
- Unit-conversion traps caught: `DEV_001` (kW→TR), `DEV_007` (kVA vs kW
  power-factor trap).
