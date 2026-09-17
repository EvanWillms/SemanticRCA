# Independent frontend-first investigator protocol

You are a fresh **gpt-5.6-luna** agent with **high** reasoning effort assigned to exactly one prompt. Complete the work in your assigned case directory. Your time budget is 15 minutes once prepared case data are available. Do not delegate.

## Inputs and prohibitions

Read your own scope.json, rankings.json, trace_evidence.json; this document; SCHEMA.md; DATA_API.md; HARNESS_API.md; and generic modules under experiments/frontend_blind_v1 as needed. Use only bounded retrieval.py functions for metrics and logs.

Do not read dev/query_dev.csv, scoring_points, record.csv, answer keys, other case directories, previous research/example reports, the planning document's exposed-control details, Git history, or web results about case answers. Do not inspect source telemetry directly to bypass retrieval policy. Do not alter shared code/config. If an API fails, report its exception to root before trying a workaround. Procedural blinding is part of the experiment; report any accidental exposure.

The public instruction supplies the deployment, time window, requested fields, and incident count. These constrain scope but do not supply diagnostic evidence. Adjacent reference intervals are not certified healthy. A completed span is not verified success; no recorded children does not prove no downstream work.

## Runtime

Work from the repository root with `PYTHONPATH` set to that root. Use `/private/tmp/symbolicrca-pyod-venv/bin/python`. This environment already contains the frozen PyOD dependencies. Do not install or change packages for an individual case.

Read large JSON files programmatically and print compact summaries. Use the existing harness and prepared files, avoiding repeated full-day scans. Your case code must recompute numerical evidence from allowed inputs; a file containing only a hard-coded diagnosis is not executable investigation.

Treat `scope.json`, `rankings.json`, `trace_evidence.json`, `run_inputs.json`, and `index.json` as read-only prepared inputs. Do not call `prepare_case` or `prepare_all`: preparation is already complete, and rerunning it would overwrite case provenance. `inspect_case` is a read-only helper.

## Stage T: trace-only, sealed first

1. Write `investigate.py` in your case directory. Execute it to inspect the prepared three-arm rankings and compute useful comparisons and trace measurements. Save a numerical output such as investigation_trace.json. Preserve code, stdout/command information, and the actual execution timestamp.
2. The arms are raw duration, signed reference-cohort MAD, and Isolation Forest over reference-standardized latency. They are frozen. Do not add filters, retune a model, or substitute a new ranking.
3. Inspect at most the prepared union of the top ten traces per arm. Distinguish highest statistical departure from largest absolute delay.
4. Follow explicit parent links. Distinguish frontend instrumentation, client calls, downstream receivers, and receiver-uncovered time. Overlapping child intervals must be unioned; cross-host timestamp gaps do not isolate network delay. Record unresolved parents/cycles/truncation as limitations.
5. Select up to five exact component IDs for further investigation, with supporting trace IDs and span paths. If there are no trace component candidates, explicitly record that result; only then is a labelled global-metric rescue permitted.
6. Write `trace_only.json` using SCHEMA.md: incident hypotheses, component candidates, observations, alternatives, symptom times, inferred occurrence times, and requested-field answer. Unknown fields may be empty; do not present guesses as measurements. Preserve the prompt's incident count with separate incident slots.
7. Seal Stage T using the seal module **before requesting or reading metrics/logs**. A stage seal is immutable. Final-stage investigation may revise the hypothesis in final.json but cannot edit trace_only.json.

All detector arms contribute to the union used for this investigation. Your final diagnosis cannot be credited to a specific detector merely because that detector supplied one helpful trace.

## Stage M: bounded corroboration

Use `get_metrics` and `get_logs` from retrieval.py. Check DATA_API.md for exact syntax and schema.

- At most 20 metric retrieval calls and 10 log retrieval calls total. Metric responses contain at most 50 series and 120 representative/time-binned values per series; logs at most 200 records/call.
- Begin with your Stage T candidates (maximum five). You may expand once to at most five additional explicitly linked components/hosts, recording the link and justification.
- Container-to-node mappings require recorded mapping evidence, not name similarity. Metric service aggregation is not a specific replica measurement.
- If Stage T has no component candidate, a single component-balanced global metric rescue is allowed, labelled as rescue. It does not make latency discovery successful.
- Compare query and preceding reference intervals. Check timestamp units, series coverage, sampling cadence, zeros, missing values, and counter/gauge uncertainty. No epsilon-based score for zero MAD. A reset counter is not a negative physical rate.
- Use logs to corroborate relevant component behavior, recording filters and truncation. Lack of a matching log in a capped search does not prove no event.
- Infer onset from a sustained change or other identified mechanism evidence when available, stating how. The timestamp of the selected slow request alone is a symptom occurrence.
- Explain why the candidate component contributed the delay and distinguish evidence for a resource change from evidence that it caused the incident. If the initiating mechanism is unresolved, say so.

Write executable case code for additional numerical analysis of retrieval responses, run it, and preserve the response files and derived output. Log retrieval calls automatically through the API. Do not spend the entire budget printing raw telemetry.

## Incident association and reason vocabulary

Two slow requests are not necessarily two failures. Group evidence by temporal episode, component, and dependency chain; explain separate incident hypotheses. Keep every time/component/reason association intact. You can leave unresolved fields empty with an abstention reason or offer a qualified inference with alternatives, but must not fabricate observational support.

The following names come from the **public official starter**, not answer keys, and may be used when the evidence supports them:

- Node: `node CPU load`, `node CPU spike`, `node memory consumption`, `node disk read I/O consumption`, `node disk write I/O consumption`, `node disk space consumption`.
- Container: `container CPU load`, `container memory load`, `container read I/O load`, `container write I/O load`, `container network latency`, `container packet loss`, `container network packet retransmission`, `container network packet corruption`, `container process termination`.

These are vocabulary options, not an instruction to map any metric with a matching word directly to a cause. Do not infer specific packet manipulation merely from generic latency or error symptoms. Additional descriptions may be retained in hypotheses; official reason scoring uses exact strings, and uncertainty must remain visible.

## Completion

Create `final.json` and `evidence.md` with:

- Requested-field prediction and associated internal incident tuples.
- Exact observed evidence, provenance, comparative statistics, and inferred mechanisms kept distinct.
- Trace-only versus corroborated changes, retrieval limits, rescue status, uncertainty, and alternative explanations.
- Executed code and generated numerical artifact paths, commands, elapsed time if available, and any data/API/protocol errors.

Before final sealing, update your case's `run.json` (preserving its prepared provenance) with `status: "completed"`, your model/effort, investigation start/end UTC timestamps, executed command(s), code/data artifact references, and any errors. If you cannot complete the investigation, use `status: "failed"` with a nonempty `failure` object, while still producing schema-valid incident slots with honest abstentions. This keeps every scheduled prompt in the results.

Seal final only after code, evidence, and outputs are finished. Do not edit a sealed file. The final task message should identify the row, output directory, both seals, execution outcome, and any failure/exposure. Do not evaluate labels; that happens after every investigator finishes.
