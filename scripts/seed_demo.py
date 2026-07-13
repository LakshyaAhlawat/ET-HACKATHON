"""Brings up a fully-populated demo instance from a fresh checkout.

"Seed" here means what CLAUDE.md's "precompute everything" rule implies:
every data/*.json artifact this script checks for is already computed and
committed to git, so there is nothing to (re)compute at demo time — this
script's only job is to verify that data is present, then start the two
already-built services and wait for them to answer.

No network calls: nothing here talks to Groq, HuggingFace, or any other
external service. If you deleted a data/*.json file, this script tells you
which offline precompute command regenerates it instead of doing it for you
live (regenerating live would reintroduce the network dependency this
script exists to avoid).

Usage: python scripts/seed_demo.py
"""

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

BACKEND_HEALTH_URL = "http://localhost:8000/health"
FRONTEND_HEALTH_URL = "http://localhost:3000"
STARTUP_TIMEOUT_S = 100

# Every file the demo script (docs/DEMO_SCRIPT.md) touches. Path -> the
# offline command that (re)generates it if missing.
REQUIRED_DATA = {
    "data/cascade_tasks.json": "cd backend && python -m cascade.precompute",
    "data/cascade_lookup.json": "cd backend && python -m cascade.precompute",
    "data/cascade_mitigations.json": "cd backend && python -m cascade.precompute",
    "data/sld_results.json": "cd backend && python -m sld.precompute",
    "data/graph.json": "cd backend && python -m graph.precompute",
    "data/rfi_analysis.json": "cd backend && python -m rfi.precompute",
    "data/demo_query_cache.json": "cd backend && python -m retrieval.cache_demo_queries",
    "data/qdrant_local/meta.json": "cd backend && python -m retrieval.precompute",
    "data/extracted/spec.requirements.json": (
        "cd backend && python -m ingestion.ingest "
        "--spec ../data/fixtures/spec.pdf --submittal ../data/fixtures/submittal.pdf"
    ),
    "data/extracted/submittal.values.json": (
        "cd backend && python -m ingestion.ingest "
        "--spec ../data/fixtures/spec.pdf --submittal ../data/fixtures/submittal.pdf"
    ),
}


def check_data_seeded() -> None:
    missing = [(rel, cmd) for rel, cmd in REQUIRED_DATA.items() if not (ROOT / rel).exists()]
    if not missing:
        print(f"[seed] all {len(REQUIRED_DATA)} precomputed data files present.")
        return
    print("[seed] missing precomputed data -- this is an offline-generation gap, not", file=sys.stderr)
    print("       something this script will fix live (that would need network):", file=sys.stderr)
    for rel, cmd in missing:
        print(f"  missing {rel}\n    -> {cmd}", file=sys.stderr)
    sys.exit(1)


def _wait_for(url: str, label: str, timeout_s: int) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            print(f"[seed] {label} is up ({url})")
            return
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            time.sleep(1)
    print(f"[seed] {label} did not respond within {timeout_s}s ({url})", file=sys.stderr)
    sys.exit(1)


def start_backend() -> subprocess.Popen:
    venv_python = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable
    return subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
    )


def start_frontend() -> subprocess.Popen:
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    return subprocess.Popen([npm, "run", "dev"], cwd=FRONTEND_DIR)


def main() -> None:
    start = time.monotonic()
    check_data_seeded()

    print("[seed] starting backend (uvicorn)...")
    backend = start_backend()
    print("[seed] starting frontend (next dev)...")
    frontend = start_frontend()

    try:
        _wait_for(BACKEND_HEALTH_URL, "backend", STARTUP_TIMEOUT_S)
        _wait_for(FRONTEND_HEALTH_URL, "frontend", STARTUP_TIMEOUT_S)
    except SystemExit:
        backend.terminate()
        frontend.terminate()
        raise

    elapsed = time.monotonic() - start
    print(f"\n[seed] ready in {elapsed:.0f}s -- http://localhost:3000")
    print("[seed] backend PID", backend.pid, "| frontend PID", frontend.pid)
    print("[seed] Ctrl+C to stop both.")

    try:
        backend.wait()
    except KeyboardInterrupt:
        backend.terminate()
        frontend.terminate()


if __name__ == "__main__":
    main()
