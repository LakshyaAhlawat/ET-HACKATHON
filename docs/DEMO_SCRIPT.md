# 90-second demo script

**Never live-demo on hackathon wifi.** Every step below is verified to run
with zero network access — see `scripts/verify_offline.py` (unsets
`GROQ_API_KEY`, forces `HF_HUB_OFFLINE=1`) and the physical wifi-off
checklist at the bottom of this file. Bring the instance up with
`make demo` (or `python scripts/seed_demo.py`) *before* you're in the room —
it takes about 30 seconds from a fresh checkout, but do it once ahead of
time so the recording (or the live screen-share) starts from an
already-running app.

This is a **recording script**, not a transcript — screen-record yourself
following it and narrate live. Total: ~90 seconds across six cuts.

---

## 0:00–0:20 — Compliance verifier (`/compliance`)

**Show:** split-pane spec.pdf / submittal.pdf, source highlighting on both
sides.

**Say:** "Spec clause 3.4.2 requires the chiller do at least 500 tons of
refrigeration at 35°C ambient. The vendor's cut sheet says 480. Our system
caught it automatically — read the spec, read the submittal, and flagged a
4% shortfall. That's not a keyword match, it's a real requirement-vs-value
comparison, and it points at the exact line on both PDFs."

**Click:** the `NON_CONFORMANCE` verdict row → both red boxes highlight.

**Why this one:** it's the flagship, non-negotiable case from CLAUDE.md's
own worked example (500 TR required vs. 480 TR submitted, −4%) — the
`req_id` is `spec.pdf-p1-0` on screen since it's the real, non-negotiable
end-to-end pipeline (Docling → Groq extraction → deterministic evaluator),
not a synthesized fixture.

---

## 0:20–0:35 — Cascade simulator (`/cascade`)

**Show:** Gantt chart + slip histogram + delay slider.

**Say:** "A 3-week transformer delay doesn't cost 3 weeks — it cascades
through the critical path and into the monsoon window. Watch the handover
date move as I drag this."

**Do:** drag the transformer-delay slider to 3 weeks. Histogram and p50/p90
handover dates update instantly (client-side, precomputed Monte Carlo
sweep — no network, no server round-trip).

---

## 0:35–0:50 — SLD redundancy analyser (`/sld`)

**Show:** topology `sld-03` ("SPOF: shared busbar upstream").

**Say:** "This diagram claims 2N redundancy. Our pipeline reads the
drawing, traces both power paths, and — watch — they collide at a shared
busbar. That's not two independent paths, that's one path pretending to be
two."

**Click:** "Trace paths" → both paths animate from IT load back to source,
flash red at the shared node.

**Note:** use `sld-03` or `sld-04` specifically — 3 of the 5 demo topologies
currently have a known wire-detection gap (see `ARCHITECTURE.md`'s
"known limitations" section) and show no path at all, which reads as
broken on screen. This is disclosed, not hidden.

---

## 0:50–1:05 — Knowledge graph (`/graph`)

**Show:** force-directed graph, `MECH-3.4.2` selected.

**Say:** "The same spec clause traces all the way through — which vendor
submitted the chiller, which shipment it's on, which task in the real
111-task schedule it blocks — straight through to handover."

**Click:** "Trace" → path animates node by node: Spec → Equipment → Vendor →
Shipment → the real cascade schedule → HANDOVER.

---

## 1:05–1:20 — Query router (terminal)

**Show:** a terminal window, not a UI screen — the router is a backend
capability (see `ARCHITECTURE.md`), demoed via its API directly.

**Say:** "One box, four kinds of questions. An LLM only decides *which*
engine answers — the answer itself always comes from deterministic code."

**Run** (or paste pre-typed, don't type live):

```bash
curl -s localhost:8000/api/query -H 'content-type: application/json' \
  -d '{"query": "Does the chiller in MECH-3.4.2 meet its cooling capacity requirement?"}' | jq
```

Point at `"category": "compliance_check"` and the real `NON_CONFORMANCE`
verdict in `result`. Optionally show one more (`"...delayed by 3 weeks..."`
→ `"category": "schedule"`) if time allows.

---

## 1:20–1:30 — Benchmark proof (`data/benchmark/results/`)

**Show:** `results_table.md` or `pr_curve.png` on screen.

**Say:** "And here's why you should believe any of that: fifty planted
questions, four systems, same test. We hit 1.00 precision and recall on
deviation detection. Naive keyword search gets 0.80/0.73. A vanilla RAG
chatbot gets 0.42/0.45 — because it never says 'I don't know,' it just
guesses. We tuned for precision on purpose, and here's the curve that
proves it."

**Cut to black / logo.**

---

## Pre-recording checklist

1. `make demo` from a fresh terminal, confirm both services answer within
   ~30s.
2. `cd backend && .venv/Scripts/python.exe ../scripts/verify_offline.py` —
   all steps must print `OK`.
3. **Physically disable wifi** (or pull the ethernet cable), then click
   through all six cuts above for real, once, before recording. If
   anything spins or errors, do not record yet.
4. Re-enable networking, start the screen recorder, run through the script
   at pace.
5. Keep the terminal step (`curl ... /api/query`) pre-typed in a saved
   command/snippet — never type it live, typos during a 90-second window
   are expensive.
