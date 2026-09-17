from experiments.frontend_blind_v1.trace_evidence import evidence_for_trace, interval_union


def span(sid, parent, component, start, duration, trace="t"):
    return {"span_id": sid, "parent_span": parent, "cmdb_id": component,
            "timestamp": str(start), "duration": str(duration), "trace_id": trace,
            "source_file": "fixture.csv", "source_record": 2}


def test_overlap_union_and_uncovered_time_are_clipped():
    assert interval_union([(0, 10), (5, 20), (30, 40)], (3, 25)) == 17
    root = span("r", "", "frontend-0", 100, 100_000)
    children = [span("a", "r", "a", 100, 80_000), span("b", "r", "b", 130, 50_000)]
    result = evidence_for_trace(root, [root] + children)
    assert result["intervals"]["root_direct_child_union_ms"] == 80
    assert result["intervals"]["root_direct_child_uncovered_ms"] == 20


def test_receiver_uncovered_uses_receiver_children_not_client_gap():
    root = span("r", "", "frontend-0", 100, 100_000)
    client = span("client", "r", "frontend-0", 100, 80_000)
    receiver = span("receiver", "client", "checkout", 100, 80_000)
    receiver_child = span("receiver-child", "receiver", "db", 100, 30_000)
    result = evidence_for_trace(root, [root, client, receiver, receiver_child])
    accounting = result["immediate_attribution"]["receiver_interval_accounting"]["receiver"]
    assert accounting["uncovered_ms"] == 50
    assert accounting["client_minus_receiver_ms"] == 0


def test_missing_parent_cycle_and_depth_flags_preserve_paths():
    root = span("r", "", "frontend-0", 0, 100)
    rows = [root, span("a", "r", "svc", 0, 10), span("b", "a", "db", 0, 5),
            span("missing", "ghost", "svc", 0, 1), span("cycle", "cycle", "svc", 0, 1)]
    result = evidence_for_trace(root, rows)
    assert result["flags"]["missing_parents"] == ["ghost"]
    assert result["dependency_reachability"]["components"] == ["svc", "db"]
    assert result["recorded_span_count"] == 5
