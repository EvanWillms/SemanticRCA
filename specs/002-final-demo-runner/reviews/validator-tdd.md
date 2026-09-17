# Validator TDD evidence

## Slice 1: valid non-contiguous output and notice

Red command (before `scripts/validate_harness.py` existed):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: FAIL (`test_accepts_valid_noncontiguous_outputs_with_scaffold_notice`; validator file was missing and the subprocess exited 2).

Green command (after the first validator implementation):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: PASS (1 test).

## Slice 2: strict prediction CSV shape

Red command (after adding duplicate-header and missing-column cases, before strict CSV parsing):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: FAIL (duplicate prediction headers were silently overwritten by `DictReader`; 1 of 3 tests failed).

Green command (after strict CSV parsing, unique-header checks, and row-width checks):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: PASS (3 tests).

## Slice 3: truthful placeholder evidence

Red command (after adding a case with headings but no unimplemented Answer notice):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: FAIL (the validator accepted the structurally correct but semantically uninformative evidence; 1 of 4 tests failed).

Green command (after requiring section-specific unimplemented/no-evidence/no-alternatives markers):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: PASS (4 tests).

## Slice 4: explicit zero usage counters

Red command (after adding a case with the `calls` counter removed):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: FAIL (the validator accepted usage with no explicit call count; 1 of 5 tests failed).

Green command (after requiring integer zero values for prompt, completion, and call counters):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: PASS (5 tests).

## Slice 5: sanitized malformed timing and evidence diagnostics

Red command (after adding malformed heading and huge-integer timing cases):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: FAIL (the malformed heading and huge timing produced tracebacks; 2 of 7 tests failed).

Green command (after positional section parsing, strict heading rejection, overflow-safe timing checks, and UTF-8 BOM-tolerant CSV input):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: PASS (7 tests).

## Slice 6: artifact coverage and header-only behavior

Follow-up contract checks (duplicate/missing/extra prediction, usage, and evidence IDs, canonical evidence names, boolean/nonfinite counters, and header-only inputs) were added against the green validator:

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: PASS (10 tests).

## Slice 7: exact root artifact set

Red command (after adding a case with an unexpected root-level output artifact):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: FAIL (the validator accepted an extra root artifact; 1 of 11 tests failed).

Green command (after requiring exactly `predictions.csv`, `usage.jsonl`, and `evidence/` under `--out`):

```text
python3.12 -m unittest tests.contract.test_validate_harness -v
```

Result: PASS (11 tests).
