from experiments.frontend_blind_v1.detectors import attach_signatures, detect


def _root(trace_id, duration, op="op", component="frontend-0"):
    return {"trace_id": trace_id, "span_id": f"root-{trace_id}", "parent_span": "",
            "duration": str(duration), "timestamp": "100", "cmdb_id": component,
            "operation_name": "root"}


def _child(trace_id, span_id, op="op"):
    return {"trace_id": trace_id, "span_id": span_id, "parent_span": f"root-{trace_id}",
            "duration": "1", "timestamp": "100", "cmdb_id": "frontend-0",
            "operation_name": op}


def test_signature_cohorts_and_slow_only_zero_mad_exclusion():
    refs = [_root(f"r{i}", 100) for i in range(20)]
    query = [_root("slow", 200), _root("fast", 50)]
    rows = refs + query + [_child("slow", "child-slow"), _child("fast", "child-fast")]
    ref = attach_signatures(refs, rows)
    q = attach_signatures(query, rows)
    result = detect(ref, q)
    assert result.query_count == 2
    assert all(not row["b_eligible"] for row in result.rows)  # MAD is zero
    assert result.leaders["mad"] == []


def test_new_cohort_and_sparse_reference_are_explicit():
    refs = [_root(f"r{i}", 100 + i) for i in range(20)]
    query = [_root("known", 200), _root("new", 300)]
    rows = refs + query
    rows += [_child(f"r{i}", f"c{i}") for i in range(20)]
    rows += [_child("known", "cknown")]
    ref = attach_signatures(refs, rows)
    q = attach_signatures(query, rows)
    result = detect(ref, q)
    by_id = {row["trace_id"]: row for row in result.rows}
    assert by_id["known"]["b_eligible"]
    assert not by_id["new"]["b_eligible"]
    assert by_id["new"]["eligibility_reason"] == "no_matching_reference_cohort"
