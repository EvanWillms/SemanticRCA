# Authored demo fixture

- `traces.json`: two caller-selected traces with three recorded occurrences.
  One child operation has no declared meaning; its parent relation remains known.
- `policy.json`: an explicit operation dictionary and millisecond timing units.
- `expected.json`: independently stated demo expectations, used only by the
  demo verifier after partitioning and description construction.

These records are synthetic. The `authored-demo.csv` locators are authored
evidence labels, not files fetched or verified by the library. Selection is a
caller-provided premise. Raw status `0` has no declared interpretation.

To create a variant, copy the three JSON files into a new directory and pass it
to `python -m trace_semantics.demo --fixture-dir DIRECTORY`. Update expectations
deliberately when changing evidence. The encoder never receives expectations.
