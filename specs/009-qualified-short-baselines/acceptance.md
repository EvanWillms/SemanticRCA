# Baseline acceptance matrix

These are required future feature checks, not claims of implementation completion. Expected memberships and outcomes must be authored independently of the selector.

| Case | Fixture and required result | Requirements |
| --- | --- | --- |
| B01 | Interleaved two-partition traces, duplicate identities and a new replica: exact resolved allowlisted membership, conflicts/out-of-scope records retained, no suffix-based equivalence | FR-001, FR-010 |
| B02 | Root at T−5 minutes is considered; root at T is excluded; root or child endpoint exactly T is completion-excluded; query completing after its start slice is recovered without truncation | FR-003 |
| B03 | C1 presence equal/counts different gives one latency cohort and retained counts; recovered empty versus unknown structure never match; planted new operation stays unmatched and visible | FR-002, FR-009 |
| B04 | Count 19 fails; count 20 across 3 bins passes if largest bin 10; two bins fail; largest bin 11/20 fails; invalid values/ambiguous members cannot pad counts | FR-005, FR-008 |
| B05 | Independent resampling fixture includes empty blocks: 189 usable is inconclusive; 190 usable with width exactly 40% passes; greater width fails; audit interval and replicate counts reconcile | FR-006, FR-007 |
| B06 | Supported constant-positive and all-zero references retain median eligibility; zero MAD and zero center affect only the defined fields/screens, without epsilon or infinity | FR-006, FR-008 |
| B07 | Sparse five-minute cohort has no implicit ten-minute/same-replica fallback; all six query offsets use the same baseline; beyond-horizon use reports unavailable | FR-004 |
| B08 | One failing rare class among high-volume supported classes remains visible; supported+unavailable equals resolved queries; raw unresolved records separate; empty denominators unavailable | FR-009 |
| B09 | Reordered records reproduce membership/statistics; consistent ID renaming reconciles through a map; source/version changes reject stale reuse without overwriting history | FR-010 |
| B10 | Minority-replica shift, all-replica shift, temporal drift and 10/30/60% reference-contamination controls retain diagnostics and qualifications; no health conclusion or favorable-reference selection | FR-007, FR-008, FR-011 |
| B11 | Benchmark-shaped regressions preserve low support around 54%, a supported ~60 s median, and supported references with wide intervals. When the same research snapshot/profile is replayed, compare against retained source-linked counts and flag differences rather than relaxing rules | FR-005–009, FR-011 |
| B12 | Every member/statistic/qualification resolves to source and version; all checks run without labels, diagnostic models or a local author's prebuilt cache; shared costs and overlap recorded | FR-001, FR-010, FR-011 |

## Constitution and quality review

This feature supplies evidence rather than a diagnosis, preserves bounded source access and reproducible qualifications, and makes no model-routing change. The full runtime/submission and unseen-case diagnostic evaluations remain separate obligations. Specification review establishes testable requirements only; integration planning and execution must supply their own acceptance evidence.
