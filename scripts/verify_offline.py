"""Rigorous offline-mode verification: proves the demo script's exact
sequence of calls needs zero network access, rather than just hoping wifi
happens to be off.

Physically toggling the OS network adapter only proves the machine you
tested on was offline at that moment -- it doesn't prove *why* something
worked or failed. This script is a stronger test: it unsets GROQ_API_KEY
and forces HF_HUB_OFFLINE=1 / TRANSFORMERS_OFFLINE=1 in-process, so any
code path that actually needs the network fails loudly (a clear exception)
instead of silently succeeding because the machine happened to have wifi
anyway. Run this, then ALSO do the physical wifi-off run before recording --
this is the fast feedback loop, that's the final confirmation.

Usage: cd backend && .venv/Scripts/python.exe ../scripts/verify_offline.py
"""

import os
import sys

os.environ.pop("GROQ_API_KEY", None)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from starlette.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

# Mirrors docs/DEMO_SCRIPT.md step by step -- if a step is added there,
# add it here too.
DEMO_STEPS: list[tuple[str, str, dict[str, object] | None]] = [
    ("GET", "/health", None),
    ("POST", "/api/verify/submittal", None),
    ("GET", "/api/cascade/tasks", None),
    ("GET", "/api/cascade/lookup", None),
    ("GET", "/api/cascade/mitigations", None),
    ("GET", "/api/sld/topologies", None),
    ("GET", "/api/graph", None),
    ("GET", "/api/graph/traverse?start_req_id=MECH-3.4.2", None),
    (
        "POST",
        "/api/query",
        {"query": "Does the chiller in MECH-3.4.2 meet its cooling capacity requirement?"},
    ),
    (
        "POST",
        "/api/query",
        {"query": "If the transformer is delayed by 3 weeks, when will handover happen?"},
    ),
    (
        "POST",
        "/api/query",
        {"query": "Trace the dependency chain from the chiller spec to project handover."},
    ),
    ("POST", "/api/query", {"query": "What HVAC setpoint does the spec require for the data hall?"}),
    ("GET", "/api/rfi/analysis", None),
    ("POST", "/api/rfi/match", {"question": "What temperature should chilled water be?"}),
]


def run() -> int:
    print("GROQ_API_KEY set:", "GROQ_API_KEY" in os.environ, "(must be False)")
    print("HF_HUB_OFFLINE:", os.environ.get("HF_HUB_OFFLINE"))
    print()

    failures = []
    for method, path, body in DEMO_STEPS:
        try:
            response = client.get(path) if method == "GET" else client.post(path, json=body)
            ok = response.status_code == 200
            marker = "OK  " if ok else "FAIL"
            print(f"{marker} {response.status_code} {method:4s} {path}")
            if not ok:
                failures.append((method, path, response.status_code, response.text[:200]))
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL ERR  {method:4s} {path}  {type(exc).__name__}: {exc}")
            failures.append((method, path, "exception", str(exc)))

    print()
    if failures:
        print(f"{len(failures)} step(s) failed without network access:")
        for method, path, status, detail in failures:
            print(f"  {method} {path} -> {status}: {detail}")
        return 1

    print(f"All {len(DEMO_STEPS)} demo steps succeeded with GROQ_API_KEY unset and HF forced offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
