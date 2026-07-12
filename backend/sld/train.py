"""Fine-tunes YOLOv8n on the synthesized SLD symbol dataset.

Usage: python -m sld.train
"""

from pathlib import Path

from ultralytics import YOLO  # type: ignore[attr-defined]

DATASET_YAML = Path(__file__).resolve().parent.parent.parent / "data" / "sld_dataset" / "data.yaml"
RUNS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sld_runs"


def train(epochs: int = 15, imgsz: int = 256, batch: int = 32) -> Path:
    model = YOLO("yolov8n.pt")
    model.train(
        data=str(DATASET_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=8,
        project=str(RUNS_DIR),
        name="symbol_detector",
        exist_ok=True,
        verbose=True,
    )
    best_weights = RUNS_DIR / "symbol_detector" / "weights" / "best.pt"
    return best_weights


if __name__ == "__main__":
    weights_path = train()
    print(f"Best weights: {weights_path}")
