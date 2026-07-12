"""Synthesizes YOLO training data: symbol sprites placed at random
positions/rotations on grid backgrounds, with auto-generated labels.

Usage: python -m sld.dataset
"""

import random
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

from sld.symbols import CLASSES, SPRITE_SIZE, render_symbol

IMAGE_SIZE = 640
GRID_SPACING = 32
MIN_SYMBOLS = 4
MAX_SYMBOLS = 10
MIN_SCALE = 1.0
MAX_SCALE = 2.2

_TAG_PREFIXES = {
    "transformer": "TX",
    "breaker": "BRK",
    "ats": "ATS",
    "ups": "UPS",
    "generator": "GEN",
    "busbar": "BUS",
    "it_load": "LOAD",
}


def _font(size: int = 12) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _random_tag(rng: random.Random, class_name: str) -> str:
    prefix = _TAG_PREFIXES[class_name]
    return f"{prefix}-{rng.randint(1, 99):02d}"
ROTATIONS = [0, 90, 180, 270]

ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = ROOT / "data" / "sld_dataset"

Label = tuple[int, float, float, float, float]


def _grid_background(size: int = IMAGE_SIZE) -> Image.Image:
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for x in range(0, size, GRID_SPACING):
        draw.line((x, 0, x, size), fill=(230, 230, 230), width=1)
    for y in range(0, size, GRID_SPACING):
        draw.line((0, y, size, y), fill=(230, 230, 230), width=1)
    return img


def _overlaps(
    box: tuple[int, int, int, int], placed: list[tuple[int, int, int, int]], margin: int = 6
) -> bool:
    x0, y0, x1, y1 = box
    for px0, py0, px1, py1 in placed:
        if x0 - margin < px1 and x1 + margin > px0 and y0 - margin < py1 and y1 + margin > py0:
            return True
    return False


def generate_image(
    rng: random.Random, n_symbols: int | None = None
) -> tuple[Image.Image, list[Label]]:
    """Returns (image, labels); labels are (class_idx, x_center, y_center,
    width, height), all normalized to [0, 1] per YOLO convention.

    Draws connecting wires between symbols (as real SLDs have) BEFORE
    pasting the symbol sprites on top — a detector trained only on isolated
    symbols with no wire clutter degrades sharply on real-looking diagrams
    (confidence collapses, classes get confused near line crossings).
    """
    img = _grid_background()
    n = n_symbols if n_symbols is not None else rng.randint(MIN_SYMBOLS, MAX_SYMBOLS)
    placed: list[tuple[int, tuple[int, int, int, int], Image.Image]] = []

    attempts = 0
    while len(placed) < n and attempts < n * 20:
        attempts += 1
        class_idx = rng.randrange(len(CLASSES))
        scale = rng.uniform(MIN_SCALE, MAX_SCALE)
        rotation = rng.choice(ROTATIONS)

        sprite = render_symbol(CLASSES[class_idx])
        size = int(SPRITE_SIZE * scale)
        sprite = sprite.resize((size, size), Image.Resampling.LANCZOS).rotate(
            rotation, expand=True
        )

        w, h = sprite.size
        max_x, max_y = IMAGE_SIZE - w - 10, IMAGE_SIZE - h - 10
        if max_x <= 10 or max_y <= 10:
            continue
        x0, y0 = rng.randint(10, max_x), rng.randint(10, max_y)
        box = (x0, y0, x0 + w, y0 + h)
        if _overlaps(box, [p[1] for p in placed]):
            continue

        placed.append((class_idx, box, sprite))

    if placed and rng.random() < 0.7:
        draw = ImageDraw.Draw(img)
        centers = [((b[0] + b[2]) // 2, (b[1] + b[3]) // 2) for _, b, _ in placed]
        n_wires = rng.randint(1, min(4, len(centers)))
        for _ in range(n_wires):
            a, b = rng.sample(range(len(centers)), 2) if len(centers) >= 2 else (0, 0)
            draw.line((centers[a], centers[b]), fill=(20, 20, 20), width=2)

    label_draw = ImageDraw.Draw(img)
    font = _font()
    labels: list[Label] = []
    for class_idx, box, sprite in placed:
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        img.paste(sprite, (x0, y0), sprite)
        if rng.random() < 0.85:
            tag = _random_tag(rng, CLASSES[class_idx])
            label_draw.text((x0, y1 + 2), tag, fill=(20, 20, 20), font=font)
        labels.append(
            (
                class_idx,
                (x0 + w / 2) / IMAGE_SIZE,
                (y0 + h / 2) / IMAGE_SIZE,
                w / IMAGE_SIZE,
                h / IMAGE_SIZE,
            )
        )

    return img, labels


def _write_split(split: str, n_images: int, seed: int) -> None:
    images_dir = DATASET_DIR / "images" / split
    labels_dir = DATASET_DIR / "labels" / split
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    for i in range(n_images):
        img, labels = generate_image(rng)
        img.save(images_dir / f"{split}_{i:04d}.png")
        label_lines = [f"{c} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}" for c, cx, cy, w, h in labels]
        (labels_dir / f"{split}_{i:04d}.txt").write_text("\n".join(label_lines))


def build_dataset(n_train: int = 900, n_val: int = 150) -> Path:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    _write_split("train", n_train, seed=1)
    _write_split("val", n_val, seed=2)

    data_yaml = {
        "path": str(DATASET_DIR),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(CLASSES)},
    }
    yaml_path = DATASET_DIR / "data.yaml"
    yaml_path.write_text(yaml.safe_dump(data_yaml, sort_keys=False))
    return yaml_path


if __name__ == "__main__":
    path = build_dataset()
    print(f"Dataset written to {DATASET_DIR} (config: {path})")
