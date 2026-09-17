# SymbolicRCA

SymbolicRCA aims to build a multimodal symbolic evidence layer for efficient,
explainable infrastructure root-cause analysis. Its execution flow separates
deterministic data preparation from a bounded agentic investigation loop:
repeatable operations produce qualified evidence, the agent asks follow-up
questions and compares hypotheses, and validated answer assembly returns the
requested incident fields with supporting evidence.

See the [execution architecture](docs/architecture.md) for the flow and stage
contracts, and the [project vision](.specify/memory/constitution.md#project-vision-and-success-criteria)
for success criteria. This is the target architecture; the current runtime is
the empty-output harness described below.

The short-window study is translated into [qualified frontend baseline requirements](specs/009-qualified-short-baselines/spec.md) and [comparative descriptor requirements](specs/010-comparative-descriptors/spec.md), governed by ADRs [0013](docs/adr/0013-qualified-short-window-frontend-baselines.md) and [0014](docs/adr/0014-reference-relative-comparative-descriptors.md). These specify future behavior; they do not establish implementation completion.

## Current implementation

This repository currently ships the bounded, offline demo harness for the final runner milestone. It accepts the official three-flag command, validates the supplied dataset and query paths, and writes one structurally valid artifact set per query:

- `predictions.csv` has the original `row_id` values and blank `prediction` fields.
- `evidence/<row_id>.md` has `Answer`, `Confidence`, `Evidence`, and `Ruled out` sections that identify diagnosis as unimplemented.
- `usage.jsonl` records measured wall time with `models={}` and zero model calls/tokens.

The harness does not read telemetry, call a model, access the network, or require an API key. A successful run means that the CLI and output scaffolding completed; it is not a diagnosis or benchmark result. Diagnosis, routing, accuracy, evidence-quality review, and final release checks remain unimplemented or unmeasured. See [REPORT.md](REPORT.md), [the demo guide](docs/demo-harness.md), and [the fixture notes](eval/README.md).

## Run locally

The runner uses Python 3.12 and the standard library only. Start with a fresh, empty output directory:

~~~
REPO="$(pwd)"
BUNDLE="$(mktemp -d)"
OUT="$(mktemp -d)"
cp "$REPO/eval/fixtures/query.csv" "$BUNDLE/query.csv"

python3.12 "$REPO/run.py" \
  --dataset "$BUNDLE" \
  --queries "$BUNDLE/query.csv" \
  --out "$OUT"

python3.12 "$REPO/scripts/validate_harness.py" \
  --queries "$BUNDLE/query.csv" \
  --out "$OUT"
~~~

The validator checks the harness shape only and says so in its success message. The full command walkthrough, including output inspection, is in [docs/demo-harness.md](docs/demo-harness.md).

The optional agent module switch is --agent and defaults to agents.heuristic. The runner recognizes --resume only to reject it explicitly; resume is unsupported, and no --limit flag is provided.

## Build and run the image

The application layer contains only `run.py`, `agents/`, and `rca/`. It installs no packages at build time and has no runtime dependency on host Python packages. Build from the repository root, then mount the bundle read-only and an empty output directory:

~~~
REPO="$(pwd)"
BUNDLE="$(mktemp -d)"
OUT="$(mktemp -d)"
cp "$REPO/eval/fixtures/query.csv" "$BUNDLE/query.csv"

docker build -t symbolic-rca-harness .

docker run --rm \
  --network=none \
  --cpus=2 \
  --memory=8g \
  -v "$(cd "$BUNDLE" && pwd):/data:ro" \
  -v "$(cd "$OUT" && pwd):/out" \
  symbolic-rca-harness \
  python run.py --dataset /data --queries /data/query.csv --out /out
~~~

The command intentionally retains the official `python run.py --dataset /data --queries /data/query.csv --out /out` shape. The current stub ignores `FEATHERLESS_API_KEY` and `FEATHERLESS_BASE_URL`; no key or network access is needed for this milestone. Do not add a key to fixture runs.

## Verification

Run the contract and integration checks with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s tests -v
```

The reviewed milestone passed 26 tests and an offline Docker rehearsal. See [validation and review evidence](specs/002-final-demo-runner/checklists/harness-validation.md). These checks verify the empty-output scaffold only.

## AI and authorship disclosure

Human-provided requirements and review direction define this milestone. OpenAI Codex served as the planning and review assistant, and implementation subagents used OpenAI `gpt-5.6-luna` with `xhigh` reasoning. Within this milestone, the harness code, tests, and documentation were AI-generated under that direction. This disclosure does not infer individual team authorship and does not claim model-generated diagnosis quality.

The shipped runtime uses Python 3.12's standard library and Docker's official Python 3.12 base image. It does not use a model SDK, telemetry framework, pandas, or an external service in the empty-output harness.
