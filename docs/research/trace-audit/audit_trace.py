#!/usr/bin/env python3
"""Stream-audit one trace from a potentially unsorted span CSV.

Usage: audit_trace.py INPUT_CSV TRACE_ID OUTPUT_DIR
All rows are read; source_record is the one-based logical CSV record number
(header is record 1), and source_physical_end_line preserves the physical line
where that record ended.  The extractor intentionally does not assume trace rows
are contiguous or globally sorted.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path


def key(row):
    return (row["trace_id"], row["span_id"])


def interval(row, unit):
    """Exact integer interval, avoiding float precision loss at epoch scale."""
    timestamp, duration = int(row["timestamp"]), int(row["duration"])
    if unit == "ms":
        return timestamp, timestamp + duration
    if unit == "us":
        return timestamp * 1000, timestamp * 1000 + duration
    if unit == "ns":
        return timestamp * 1_000_000, timestamp * 1_000_000 + duration
    raise ValueError(unit)


def find_cycles(nodes, children):
    # Iterative tri-color DFS; output every back-edge witness, not an exhaustive
    # enumeration of all simple cycles.
    color, witnesses = {}, []
    for first in nodes:
        if color.get(first, 0):
            continue
        color[first] = 1
        stack = [(first, iter(children.get(first, ())))]
        path = [first]
        while stack:
            node, it = stack[-1]
            try:
                nxt = next(it)
            except StopIteration:
                color[node] = 2
                stack.pop(); path.pop()
                continue
            state = color.get(nxt, 0)
            if state == 0:
                color[nxt] = 1; stack.append((nxt, iter(children.get(nxt, ())))); path.append(nxt)
            elif state == 1:
                witnesses.append(path[path.index(nxt):] + [nxt])
    return witnesses


def main(source, trace_id, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    total_records = 0
    with source.open(newline="") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type", "status_code", "operation_name", "parent_span"}
        if not required.issubset(reader.fieldnames or []):
            raise SystemExit("unexpected CSV schema: " + repr(reader.fieldnames))
        for r in reader:
            total_records += 1
            if r["trace_id"] == trace_id:
                r["source_record"] = total_records + 1
                r["source_physical_end_line"] = reader.line_num
                rows.append(r)
    # Composite identity is required even though this is a single-trace export.
    by_id = defaultdict(list)
    for r in rows:
        by_id[key(r)].append(r)
    duplicate_ids = {sid: rs for (_, sid), rs in by_id.items() if len(rs) > 1}
    canonical = {k: rs[0] for k, rs in by_id.items() if len(rs) == 1}
    ids = set(canonical)
    resolved, ambiguous, orphan, self_loops = [], [], [], []
    children, undirected = defaultdict(list), defaultdict(set)
    for child_id, child in canonical.items():
        parent_span = child["parent_span"]
        if not parent_span:
            continue
        parent_id = (trace_id, parent_span)
        if parent_id == child_id:
            self_loops.append(child_id); continue
        if parent_id in canonical:
            resolved.append((parent_id, child_id)); children[parent_id].append(child_id)
            undirected[parent_id].add(child_id); undirected[child_id].add(parent_id)
        elif parent_id in by_id:
            ambiguous.append((parent_id, child_id))
        else:
            orphan.append((parent_id, child_id))
    # Root sentinels are recorded separately from blank/missing parent fields.
    # This export uses blank, but keep the test reproducible for adjacent files.
    root_sentinels = {"0", "0000000000000000"}
    blank_roots = [i for i, r in canonical.items() if not r["parent_span"]]
    sentinel_roots = [i for i, r in canonical.items() if r["parent_span"] in root_sentinels]
    explicit_roots = blank_roots + sentinel_roots
    # Connected components of the resolved undirected graph, including isolated rows.
    unseen, components = set(ids), []
    while unseen:
        start = unseen.pop(); part = [start]; q = deque([start])
        while q:
            n = q.popleft()
            for nxt in undirected[n]:
                if nxt in unseen: unseen.remove(nxt); part.append(nxt); q.append(nxt)
        components.append(sorted(part))
    cycles = find_cycles(ids, children)
    factors = {"duration_as_ms": "ms", "duration_as_us": "us", "duration_as_ns": "ns"}
    timing = {}
    for label, unit in factors.items():
        enclosed = inverted = nonoverlap = 0
        for parent_id, child_id in resolved:
            ps, pe = interval(canonical[parent_id], unit); cs, ce = interval(canonical[child_id], unit)
            if ps <= cs and ce <= pe: enclosed += 1
            elif ce < ps or cs > pe: nonoverlap += 1
            else: inverted += 1
        timing[label] = {"resolved_edges": len(resolved), "enclosed": enclosed, "partial_or_start_before_parent": inverted, "nonoverlapping": nonoverlap}
    sibling = {"parents_with_two_or_more_children": 0, "sibling_pairs": 0, "overlapping_pairs_duration_as_us": 0}
    sibling_details = []
    for p, kids in children.items():
        if len(kids) < 2: continue
        sibling["parents_with_two_or_more_children"] += 1
        pair_count = overlap_count = 0
        overlap_widths_us = []
        for n, left in enumerate(kids):
            for right in kids[n + 1:]:
                sibling["sibling_pairs"] += 1
                pair_count += 1
                ls, le = interval(canonical[left], "us"); rs, re = interval(canonical[right], "us")
                if max(ls, rs) < min(le, re):
                    sibling["overlapping_pairs_duration_as_us"] += 1; overlap_count += 1
                    overlap_widths_us.append(min(le, re) - max(ls, rs))
        sibling_details.append({"parent_span_id": p[1], "child_count": len(kids), "pair_count": pair_count, "overlapping_pairs_duration_as_us": overlap_count, "overlap_widths_us": overlap_widths_us})
    ordered = sorted(rows, key=lambda r: (int(r["timestamp"]), r["source_record"]))
    # Readable rooted forest only follows unambiguous relations; remaining nodes listed separately.
    def tree(n):
        r = canonical[n]
        return {"span_id": n[1], "source_record": r["source_record"], "emitter_cmdb_id": r["cmdb_id"], "type": r["type"], "status_code": r["status_code"], "operation_name": r["operation_name"], "children": [tree(c) for c in sorted(children[n], key=lambda x: (int(canonical[x]["timestamp"]), x[1]))]}
    edge_rows = [{"parent_span_id": p[1], "parent_source_record": canonical[p]["source_record"], "parent_emitter_cmdb_id": canonical[p]["cmdb_id"], "parent_operation": canonical[p]["operation_name"], "child_span_id": c[1], "child_source_record": canonical[c]["source_record"], "child_emitter_cmdb_id": canonical[c]["cmdb_id"], "child_operation": canonical[c]["operation_name"], "same_emitter": canonical[p]["cmdb_id"] == canonical[c]["cmdb_id"]} for p,c in resolved]
    nonoverlap_us = [e for e in edge_rows if (interval(canonical[(trace_id, e["child_span_id"])], "us")[0] > interval(canonical[(trace_id, e["parent_span_id"])], "us")[1] or interval(canonical[(trace_id, e["child_span_id"])], "us")[1] < interval(canonical[(trace_id, e["parent_span_id"])], "us")[0])]
    root_timing = []
    for root in explicit_roots:
        root_start, root_end = interval(canonical[root], "us")
        direct = []
        for child in sorted(children[root], key=lambda x: (int(canonical[x]["timestamp"]), x[1])):
            cs, ce = interval(canonical[child], "us")
            direct.append({"span_id": child[1], "operation_name": canonical[child]["operation_name"], "start_offset_us": cs - root_start, "duration_us": ce - cs})
        root_timing.append({"root_span_id": root[1], "root_duration_us": root_end - root_start, "latest_any_span_end_offset_us": max(interval(r, "us")[1] for r in rows) - root_start, "latest_nonroot_span_end_offset_us": max((interval(r, "us")[1] - root_start for r in rows if key(r) != root), default=None), "direct_children_by_start": direct})
    report = {
        "source": str(source), "trace_id": trace_id, "scan": {"data_records_scanned": total_records, "matched_records": len(rows), "matched_span_ids": len(by_id), "unique_unambiguous_span_ids": len(canonical)},
        "identity": {"key": ["trace_id", "span_id"], "duplicate_span_ids": {sid: [r["source_record"] for r in rs] for sid, rs in duplicate_ids.items()}},
        "graph": {"blank_parent_roots": [x[1] for x in blank_roots], "sentinel_parent_roots": [x[1] for x in sentinel_roots], "sentinel_values_checked": sorted(root_sentinels), "explicit_roots": [x[1] for x in explicit_roots], "explicit_root_count": len(explicit_roots), "resolved_parent_child_edges": len(resolved), "same_emitter_edges": sum(e["same_emitter"] for e in edge_rows), "cross_emitter_edges": sum(not e["same_emitter"] for e in edge_rows), "ambiguous_parent_references": [{"parent_span_id": p[1], "child_span_id": c[1]} for p,c in ambiguous], "orphan_parent_references": [{"parent_span_id": p[1], "child_span_id": c[1]} for p,c in orphan], "self_loops": [x[1] for x in self_loops], "cycle_witnesses": [[x[1] for x in cyc] for cyc in cycles], "components": [{"size": len(c), "span_ids": [x[1] for x in c]} for c in sorted(components, key=len, reverse=True)], "representative_edges": edge_rows[:8], "duration_as_us_nonoverlapping_edges": nonoverlap_us},
        "attributes": {"emitters_cmdb_id": dict(Counter(r["cmdb_id"] for r in rows)), "types": dict(Counter(r["type"] for r in rows)), "status_codes": dict(Counter(r["status_code"] for r in rows)), "operations": dict(Counter(r["operation_name"] for r in rows))},
        "timing": {"timestamp_unit": "milliseconds (inferred from epoch values)", "arithmetic": "exact integer arithmetic: timestamps multiplied into each candidate duration unit before interval comparison", "candidate_duration_conversions_to_ms": timing, "sibling_concurrency": sibling, "sibling_parent_details": sibling_details, "root_dispatch_timing_duration_as_us": root_timing},
        "rooted_forest": [tree(r) for r in sorted(explicit_roots, key=lambda x: (int(canonical[x]["timestamp"]), x[1]))],
        "chronological_span_ids": [r["span_id"] for r in ordered],
        "method_notes": ["cmdb_id labels the emitter of this record. It does not identify the called service unless operation_name or other service metadata establishes that mapping.", "A parent_span relation is a span-context reference. Client/server records can represent one RPC with distinct spans; it must not automatically be counted as an interservice network edge.", "Rows were not assumed contiguous or sorted; all CSV records were streamed before extracting the trace."]
    }
    (outdir / f"trace_{trace_id}.json").write_text(json.dumps({"trace_id": trace_id, "rows": rows}, indent=2) + "\n")
    (outdir / "graph_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 4: raise SystemExit("usage: audit_trace.py INPUT_CSV TRACE_ID OUTPUT_DIR")
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
