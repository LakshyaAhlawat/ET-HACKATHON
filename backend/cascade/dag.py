"""Builds the ~120-task data-centre EPC schedule DAG.

Structure: a civil/structural prerequisite chain, ~11 discipline chains
(procurement -> manufacturing -> FAT -> shipping -> receiving -> install ->
site test), converging through per-group IST sub-tests -> integrated systems
test -> commissioning levels 3/4/5 -> regulatory approvals -> handover.

The transformer chain is deliberately the pitch's bottleneck: its site
install sits in an outdoor switchyard, which is the one task type subject to
the monsoon SeasonalWindow. A transformer delay that's absorbed by float
under normal conditions can push the switchyard install into the monsoon
window, multiplying its duration — a 3-week supply delay amplifying into a
larger handover slip, not a 1:1 pass-through.
"""

import networkx as nx

from app.models.cascade import SeasonalWindow, Task

# Monsoon window: ~day 150-210 (roughly months 5-7 of an 11-month build).
_MONSOON = SeasonalWindow(start_day=150, end_day=210, multiplier=1.35)

TRANSFORMER_DELAY_TASK_ID = "XFMR-PROCURE"
HANDOVER_TASK_ID = "HANDOVER"
# Baseline target handover, in project days from mobilization. Calibrated
# against the simulated distribution (zero-delay P50 ~= 222 days, P90 ~= 237
# days) so P(slip) starts near the natural tail risk and climbs meaningfully
# as the transformer delay grows — not pinned to an arbitrary loose date.
TARGET_HANDOVER_DAY = 240.0

# code, display name, manufacture_mean, manufacture_std, ship_mean, ship_std
_DISCIPLINES = [
    ("XFMR", "Utility Transformer", 70.0, 10.0, 21.0, 5.0),
    ("DG", "Diesel Generator", 60.0, 9.0, 18.0, 4.0),
    ("CHW", "Chiller Plant", 55.0, 8.0, 14.0, 4.0),
    ("UPS", "UPS & Battery", 35.0, 6.0, 10.0, 3.0),
    ("FLS", "Fire & Life Safety", 25.0, 5.0, 7.0, 2.0),
    ("ITN", "IT Networking & Security", 20.0, 4.0, 7.0, 2.0),
    ("BMS", "Building Management System", 22.0, 4.0, 6.0, 2.0),
    ("ELEC", "LV Electrical Distribution", 30.0, 5.0, 9.0, 3.0),
    ("SCAC", "Structured Cabling & Access Control", 18.0, 3.0, 5.0, 2.0),
    ("PLMB", "Plumbing & Water Treatment", 24.0, 4.0, 7.0, 2.0),
    ("VERT", "Elevators & Vertical Transport", 45.0, 7.0, 12.0, 3.0),
]

_CIVIL_TASKS: list[tuple[str, str, float, float, list[str]]] = [
    ("CIVIL-MOBILIZE", "Site Mobilization", 5.0, 1.0, []),
    ("CIVIL-EXCAVATE", "Excavation & Earthwork", 12.0, 3.0, ["CIVIL-MOBILIZE"]),
    ("CIVIL-SWITCHYARD", "Outdoor Switchyard Civil Works", 15.0, 3.0, ["CIVIL-EXCAVATE"]),
    ("CIVIL-FOUNDATION", "Foundation & Footings", 20.0, 4.0, ["CIVIL-EXCAVATE"]),
    ("CIVIL-STRUCTURE", "Structural Steel & Slab", 35.0, 6.0, ["CIVIL-FOUNDATION"]),
    ("CIVIL-ENVELOPE", "Building Envelope & Roofing", 25.0, 5.0, ["CIVIL-STRUCTURE"]),
    ("CIVIL-RAISEDFLOOR", "Raised Floor Install", 10.0, 2.0, ["CIVIL-ENVELOPE"]),
    ("CIVIL-CONTAINMENT", "Cable Tray & Containment", 12.0, 3.0, ["CIVIL-RAISEDFLOOR"]),
    ("CIVIL-FITOUT", "Interior Fit-Out & Finishes", 18.0, 4.0, ["CIVIL-CONTAINMENT"]),
]


def _discipline_tasks(
    code: str,
    name: str,
    manufacture_mean: float,
    manufacture_std: float,
    ship_mean: float,
    ship_std: float,
    civil_ready_id: str,
) -> tuple[list[Task], str]:
    design_id, procure_id = f"{code}-DESIGN", f"{code}-PROCURE"
    manufacture_id, fat_id = f"{code}-MFG", f"{code}-FAT"
    ship_id, receive_id = f"{code}-SHIP", f"{code}-RECEIVE"
    install_id, test_id = f"{code}-INSTALL", f"{code}-SAT"

    install_predecessors = [receive_id, civil_ready_id]
    install_seasonal = None
    if code == "XFMR":
        # The one install task actually exposed to the outdoor monsoon window.
        install_predecessors = [receive_id, "CIVIL-SWITCHYARD"]
        install_seasonal = _MONSOON

    tasks = [
        Task(
            task_id=design_id,
            name=f"{name}: Design & Submittal Approval",
            discipline=code,
            phase="design",
            duration_mean_days=12.0,
            duration_std_days=3.0,
            predecessors=[],
        ),
        Task(
            task_id=procure_id,
            name=f"{name}: Procurement / PO Issuance",
            discipline=code,
            phase="procure",
            duration_mean_days=8.0,
            duration_std_days=2.0,
            predecessors=[design_id],
        ),
        Task(
            task_id=manufacture_id,
            name=f"{name}: Manufacturing",
            discipline=code,
            phase="manufacture",
            duration_mean_days=manufacture_mean,
            duration_std_days=manufacture_std,
            predecessors=[procure_id],
        ),
        Task(
            task_id=fat_id,
            name=f"{name}: Factory Acceptance Test",
            discipline=code,
            phase="fat",
            duration_mean_days=5.0,
            duration_std_days=1.5,
            predecessors=[manufacture_id],
        ),
        Task(
            task_id=ship_id,
            name=f"{name}: Shipping & Delivery",
            discipline=code,
            phase="ship",
            duration_mean_days=ship_mean,
            duration_std_days=ship_std,
            predecessors=[fat_id],
        ),
        Task(
            task_id=receive_id,
            name=f"{name}: Site Receiving & Inspection",
            discipline=code,
            phase="receive",
            duration_mean_days=3.0,
            duration_std_days=1.0,
            predecessors=[ship_id],
        ),
        Task(
            task_id=install_id,
            name=f"{name}: Site Installation",
            discipline=code,
            phase="install",
            duration_mean_days=14.0,
            duration_std_days=4.0,
            predecessors=install_predecessors,
            seasonal_window=install_seasonal,
            is_milestone=True,
        ),
        Task(
            task_id=test_id,
            name=f"{name}: Site Acceptance Test",
            discipline=code,
            phase="test",
            duration_mean_days=6.0,
            duration_std_days=2.0,
            predecessors=[install_id],
            is_milestone=True,
        ),
    ]
    return tasks, test_id


def build_tasks() -> list[Task]:
    tasks: list[Task] = []

    for task_id, name, mean, std, preds in _CIVIL_TASKS:
        tasks.append(
            Task(
                task_id=task_id,
                name=name,
                discipline="CIVIL",
                phase="civil",
                duration_mean_days=mean,
                duration_std_days=std,
                predecessors=preds,
                is_milestone=True,
            )
        )

    sat_ids: dict[str, str] = {}
    for code, name, mfg_mean, mfg_std, ship_mean, ship_std in _DISCIPLINES:
        discipline_tasks, test_id = _discipline_tasks(
            code, name, mfg_mean, mfg_std, ship_mean, ship_std, "CIVIL-FITOUT"
        )
        tasks.extend(discipline_tasks)
        sat_ids[code] = test_id

    # LV distribution currently waits for the transformer's FULL site
    # acceptance test — but panel installation only actually needs the
    # transformer physically placed, not fully tested. This over-strict
    # dependency is the real conduit for the transformer delay downstream,
    # and mitigate.py's zero-cost "resequence trades" option fast-tracks it
    # by depending on XFMR-INSTALL instead.
    for task in tasks:
        if task.task_id == "ELEC-INSTALL":
            task.predecessors.append(sat_ids["XFMR"])

    ist_groups = [
        (
            "IST-POWER",
            "IST - Power Systems",
            [sat_ids["XFMR"], sat_ids["DG"], sat_ids["UPS"], sat_ids["ELEC"]],
        ),
        ("IST-MECH", "IST - Mechanical Systems", [sat_ids["CHW"], sat_ids["BMS"]]),
        ("IST-LIFE-SAFETY", "IST - Fire & Life Safety", [sat_ids["FLS"]]),
        ("IST-IT", "IST - IT & Security Systems", [sat_ids["ITN"], sat_ids["SCAC"]]),
        (
            "IST-VERT-PLMB",
            "IST - Vertical Transport & Plumbing",
            [sat_ids["VERT"], sat_ids["PLMB"]],
        ),
    ]
    for task_id, name, preds in ist_groups:
        tasks.append(
            Task(
                task_id=task_id,
                name=name,
                discipline="IST",
                phase="ist",
                duration_mean_days=6.0,
                duration_std_days=1.5,
                predecessors=preds,
                is_milestone=True,
            )
        )

    tasks.append(
        Task(
            task_id="IST-INTEGRATED",
            name="Integrated Systems Test (Full Building)",
            discipline="IST",
            phase="ist",
            duration_mean_days=10.0,
            duration_std_days=3.0,
            predecessors=[
                "IST-POWER",
                "IST-MECH",
                "IST-LIFE-SAFETY",
                "IST-IT",
                "IST-VERT-PLMB",
            ],
            is_milestone=True,
        )
    )

    final_tasks = [
        ("COMM-L3", "Commissioning Level 3 (System Function)", 7.0, 2.0, ["IST-INTEGRATED"]),
        ("COMM-L4", "Commissioning Level 4 (Integrated Function)", 9.0, 2.0, ["COMM-L3"]),
        ("COMM-L5", "Commissioning Level 5 (Load / Stress Test)", 8.0, 2.0, ["COMM-L4"]),
        ("REGULATORY-UTILITY", "Utility Energization Approval", 10.0, 3.0, [sat_ids["XFMR"]]),
        ("REGULATORY-FIRE", "Fire Marshal Inspection", 5.0, 1.5, ["IST-LIFE-SAFETY"]),
        (
            "REGULATORY-OCCUPANCY",
            "Occupancy Certificate",
            6.0,
            2.0,
            ["REGULATORY-FIRE", "REGULATORY-UTILITY", "COMM-L5"],
        ),
        ("PUNCHLIST", "Punch List & Snagging", 10.0, 3.0, ["COMM-L5"]),
        ("HANDOVER", "Client Handover", 3.0, 1.0, ["REGULATORY-OCCUPANCY", "PUNCHLIST"]),
    ]
    for task_id, name, mean, std, preds in final_tasks:
        tasks.append(
            Task(
                task_id=task_id,
                name=name,
                discipline="FINAL",
                phase="commissioning" if task_id.startswith("COMM") else "closeout",
                duration_mean_days=mean,
                duration_std_days=std,
                predecessors=preds,
                is_milestone=True,
            )
        )

    return tasks


def build_dag() -> nx.DiGraph:
    dag = nx.DiGraph()
    for task in build_tasks():
        dag.add_node(
            task.task_id,
            name=task.name,
            discipline=task.discipline,
            phase=task.phase,
            duration_mean=task.duration_mean_days,
            duration_std=task.duration_std_days,
            seasonal_window=task.seasonal_window,
            is_milestone=task.is_milestone,
        )
    for task in build_tasks():
        for pred in task.predecessors:
            dag.add_edge(pred, task.task_id)

    if not nx.is_directed_acyclic_graph(dag):
        raise ValueError("Cascade schedule graph contains a cycle")

    return dag
