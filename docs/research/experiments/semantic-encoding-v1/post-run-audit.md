# S01 post-run audit

Run: `20260917-s01-001`  
Artifact: `data/experiments/semantic-encoding-v1/S01/20260917-s01-001/`  
Audit status: **passed**. The experiment was not rerun.

I independently parsed the saved JSON artifacts with Python's standard library
and recomputed SHA-256, compact UTF-8 byte lengths, packet reconstruction,
structural facts, provenance, and contrasts. I did not import the S01 codec.

## Checks

- The manifest SHA-256 matches the recorded value
  `0995860c92f9e005f14f6456a6e30792e09165fd8d3ab0065fd9becb5ff57532`.
- All manifest source hashes, frozen fixture hashes, copied-input hashes, code
  snapshot hashes, and 27 non-manifest output hashes match. The saved manifest
  says `supported_on_fixture`, `model_calls: 0`, and `S01 only; S02 not started`.
- Packet-only reconstruction matches every saved decoded node for T0, T1, and
  T2. Independently recomputed expected fact sheets pass for nodes, edges,
  operation counts, span/edge counts, same-entity pairs, and all derived
  different-entity pairs.
- Provenance passes for all 22 source records: packet and sidecar source hashes,
  declared sidecar filenames, sidecar cardinality, every evidence pointer,
  source index, all nine raw fields, row digests, trace/span identity, complete
  source membership, and context.
- Quality and unknown fields pass for every fixture, including one root marker
  and resolved parent status for each non-root node.
- Independently recomputed contrasts all pass: T0/T1 equivalent, T0/T2
  distinct, one exact T2 node and edge added, all prior facts unchanged, count
  deltas `(1, 1, 1)`, and constant-output control rejected.
- Byte accounting matches `sizes.json`: T0/T1 source 1548, cold packet 3455,
  compact provenance 1181 bytes; T2 source 1741, cold packet 3645, compact
  provenance 1336 bytes. These are byte measurements only; no compression or
  model-cost claim is supported.

The first focused-test preflight had one contaminated negative-case failure
because a deliberately bad-index sidecar was reused for the next assertion.
The sidecar was reset, the failed log/source were retained, and no codec or
frozen expected input changed. This artifact audit concerns the subsequent
S01 run and does not treat that test-harness issue as an S01 semantic failure.

## Interpretation

The saved run supports the declared narrow result: this implementation preserves
the reviewed synthetic T0/T1 colored rooted-tree facts through identifier/order
changes and exposes the single T2 occurrence/edge addition, with source-linked
raw-field provenance. The result remains provisional fidelity against authored
expectations reviewed by agents. It does not establish general graph fidelity,
real-telemetry fidelity, timing or status semantics, compression, model-token
efficiency, or deployment accuracy.

Independent audit result: **no artifact discrepancies found; bounded S01 result
confirmed**.
