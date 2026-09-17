State: blocked
Updated: 2026-09-17T21:24:49.484563+00:00
Latest checkpoint: User-approved six-call run 20260917-s09-approved-001; all six HTTP 403 / Cloudflare 1010 browser_signature_banned.
Working now: Live execution stopped on explicit non-retryable provider access block; deterministic demo remains available.
Demo evidence: python3 -m unittest experiments.semantic_encoding_v1.test_s02_s09 -v — 7/7 passed; deterministic S02–S08 run 20260917-s02-s09-009.
Next handoff: Featherless site owner must permit this client; saved response Ray ID a3cb2cfb79671be5. No further calls until access is restored.
Blocker / overlap: Paid transport explicitly approved; provider rejects client signature. No model outputs, actual usage or billing available, so full live capability unproven. P01 remains glm-semantics ownership. Local R0 /private/tmp dependency remains.

Launcher checkpoint: run_s09.sh now loads the existing local SDK dependency directory when global Python lacks openai. SDK 3.14.1 import and prepare-only run passed; no paid calls made for this fix. Run with sh experiments/semantic_encoding_v1/run_s09.sh. The /private/tmp dependency directory must remain available, or set S09_PYTHON/S09_DEPENDENCIES.
