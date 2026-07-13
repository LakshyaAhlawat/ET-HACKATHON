"""Tests the deterministic dispatch handlers directly, bypassing
classify_query() (a live Groq call) -- these are the functions CLAUDE.md's
rule actually cares about: whatever category the LLM picks, the answer
itself must come from evaluator.py / graph.py / cascade/simulate.py, never
from the model.

_dispatch_compliance's no-clause-id fallback path calls hybrid.retrieve(),
which loads a sentence-transformer and queries the local Qdrant collection
-- deliberately not exercised here to keep this suite fast; it's covered by
manual end-to-end testing (see the session's API smoke tests) instead.
"""

import pytest

from retrieval.router import (
    _CLAUSE_ID_RE,
    _dispatch_compliance,
    _dispatch_schedule,
    _dispatch_topological,
)


def _match(text: str) -> str:
    match = _CLAUSE_ID_RE.search(text)
    assert match is not None
    return match.group(1)


def test_clause_id_regex_matches_known_formats() -> None:
    assert _match("Does MECH-3.4.2 pass?") == "MECH-3.4.2"
    assert _match("per DIV-16 §16.1.2 rules") == "DIV-16 §16.1.2"
    assert _match("see ELEC-2.8.1 for runtime") == "ELEC-2.8.1"


def test_dispatch_compliance_returns_real_verdict_for_known_clause() -> None:
    result = _dispatch_compliance("Does the chiller in MECH-3.4.2 meet its cooling capacity spec?")
    assert result["status"] == "NON_CONFORMANCE"
    assert result["delta_pct"] == pytest.approx(-4.0, abs=0.5)


def test_dispatch_schedule_parses_delay_weeks_from_query() -> None:
    result = _dispatch_schedule("If the transformer is delayed by 5 weeks, what happens?")
    assert result["assumed_delay_weeks"] == 5.0
    p_slip = result["p_slip"]
    assert isinstance(p_slip, float)
    assert 0.0 <= p_slip <= 1.0


def test_dispatch_schedule_defaults_to_three_weeks_without_a_number() -> None:
    result = _dispatch_schedule("What happens if the transformer is delayed?")
    assert result["assumed_delay_weeks"] == 3.0


def test_dispatch_topological_traces_a_known_clause_to_handover() -> None:
    result = _dispatch_topological("Trace MECH-3.4.2 through to handover.")
    path = result["path_node_ids"]
    assert isinstance(path, list)
    assert path[0] == "MECH-3.4.2"
    assert path[-1] == "HANDOVER"


def test_dispatch_topological_falls_back_without_a_clause_id() -> None:
    result = _dispatch_topological("Show me the dependency graph.")
    assert result["path_node_ids"]  # falls back to a default demo path
