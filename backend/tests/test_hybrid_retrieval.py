from retrieval.hybrid import reciprocal_rank_fusion


def test_rrf_ranks_documents_appearing_in_both_lists_highest() -> None:
    # "b" and "c" appear in both lists; "a" and "d" appear in only one each.
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "c", "d"]])
    fused_ids = [doc_id for doc_id, _score in fused]

    assert fused_ids[0] in ("b", "c")
    assert fused_ids[1] in ("b", "c")
    assert set(fused_ids[:2]) == {"b", "c"}
    assert set(fused_ids[2:]) == {"a", "d"}


def test_rrf_symmetric_swap_gives_equal_scores() -> None:
    # x is rank0 in list1 and rank2 in list2; z is the mirror (rank2, rank0)
    # -- by symmetry these two must score identically regardless of k.
    fused = dict(reciprocal_rank_fusion([["x", "y", "z"], ["z", "y", "x"]]))
    assert fused["x"] == fused["z"]


def test_rrf_empty_lists_yield_empty_result() -> None:
    assert reciprocal_rank_fusion([[], []]) == []


def test_rrf_single_list_preserves_rank_order() -> None:
    fused = reciprocal_rank_fusion([["first", "second", "third"]])
    fused_ids = [doc_id for doc_id, _score in fused]
    assert fused_ids == ["first", "second", "third"]
