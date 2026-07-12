"""Renders simplified IEEE-315-style single-line-diagram symbols as small
RGBA sprites, used to synthesize YOLO training data and the 5 evaluation
SLDs. Not scanned from real drawings — synthesised, per CLAUDE.md's data
provenance policy.
"""

from PIL import Image, ImageDraw, ImageFont

CLASSES = ["transformer", "breaker", "ats", "ups", "generator", "busbar", "it_load"]
SPRITE_SIZE = 64
LINE_WIDTH = 3
INK = (20, 20, 20, 255)


def _blank() -> Image.Image:
    return Image.new("RGBA", (SPRITE_SIZE, SPRITE_SIZE), (0, 0, 0, 0))


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_transformer() -> Image.Image:
    # Two overlapping circles: the classic two-winding transformer symbol.
    img = _blank()
    draw = ImageDraw.Draw(img)
    r = 16
    cx = SPRITE_SIZE // 2
    draw.ellipse((cx - r, 10, cx + r, 10 + 2 * r), outline=INK, width=LINE_WIDTH)
    draw.ellipse((cx - r, 26, cx + r, 26 + 2 * r), outline=INK, width=LINE_WIDTH)
    return img


def draw_breaker() -> Image.Image:
    # A square with a full X: the ANSI circuit breaker symbol. Both diagonals
    # (not just one) so it's not confusable with a single-diagonal square.
    img = _blank()
    draw = ImageDraw.Draw(img)
    pad = 12
    draw.rectangle((pad, pad, SPRITE_SIZE - pad, SPRITE_SIZE - pad), outline=INK, width=LINE_WIDTH)
    draw.line((pad, pad, SPRITE_SIZE - pad, SPRITE_SIZE - pad), fill=INK, width=LINE_WIDTH)
    draw.line((pad, SPRITE_SIZE - pad, SPRITE_SIZE - pad, pad), fill=INK, width=LINE_WIDTH)
    return img


def draw_ats() -> Image.Image:
    # A double-throw switch: common node, two contacts, one live blade.
    img = _blank()
    draw = ImageDraw.Draw(img)
    common = (SPRITE_SIZE // 2, SPRITE_SIZE - 8)
    contact_a = (16, 10)
    contact_b = (SPRITE_SIZE - 16, 10)
    r = 4
    for pt in (contact_a, contact_b, common):
        draw.ellipse((pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r), outline=INK, width=2)
    draw.line((common[0], common[1], contact_a[0], contact_a[1] + r), fill=INK, width=LINE_WIDTH)
    draw.line((contact_b[0], contact_b[1] + r, contact_b[0], common[1]), fill=INK, width=2)
    return img


def draw_ups() -> Image.Image:
    # A hexagon (distinct silhouette from the other box-shaped symbols) with
    # a battery glyph (long/short parallel bars) inside.
    img = _blank()
    draw = ImageDraw.Draw(img)
    cx, cy, r = SPRITE_SIZE // 2, SPRITE_SIZE // 2, 26
    points = [
        (cx + r * dx, cy + r * dy)
        for dx, dy in (
            (0, -1),
            (0.87, -0.5),
            (0.87, 0.5),
            (0, 1),
            (-0.87, 0.5),
            (-0.87, -0.5),
        )
    ]
    draw.polygon(points, outline=INK, width=LINE_WIDTH)
    mid = SPRITE_SIZE // 2
    draw.line((mid - 8, mid - 4, mid - 8, mid + 4), fill=INK, width=3)
    draw.line((mid + 8, mid - 8, mid + 8, mid + 8), fill=INK, width=3)
    draw.line((mid - 8, mid, mid + 8, mid), fill=INK, width=2)
    return img


def draw_generator() -> Image.Image:
    # A circle with a "G" — the standard generator symbol.
    img = _blank()
    draw = ImageDraw.Draw(img)
    pad = 8
    draw.ellipse((pad, pad, SPRITE_SIZE - pad, SPRITE_SIZE - pad), outline=INK, width=LINE_WIDTH)
    font = _font(28)
    bbox = draw.textbbox((0, 0), "G", font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((SPRITE_SIZE - w) / 2 - bbox[0], (SPRITE_SIZE - h) / 2 - bbox[1]),
        "G",
        fill=INK,
        font=font,
    )
    return img


def draw_busbar() -> Image.Image:
    # A thick horizontal bar.
    img = _blank()
    draw = ImageDraw.Draw(img)
    mid = SPRITE_SIZE // 2
    draw.rectangle((4, mid - 4, SPRITE_SIZE - 4, mid + 4), fill=INK)
    return img


def draw_it_load() -> Image.Image:
    # A rectangle with a cross-hatch grid (server rack grille) — busier and
    # denser than breaker's single X or UPS's hexagon, not just a square
    # with horizontal-only lines that a blurred/rotated breaker could mimic.
    img = _blank()
    draw = ImageDraw.Draw(img)
    pad = 10
    draw.rectangle((pad, pad, SPRITE_SIZE - pad, SPRITE_SIZE - pad), outline=INK, width=LINE_WIDTH)
    for y in range(pad + 8, SPRITE_SIZE - pad, 8):
        draw.line((pad, y, SPRITE_SIZE - pad, y), fill=INK, width=1)
    for x in range(pad + 8, SPRITE_SIZE - pad, 8):
        draw.line((x, pad, x, SPRITE_SIZE - pad), fill=INK, width=1)
    return img


_RENDERERS = {
    "transformer": draw_transformer,
    "breaker": draw_breaker,
    "ats": draw_ats,
    "ups": draw_ups,
    "generator": draw_generator,
    "busbar": draw_busbar,
    "it_load": draw_it_load,
}


def render_symbol(class_name: str) -> Image.Image:
    return _RENDERERS[class_name]()
