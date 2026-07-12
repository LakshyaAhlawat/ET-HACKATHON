"""Defines and renders the 5 evaluation single-line diagrams: hand-designed
2N power topologies (3 with a planted single point of failure, 2 fully
redundant), used to validate detect.py/ocr.py/connect.py/redundancy.py
against a known-correct ground truth.

"Source" for redundancy analysis means a transformer node — the diagram's
7 detection classes don't include a separate utility/grid symbol, so a
transformer is where utility power enters the diagram.
"""

from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFont

from sld.symbols import SPRITE_SIZE, render_symbol

IMAGE_SIZE = (900, 700)
GRID_SPACING = 32


@dataclass
class Node:
    node_id: str
    node_class: str
    x: int
    y: int
    label: str


@dataclass
class SldTopology:
    topology_id: str
    name: str
    nodes: list[Node]
    edges: list[tuple[str, str]]
    expected_2n_holds: bool
    expected_spof: str | None = field(default=None)


def _grid_background() -> Image.Image:
    img = Image.new("RGB", IMAGE_SIZE, (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for x in range(0, IMAGE_SIZE[0], GRID_SPACING):
        draw.line((x, 0, x, IMAGE_SIZE[1]), fill=(235, 235, 235), width=1)
    for y in range(0, IMAGE_SIZE[1], GRID_SPACING):
        draw.line((0, y, IMAGE_SIZE[0], y), fill=(235, 235, 235), width=1)
    return img


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def render_topology(topology: SldTopology) -> Image.Image:
    img = _grid_background()
    draw = ImageDraw.Draw(img)
    font = _font(13)

    by_id = {n.node_id: n for n in topology.nodes}
    for a_id, b_id in topology.edges:
        a, b = by_id[a_id], by_id[b_id]
        draw.line((a.x, a.y, b.x, b.y), fill=(20, 20, 20), width=2)

    half = SPRITE_SIZE // 2
    for node in topology.nodes:
        sprite = render_symbol(node.node_class)
        img.paste(sprite, (node.x - half, node.y - half), sprite)
        draw.text((node.x - half, node.y + half + 2), node.label, fill=(20, 20, 20), font=font)

    return img


def _t1_true_2n() -> SldTopology:
    nodes = [
        Node("XFMR_A", "transformer", 120, 100, "TX-01 2000kVA"),
        Node("BRK_A1", "breaker", 120, 220, "BRK-A1"),
        Node("BUS_A", "busbar", 120, 320, "BUS-A"),
        Node("UPS_A", "ups", 120, 420, "UPS-A 500kVA"),
        Node("BRK_A2", "breaker", 120, 520, "BRK-A2"),
        Node("XFMR_B", "transformer", 700, 100, "TX-02 2000kVA"),
        Node("BRK_B1", "breaker", 700, 220, "BRK-B1"),
        Node("BUS_B", "busbar", 700, 320, "BUS-B"),
        Node("UPS_B", "ups", 700, 420, "UPS-B 500kVA"),
        Node("BRK_B2", "breaker", 700, 520, "BRK-B2"),
        Node("IT_LOAD", "it_load", 410, 620, "IT-LOAD-01"),
    ]
    edges = [
        ("XFMR_A", "BRK_A1"),
        ("BRK_A1", "BUS_A"),
        ("BUS_A", "UPS_A"),
        ("UPS_A", "BRK_A2"),
        ("BRK_A2", "IT_LOAD"),
        ("XFMR_B", "BRK_B1"),
        ("BRK_B1", "BUS_B"),
        ("BUS_B", "UPS_B"),
        ("UPS_B", "BRK_B2"),
        ("BRK_B2", "IT_LOAD"),
    ]
    return SldTopology("sld-01", "True 2N (fully redundant)", nodes, edges, True, None)


def _t2_spof_shared_ats() -> SldTopology:
    nodes = [
        Node("XFMR_A", "transformer", 120, 100, "TX-01 1600kVA"),
        Node("BRK_A1", "breaker", 120, 220, "BRK-A1"),
        Node("UPS_A", "ups", 120, 340, "UPS-A 400kVA"),
        Node("XFMR_B", "transformer", 700, 100, "TX-02 1600kVA"),
        Node("BRK_B1", "breaker", 700, 220, "BRK-B1"),
        Node("UPS_B", "ups", 700, 340, "UPS-B 400kVA"),
        Node("ATS", "ats", 410, 460, "ATS-01"),
        Node("BRK_OUT", "breaker", 410, 560, "BRK-OUT"),
        Node("IT_LOAD", "it_load", 410, 640, "IT-LOAD-01"),
    ]
    edges = [
        ("XFMR_A", "BRK_A1"),
        ("BRK_A1", "UPS_A"),
        ("UPS_A", "ATS"),
        ("XFMR_B", "BRK_B1"),
        ("BRK_B1", "UPS_B"),
        ("UPS_B", "ATS"),
        ("ATS", "BRK_OUT"),
        ("BRK_OUT", "IT_LOAD"),
    ]
    return SldTopology(
        "sld-02", "SPOF: shared ATS before load", nodes, edges, False, "ATS"
    )


def _t3_spof_shared_bus() -> SldTopology:
    nodes = [
        Node("XFMR_A", "transformer", 120, 80, "TX-01 2000kVA"),
        Node("BRK_A1", "breaker", 120, 200, "BRK-A1"),
        Node("XFMR_B", "transformer", 700, 80, "TX-02 2000kVA"),
        Node("BRK_B1", "breaker", 700, 200, "BRK-B1"),
        Node("BUS_SHARED", "busbar", 410, 300, "BUS-MAIN"),
        Node("UPS_A", "ups", 250, 420, "UPS-A 500kVA"),
        Node("UPS_B", "ups", 570, 420, "UPS-B 500kVA"),
        Node("IT_LOAD", "it_load", 410, 560, "IT-LOAD-01"),
    ]
    edges = [
        ("XFMR_A", "BRK_A1"),
        ("BRK_A1", "BUS_SHARED"),
        ("XFMR_B", "BRK_B1"),
        ("BRK_B1", "BUS_SHARED"),
        ("BUS_SHARED", "UPS_A"),
        ("BUS_SHARED", "UPS_B"),
        ("UPS_A", "IT_LOAD"),
        ("UPS_B", "IT_LOAD"),
    ]
    return SldTopology(
        "sld-03", "SPOF: shared busbar upstream", nodes, edges, False, "BUS_SHARED"
    )


def _t4_true_2n_with_generator() -> SldTopology:
    nodes = [
        Node("XFMR_A", "transformer", 120, 80, "TX-01 2000kVA"),
        Node("GEN_A", "generator", 260, 80, "GEN-01 1500kW"),
        Node("ATS_A", "ats", 190, 190, "ATS-A"),
        Node("BRK_A1", "breaker", 190, 300, "BRK-A1"),
        Node("UPS_A", "ups", 190, 410, "UPS-A 500kVA"),
        Node("XFMR_B", "transformer", 700, 80, "TX-02 2000kVA"),
        Node("BRK_B1", "breaker", 700, 220, "BRK-B1"),
        Node("UPS_B", "ups", 700, 410, "UPS-B 500kVA"),
        Node("IT_LOAD", "it_load", 410, 560, "IT-LOAD-01"),
    ]
    edges = [
        ("XFMR_A", "ATS_A"),
        ("GEN_A", "ATS_A"),
        ("ATS_A", "BRK_A1"),
        ("BRK_A1", "UPS_A"),
        ("UPS_A", "IT_LOAD"),
        ("XFMR_B", "BRK_B1"),
        ("BRK_B1", "UPS_B"),
        ("UPS_B", "IT_LOAD"),
    ]
    return SldTopology(
        "sld-04", "True 2N with generator backup on path A", nodes, edges, True, None
    )


def _t5_spof_final_breaker() -> SldTopology:
    nodes = [
        Node("XFMR_A", "transformer", 120, 100, "TX-01 2000kVA"),
        Node("BRK_A1", "breaker", 120, 220, "BRK-A1"),
        Node("UPS_A", "ups", 120, 340, "UPS-A 500kVA"),
        Node("XFMR_B", "transformer", 700, 100, "TX-02 2000kVA"),
        Node("BRK_B1", "breaker", 700, 220, "BRK-B1"),
        Node("UPS_B", "ups", 700, 340, "UPS-B 500kVA"),
        Node("BRK_FINAL", "breaker", 410, 460, "BRK-FINAL"),
        Node("IT_LOAD", "it_load", 410, 580, "IT-LOAD-01"),
    ]
    edges = [
        ("XFMR_A", "BRK_A1"),
        ("BRK_A1", "UPS_A"),
        ("UPS_A", "BRK_FINAL"),
        ("XFMR_B", "BRK_B1"),
        ("BRK_B1", "UPS_B"),
        ("UPS_B", "BRK_FINAL"),
        ("BRK_FINAL", "IT_LOAD"),
    ]
    return SldTopology(
        "sld-05", "SPOF: shared final breaker before load", nodes, edges, False, "BRK_FINAL"
    )


def all_topologies() -> list[SldTopology]:
    return [
        _t1_true_2n(),
        _t2_spof_shared_ats(),
        _t3_spof_shared_bus(),
        _t4_true_2n_with_generator(),
        _t5_spof_final_breaker(),
    ]
