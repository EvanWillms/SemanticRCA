# Empty-output harness demo

This walkthrough exercises the local scaffold with synthetic queries. It demonstrates input validation and output plumbing only. The stub performs no telemetry analysis, diagnosis, model call, network request, routing comparison, accuracy evaluation, or evidence-quality review.

## Local run

Run from the repository root with Python 3.12. The temporary bundle and output paths returned by mktemp -d are absolute. The output directory must be empty for a new run.

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

The default agent is agents.heuristic, which delegates to the no-call submission stub. The optional agent flag is retained for compatibility. A resume flag is rejected explicitly, and no limit flag is provided. The runner prints a harness-only notice and exits zero after writing the placeholders. The validator accepts only the expected harness shape and prints that it is not official benchmark validation.

Inspect the generated files and one evidence document:

~~~
find "$OUT" -maxdepth 2 -type f -print | sort
sed -n '1,120p' "$(find "$OUT/evidence" -type f -name '*.md' | sort | sed -n '1p')"
sed -n '1,20p' "$OUT/predictions.csv"
sed -n '1,20p' "$OUT/usage.jsonl"
~~~

Each query keeps its original integer row_id. predictions.csv contains a blank value after each ID. Every evidence file has the four required headings and says that diagnosis, evidence assessment, and alternatives assessment are unimplemented. Each usage record has an empty models mapping and zero calls/tokens.

## Container run

Use a fresh output mount for the image run. The source bundle is mounted read-only, output is mounted separately, and network/resource limits make the offline scope explicit:

~~~
CONTAINER_OUT="$(mktemp -d)"

docker build -t symbolic-rca-harness "$REPO"

docker run --rm \
  --network=none \
  --cpus=2 \
  --memory=8g \
  -v "$(cd "$BUNDLE" && pwd):/data:ro" \
  -v "$(cd "$CONTAINER_OUT" && pwd):/out" \
  symbolic-rca-harness \
  python run.py --dataset /data --queries /data/query.csv --out /out

python3.12 "$REPO/scripts/validate_harness.py" \
  --queries "$BUNDLE/query.csv" \
  --out "$CONTAINER_OUT"
~~~

The image copies only run.py, agents/, and rca/; it does not copy local datasets, experiments, research, tests, or credentials. No API-key setup is part of this stub demonstration. REPORT.md records the deferred diagnosis and evaluation work.
