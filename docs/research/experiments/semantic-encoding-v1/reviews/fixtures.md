# S01 fixture review

Reviewed read-only against the active A1 plan (`specs/001-candidate-recall-experiment/plan.md:43-73`), the S01 handoff (`docs/research/reliability-taxonomy-review.v1/07-incremental-experiments-handoff.v1.md:45-73`), and the descriptive evidence contract (`specs/001-candidate-recall-experiment/contracts/semantic-evidence.md:16-38,42-76`). No encoder was imported or run.

## Coverage and independent checks

- `T0.json:1-90`, `T1.json:1-90`, and `T2.json:1-100` were parsed with a standalone Python-stdlib checker. Each has one root, unique span IDs, no dangling parent references, the same declared synthetic millisecond context, and every operation name maps through `codebook.json:2-14`.
- `T0` independently computes 7 spans, 6 edges, counts `request.handle=1`, `cart.get=2`, `db.hget=1`, `catalog.get_product=3`, 19 distinct entity pairs, and same-entity pairs `(2bd2,7ac3)` and `(4de4,1ef5)`. Counts, edge/span totals, and same-entity relations match `expected-facts.json:20-84`.
- `T1` independently has the same non-ID record multiset as T0, with all IDs/parent references renamed and storage order shuffled. Its canonical rooted unordered graph matches T0 when operation/entity colors are retained and IDs are ignored, as required by `policy.json:2-5`.
- `T2` is T0's first seven records byte-for-byte followed by `0ab7` (`synthetic.Catalog/GetProduct`, parent `8af0`, entity `catalog#1`, timestamp `1024`, duration `2`). Independent deltas are exactly +1 span, +1 edge, and +1 `catalog.get_product` occurrence, matching `expected-facts.json:4-18` and the A1 plan.
- `freeze.json:2-10` hashes were independently recomputed with stdlib SHA-256. All six listed hashes match; no frozen input drift was found.

## Findings

1. **Data and core A1 facts are ready.** The fixtures meet the intended T0/T1/T2 shape, the codebook is total over observed operation names, and the declared unknowns are preserved in `policy.json:18-23` (`business_outcome`, status interpretation, interaction role, backend target, instrumentation completeness). This supports isolated S01 execution once the encoder/decoder is wired.

2. **Expected-facts array ordering is underspecified in the fixture, but the current runner resolves it (informational).** `policy.json:2` defines a “rooted unordered tree,” while `expected-facts.json` stores arrays. `T1`'s expected `nodes` are in T0's canonical tree order (`expected-facts.json:95-137`) while source rows are deliberately shuffled (`T1.json:11-88`); `same_entity_pairs` also uses semantic/source order rather than one obvious lexical order (`expected-facts.json:139-147,210-226`). The new runner's `compare()` normalizes node arrays and pair endpoints/lists (`experiments/semantic_encoding_v1/run_s01.py:29-45`), so this does not block S01 and the frozen files remain unchanged. Preserve that comparison behavior in any future runner revision.

3. **No explicit T0↔T1 ID alias map is provided (minor implementation ambiguity).** The policy deliberately ignores trace/span IDs for equivalence and keeps entity names exact (`policy.json:2`), so graph canonicalization can test equivalence without aliases. However, the handoff also asks for exact parent references and provenance/raw-ID mappings (`07...md:53-58, Result artifact contract`), while `freeze.json` freezes only the fixture/codebook/fact/policy files. If the runner wants to report an occurrence-level correspondence between T0 and T1, it needs either a declared alias derivation rule or a report field saying aliases are inferred by graph matching and may be non-unique. This does not block a set-based A1 gate.

4. **`distinct_pairs` is meaningful but its definition should be made explicit (minor documentation gap).** The expected values 19 and 24 equal all unordered span pairs minus same-recording-entity pairs, not graph-edge pairs. The current policy says “all pairwise equality/distinctness” (`policy.json:8-11`) but does not state unordered-pair counting. A short definition prevents an encoder from treating this as distinct `(entity, operation)` pairs or directed pairs.

## S01 decision

The independent content/hash checks pass. The runner already handles the unordered relation arrays without changing frozen fixtures. The `distinct_pairs` counting convention remains a minor documentation improvement: the expected 19/24 values are all unordered span pairs minus same-entity pairs. Do not alter the frozen fixture files or their hashes. S01 remains isolated: no frontend-blind harness, trace-audit script, real telemetry, model, or answer-key input is needed.
