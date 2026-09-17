# Combined offline workflow demo

For an input dataset and query CSV, run:

```sh
python3.12 scripts/discover.py --dataset /path/to/dataset \
  --queries /path/to/query.csv --out /tmp/my-findings
```

The command prints source-backed observed departures and saves `findings.md`
alongside the complete case artifacts. It uses real discovery results; a
finding describes a measured change and does not by itself establish causality.
Repeated cases reuse the prepared trace view within the run, with preparation
identity and time recorded in `discovery-run.json`.

From the repository root, choose a new output directory:

```sh
python3.12 scripts/demo_discovery.py --out /tmp/symbolicrca-demo
```

Open `/tmp/symbolicrca-demo/demo.md`. No credentials or network access are needed.
The command generates one authored query and eight telemetry families, then runs
the actual discovery CLI and its artifact validator. The same sources feed the
baseline/comparison library and the trace descriptions feed the investigation
library through scripted callbacks.

The report links the scope, source-linked trace and metric findings, targeted
logs, baseline descriptors, semantic descriptions, and investigation receipt.
The authored example has 20 reference requests, a positive query duration
departure, and a separate resource metric departure. The loop performs two
assessments and one request for recorded reference evidence before assembling
the scripted component answer.

The investigation demonstrates control flow and evidence handoffs. Its scripted
answer identifies a changed recording component; it does not establish root
cause or measure diagnosis accuracy. The discovery prediction stays blank and
all model usage stays zero. Unmapped operations and unestablished duration
semantics remain explicitly deferred in the semantic artifact.

For the richer eight-request baseline demonstration, see
[the baseline guide](demo-baseline-comparison.md).

## Container

```sh
docker build -t symbolicrca-discovery-happy .
mkdir /tmp/symbolicrca-container-demo
docker run --rm --network=none --cpus=2 --memory=8g \
  -v /tmp/symbolicrca-container-demo:/demo \
  symbolicrca-discovery-happy python scripts/demo_discovery.py --out /demo
```

This is a small synthetic rehearsal. Full real-data performance, complete
pagination/replay and default-runner promotion remain outside this checkpoint.
