# Release checklist — execution pending

- [ ] Exactly one root Dockerfile; root run.py accepts the official command with the submission agent as default.
- [ ] README documents build/run, runtime key/endpoint, actual AI tools/models/frameworks and generated versus team-written contributions.
- [ ] REPORT.md and eval/ contain real results, routing ablation, repeated-run variation, evidence review and limitations; offline metrics reproduce.
- [ ] Dependencies are pinned and build context excludes credentials, local data, private telemetry and irrelevant generated artifacts.
- [ ] Secret scan covers source, publishable Git history, build context and image. Findings resolved; exposed credentials rotated. Evidence saved without secret values.
- [ ] Official-equivalent two-case validation and Docker smoke pass from a clean checkout.
- [ ] Endpoint override/isolation, read-only dataset, all runtime writes under --out, fault recovery and atomic checkpoint checks pass.
- [ ] 20-case rehearsal fits 2 CPUs/8 GB/no GPU, per-case 600 seconds/$3 and total 1,200 seconds/$25.
- [ ] Seven task projections, exact labels, UTC+8, multiple incidents, original row IDs and all evidence files validated.
- [ ] Approximately four-minute demo rehearsed with actual output and transparent recorded fallback.
- [ ] Intended work merged and pushed to actual remote default branch before September 17, 2026, 3:00 p.m. PDT.
- [ ] Fresh public clone resolves to tested revision; judge-facing link opens successfully.
- [ ] Official submission form completed with team members/statuses, title/description, Track 1, public repo, and presentation as requested: https://forms.gle/UbPSwZhKNfkovM8s5.
- [ ] Release record captures revision and timestamps; post-deadline changes limited to permitted bug/deployment fixes.
