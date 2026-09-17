#!/usr/bin/env python3
"""Bounded trace semantic audit; no labels or gold files are read."""
import csv, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

CSV = Path(sys.argv[1])
OUT = Path(sys.argv[2])
LIMIT = 100_000
TARGET = "9451fd8fdf746a80687451dae4c4e984"

def pct(xs, p):
    if not xs: return None
    xs = sorted(xs); i = (len(xs)-1)*p
    lo, hi = int(i), math.ceil(i)
    return xs[lo] if lo == hi else xs[lo] + (xs[hi]-xs[lo])*(i-lo)

def mad(xs):
    if not xs: return None
    m = pct(xs, .5)
    return pct([abs(x-m) for x in xs], .5)

def row_to_span(r):
    return {"timestamp_ms": int(r["timestamp"]), "component": r["cmdb_id"],
            "span_id": r["span_id"], "trace_id": r["trace_id"],
            "duration_raw": int(r["duration"]), "type": r["type"] or "<empty>",
            "status_code": r["status_code"] or "<empty>", "operation": r["operation_name"],
            "parent_span": r["parent_span"] or None}

def relation_metrics(spans):
    candidates = defaultdict(list)
    for s in spans: candidates[(s["trace_id"], s["span_id"])].append(s)
    by_key = {k:v[0] for k,v in candidates.items() if len(v) == 1}
    duplicate_keys = sum(len(v) > 1 for v in candidates.values())
    duplicate_rows = sum(len(v) for v in candidates.values() if len(v) > 1)
    pairs = []
    for c in spans:
        if c["parent_span"] and c["parent_span"] != "0":
            p = by_key.get((c["trace_id"], c["parent_span"]))
            if p: pairs.append((p,c))
    scales = {}
    for scale in (1.0, .001, .000001):
        enclosed = sum(p["timestamp_ms"] <= c["timestamp_ms"] and
                       c["timestamp_ms"] + c["duration_raw"]*scale <= p["timestamp_ms"] + p["duration_raw"]*scale
                       for p,c in pairs)
        slacks = [p["timestamp_ms"] + p["duration_raw"]*scale - (c["timestamp_ms"] + c["duration_raw"]*scale)
                  for p,c in pairs]
        tight = [x for x in slacks if 0 <= x <= 2] # timestamps only have millisecond precision
        scales[str(scale)] = {"enclosed": enclosed, "rate": enclosed/len(pairs) if pairs else None,
                              "slack_ms_p50":pct(slacks,.5), "slack_ms_p95":pct(slacks,.95),
                              "enclosed_within_2ms_of_parent_end":len(tight)}
    return pairs, scales, {"duplicate_trace_span_keys":duplicate_keys,"rows_in_duplicate_keys":duplicate_rows}

def edge_bin_stats(pairs):
    # Per directed component pair and one-minute child-start bin; values are not assumed to be network latency.
    bins = defaultdict(list)
    for p,c in pairs:
        key = (p["component"], c["component"], c["timestamp_ms"]//60_000)
        bins[key].append(c["duration_raw"])
    series = defaultdict(list); detailed_series = defaultdict(list)
    for (src,dst,b), vals in bins.items():
        if len(vals) >= 5:
            series[(src,dst)].append(pct(vals,.95))
            # A stricter approximation of plan's "operation/type bins"; child operation/type are included.
            detailed_series[(src,dst)].append((b, pct(vals,.95)))
    # Recompute detailed bins rather than assuming component-pair aggregation satisfies operation/type policy.
    detailed_bins = defaultdict(list)
    for p,c in pairs:
        detailed_bins[(p["component"],c["component"],p["type"],c["type"],p["operation"],c["operation"],c["timestamp_ms"]//60_000)].append(c["duration_raw"])
    detailed_by_edge = defaultdict(list)
    for k,vals in detailed_bins.items():
        if len(vals)>=5: detailed_by_edge[k[:-1]].append(pct(vals,.95))
    eligible = {"edge_minute_bins": len(bins), "bins_with_at_least_5_matched_spans": sum(len(v)>=5 for v in bins.values()),
                "directed_edges_with_any_5_span_bin": len(series),
                "directed_edges_with_20_plus_5_span_bins": sum(len(v)>=20 for v in series.values()),
                "directed_edges_with_20_plus_bins_and_positive_mad": sum(len(v)>=20 and (mad(v) or 0)>0 for v in series.values()),
                "strict_component_operation_type_bins_with_at_least_5_matched_spans":sum(len(v)>=5 for v in detailed_bins.values()),
                "strict_component_operation_type_series_with_20_plus_5_span_bins":sum(len(v)>=20 for v in detailed_by_edge.values()),
                "strict_component_operation_type_series_with_20_plus_bins_and_positive_mad":sum(len(v)>=20 and (mad(v) or 0)>0 for v in detailed_by_edge.values()),
                "note":"Component-pair fields are optimistic upper-bound coverage; strict fields approximate the plan's operation/type-bin policy."}
    return eligible

def main():
    sample=[]; target=[]; type_status=Counter(); durations=defaultdict(list)
    with CSV.open(newline="") as f:
        reader=csv.DictReader(f)
        for n,r in enumerate(reader, 1):
            s=row_to_span(r)
            if n <= LIMIT:
                sample.append(s); type_status[(s["type"],s["status_code"])] += 1; durations[s["type"]].append(s["duration_raw"])
            if s["trace_id"] == TARGET: target.append(s)
    pairs, scales, sample_join = relation_metrics(sample)
    same = sum(p["component"] == c["component"] for p,c in pairs)
    cross = len(pairs)-same
    start_gaps = [c["timestamp_ms"]-p["timestamp_ms"] for p,c in pairs]
    # Target trace parent relationships are complete only if all parent ids resolve in the scanned CSV.
    target_pairs, target_scales, target_join = relation_metrics(target)
    target_by_id = {s["span_id"]:s for s in target}
    roots = [s for s in target if not s["parent_span"] or s["parent_span"] == "0" or s["parent_span"] not in target_by_id]
    tmin = min((s["timestamp_ms"] for s in target), default=None); tmax=max((s["timestamp_ms"] for s in target), default=None)
    target_rows = sorted(target, key=lambda s:(s["timestamp_ms"],s["span_id"]))
    target_root_children = []
    if len(roots) == 1:
        root = roots[0]
        target_root_children = [{"span_id":s["span_id"], "component":s["component"], "operation":s["operation"],
                                 "start_offset_ms":s["timestamp_ms"]-root["timestamp_ms"],
                                 "duration_at_0.001_ms":s["duration_raw"]*.001}
                                for s in target_rows if s["parent_span"] == root["span_id"]]
    last_end_us = max((s["timestamp_ms"]*1000 + s["duration_raw"] for s in target), default=None)
    last_nonroot_end_us = max((s["timestamp_ms"]*1000 + s["duration_raw"] for s in target if s not in roots), default=None)
    report = {
      "scope":{"csv":str(CSV),"bounded_sample_rows":len(sample),"target_trace_id":TARGET,"target_trace_rows_found_full_file":len(target),"no_gold_files_read":True},
      "observed":{
        "sample_timestamp_ms":{"min":min(s["timestamp_ms"] for s in sample),"max":max(s["timestamp_ms"] for s in sample)},
        "duration_raw_by_type":{k:{"n":len(v),"p50":pct(v,.5),"p95":pct(v,.95),"max":max(v)} for k,v in durations.items()},
        "status_code_by_type":[{"type":t,"status_code":st,"n":n} for (t,st),n in sorted(type_status.items())],
        "resolved_parent_child_pairs_in_sample":len(pairs),
        "join_integrity":sample_join,
        "root_sentinel_parent_span_0_in_sample":sum(s["parent_span"] == "0" for s in sample),
        "unresolved_nonroot_parent_references_in_sample":sum(bool(s["parent_span"]) and s["parent_span"] != "0" for s in sample)-len(pairs),
        "parent_child_component_relation":{"same_component":same,"cross_component":cross},
        "parent_child_start_gap_ms":{"min":min(start_gaps) if start_gaps else None,"p50":pct(start_gaps,.5),"p95":pct(start_gaps,.95),"negative":sum(x<0 for x in start_gaps)},
        "duration_scale_enclosure_test":scales,
        "p95_policy_screen":edge_bin_stats(pairs),
      },
      "target_trace_observed":{
        "root_or_unresolved_parent_spans":len(roots),"resolved_parent_child_pairs":len(target_pairs),
        "join_integrity":target_join,
        "timestamp_elapsed_ms":(tmax-tmin) if tmin is not None else None,
        "last_observed_span_end_under_us_hypothesis":{"epoch_us":last_end_us,"elapsed_us":last_end_us-tmin*1000 if last_end_us is not None else None,"includes_root":True},
        "last_nonroot_span_end_under_us_hypothesis":{"epoch_us":last_nonroot_end_us,"elapsed_us":last_nonroot_end_us-tmin*1000 if last_nonroot_end_us is not None else None},
        "root_duration_raw_and_scaled_ms":[{"span_id":s["span_id"],"duration_raw":s["duration_raw"],"at_scale_0.001_ms":s["duration_raw"]*.001,"at_scale_1_ms":s["duration_raw"]} for s in roots],
        "duration_scale_enclosure_test":target_scales,
        "root_direct_children_timing_at_0.001_ms":target_root_children,
        "spans":target_rows,
      },
      "interpretation_limits":[
        "Enclosure rate alone favors overly large duration scales because an overlong parent trivially contains a child. Compare slack, sequential-call timing, and root elapsed time before inferring a duration unit.",
        "A parent-to-child start gap is ordering/scheduling evidence, not network latency. Child duration is not safely subtractable from parent duration because children may overlap.",
        "Status codes are reported as observed strings by span type. Error semantics are not established by this audit or the cited data guide, so error fractions should remain disabled.",
        "The first 100,000 physical CSV rows cover only the initial 159.96 minutes of this day. They are a time-prefix, not an unbiased sample; the 76,228 unresolved non-root references cannot be interpreted as a full-dataset missing-parent rate.",
        "The p95/MAD screen only tests matched component edges inside this sample; it cannot establish full-day reference eligibility or fault usefulness. Its component-only counts are explicitly optimistic; strict operation/type counts are the closer policy test."
      ]
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")

if __name__ == "__main__": main()
