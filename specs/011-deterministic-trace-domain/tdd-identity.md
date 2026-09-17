# Trace identity and evidence addressing TDD log

This worktree started from the reviewed trace semantics checkpoint. The
baseline package suite passed 20 tests. The six new acceptance tests for root
handling, mixed numeric identifiers, malformed-envelope evidence addressing,
duplicate-envelope ordering, and context-unit compatibility were initially
added together; that first focused run was red (six failures). The following
implementation was then verified with focused tests and the complete package
suite where the partition-owned behavior was available.

The public contract keeps JSON values in raw evidence. Identity promotion uses
type-sensitive keys for accepted scalar identifiers, so integer `1`, floating
point `1.0`, and string `"1"` cannot merge through Python equality. Boolean
identifiers remain rejected for promotion and are preserved with a deferral.
This retains numeric source evidence without silently coercing it to strings or
collapsing distinct JSON values.

The exact blank string is the root marker. `None` and other non-scalar parent
values are malformed parent evidence and remain unpromoted. Evidence IDs carry
the source envelope index and combined record ordinal in addition to their
digest, making references unique across malformed envelopes in one partition
call while remaining deterministic for the same supplied evidence.
An empty trace identifier is malformed context; the blank-string exception is
reserved for `parent_span` roots.

Duplicate envelopes combine every valid span list, even when an earlier
envelope has malformed `spans`; each malformed list gets an explicit deferral.
Context variation is ignored unless a declared timestamp or duration unit
contradicts a selected nonempty policy unit. Equivalent unit aliases and
unrelated context metadata do not create timing conflicts; when policy units
are absent, explicit source units remain unknown timing evidence.

Focused verification:

```text
PYTHONPATH=libraries/trace_semantics/src python3 -m pytest \
  libraries/trace_semantics/tests/test_partition.py -q
27 passed
```

The complete package suite also passed (`34 passed`). Ruff passes for the
partition source and tests; the repository-wide check still reports one
import-order finding in the parent-owned `test_description.py` file.
