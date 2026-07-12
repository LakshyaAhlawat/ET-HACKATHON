from cascade.mitigate import run_mitigation_analysis


def test_returns_all_candidates() -> None:
    results = run_mitigation_analysis()
    ids = {r.intervention_id for r in results}

    assert ids == {
        "resequence_trades",
        "split_ist_phases",
        "second_crew_transformer_install",
        "air_freight_transformer",
    }


def test_zero_cost_option_surfaces_first() -> None:
    results = run_mitigation_analysis()

    assert results[0].intervention_id == "resequence_trades"
    assert results[0].is_zero_cost
    assert results[0].cost_inr == 0.0
    assert results[0].efficiency_per_inr is None


def test_zero_cost_option_actually_helps() -> None:
    # The whole point of the "pitch moment": resequencing must show a real,
    # positive P(slip) reduction, not just be present with zero effect.
    results = run_mitigation_analysis()
    resequence = next(r for r in results if r.intervention_id == "resequence_trades")

    assert resequence.delta_p_slip > 0


def test_paid_candidates_ranked_by_descending_efficiency() -> None:
    results = run_mitigation_analysis()
    paid = [r for r in results if not r.is_zero_cost]

    assert len(paid) == 3
    efficiencies = [r.efficiency_per_inr for r in paid]
    assert all(e is not None for e in efficiencies)
    non_null_efficiencies = [e for e in efficiencies if e is not None]
    assert non_null_efficiencies == sorted(non_null_efficiencies, reverse=True)


def test_all_candidates_have_valid_probabilities() -> None:
    results = run_mitigation_analysis()

    for r in results:
        assert 0.0 <= r.baseline_p_slip <= 1.0
        assert 0.0 <= r.mitigated_p_slip <= 1.0
