# Validation guide: first descriptive compression experiment

**Status**: Planned procedure. No encoder or experiment CLI exists under this design, and no experiment was executed in this documentation revision.

1. Read [spec.md](spec.md), [ADR 0002](../../docs/adr/0002-descriptive-semantic-compression.md), and the [evidence contract](contracts/semantic-evidence.md). Generate implementation tasks for A1 only, following the repository workflow.
2. Author the seven-span T0 graph, its renamed/shuffled T1 equivalent, and the eight-span T2 contrast from [plan.md](plan.md). Declare all synthetic units and meanings. Keep any real telemetry outside source fixtures.
3. Independently record the operation/parent/count/entity fact sheets. Freeze fixtures, codebook, pattern, fidelity and equivalence policies, hashes, and reference answers before implementing the encoder. Do not derive the answer key from its output.
4. Encode each trace without giving the encoder the expected facts. Expand each packet using only its declared dictionaries, then compare all contracted facts. Separately check provenance links and original-ID recovery.
5. Verify T0/T1 structural equivalence and T0/T2's exact added child and count delta. Preserve every error and unknown. A failure rejects this encoder for the tested assumption; no LLM or RCA score is needed.
6. Produce a short report showing inputs, packets, facts, differences, and raw/normalized/symbolic bytes including metadata. Size is descriptive in A1; A3 separately tests a compression advantage. Record that no actual model-cost or accuracy measurement was made.
7. Stop after the A1 result. A2 and later tests require their own scoped tasks and references. A pass supports only the fixture claim; a negative result is a completed experiment, not a reason to build the whole pipeline.

The [old CLI](contracts/experiment-cli.md) and [old validation guide](deferred-quickstart.md) describe deferred candidate-recall work. Their commands are not prerequisites or implementation instructions for A1.
