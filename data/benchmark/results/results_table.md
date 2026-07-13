# Benchmark results — PS4 Data Centre EPC Project Intelligence

50-question ground-truth key (`data/benchmark/ground_truth_50.json`) + 5 PR-curve negative-class controls (`data/benchmark/pr_curve_controls.json`), scored against four systems on the same question set.

## Deviation detection (15 planted deviations + 5 controls, tolerance = 0%)

Precision/recall framed around **flagging a deviation** (predicting `NON_CONFORMANCE`) as the positive class.

| System | Precision | Recall | F1 | 3-way exact match | INSUFFICIENT_DATA accuracy |
|---|---|---|---|---|---|
| Ctrl+F (manual) | 1.00 | 0.91 | 0.95 | 0.85 | 0.50 |
| bm25 | 0.80 | 0.73 | 0.76 | 0.65 | 0.25 |
| vanilla_rag | 0.42 | 0.45 | 0.43 | 0.30 | 0.00 |
| ours | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Other categories (keyword-recall proxy against reference evidence)

| System | multi_hop | rfi_dedup | sld_topology | cascade_scenarios |
|---|---|---|---|---|
| bm25 | 0.59 | 0.27 | 0.57 | 0.24 |
| vanilla_rag | 0.57 | 0.25 | 0.51 | 0.24 |
| ours | 0.59 | 0.28 | 0.42 | 0.19 |

## Reading this table

- **ours** routes each category to the real engine: the deterministic compliance evaluator for deviations, the real YOLOv8+Hough+NetworkX pipeline for sld_topology (SLD_001-005), the real Monte Carlo cascade simulator for cascade_scenarios, and fused BM25+vector+RRF+rerank retrieval for multi_hop/rfi_dedup/SLD_006-010.
- **vanilla_rag** never emits `INSUFFICIENT_DATA` by design (see `benchmark/systems/vanilla_rag.py`) — its INSUFFICIENT_DATA accuracy column is expected to be near zero. That is the point being demonstrated, not a bug.
- **bm25** compares raw numbers with no unit conversion — expect it to fail exactly the unit-conversion-trap questions (DEV_001, DEV_007) even though it gets same-unit comparisons right.
- **Ctrl+F (manual)** numbers are a *modeled estimate* (see `data/benchmark/ctrl_f_baseline.json`'s `note` field), not an empirical timed trial — replace with a real stopwatch run before citing this row as measured data in the pitch.

## Caveat: the 'other categories' table is a weak proxy

Keyword-recall against reference text rewards surface lexical overlap, not correctness — a system that returns a concise computed number (e.g. `ours` on cascade_scenarios: an actual simulated handover day) can score *lower* on this metric than a retrieval baseline that dumps verbose prose sharing more words with the reference answer, even when the computed number is the one that's actually right. Treat this table as a rough retrieval-coverage signal, not a correctness measure — the deviation-detection table above is the rigorous one.

This run's `sld_topology` numbers also surfaced a real finding, not a scoring artifact: `ours` answers SLD_001-005 by reading `data/sld_results.json` directly, and 3 of the 5 topologies currently come back with zero detected source-to-load paths (Hough wire connectivity gap, not a redundancy judgment) — worth fixing in the SLD pipeline before relying on this category in a pitch. Check `per_question_results.json` under `SLD_001`-`SLD_005` for the exact `ours` answer per topology.

See `pr_curve.png` for the precision/recall tradeoff as the tolerance band on `ours` widens, and `per_question_results.json` for every system's answer to every question.