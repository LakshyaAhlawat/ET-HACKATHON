"""CLI entrypoint: runs bm25 / vanilla_rag / ours against the 50-question
ground-truth key (+ 5 PR-curve controls), scores them, and writes:

  data/benchmark/results/results_table.md
  data/benchmark/results/pr_curve.png
  data/benchmark/results/per_question_results.json
  data/benchmark/results/ragas_results.json   (only with --with-ragas)

Usage:  cd backend && .venv/Scripts/python.exe -m benchmark.run [--with-ragas]
"""

import asyncio
import json
import sys
import time
from typing import Any

from benchmark import report
from benchmark.schema import (
    REPO_ROOT,
    BenchmarkQuestion,
    SystemAnswer,
    load_ground_truth,
    load_pr_curve_controls,
)
from benchmark.scoring import (
    confusion_for_deviation_detection,
    exact_match_accuracy,
    insufficient_data_accuracy,
    retrieval_keyword_recall,
    tolerance_sweep,
)
from benchmark.systems import bm25_baseline, ours, vanilla_rag

RESULTS_DIR = REPO_ROOT / "data" / "benchmark" / "results"
SYSTEMS = {"bm25": bm25_baseline, "vanilla_rag": vanilla_rag, "ours": ours}
NON_DEVIATION_CATEGORIES = ["multi_hop", "rfi_dedup", "sld_topology", "cascade_scenarios"]

AnswersBySystem = dict[str, dict[str, SystemAnswer]]


def run_all_systems(questions: list[BenchmarkQuestion]) -> AnswersBySystem:
    answers: AnswersBySystem = {name: {} for name in SYSTEMS}
    for name, module in SYSTEMS.items():
        print(f"  running {name} on {len(questions)} questions...", file=sys.stderr)
        t0 = time.perf_counter()
        for q in questions:
            answers[name][q.id] = module.answer_question(q)
        print(f"    done in {time.perf_counter() - t0:.1f}s", file=sys.stderr)
    return answers


def score(
    questions: list[BenchmarkQuestion], answers: AnswersBySystem
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, float]], dict[str, float | None]]:
    deviation_questions = [q for q in questions if q.category == "planted_deviations"]

    deviation_metrics: dict[str, dict[str, Any]] = {}
    category_accuracy: dict[str, dict[str, float]] = {}
    id_accuracy: dict[str, float | None] = {}

    for system, system_answers in answers.items():
        counts = confusion_for_deviation_detection(deviation_questions, system_answers)
        deviation_metrics[system] = {
            "precision": counts.precision, "recall": counts.recall, "f1": counts.f1,
            "tp": counts.tp, "fp": counts.fp, "fn": counts.fn, "tn": counts.tn,
        }
        id_accuracy[system] = insufficient_data_accuracy(deviation_questions, system_answers)

        category_accuracy[system] = {
            "planted_deviations": exact_match_accuracy(deviation_questions, system_answers)
        }
        for category in NON_DEVIATION_CATEGORIES:
            cat_questions = [q for q in questions if q.category == category]
            if not cat_questions:
                continue
            scores = [
                retrieval_keyword_recall(q, system_answers.get(q.id)).keyword_recall
                for q in cat_questions
            ]
            category_accuracy[system][category] = sum(scores) / len(scores) if scores else 0.0

    return deviation_metrics, category_accuracy, id_accuracy


async def run_ragas(
    questions: list[BenchmarkQuestion], answers: AnswersBySystem
) -> dict[str, dict[str, dict[str, Any]]]:
    from benchmark.ragas_eval import RAGAS_CATEGORIES, score_answer

    ragas_questions = [q for q in questions if q.category in RAGAS_CATEGORIES]
    results: dict[str, dict[str, dict[str, Any]]] = {}
    for system, system_answers in answers.items():
        if system == "ours":
            continue  # scored separately below
        results[system] = {}
        for q in ragas_questions:
            ans = system_answers.get(q.id)
            if ans is None:
                continue
            results[system][q.id] = await score_answer(q, ans)
    results["ours"] = {}
    for q in ragas_questions:
        ans = answers["ours"].get(q.id)
        if ans is not None:
            results["ours"][q.id] = await score_answer(q, ans)
    return results


def main() -> None:
    with_ragas = "--with-ragas" in sys.argv
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    questions = load_ground_truth() + load_pr_curve_controls()
    print(f"Loaded {len(questions)} questions ({len(load_ground_truth())} official + "
          f"{len(load_pr_curve_controls())} PR-curve controls)", file=sys.stderr)

    answers = run_all_systems(questions)
    deviation_metrics, category_accuracy, id_accuracy = score(questions, answers)

    deviation_questions = [q for q in questions if q.category == "planted_deviations"]
    sweep = tolerance_sweep(deviation_questions, answers["ours"])

    fixed_points: dict[str, tuple[float | None, float | None]] = {}
    for system in ["bm25", "vanilla_rag"]:
        m = deviation_metrics[system]
        fixed_points[system] = (m["recall"], m["precision"])
    ctrl_f = report._read_ctrl_f(REPO_ROOT)
    dd = ctrl_f.get("deviation_detection", {})
    fixed_points["ctrl_f"] = (dd.get("recall"), dd.get("precision"))

    report.pr_curve_png(
        sweep_points=sweep, fixed_points=fixed_points, output_path=RESULTS_DIR / "pr_curve.png"
    )

    table_md = report.markdown_results_table(
        deviation_metrics=deviation_metrics,
        category_accuracy=category_accuracy,
        insufficient_data_accuracy=id_accuracy,
        repo_root=REPO_ROOT,
    )
    (RESULTS_DIR / "results_table.md").write_text(table_md, encoding="utf-8")

    per_q = report.per_question_json(questions, answers)
    (RESULTS_DIR / "per_question_results.json").write_text(
        json.dumps(per_q, indent=2, default=str), encoding="utf-8"
    )
    (RESULTS_DIR / "tolerance_sweep.json").write_text(json.dumps(sweep, indent=2), encoding="utf-8")

    if with_ragas:
        print("  running RAGAS (requires GROQ_API_KEY, network)...", file=sys.stderr)
        ragas_results = asyncio.run(run_ragas(questions, answers))
        (RESULTS_DIR / "ragas_results.json").write_text(
            json.dumps(ragas_results, indent=2, default=str), encoding="utf-8"
        )

    print(f"\nWrote results to {RESULTS_DIR}", file=sys.stderr)
    print(table_md)


if __name__ == "__main__":
    main()
