"""Render the reviewed random-eight results after the immutable output gate."""
import csv
import json
from pathlib import Path
import statistics
from datetime import datetime

from review_random8 import gate, RUN, ROOT, SELECTION, OUT
from experiments.frontend_blind_v1 import evaluate


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |" for row in rows])


def read(path):
    return json.loads(path.read_text())


def projected(incidents, fields):
    return "<br>".join(" / ".join(str(i.get(f) or "[abstain]") for f in fields) for i in incidents)


def main():
    verified = gate()
    if not (OUT / "unblinding.json").exists():
        raise RuntimeError("Run the gated evaluation first")
    selected = read(SELECTION)["selected_rows"]
    metrics = read(OUT / "metrics.json")
    with (OUT / "results.csv").open() as f:
        results = {(int(r["row_id"]), r["stage"]): r for r in csv.DictReader(f)}
    labels = {rid: row for rid, row in evaluate._load_labels(ROOT / "data/track-1/dev/query_dev.csv").items() if rid in selected}
    reviews = {r["row_id"]: r for r in (json.loads(line) for line in (RUN / "orchestration/review_before_labels.jsonl").read_text().splitlines())}
    ledger = [json.loads(line) for line in (RUN / "orchestration/dispatch.jsonl").read_text().splitlines()]
    dispatch = {r["row_id"]: r["timestamp"] for r in ledger if r["event"] == "dispatch"}
    summary = []
    for stage in ("trace_only", "final"):
        scores = [float(results[rid, stage]["official_score"]) for rid in selected]
        summary.append([stage, len(scores), f"{statistics.mean(scores):.4f}", sum(s == 1 for s in scores)])
    fields = []
    for stage, value in metrics["stages"].items():
        for field, m in value["field_metrics"].items():
            fields.append([stage, field, f"{m['hits']}/{m['denominator']}", f"{m['accuracy']:.1%}" if m['accuracy'] is not None else "Unavailable"])
    per_case = []
    executions = []
    review_text = []
    for rid in selected:
        case = RUN / f"cases/{rid}"
        scope = read(case / "scope.json")
        final = read(case / "final.json")
        task_fields = evaluate.TASK_FIELDS[scope["task_index"]]
        gold, conflict = evaluate._extract_gold(labels[rid], task_fields)
        per_case.append([rid, scope["task_index"], ", ".join(task_fields),
                         projected(gold, task_fields), projected(final["incidents"], task_fields),
                         results[rid, "trace_only"]["official_score"], results[rid, "final"]["official_score"]])
        events = [json.loads(line) for line in (case / "retrieval.jsonl").read_text().splitlines()] if (case / "retrieval.jsonl").exists() else []
        seconds = (datetime.fromisoformat(read(case / "final.seal.json")["created_at"]) - datetime.fromisoformat(dispatch[rid])).total_seconds()
        executions.append([rid, read(case / "run.json")["status"], f"{seconds / 60:.1f}",
                           sum(e["operation"] == "get_metrics" for e in events), sum(e["operation"] == "get_logs" for e in events),
                           f"[evidence]({case / 'evidence.md'})", f"[code]({case / 'investigate.py'})"])
        review = reviews[rid]
        review_text += [f"### Case {rid}", "", "Pre-label review: " + " ".join(review["strengths"]), "",
                        "Limitations: " + " ".join(review["concerns"]), ""]
    discovery = []
    for arm, values in metrics["discovery"]["arms"].items():
        for kind in ("immediate", "reachable"):
            for budget in (1, 3, 5, 10):
                m = values[f"{kind}_budget_{budget}"]
                discovery.append([arm, kind, budget, f"{m['any_incident_hits']}/{m['windows']}",
                                  f"{m['all_labelled_components_hits']}/{m['windows']}",
                                  f"{m['component_hits']}/{m['component_denominator']}"])
    pairs = []
    import itertools
    for a, b in itertools.combinations(metrics["discovery"]["arms"], 2):
        for kind in ("immediate", "reachable"):
            for budget in (1, 3, 5, 10):
                key = f"{kind}_budget_{budget}"
                differences = [len(set(w["labelled_components"]) & set(w["arms"][a][key])) - len(set(w["labelled_components"]) & set(w["arms"][b][key])) for w in metrics["discovery"]["per_window"]]
                pairs.append([f"{a} vs {b}", kind, budget, sum(d > 0 for d in differences), sum(d < 0 for d in differences), sum(d == 0 for d in differences)])
    descriptors = read(RUN / "orchestration/random8_detector_descriptive.json")
    durations = [[r["row_id"], r["query_roots"], r["eligible"], *[f"{r['leaders'][a]['duration_ms']:.3f}" for a in ("duration", "mad", "iforest")]] for r in descriptors]
    text = ["# Eight random blind trials: results and output review", "",
            "**Result: 2/8 requested answers were fully correct; mean official score was 25%, versus 6.25% for trace-only predictions.** Final exact component accuracy was 1/9, reason accuracy 2/7, and occurrence-time accuracy 0/3. The two successes were case 29 (frontend network latency) and case 32 (process termination reason). The observations show that packaged anomaly scoring is readily executable, but this frontend-first investigation procedure did not reliably solve blind diagnosis.", "",
            "Eight prompts were randomly selected with seed 42 before opening labels: **3, 6, 14, 17, 29, 32, 36, 48**. They contain twelve incident slots across eight unique windows, six on March 20 and two on March 21. All used independent Luna-high investigators and unchanged PyOD MAD/Isolation Forest scoring alongside raw-duration sorting. The original 69-prompt run was stopped at the user's request; completed pilots 0–2 are excluded.", "",
            "The [population amendment](RANDOM8-AMENDMENT.md) supersedes the original 69-case gate. All eight trace-only and final seals passed before labels were opened. The coordinator's evidence-quality reviews below were recorded before unblinding. Original predictions remain unchanged.", "",
            "## Official requested-field scores", "", table(["Stage", "Prompts", "Mean official score", "All requested fields correct"], summary), "",
            table(["Stage", "Requested field", "Correct / labelled", "Accuracy"], fields), "",
            "Official scores are equally weighted per prompt and rounded by the unchanged official scorer. These prompts do not request a full time/component/reason tuple, so a fully correct requested answer is not evidence that all three fields were solved.", "",
            "## Per-case predictions and answers", "", table(["Case", "Task", "Scored fields", "Expected", "Final prediction", "Trace score", "Final score"], per_case), "",
            "## Detector discovery", "", "All three arms return 0/9 exact component hits at request budgets 1, 3, 5, and 10, for both immediate attribution and broader reachability. The complete counts and candidate lists are retained in metrics.json.", "",
            "**The all-zero exact discovery scores do not provide a useful comparison of detector quality in this sample.** Of nine component labels, four are nodes, four are whole-service names, and one is the frontend root itself. The metric compares descendant replica span IDs: nodes are not spans, service names do not equal replica names, and the frontend root is excluded from descendant lists. The extracted lists are nonempty and contain 10–24 reachable replica IDs at budget ten; this is an evaluation-granularity limitation, not evidence that no useful dependency was found. Only the six selected prompts with component labels enter this denominator. Broad reachability also contains routine dependencies and is weaker evidence than attribution of delay. No post-hoc identity normalization or rescoring was applied.", "",
            "Every paired arm contrast consequently has zero wins, zero losses, and six ties. These ties cannot establish detector equivalence or support a best-in-class claim.", "",
            "## Absolute latency and coverage", "", table(["Case", "Frontend requests", "Eligible requests", "Duration top-1 ms", "MAD top-1 ms", "IForest top-1 ms"], durations), "",
            "In case 14, MAD and Isolation Forest choose a 0.921 ms request against a 0.172 ms reference median (0.749 ms excess), while raw sorting selects 153.242 ms. This is a real relative departure, but it illustrates why an unusual request is not automatically an important delay. No post-hoc threshold was added.", "",
            "## Review of the sealed outputs", "", *review_text,
            "An [independent Luna-high audit](" + str(RUN / "orchestration/independent_audit.md") + ") of six completed cases, performed without labels or the coordinator's review notes, confirmed the citation and causal-attribution issues. Case 14 additionally cites CPU percentage where its narrative relies on CPU-system samples. Case 17's first DNS citation belongs to emailservice-0, while its first prediction names emailservice-1. These are substantive evidence-quality issues even when nearby source files contain relevant observations.", "",
            "## What failed, and what worked", "",
            "The strongest successful path was case 29: repeated roughly 353 ms client-call excess across many downstream operations, short receiver processing, and corroborating proxy timings pointed to frontend network latency. Case 32 supplied a coherent memory-discontinuity/connection-reset timeline and matched the requested process-termination reason, although a direct lifecycle event was absent and citations need manual repair outside the sealed result.", "",
            "The failures include wrong resource mechanisms inferred from small changes (cases 3 and 14), symptom timing substituted for causal onset (case 36), unsupported splitting of one correlated episode into two failures (cases 6 and 48), and confusion among different network fault mechanisms (case 17). Identity granularity also matters: the labels name recommendationservice in case 6 and productcatalogservice plus checkoutservice in case 48, while the outputs choose individual replicas. Those family-level associations are useful leads, but normalizing them would not fix the wrong reasons, the missed node incident, or the missing second service. The official results above remain unchanged.", "",
            "## Comparison with the short-window baselining report", "",
            "The user supplied [Short-window baselining: execution and analysis](" + str(ROOT / "data/experiments/short-window-baselining-v1/final-report.md") + "). It was read after all eight outputs were sealed. Its conclusions and these results answer different questions and are compatible.", "",
            table(["Dimension", "Short-window study", "This eight-case trial"], [
                ["Question", "Can a short reference support qualified latency comparisons?", "Can frontend-first investigation recover requested fault fields?"],
                ["Frozen reference", "5 minutes, pooled C1 recorded operation-presence sets; parallel C0 structural channel", "30 minutes, pooled recorded operation/count signatures"],
                ["Reported quantity", "Median and signed absolute excess; support and stability screens", "Raw duration, signed cohort MAD, pooled IForest; sealed diagnoses"],
                ["Eligibility", "Count/time-concentration rules, completion filtering, explicit unknown structure, interval-width screen", "At least 20 references, positive median, nonzero MAD; no comparable bootstrap-width gate"],
                ["Empirical coverage", "9,763/9,802 core comparisons (99.60%); 50,366/50,933 confirmation primary comparisons (98.89%)", "46,276/46,277 full-window requests eligible for cohort scores"],
                ["Outcome claim", "Broad descriptive availability, with important abstention/stability failures; no RCA evaluation", "2/8 requested answers fully correct; no request-level anomaly accuracy or false-positive estimate"],
            ]), "",
            "The coverage percentages are not directly comparable: the request slices, cohort definitions, completion rules, and stability requirements differ. The short-window study's safeguards and signed absolute-excess reporting address weaknesses visible here, especially tiny high-relative-score requests and reference contamination. They do not establish healthy references, incident sensitivity, or diagnosis accuracy. Switching from 30 to 5 minutes was not tested in this trial, so no improvement from that change is claimed.", "",
            "## Execution and reproducibility", "", table(["Case", "Status", "Minutes dispatch to seal", "Metric calls", "Log calls", "Evidence", "Executed code"], executions), "",
            "Machine-recorded retrieval counts and dispatch-to-seal times take precedence over inconsistent agent-written summaries. Failed analysis commands and corrected runs remain in each run.json. Model token usage and dollar cost were not available.", "",
            f"- [Evaluation metrics]({OUT / 'metrics.json'})", f"- [Per-case score CSV]({OUT / 'results.csv'})", f"- [Unblinding audit]({OUT / 'unblinding.json'})", f"- [Pre-label review records]({RUN / 'orchestration/review_before_labels.jsonl'})", "",
            "Reproduce from the repository root with the pinned Python environment and PYTHONPATH set to the repository root:", "", "```sh",
            "/private/tmp/symbolicrca-pyod-venv/bin/python docs/research/experiments/frontend-blind-v1/review_random8.py gate",
            "/private/tmp/symbolicrca-pyod-venv/bin/python docs/research/experiments/frontend-blind-v1/review_random8.py evaluate",
            "/private/tmp/symbolicrca-pyod-venv/bin/python docs/research/experiments/frontend-blind-v1/collect_random8.py", "```", "",
            "## Limits", "", "This is an exploratory development sample with incident-conditioned windows and potentially contaminated reference traffic. There are no independently labelled healthy windows or request-level anomaly labels, so false-positive rates and anomaly-classification accuracy are not measured. Adjacent intervals share traffic. Eight cases from one deployment cannot establish a generally best detector, production readiness, or causal identification. The final investigation combines all three arms, so final diagnosis accuracy cannot be credited to one detector.", ""]
    target = Path(__file__).with_name("RANDOM8-RESULTS.md")
    target.write_text("\n".join(text))
    print(target)


if __name__ == "__main__":
    main()
