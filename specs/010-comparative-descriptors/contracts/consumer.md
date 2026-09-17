# Planned comparative descriptor interface

**Version**: `comparative-descriptor-bundle-v1` / `frontend-comparison-v1`.

This implementation contract supplements [descriptors.md](descriptors.md) and consumes [feature 009's producer contract](../../009-qualified-short-baselines/contracts/producer.md). APIs and commands are planned, not implemented.

## Python boundary

- `describe(observation, assignment, baseline_outcome, structural_population, definition) -> ComparativeDescriptor`: pure construction from validated inputs, with no source reads or membership selection. Baseline/population inputs may be typed MissingContext outcomes from the producer; these create unavailable subresults without inventing reference objects. Return complete unavailable outcomes when support or field eligibility is missing.
- `review_view(descriptors, baseline_set_id, slice_index) -> ReviewView`: select at most five positive-excess descriptor references, ordered under the fixed view definition. Accept only descriptors with successful semantic validation; reject unvalidated or failed-validation entries and mixed source/unit/definition scopes. Validated domain-unavailable outcomes remain in the complete population but cannot rank without an available positive excess.
- `summarize_occurrences(descriptors, assignment_index, inspection_receipt) -> DescriptorCoverage`: reconcile resolved assignments and outcomes separately from raw unresolved observations and unprocessed assignments.
- `validate_descriptor(descriptor, evidence_resolver, validation_cache) -> ValidationResult`: verify exact entity/measurement/statistic values and qualification propagation. The cache is keyed by snapshot, object content and definition versions.
- `write_bundle(descriptors, views, coverage, validation, output_dir) -> DescriptorManifest`: publish artifacts only with truthful completion/validation status.

The narrow evidence resolver exposes `resolve_source(locator)` and `resolve_derived(reference)` against declared inventories. It cannot execute user code, arbitrary SQL, shell commands or unrestricted paths. Callers provide dataset/artifact roots and a budget; the comparison core never opens files. Typed values follow the repository's frozen-dataclass and explicit serialization convention.

## Artifact interface

| Artifact | Required content |
| --- | --- |
| `manifest.json` | schema/definition versions, input baseline manifest hash, snapshot/set IDs, artifact hashes/counts, completion and validation states |
| `descriptors.jsonl` | Complete descriptor envelopes for every processed resolved query assignment, including negative, zero and unavailable outcomes |
| `descriptor-index.json` | Descriptor ID to actual artifact/logical-record locator, validated against the JSONL content |
| `review.json` | Separate top-five view per query slice, referencing descriptor IDs and retaining total rankable/full-population counts |
| `coverage.json` | Reconciled assignment/observation/occurrence/field/structural counts and explicit partial inspection state |
| `validation.json` | Source/statistic/calculation checks, failures and validator definition/version |
| `timings.json` | Distinct source/baseline validations, source reads, descriptor/view work, elapsed time and memory measurements |

References to input baselines are portable bundle-relative or content-addressed references; absolute developer paths are never required. Original raw measurements and full reference evidence remain reachable in the input bundle. Partial outputs retain a manifest/receipt and unavailable or unprocessed reasons rather than implying completeness.

Use the producer's canonical serializer rules: finite JSON numbers, explicit null/availability pairs, deterministic structured identities and immutable completed generations. Write content first and publish the manifest last. A review entry never stands in for the full descriptor. Large pattern lists may use separate addressable pattern-difference pages with explicit total/count/continuation; their total membership remains validated and accessible.

## Validation and errors

1. Validate input schema, hashes, completion state, source snapshot and policy compatibility. A corrupted or unknown-version bundle is rejected before constructing trusted comparisons.
2. Verify referenced measurements and baseline statistics through restricted evidence access. Validate each distinct source/statistic once per compatible session; reuse is recorded, not assumed.
3. Validate arithmetic and availability under `frontend-comparison-v1`, structural denominators/deltas and all propagated qualifications.
4. Reconcile complete descriptors, views and coverage before publication.

Ordinary unsupported references and zero-denominator fields are successful domain outcomes, not input-integrity failures. Wrong-entity, wrong-statistic, stale-source or missing required evidence is a validation failure: retain a failure record and construct a new immutable failure outcome with affected comparison fields unavailable, never substitute zero. Failed validation is recorded separately and the outcome cannot enter a trusted review view. A globally corrupted bundle cannot be repaired by selectively trusting attractive results. Partial producer bundles may be inspected in audit tooling but are rejected by the normal consumer CLI as complete inputs.

## Developer CLI

```sh
python -m rca.comparisons build --dataset-dir DATA --baseline-dir BASELINES --output-dir OUT
python -m rca.comparisons validate --dataset-dir DATA --baseline-dir BASELINES --bundle-dir OUT
```

An optional `--diagnostics ratio,mad` enables exactly those named fields; default is neither. Unknown diagnostic names are errors. The policy/definition is recorded in the output, and diagnostics do not change primary eligibility or review order.

Exit 0 means complete output with successfully validated evidence, even when domain comparisons are unavailable. Exit 2 means invalid arguments/schema/definition; exit 3 means input/source/evidence integrity failure; exit 4 means partial processing or exhausted work budget. Failure artifacts remain inspectable where safe. Existing output generations are immutable; use a fresh output directory for a different definition or baseline.

## Discovery adapter boundary

A later explicit discovery profile may invoke the producer and consumer through the feature 004 operation executor. Map a duration subresult to a finding with descriptor ID, exact resource/observation identity, normalized ms, reference median, signed excess, eligibility, reasons, qualifications and evidence links. Structural findings retain population/pattern references, denominators and deltas. Never flatten field availability into a single zero or remove instability.

Expose the complete finding population and a separate review view. Do not restrict findings to the prompt's failure count, merge trace and metric scores, or infer incident time/component/reason. Record `short-window-c1-pooled-v1` and `frontend-comparison-v1` in operation receipts instead of claiming legacy `track1-discovery-v1` behavior. The adapter must retain legacy policy selection explicitly and preserve independent metric discovery and the official output contract. Implementing this consumer alone does not promote the adapter or change the three-flag runner default.
