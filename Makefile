.PHONY: demo demo-docker stop test

# Brings up a fully-populated demo instance from a fresh checkout in under
# 2 minutes. All data/*.json artifacts are precomputed and already
# committed to git (see CLAUDE.md's "precompute everything" rule) --
# this only starts the two services and waits for them to answer, it
# never recomputes anything or makes a network call. See
# scripts/seed_demo.py.
demo:
	python scripts/seed_demo.py

# Same demo, containerized (matches the production deployment topology in
# ARCHITECTURE.md). Requires Docker. Not the path this repo's automated
# checks exercise -- verify locally with `make demo` before relying on this
# for a live judged run.
demo-docker:
	docker compose up --build

stop:
	docker compose down

test:
	cd backend && .venv/Scripts/python.exe -m pytest tests/ -q
