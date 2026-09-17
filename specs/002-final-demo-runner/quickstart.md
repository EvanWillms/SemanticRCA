# Validation and demo guide

## Active harness validation

The empty-output milestone is implemented. See [harness validation](checklists/harness-validation.md) for executed checks and [demo instructions](../../docs/demo-harness.md) for runnable commands. Build the root image and use the same three-flag invocation in contracts/runner.md with a synthetic query CSV and empty output directory. No credential is required. Verify one blank prediction and marked placeholder evidence per original ID, zero calls, header-only input behavior, preflight errors and checkpoint preservation. Run the container with --network=none, --cpus=2 and --memory=8g to verify the scaffold offline. This does not measure diagnostic performance. The full-agent validation and four-minute diagnosis walkthrough below remain deferred; the harness demo must say diagnosis is unimplemented.


The remaining sections below describe deferred full-diagnoser acceptance steps. They are not completed by the empty-output harness.

## Prerequisites

Use a fresh checkout of the candidate revision, Docker, the official development bundle, an empty output folder, and an exported runtime key for live tests. Never paste keys into command history or commit them. No host Python/package setup should be needed for the judge path.

## Acceptance sequence

1. Build and invoke the exact template in [contracts/runner.md](contracts/runner.md), substituting local mount paths. Confirm the default selects the submission agent. This covers FR-001/002/010.
2. Against a controlled endpoint, cover all seven task projections, multiline CSV, non-contiguous IDs, multiple failures (including same component), UTC+8 conversion, missing telemetry, empty queries, and invalid preflight inputs. Check prediction/evidence/usage associations and exact serialization with the official validator/scorer. Covers FR-003–006.
3. Inject HTTP 200 error bodies, unavailable tiers, timeouts, malformed content and unknown usage. Verify bounded retries, GLM-only fallback, conservative budget accounting, honest evidence, and later-case continuation. Kill during a checkpoint and confirm previous predictions remain valid. Covers FR-006–008.
4. Run with the dataset mounted read-only and runtime egress limited to the overridden endpoint. Enforce `--cpus=2 --memory=8g` in the rehearsal Docker invocation. Confirm no runtime downloads or writes outside --out; include temporary and bytecode files in this check. Covers FR-002/003/008.
5. Adapt official `make validate` and `make docker` into the standalone repository, preserving their checks and no external checkout dependencies. Run both with two dev cases. Then run 20 cases under the resource/time/cost caps; record peak memory, elapsed time, spend, failures and output coverage. Do not infer performance from mocks. Covers FR-001–008.
6. Freeze an exposure-aware eval split and run routed and single-model configurations at least twice each. Verify offline recomputation from saved artifacts matches REPORT.md, including missing predictions counted as zero over the full planned query set, strict/partial/per-task accuracy, evidence review, cost/time distributions and repeat variation. Covers FR-009/012.
7. Complete [release checklist](checklists/release.md) on the public default-branch candidate; no secrets, placeholders or unmeasured claims may stand in for evidence. Covers FR-010/011.

## Four-minute demo script

- 0:00–0:30: State the diagnosis question and explain that judging uses this same headless runner.
- 0:30–1:30: Run a single prepared development query through the image; show the actual command and resulting prediction. Aim for under a minute, but measure first.
- 1:30–2:30: Open the newly written evidence/<row_id>.md; connect measurements to the hypothesis, uncertainty, and a genuinely excluded alternative (or state none).
- 2:30–3:30: Show saved routed versus single-model results, dollars, seconds, accuracy, and repeat variation.
- 3:30–4:00: Explain one failure mode and point to REPORT.md/eval/ and the release revision.

Keep a clearly labeled recorded run as a presentation fallback if the provider is unavailable. It does not replace live acceptance testing, and must not be presented as a live result.
