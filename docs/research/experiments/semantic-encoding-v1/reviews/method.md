# S01 method review (pre-execution)

Review date: 2026-09-17  
Repository: `/Users/nonadmin/Development/SymbolicRCA`  
Scope: dedicated S01 codec, runner, frozen fixtures, and README/policy contract.  
Execution status: **not executed**; no tests or experiment commands were run.

## Coverage

Read completely:

- `experiments/semantic_encoding_v1/codec.py`
- `experiments/semantic_encoding_v1/run_s01.py`
- `experiments/semantic_encoding_v1/README.md`
- all frozen inputs under `experiments/semantic_encoding_v1/fixtures/`: `T0.json`, `T1.json`, `T2.json`, `codebook.json`, `expected-facts.json`, `freeze.json`, and `policy.json`

The fixture reviewer has separately confirmed the raw records, expected facts, and frozen hashes. This review therefore covers the method and acceptance wiring, not a rerun of those checks.

## Findings

### P0 — runner is syntactically invalid

`experiments/semantic_encoding_v1/run_s01.py:185` currently reads:

```python
added_nodes = sorted([[n['id'], n['operation'], n['parent'], n['entity']] for n in added)
```

The outer list-comprehension bracket is missing before `)`. The S01 runner cannot be imported or executed until this is corrected to close the list. This is a harness blocker; no result or pass/fail decision can be attributed to the current source.

### P1 — intended acceptance is meaningful but narrow

After the syntax fix, the runner checks the core S01 claim against frozen authored expectations:

- `compare()` checks sorted node facts, parent edges, operation counts, span/edge counts, same-entity pairs, and the complement of those pairs (`run_s01.py:34-50`).
- T0/T1 colored-tree canonicalization checks invariance to identifier renaming and source-order shuffling; T0/T2 checks the structural contrast (`run_s01.py:187-194`, `codec.py:108-125+`).
- T2 checks one exact added node and edge, preservation of pre-existing decoded facts, and the expected count deltas (`run_s01.py:184-193`).
- The constant-output control is rejected (`run_s01.py:194`), although it is implemented by comparing the T0 result to T2 expectations rather than by running a separately coded constant labeler.

This is a valid S01 acceptance slice for one synthetic, single-trace rooted tree. It does not establish general graph fidelity, multi-trace behavior, malformed-input behavior, timing semantics, telemetry fidelity, compression, or model-cost benefit. The README and policy state those bounds correctly (`README.md:33-38,55-64`; `fixtures/policy.json:2-25`).

The negative-pair assertion is partly derived rather than independently authored: `compare()` computes every `different_entity_pairs` value as the complement of the frozen `same_entity_pairs` over expected node IDs (`run_s01.py:37-39`). The resulting all-pairs check is still meaningful under the stated total equality/distinctness policy, but it should be described as a derived complement check, not as an independently annotated negative fact sheet.

`quality_checks()` contains explicit root-marker and resolved-parent checks (`run_s01.py:53-86`) but is never added to `diffs` or `failures` in `main()` (`run_s01.py:171-173,198-202`). Tree validity is still enforced indirectly by `canonical_structure()` (`codec.py:108-125+`), and `decode()` deterministically labels root/non-root parents (`codec.py:85-105`), but the explicit quality checks are dead acceptance code and will not appear in the recorded fact diff.

### P1 — source-independent decode is demonstrated, with a bounded claim

The serialization boundary is real: the runner compacts the packet, writes it, parses only those packet bytes, and calls `decode()` without passing a fixture, expected facts, or provenance (`run_s01.py:160-170`). `codec.decode()` reads the operation dictionary and entity inverse map from the packet and reconstructs facts from packet contents (`codec.py:85-105`). The module-level contract explicitly says decoding needs the packet only (`codec.py:1-5`).

This supports the narrow claim that a generated S01 packet can be decoded without rereading source. It does not provide a hardened standalone decoder: `decode()` trusts the packet's schema, codebook, entity map, and structural fields and does not itself reject cycles, multiple roots, or unresolved parents. The runner calls `canonical_structure()` during encode and when writing the decoded structure (`codec.py:80-82`; `run_s01.py:167-170`), so the exercised path is structurally guarded. Fuzz/tamper resistance and decoder validation outside this runner remain untested.

### P1 — provenance audit is substantive, but one linkage is not checked

The runner audits both packet and sidecar source hashes, sidecar cardinality, every evidence pointer, 1-based source index, all nine raw fields, row digest, trace/span identity, complete source membership, and context (`run_s01.py:89-127`). This is a useful separate provenance check and bounds the result to authored synthetic source rows. The codec retains the raw operation, timestamp, duration, type, status, and evidence pointer (`codec.py:54-79`); no status or timing interpretation is inferred.

The audit receives the sidecar object in memory and never verifies that `packet['provenance_sidecar']` (`codec.py:79`) names the sidecar file actually written by the runner (`run_s01.py:165-172`). A packet could therefore advertise a wrong sidecar filename while this in-memory audit still passes. This is a P2 artifact-integrity gap: verify the declared filename exists under the run directory and is the sidecar used for the audit.

The provenance audit also uses decoded `entity`, `trace_id`, and raw fields to reconstruct the row, while the sidecar selects the source row. The row digest and complete membership checks make this a meaningful source linkage check for this fixture, but it is not an independent external annotation of semantic correctness.

### P2 — size accounting is properly bounded

The reported values are UTF-8 byte lengths, explicitly labeled as such (`run_s01.py:174-178,238-248`). Cold packet size includes dictionary/policy/context/reference metadata; provenance is separately reported. The result explicitly says this is a normalized graph control, not a compression trial, and makes no compression or model-cost claim (`run_s01.py:244-248`). No baseline or token estimate is presented, so the size table should not be interpreted as an efficiency result.

The `dictionary_bytes_included_in_packet` value is a descriptive compact codebook length (`run_s01.py:178`), not an amortized/shared dictionary analysis. That is acceptable for S01 because the report makes no compression claim.

### P2 — execution has an external manifest input dependency

The manifest hashes `/Users/nonadmin/Development/mantisgrid-hackathon/hackathon-2026-official/track-1/docs/data.md` (`run_s01.py:208-213`). S01 itself uses only synthetic fixtures and does not read this guide, but execution still fails if that absolute path is unavailable. This is an operational portability dependency rather than a semantic acceptance flaw. The handoff's required source inventory may justify retaining the hash in this workspace; it should be called out if the run is moved.

## Assessment

**Actual status:** blocked before execution by the syntax error at `run_s01.py:185`.

**Method status after that fix:** the acceptance design is meaningful for the declared S01 hypothesis: packet-only decode, exact occurrence-level facts, colored rooted-tree equivalence, entity equality/distinctness, one visible T2 addition, source-row provenance, and bounded byte accounting. It is appropriately presented as provisional fidelity against reviewed authored synthetic expectations. The result must remain limited to this slice; it cannot support broad semantic encoding, real-telemetry, timing, compression, or model claims.

## Actionable handoff

1. Fix the unmatched bracket at `run_s01.py:185` before running tests or S01.
2. Decide whether to wire `quality_checks(facts)` into `diffs`/`failures`; if retained as acceptance logic, include its result in `fact-diff.json`.
3. Verify `packet['provenance_sidecar']` against the actual sidecar path before declaring provenance complete.
4. Preserve the report wording that distinct-pair results are a complement of authored same-pair facts and that all conclusions are synthetic S01-only.

No repository files were edited. This report is the only artifact written by this review: `/tmp/s01-method-review.md`.
