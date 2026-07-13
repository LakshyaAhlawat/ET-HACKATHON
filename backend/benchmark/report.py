"""Report generation: the markdown results table, the precision/recall
curve PNG, and the per-question JSON a judge can inspect on demand."""

import json
from pathlib import Path
from typing import Any

from benchmark.schema import BenchmarkQuestion, SystemAnswer


def _read_ctrl_f(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "data" / "benchmark" / "ctrl_f_baseline.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def markdown_results_table(
    *,
    deviation_metrics: dict[str, dict[str, Any]],
    category_accuracy: dict[str, dict[str, float]],
    insufficient_data_accuracy: dict[str, float | None],
    repo_root: Path,
) -> str:
    ctrl_f = _read_ctrl_f(repo_root)
    lines = [
        "# Benchmark results — PS4 Data Centre EPC Project Intelligence",
        "",
        "50-question ground-truth key (`data/benchmark/ground_truth_50.json`) "
        "+ 5 PR-curve negative-class controls (`data/benchmark/pr_curve_controls.json`), "
        "scored against four systems on the same question set.",
        "",
        "## Deviation detection (15 planted deviations + 5 controls, tolerance = 0%)",
        "",
        "Precision/recall framed around **flagging a deviation** "
        "(predicting `NON_CONFORMANCE`) as the positive class.",
        "",
        "| System | Precision | Recall | F1 | 3-way exact match | INSUFFICIENT_DATA accuracy |",
        "|---|---|---|---|---|---|",
    ]

    def fmt(x: float | None) -> str:
        return f"{x:.2f}" if x is not None else "—"

    for system in ["ctrl_f", "bm25", "vanilla_rag", "ours"]:
        if system == "ctrl_f":
            dd = ctrl_f.get("deviation_detection", {})
            precision, recall = dd.get("precision"), dd.get("recall")
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision is not None and recall is not None and (precision + recall) > 0
                else None
            )
            row = (
                f"| Ctrl+F (manual) | {fmt(precision)} | {fmt(recall)} | {fmt(f1)} "
                f"| {fmt(ctrl_f.get('three_way_exact_match'))} "
                f"| {fmt(ctrl_f.get('insufficient_data_accuracy'))} |"
            )
            if precision is None:
                row += "  _fill in `data/benchmark/ctrl_f_baseline.json`_"
            lines.append(row)
            continue
        m = deviation_metrics.get(system, {})
        acc = category_accuracy.get(system, {}).get("planted_deviations")
        idacc = insufficient_data_accuracy.get(system)
        lines.append(
            f"| {system} | {fmt(m.get('precision'))} | {fmt(m.get('recall'))} "
            f"| {fmt(m.get('f1'))} | {fmt(acc)} | {fmt(idacc)} |"
        )

    lines += [
        "",
        "## Other categories (keyword-recall proxy against reference evidence)",
        "",
        "| System | multi_hop | rfi_dedup | sld_topology | cascade_scenarios |",
        "|---|---|---|---|---|",
    ]
    for system in ["bm25", "vanilla_rag", "ours"]:
        cat_row = category_accuracy.get(system, {})
        lines.append(
            f"| {system} | {fmt(cat_row.get('multi_hop'))} | {fmt(cat_row.get('rfi_dedup'))} "
            f"| {fmt(cat_row.get('sld_topology'))} | {fmt(cat_row.get('cascade_scenarios'))} |"
        )

    lines += [
        "",
        "## Reading this table",
        "",
        "- **ours** routes each category to the real engine: the deterministic "
        "compliance evaluator for deviations, the real YOLOv8+Hough+NetworkX "
        "pipeline for sld_topology (SLD_001-005), the real Monte Carlo cascade "
        "simulator for cascade_scenarios, and fused BM25+vector+RRF+rerank "
        "retrieval for multi_hop/rfi_dedup/SLD_006-010.",
        "- **vanilla_rag** never emits `INSUFFICIENT_DATA` by design (see "
        "`benchmark/systems/vanilla_rag.py`) — its INSUFFICIENT_DATA accuracy "
        "column is expected to be near zero. That is the point being "
        "demonstrated, not a bug.",
        "- **bm25** compares raw numbers with no unit conversion — expect it to "
        "fail exactly the unit-conversion-trap questions (DEV_001, DEV_007) "
        "even though it gets same-unit comparisons right.",
        "- **Ctrl+F (manual)** numbers are a *modeled estimate* "
        "(see `data/benchmark/ctrl_f_baseline.json`'s `note` field), not an "
        "empirical timed trial — replace with a real stopwatch run before "
        "citing this row as measured data in the pitch.",
        "",
        "## Caveat: the 'other categories' table is a weak proxy",
        "",
        "Keyword-recall against reference text rewards surface lexical overlap, "
        "not correctness — a system that returns a concise computed number "
        "(e.g. `ours` on cascade_scenarios: an actual simulated handover day) "
        "can score *lower* on this metric than a retrieval baseline that dumps "
        "verbose prose sharing more words with the reference answer, even when "
        "the computed number is the one that's actually right. Treat this table "
        "as a rough retrieval-coverage signal, not a correctness measure — the "
        "deviation-detection table above is the rigorous one.",
        "",
        "This run's `sld_topology` numbers also surfaced a real finding, not a "
        "scoring artifact: `ours` answers SLD_001-005 by reading "
        "`data/sld_results.json` directly, and 3 of the 5 topologies currently "
        "come back with zero detected source-to-load paths (Hough wire "
        "connectivity gap, not a redundancy judgment) — worth fixing in the SLD "
        "pipeline before relying on this category in a pitch. Check "
        "`per_question_results.json` under `SLD_001`-`SLD_005` for the exact "
        "`ours` answer per topology.",
        "",
        "See `pr_curve.png` for the precision/recall tradeoff as the tolerance "
        "band on `ours` widens, and `per_question_results.json` for every "
        "system's answer to every question.",
    ]
    return "\n".join(lines)


def pr_curve_png(
    *,
    sweep_points: list[dict[str, Any]],
    fixed_points: dict[str, tuple[float | None, float | None]],
    output_path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 6))

    xs = [p["recall"] for p in sweep_points if p["recall"] is not None]
    ys = [p["precision"] for p in sweep_points if p["precision"] is not None]
    ax.plot(xs, ys, marker="o", color="#F5A623", label="ours (tolerance sweep 0-20%)", zorder=3)
    for p in sweep_points:
        if p["tolerance_pct"] in (0.0, 5.0, 10.0, 20.0) and p["recall"] is not None:
            ax.annotate(f"{p['tolerance_pct']:.0f}%", (p["recall"], p["precision"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=8, color="#8B93A1")

    markers = {
        "bm25": ("s", "#60A5FA"),
        "vanilla_rag": ("^", "#EF4444"),
        "ctrl_f": ("D", "#9CA3AF"),
    }
    for name, (marker, color) in markers.items():
        recall, precision = fixed_points.get(name, (None, None))
        if recall is not None and precision is not None:
            ax.scatter(
                [recall], [precision], marker=marker, s=90, color=color, label=name, zorder=4
            )

    ax.set_xlabel("Recall (of true deviations flagged)")
    ax.set_ylabel("Precision (of flagged deviations that are real)")
    ax.set_title("Deviation detection: precision vs recall")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def per_question_json(
    questions: list[BenchmarkQuestion],
    answers_by_system: dict[str, dict[str, SystemAnswer]],
) -> list[dict[str, Any]]:
    rows = []
    for q in questions:
        row_answers: dict[str, Any] = {}
        for system, answers in answers_by_system.items():
            answer = answers.get(q.id)
            row_answers[system] = answer.model_dump() if answer is not None else None
        rows.append(
            {
                "id": q.id,
                "category": q.category,
                "question": q.question,
                "expected_answer": q.expected_answer,
                "answers": row_answers,
            }
        )
    return rows
