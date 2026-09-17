# Empty-output harness validation

**Date**: 2026-09-17
**Scope**: H-001–H-004; no diagnostic or official benchmark validity claim.
**Status**: Local tests, isolated Docker rehearsal and parent code review passed.

## Automated tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s tests -q
```

Result: 26 tests passed in 1.217 seconds on Python 3.12.5 (2 runner contract, 11 validator contract, 13 integration tests). Covers non-contiguous IDs, all task labels, multiline CSV, blank predictions, empty input, malformed CSV/IDs, path overlap, stale output preservation, unsupported resume, missing agent, checkpoint replacement failure, credential sentinel non-disclosure, no-key execution and clean-source bytecode prevention. Validator negative cases cover malformed/missing/duplicate artifacts, usage values and evidence sections.

## Local demo

Ran `python3.12 run.py --dataset <temporary bundle> --queries <temporary bundle>/query.csv --out <empty temporary output>` against eval/fixtures/query.csv, then scripts/validate_harness.py with --queries/--out. Both returned zero with explicit harness-only/scaffold-only messages. Outputs contained row IDs 9 and 42 with blank prediction values, both evidence files and zero-call usage.

## Docker rehearsal

Built from an isolated context containing only Dockerfile, .dockerignore, run.py, agents/ and rca/. Source bytes were compared to the final repository runtime after review. No adjacent checkout or host dependency was included.

```bash
docker build --network=none -t symbolic-rca-harness <isolated-context>
docker run --rm --network=none --cpus=2 --memory=8g --read-only \
  -v <temporary-bundle>:/data:ro -v <empty-output>:/out \
  symbolic-rca-harness \
  python run.py --dataset /data --queries /data/query.csv --out /out
```

Final image: `sha256:519b8a3a61c8561fbcd4ff91520a1f0fd8f9dab9c267d48a3b9572feea546769`.
Build and run returned zero; runtime completed in approximately 0.29 seconds including Docker startup as measured by the command tool. This is a two-query scaffold smoke result, not benchmark latency. Independent host validator passed the resulting artifacts. No FEATHERLESS environment values were supplied. The cached Python 3.12-slim base was available; no dependency installs were needed. Container Python inspected as 3.12.14.

Application-file inspection showed exactly run.py, agents/{__init__,heuristic,submission}.py and rca/{__init__,contracts,inputs,outputs}.py. No application data, credentials, Git metadata, tests, research, or bytecode appeared in /app. This is source/context/image-content review, not a full repository-history secret audit.

## Review and TDD evidence

- [Parent code review and file fingerprints](../reviews/code-review.md)
- [Runner test-first and regression record](../reviews/runner-tdd.md)
- [Validator red/green record](../reviews/validator-tdd.md)
- [Packaging record](../reviews/packaging.md)

## Remaining limits

All 14 final-release checklist items remain unchecked. Diagnosis, telemetry retrieval, GLM access/routing/fallback, valid incident predictions, evidence quality, repeated held-out model comparison, full 20-case resource rehearsal and publication remain deferred. No keys, paid calls, commits, merges, pushes, or form submissions were made by this milestone. Optional implementation commit hooks were skipped because auto_commit is disabled.
