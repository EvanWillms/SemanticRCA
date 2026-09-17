# Validation guide

For the immediate P01 test, use [minimal-test.md](minimal-test.md), its six checked design inputs and exact prompt. P01 is now implemented and its first live study completed; see the [result](../../docs/research/experiments/semantic-encoding-v1/P01-result.md). Use the commands below to replay scoring or start a separately frozen new run. The S09 commands below remain future, deferred examples.

The S09 commands in the next section describe the deferred protocol, not the completed P01 runner. Separately owned exploratory S09 work does not establish implementation of this protocol.

## Existing baseline

From the repository root, the existing structural check is:

```sh
python3 -m unittest experiments.semantic_encoding_v1.test_s01 -v
```

It covers S01 only. It cannot prove general trace, timing, mapping or model fidelity.

## After implementation

1. Freeze the three authored S06 inputs and independent expected facts. Keep two equal-information representations. Record reviewer independence and known exposure. Use one frozen candidate/settings/output cap and exactly 18 planned trials.
2. Run the proposed offline tests and dry-run; verify requests contain no expected labels, case-specific prior diagnoses or earlier responses. Check stable prefixes, complete unknown/conflict fields, strict schema validation, fake transport failures, missing usage and conservative budget refusal.

```sh
python3 -m unittest experiments.semantic_encoding_v1.test_s09 -v
python3 -m experiments.semantic_encoding_v1.run_s09 --manifest experiments/semantic_encoding_v1/fixtures/s09/manifest.json --run-id s09-preview-001 --mode dry-run
```

3. Before a live execution, confirm effective model rates/account limits, allowed GLM model identity, input token admission bounds and capability settings; freeze changes before results. Supply credentials through the environment without printing them. Live is a separate execution action, not part of this plan.

```sh
python3 -m experiments.semantic_encoding_v1.run_s09 --manifest experiments/semantic_encoding_v1/fixtures/s09/manifest.json --run-id s09-live-001 --mode live
python3 -m experiments.semantic_encoding_v1.score_s09 --run-dir data/experiments/semantic-encoding-v1/S09/s09-live-001 --expected experiments/semantic_encoding_v1/fixtures/s09/expected-facts.json
```

4. Inspect all 18 slots, raw outputs and independent adjudication. Missing access means not run; failed calls remain visible. Require correct status/outcome distinctions and zero unsupported promotions across every output for feasibility. Compare factual entailment separately from JSON validity and label agreement.
5. Report total actual input tokens including schema/dictionary for each arm, output usage, end-to-end latency, cache-token availability and cost bounds. Smaller bytes do not prove token benefit. Lower cached cost does not prove compression. Repeat saved scoring with network disabled; the result should reproduce without another call.
6. Publish supported_on_fixture/falsified/inconclusive, all qualifications and the next smallest study. Stop here. Any extra model comparison, retry study, cache probe or broader variable-trace experiment gets a new frozen manifest/run.

A cache-free run must remain correct and budgeted. No fixed hit rate, TTL or latency speedup is an acceptance requirement. Refer to [the contract](contracts/annotation-study.md) for artifact states and [the plan](plan.md) for the optional later probe.

## Implemented P01 commands

```sh
python3 -m unittest experiments.semantic_encoding_v1.test_p01 -v
python3 -m experiments.semantic_encoding_v1.run_p01 score --run-id 20260917-p01-002 --report-name result-demo-reviewed.json
```

The demo command is offline and spends no credits. It verifies retained frozen artifacts, preserves the original live and audited summaries, and writes/confirms a separate reviewed demo report. The original evidence folder must be present locally. The older live code snapshot remains in the run directory. For an explicitly authorized new live run, set FEATHERLESS_API_KEY in the environment or a local Git-ignored .env, then use `prepare --run-id NEW_ID` followed by `run --run-id NEW_ID`. Prepare makes bounded metadata/tokenization calls; run admits at most 18 generation attempts and refuses reused execution IDs. Never use shell sourcing to load the environment file. No cache-smoke sender is enabled: the observed natural-prefix gate fails. Current code is the bounded P01 slice, not S09 or production integration.
