# Bring local work into main

Assessment: 2026-09-17. This is an integration plan, not a merge or release certification.

## Repository snapshot

- Current branch: `008-featherless-trace-semantics`, HEAD `f2ba81c`, matching origin at inspection.
- Local `main`: `270e4f2` (initial commit), 38 commits behind current HEAD.
- Remote inspection over SSH found only `008-featherless-trace-semantics`; it is also the remote default. There is no remote `main`.
- The six older numbered local branches are ancestors of current HEAD and need no separate merge.
- `fix/trace-semantics-robustness` at `05133ad` has one unique commit; current HEAD has eight commits beyond their common ancestor. Its committed delta is the linear conflict-reference fix plus its regression test.
- Worktrees: primary checkout and `/private/tmp/symbolicrca-trace-robustness`. No stashes were reported.
- Primary checkout initially contained 11 tracked modifications and 183 untracked files (about 2.33 MB): docs 74, experiments 63, specs 41, coordination 2, eval 2, and REPORT.md. Tracked modifications increased to 12 during assessment.
- Robustness checkout contains five modified tracked files and two untracked files (`TDD-identity.md`, feature acceptance). Its diff grew during assessment. Both observations establish that this is a moving snapshot; stop writers before final inventory.
- Local data occupies about 65 GB. Dataset, experiment data, credentials and caches are ignored; preserve these locally without adding them to Git.

## Evidence and gaps

- Fresh core check: `PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s tests` passed 59 tests.
- `git diff --check` passed in both checkouts at inspection.
- Broader pytest verification could not start because Python 3.12 lacks pytest. Experiment discovery also exposed missing numpy and httpx2. Unittest is not a replacement for the libraries' pytest function tests.
- Existing coordination records report passing domain demos and an offline Docker rehearsal. These are historical evidence, not fresh full-tree validation.
- `experiments/semantic_encoding_v1/run_s02_s09.py` depends on `/private/tmp/symbolicrca-trace-audit/...`; `run_s01.py` references a developer-specific neighboring checkout. A clean clone cannot be assumed to reproduce these experiments.
- README and architecture still describe the empty-output harness as the current runtime; the combined discovery/domain demo now exists. Documentation must distinguish default harness, optional discovery, scripted investigation and unfinished production diagnosis.
- Two feature directories use number 011. Use complete names in links and reconcile numbering/tool selection before relying on automatic feature discovery.
- Live S09 evidence reports provider HTTP 403 blocking. Full diagnosis, complete acceptance matrices and real-data release qualification remain deferred; a main integration must retain these limitations.

## Ordered integration plan

1. **Freeze and preserve the complete inventory.** Coordinate with owners of both checkouts to stop writes at a checkpoint. Record HEADs, status, ignored paths and untracked file manifests. Preserve all intentional work in explicit checkpoint commits/backup branches; do not use a blanket add of the repository. Do not remove worktrees or old branches yet.
2. **Commit the primary checkout in coherent groups.** Review each untracked file, including generated reports and archives. Suggested groups: ignore rules and harness report/eval fixtures; domain ADRs and specifications; frontend/short-window experiment source and tests; semantic encoding source and fixtures; research/results/presentation and coordination records. Keep source snapshots only where audit provenance requires them. For duplicate ZIP/Markdown outputs, select a canonical artifact and preserve/export redundant material explicitly. Review tracked report content for credentials and unintended dataset inclusion before publication.
3. **Finish the robustness checkpoint in its own worktree.** Inspect the full changed algorithms, acceptance document and identity tests with the owner. Run its focused suite and commit all intended edits. Merely merging `05133ad` would omit the larger uncommitted changes.
4. **Assemble on an integration branch from the checkpointed primary branch.** Merge the completed robustness branch with history preserved. Resolve overlap in trace partition/description code, tests and feature specification against the newer fixture-demo behavior. There is no need to merge each historical numbered branch or cherry-pick changes already in ancestry.
5. **Make the assembled checkout reproducible.** Declare/install development and experiment dependencies in an isolated environment; keep optional experiment dependencies separate from the standard-library runner. Replace machine-specific experiment paths with explicit input arguments or documented external input manifests. Reconcile README, REPORT, architecture, feature links and coordination status. Add a repeatable offline CI entry point; identify live/data-dependent checks separately.
6. **Validate the exact committed candidate from a clean checkout.** Run the 59-test core suite, both library pytest suites, all offline experiment suites and new robustness regression tests. Exercise packaged library fixture demos, the combined discovery demo and the documented Docker workflow with networking disabled. Verify all referenced fixtures and reports are tracked, imports work without incidental local files, diff checks pass, and intentional ignored data/secrets remain excluded. Record commands, versions, outcomes and explicit skips. Do not require paid inference for a repository consolidation.
7. **Promote to main.** Confirm local main remains an ancestor of the validated candidate, then fast-forward it. Push `main` using the requested SSH identity and set tracking. Change GitHub's default branch to main and establish desired branch protection/checks. A bootstrap main branch is necessary before a PR targeting main is possible; alternatively, push the validated main directly for this initial consolidation.
8. **Verify publication, then clean up.** Confirm remote main equals the tested commit and default-branch configuration is correct. Retain backup branches until every manifest item is accounted for. Remove the robustness worktree and obsolete branches only after confirming clean status, ancestry and owner completion.

## Completion criteria

Every intentional local source/document/artifact is committed or explicitly accounted for outside Git; both worktrees have no unexplained work; the robustness work is included; a clean checkout passes the declared offline checks; GitHub main points to that tested candidate and is the default. Remaining research and diagnosis limitations are documented without representing the demo as a complete benchmark submission.
