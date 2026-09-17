# Luna runner TDD evidence

## Slice 1 — public contracts

- Red: `python3.12 -m unittest tests.contract.test_empty_outputs.PublicContractsTests.test_solution_and_query_row_are_small_public_value_objects`
- Result: failed as expected with `ModuleNotFoundError: No module named 'rca.contracts'`.
- Green: added `rca/contracts.py`; the contract now passes.

## Slice 2 — first public CLI tracer bullet

- Red: `python3.12 -m unittest tests.contract.test_empty_outputs.EmptyOutputContractTests.test_cli_preserves_noncontiguous_ids_and_writes_empty_case_artifacts`
- Result: failed as expected because the public `run.py` entrypoint did not exist.
- Green: added validated input loading, the no-call submission/heuristic seam, atomic outputs, and `run.py`; the tracer bullet now passes.

## Slice 3 — all task labels

- Green extension: `python3.12 -m unittest tests.contract.test_empty_outputs` passes for all seven task labels, multiline input, original IDs, four evidence headings, and zero-call usage records.

## Slice 4 — preflight failures

- Green extension: `python3.12 -m unittest tests.integration.test_harness_failures` passes header-only output, duplicate/noninteger IDs, missing headers, malformed CSV, missing paths, nonempty output preservation, and both-way input/output overlap rejection.

## Slice 5 — checkpoint failures and credential boundary

- Green extension: `python3.12 -m unittest tests.integration.test_checkpointing` passes injected replacement failure preservation, removal of failed-case evidence/usage, no temporary CSV residue, and sentinel credential absence from output.

## Slice 6 — invocation safety

- Green extension: the combined runner tests now pass 15 tests, including explicit unsupported-resume rejection, unknown-agent failure before output initialization, keyless execution, and no new source bytecode.
- Review fix green: bytecode coverage now invokes a clean temporary copy with `PYTHONDONTWRITEBYTECODE` and `PYTHONPYCACHEPREFIX` removed, and confirms no `.pyc` files are created.
- Final review green: `python3.12 -m unittest tests.contract.test_empty_outputs tests.integration.test_harness_failures tests.integration.test_checkpointing` passes all 15 owned runner tests after usage serialization and checkpoint cleanup hardening.
