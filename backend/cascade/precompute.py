"""Offline batch script: runs the full Monte Carlo sweep + mitigation ranking
and ships the results as JSON, per CLAUDE.md's "precompute everything" rule.

The frontend slider must respond in <16ms — it reads data/cascade_lookup.json
once on load and does all further interpolation client-side. It must never
trigger a new simulation on a drag event.

Usage: python -m cascade.precompute
"""

import json
from pathlib import Path

from cascade.dag import (
    HANDOVER_TASK_ID,
    TARGET_HANDOVER_DAY,
    TRANSFORMER_DELAY_TASK_ID,
    build_dag,
    build_tasks,
)
from cascade.mitigate import run_mitigation_analysis
from cascade.simulate import sweep_transformer_delay

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    tasks = build_tasks()
    (DATA_DIR / "cascade_tasks.json").write_text(
        json.dumps([t.model_dump() for t in tasks], indent=2)
    )
    print(f"Wrote {len(tasks)} tasks to data/cascade_tasks.json")

    dag = build_dag()
    sweep = sweep_transformer_delay(
        dag,
        transformer_task_id=TRANSFORMER_DELAY_TASK_ID,
        sink_task_id=HANDOVER_TASK_ID,
        target_handover_day=TARGET_HANDOVER_DAY,
        weeks_range=(0.0, 8.0),
        step_weeks=0.5,
        n_runs=10_000,
        seed=42,
    )
    (DATA_DIR / "cascade_lookup.json").write_text(
        json.dumps(
            {
                "target_handover_day": TARGET_HANDOVER_DAY,
                "points": [p.model_dump() for p in sweep],
            },
            indent=2,
        )
    )
    print(f"Wrote {len(sweep)} sweep points to data/cascade_lookup.json")

    mitigations = run_mitigation_analysis()
    (DATA_DIR / "cascade_mitigations.json").write_text(
        json.dumps([m.model_dump() for m in mitigations], indent=2)
    )
    print(f"Wrote {len(mitigations)} ranked mitigations to data/cascade_mitigations.json")


if __name__ == "__main__":
    main()
