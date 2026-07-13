# Deck outline — PS4 Data Centre EPC Project Intelligence

Order matters: **the proof comes before the demo, and the demo comes
before the architecture.** A judge who sees the numbers first watches the
demo asking "does this match what they claimed," not "is this even real."

Numbers below are pulled live from `data/benchmark/results/results_table.md`
— regenerate that file (`cd backend && .venv/Scripts/python.exe -m
benchmark.run`) before finalizing slides if anything upstream changed.

---

## Slide 1 — The problem (hook, ~20s spoken)

**Headline:** 67% of data-centre EPC projects finish late. Not because the
teams are careless — because the information that would have caught the
mistake already existed, scattered across a spec PDF, a vendor cut-sheet,
and an RFI log nobody cross-referenced in time.

**One line, concrete:** "Spec demands ≥500 TR. Vendor submittal says 480.
Nobody caught it for six months."

**Visual:** a single red-circled number on a scanned cut-sheet. No logo
slide, no agenda slide — open on the mistake.

---

## Slide 2 — The proof (benchmark table, before any demo)

**Headline:** "We didn't build a demo. We built a system we can prove
beats the alternatives — on a 50-question test key we wrote *before*
looking at how the system answers."

| System | Precision | Recall | F1 | 3-way exact match | INSUFFICIENT_DATA accuracy |
|---|---|---|---|---|---|
| Ctrl+F (manual) | 1.00 | 0.91 | 0.95 | 0.85 | 0.50 |
| BM25 keyword search | 0.80 | 0.73 | 0.76 | 0.65 | 0.25 |
| Vanilla RAG chatbot | 0.42 | 0.45 | 0.43 | 0.30 | 0.00 |
| **Ours** | **1.00** | **1.00** | **1.00** | **1.00** | **1.00** |

**The line to say out loud:** "A vanilla RAG chatbot — the thing everyone
assumes 'AI for compliance' means — gets 0.42 precision, and its
`INSUFFICIENT_DATA` accuracy is *zero*. It never says 'I don't know.' It
always guesses. That's the exact failure mode this system exists to
prevent, and the number proves it, it doesn't just assert it."

**Second visual (bottom half or slide 2b):** `pr_curve.png` — precision
pinned at 1.0 as the tolerance band widens. "We tuned for precision on
purpose. A false non-conformance costs an engineer twenty minutes
double-checking. A missed one costs three weeks downstream. Here's the
curve that proves which one we optimized for."

**Caveat to state, not hide (builds credibility, not weakens it):** "Ctrl+F's
number is a modeled estimate, not a stopwatch run — we say so on the slide,
we don't hide it in a footnote."

---

## Slide 3 — Live demo (or embedded recording)

Run `docs/DEMO_SCRIPT.md`'s 90-second sequence, or embed the pre-recorded
video. **Never live on hackathon wifi** — `make demo` brings up a fully
offline instance in ~30 seconds; `scripts/verify_offline.py` proves zero
network calls in the path you're about to show.

Six cuts, ~15s each: compliance verifier (the 500-vs-480 TR catch) →
cascade simulator (drag the delay slider) → SLD analyser (path-collision
reveals a fake 2N) → knowledge graph (spec clause traced to HANDOVER) →
query router (one terminal call, four question types) → back to the
benchmark table for 3 seconds as a closing beat.

---

## Slide 4 — Architecture: the one rule

**Headline, verbatim, large type:** "The LLM perceives. Deterministic code
judges."

**Visual:** the four-layer diagram from `ARCHITECTURE.md` (Ingestion &
Perception → Storage → Judgment → Serving & UI), amber-highlighted
Judgment layer.

**The 15-second explanation:** "An LLM reads the spec and reads the
submittal — that's perception, LLMs are good at that. A plain Python
function compares the numbers and decides pass or fail — that's judgment,
and we never let the model do it. `480 kW` and `480 kVA` look identical as
text and differ by a power factor; a unit-conversion library catches that
every time, an LLM catches it only when it feels like it."

---

## Slide 5 — Three capabilities, one architecture

Three columns, one line each, tied back to slide 4's layers:

1. **Compliance verifier** — spec vs. submittal, deterministic evaluator,
   red box on both PDFs.
2. **Cascade simulator** — a 3-week supply delay, propagated through the
   critical path + Monte Carlo, into a 7-week handover slip.
3. **SLD redundancy analyser** — computer vision + graph reachability:
   does the "2N" on the drawing actually hold?

Plus, briefly: the query router (one interface, four engines dispatched
by an LLM classifier that never itself judges) and the knowledge graph
(spec → equipment → vendor → shipment → the real schedule).

---

## Slide 6 — Business impact

- Manual compliance review: ~4 hours per submittal, at scale across
  hundreds of submittals per project.
- Automated: seconds, with the same or better precision (slide 2's
  numbers).
- RFI contradiction detection catches conflicting answers across the RFI
  log *before* construction, not after — hours saved, not a vague
  percentage (see `data/rfi_analysis.json`'s methodology field for the
  exact assumption: ~6h avoided rework per flagged contradiction).

---

## Slide 7 — What's real vs. roadmap (say this before a judge asks)

- **Real today:** everything demoed in slide 3, benchmarked in slide 2,
  running on `make demo`.
- **Represents target deployment, not yet live:** Postgres + Qdrant as
  hosted services (the demo runs an embedded local Qdrant), Neo4j AuraDB
  sync (`graph/neo4j_sync.py` is written, needs real credentials).
- **Known limitation, disclosed:** SLD wire detection has a connectivity
  gap on 3 of 5 test topologies — timeboxed per the project's own
  priority order, not silently swept under the rug.

---

## Slide 8 — Close

Restate slide 1's number (67% late) next to slide 2's number (1.00
precision/recall vs. 0.42 for the naive alternative). One sentence: "The
information to catch this already exists in your documents. We just make
sure someone — or something — actually reads all of it, and never guesses
when it isn't sure."

Contact / repo link.
