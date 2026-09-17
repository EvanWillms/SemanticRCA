# S01: structural equivalence and one contrast

This standalone standard-library experiment implements only S01 from
`docs/research/reliability-taxonomy-review.v1/07-incremental-experiments-handoff.v1.md`.
It does not import the final runner, other experiments, telemetry, or model clients.

The freeze in `fixtures/freeze.json` records authored source fixtures, expected
structural facts, operation dictionary, and equivalence policy before encoder
implementation. Inputs are synthetic; timestamp and duration strings have declared
millisecond units. All outcomes and status interpretations remain unknown.

```text
T0 (7 nodes, 6 parent edges)              T1: same graph; renamed IDs/shuffled rows
frontend#1 request.handle
├─ checkout#1 cart.get
│  └─ cart#1 cart.get
│     └─ cart#1 db.hget
├─ catalog#1 catalog.get_product
├─ catalog#1 catalog.get_product
└─ catalog#2 catalog.get_product

T2 (8 nodes, 7 parent edges)
frontend#1 request.handle
├─ checkout#1 cart.get
│  └─ cart#1 cart.get
│     └─ cart#1 db.hget
├─ catalog#1 catalog.get_product
├─ catalog#1 catalog.get_product
├─ catalog#2 catalog.get_product
└─ catalog#1 catalog.get_product  ← added occurrence
```

`codec.py` encodes one normalized node per occurrence. It preserves raw values,
explicit entity bindings, parent references, and count checks. Tree equivalence
ignores trace/span names and sibling serialization order, while retaining exact
operation and entity identity. It is restricted to one resolved rooted tree;
missing/conflicting records need later slices, not silent repair. There is no
motif discovery, claimed compression advantage, or inferred interaction role.

`decode(packet)` does not read raw records or provenance. The runner separately
audits recovered raw values and evidence pointers against all source rows.
It publishes the packets, full decoded facts, tree signatures, fact differences,
size accounting, manifest, code snapshot, and copied frozen inputs under a new
`data/experiments/semantic-encoding-v1/S01/<run-id>/` directory. Reusing a run ID
fails instead of replacing prior evidence. The data directory is Git-ignored;
keep it together with the compact research report when sharing results.

After code and fixture review, run from the repository root:

```sh
python3 -m unittest experiments.semantic_encoding_v1.test_s01 -v
python3 -m experiments.semantic_encoding_v1.run_s01 --run-id YOUR_NEW_RUN_ID
```

Stop after reporting S01. Real telemetry fidelity, ambiguous evidence, timing
semantics, compression, and LLM descriptions remain untested by this slice.

The acceptance comparison sorts node and edge rows by opaque IDs within each
fixture; pair relations are unordered, so each pair and the pair list are sorted.
`distinct_pairs` counts unordered pairs of spans recorded by different entities,
not parent edges or unique entity pairs. T0/T1 comparison uses colored-tree
canonicalization rather than an occurrence-level alias map: identical siblings
need not have a unique cross-fixture correspondence. Each packet's original
trace/span IDs remain exact and independently resolvable through provenance.

## S09 live status-boundary study

The live runner uses Featherless's documented OpenAI SDK client. Install its
optional dependency into your Python environment, then run a new six-case study:

```sh
python3 -m pip install -r experiments/semantic_encoding_v1/requirements-live.txt
python3 -m unittest experiments.semantic_encoding_v1.test_s09_transport -v
python3 -m experiments.semantic_encoding_v1.run_s09_live --run-id YOUR_NEW_RUN_ID
```

The runner reads `FEATHERLESS_API_KEY` from `.env` or the environment, disables
SDK retries, and stops the schedule on a non-retryable HTTP error. It retains
raw responses, request IDs, Cloudflare Ray IDs, and provider usage. Each manifest
records the client version. `--prepare-only` and the existing offline fixture
checks do not require the SDK.

The original S09 urllib requests received Cloudflare 1010. On 2026-09-17,
Featherless's documented SDK and independent curl calls both returned model
output and usage with the existing key. These connectivity checks establish
API access; the six-case S09 run separately assesses status interpretation.

### Docker

Build the standalone S09 image from its restricted experiment directory:

```sh
docker build -t symbolicrca-s09:latest experiments/semantic_encoding_v1
docker run --rm --network none symbolicrca-s09:latest \
  python -m unittest experiments.semantic_encoding_v1.test_s09_transport -v
```

From the repository root, run six live cases with a new run ID:

```sh
mkdir -p data/experiments/semantic-encoding-v1/S09
docker run --rm \
  --mount "type=bind,source=$PWD/.env,target=/app/.env,readonly" \
  --mount "type=bind,source=$PWD/data/experiments/semantic-encoding-v1/S09,target=/app/data/experiments/semantic-encoding-v1/S09" \
  symbolicrca-s09:latest \
  python -m experiments.semantic_encoding_v1.run_s09_live --run-id YOUR_NEW_RUN_ID
```

The key is read from the runtime mount. The image contains only the S09 source,
synthetic fixture, transport tests, and SDK dependency; the main demo image is
separate. Results persist in the mounted host directory. Exit status 1 can mean
semantic validation failed even when all six HTTP requests succeeded; inspect
`result.json` and `responses/` to distinguish the outcomes.
