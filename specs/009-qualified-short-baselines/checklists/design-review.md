# Planning review: Qualified baselines

Reviewed 2026-09-17. Checked items describe design review only; B01–B12 implementation acceptance remains pending.

- [x] Phase 0 choices and alternatives are source-grounded; no unresolved planning questions remain.
- [x] Both pre-research and post-design constitution checks are recorded in the plan.
- [x] Snapshot-bound exact-root selection replaces use of a capped response as population evidence.
- [x] Duplicate/conflict policy, endpoint arithmetic, bin boundaries and bootstrap replay evidence are explicit.
- [x] Support, stability, statistic availability and partial inspection remain separate.
- [x] C0 known/unknown denominators and complete query assignments support the feature 010 handoff.
- [x] API, artifact schema, publication, source validation, errors and offline CLI are defined.
- [x] Independent B01–B12, scan/index, reuse and joint acceptance gates map to delivery stages.
- [x] Quickstart commands are clearly planned; no nonexistent implementation was reported tested.
- [x] Existing discovery policy differences and future integration ownership are explicit.
- [x] Local documentation links and template/requirement consistency were checked.

Setup used `SPECIFY_FEATURE_DIRECTORY` for feature 009. Actual Git branch is `008-featherless-trace-semantics`; no branch creation was requested by planning. Before/after-plan commit hooks are optional and disabled by repository auto-commit configuration. No task file, production code or experiment output is created by this plan.

Parallel cross-review completed: late missing-context lookups now preserve the reference-only frozen catalog; field kinds and validated-only review entry are explicit. Both reviewers verified the corrections with no remaining material findings. Across both packages, all 12 planning artifacts and 43 local links passed documentation checks. Per the user's checkpoint instruction, a scoped semantic commit is created after this review; the optional automatic hook remains disabled.
