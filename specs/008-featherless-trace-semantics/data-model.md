# Planned data model

All records have a schema version. IDs are scoped, stable audit identities; hashes are not provider cache controls. Existing S01 packets keep their contract. These records describe S09 sidecars and future adapters.

| Entity | Required fields and rules |
|---|---|
| EvidencePacket | packet_id, source_kind (authored/indexed), fidelity_version, codebook_version, raw facts, occurrence/entity bindings, recorded edges, qualified timing, status strings, evidence IDs, coverage/conflict facts, provenance hash. Encoding never consults expected answers. |
| EquivalencePolicy | policy_id/version, included facets, ignored incidental identifiers, permitted alias map, unknown/conflict behavior. A structural match does not imply equal timing or exact entity identity. |
| ScopedMapping | mapping_id/version, producer applicability predicate, raw value, interpretation, evidence IDs. Unknown applicability cannot match; conflicting applicable mappings yield conflicting. Synthetic mappings apply only to their authored fixtures. |
| PromptPack | pack_id/version, exact system text, shared representation definitions/schema, serialization version, prefix hash, token count and measurement source if available. Hash includes all semantic definitions. |
| Annotation | claim_id, packet_id, facet/definition version, semantic_layer (description/interpretation), production_method, support_strength, scoped value, evidence IDs, limitations, validation_state. Values may be unknown/conflicting; a mechanism hypothesis is not an observed cause. |
| ModelAttempt | run_id/trial_id/attempt_id, format/repetition/order, requested/returned model, settings, exact request hash, prompt pack hash, start/end/wall time, HTTP/finish status, raw response path/hash, failure, usage record, validation links. Store no auth headers. |
| UsageRecord | total_input_tokens, cached_input_tokens, output_tokens, optional reasoning-token details, raw provider usage, rate snapshot, estimate bounds, observed charge if supplied, source/availability of each quantity. Null means unknown; measured zero is distinct. |
| StudyManifest | study_id, hypothesis, limits, 18 planned trial identities, counterbalanced schedule, frozen source/code/fixture/prompt/rate hashes, independence/exposure record, available provider capabilities, isolated/integrated designation. |
| ClaimAdjudication | attempt_id, expected_fact_id, claim_id, entailment judgment, evidence resolution, unsupported-promotion flag, reviewer identity/method, disagreement, decision with rationale. Gold lives only in scorer inputs. |

Each packet may have many annotations and attempts. An annotation cites evidence within its packet/context scope; cross-packet references are invalid unless explicitly included in the input contract. A dictionary proposal is a separate interpretation record, never an in-place codebook update.

Attempt states: planned → admitted → dispatched → received → validated/invalid. Admission may yield budget_refused or unavailable; dispatch may yield transport_failed or interrupted_uncertain. All terminal states retain consumed/reserved budget. No automatic retry or repair exists in S09. Raw responses are immutable even when invalid.

Study states: frozen → running → complete/incomplete → adjudicated. Conclusions are supported_on_fixture, falsified, or inconclusive. A failed fidelity boundary blocks dependent integrated studies; isolated studies with correct authored facts explicitly retain their isolation qualification.

## P01 specialization

The P01 output contract is the complete [candidate prompt](prompts/structural-v1.txt): schema_version, packet_id, trace_id, context, entities, occurrences and unknowns. Each occurrence tuple preserves the ten declared values, including an opaque evidence ID. The deterministic scorer expands codes and aliases to source facts; GLM output never overwrites the source packet. This experimental output is a candidate symbolic packet, not the later interpretive annotation sidecar.

P01's evaluator-only manifest maps opaque packets to source fixtures, hashes inputs/prompt/expected facts and fixes 18 trial slots. It must not be loaded by the model-message builder. CacheProbePair adds block_id, seed_attempt_id, shared_target_attempt_id, control_target_attempt_id, early_tag/token identity, common_static_prefix_tokens and suffix-divergence location. These records join the same immutable attempt/usage ledger; six probe attempts form two separately reported comparisons.
