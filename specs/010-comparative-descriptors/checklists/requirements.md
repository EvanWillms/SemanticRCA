# Specification quality checklist: Comparative descriptors

**Purpose**: Validate specification completeness before implementation planning. These checks assess documentation, not implementation acceptance.

**Specification**: [spec.md](../spec.md)

- [x] Scope and user value are explicit; diagnosis and alert calibration are outside this feature.
- [x] Requirements describe observable semantics without prescribing an implementation library, storage format or transport.
- [x] Primary median/signed-excess output and optional diagnostics are distinguished.
- [x] Support, stability, per-field availability and qualifications remain separate.
- [x] Zero median/MAD, unavailable references, incompatible units and unknown structure have explicit outcomes.
- [x] Structural conditioning cannot erase unmatched requests or multiplicity changes.
- [x] Complete outcomes, review views and aggregation denominators are specified.
- [x] Evidence must resolve to the correct measurement and entity, not merely a syntactically valid pointer.
- [x] Every functional requirement maps to acceptance cases D01–D12 and measurable success criteria.
- [x] Assumptions and boundaries are explicit; no clarification or template placeholders remain.
- [x] Research evidence and planned feature acceptance are distinguished.
- [x] ADR, baseline dependency, semantic contract and acceptance links resolve.

Ready for planning, not marked implemented. The mandatory branch hook was attempted once and failed on read-only Git metadata. No branch or commit was created. The optional after-specify commit hook is disabled by repository configuration and was skipped.
