# Authored demo fixture

This fixture has no fault labels or external data. It supplies two reference
contexts with 20 roots each across three absolute minutes (8/6/6). Their durations
are constant 10 ms and constant 0 ms. The CSV's duration field is provisionally
interpreted as microseconds; start timestamps are epoch milliseconds.

Six `constant` queries cover the six five-minute slices with independently
specified signed excesses of +2, −2, 0, +2, +2, +2 ms. One zero-center query has
+12 ms excess. An operation first appearing in the last slice must remain
unavailable without changing the frozen catalog. `expected.json` records the
small happy-path oracle; it is not a full B01–B12 acceptance fixture.
