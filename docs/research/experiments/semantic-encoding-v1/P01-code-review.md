# P01 execution checkpoint review

Scope: `featherless_p01.py`, `run_p01.py`, `score_p01.py` and `test_p01.py`,
plus specification 008 and the P01 result report. Two Luna extra-high agents
reviewed standards and specification fidelity independently. Existing S01,
S02–S09 and the concurrent standalone library were inspected for context;
findings for other tasks were handed to their owners, not silently patched here.

## Standards

The client loads the named environment settings without shell evaluation,
uses HTTPS, refuses redirects, sanitizes response bodies and makes no retries.
The experiment counts attempted requests conservatively at fresh-input rates.
The original runner's socket timeout was not an absolute wall-clock deadline,
and errors while reading an HTTP error body could escape attempt accounting.
These are transport limitations identified after the completed live run, not
changes to the recorded model responses or measured cost.

## Specification

The completed study tests only the frozen authored structural family. Source
identity, raw fields, multiplicity, evidence references and unknown meanings
are scored independently of generated explanations. The natural-prefix gate
correctly skipped the additional six cache calls. Reusing an execution ID is
refused; this prevents accidental retry spend and does not provide resumable
inference. Offline scoring is the recovery path for retained responses.

Review identified that replay should validate frozen input artifacts before
scoring, while allowing an explicitly identified newer offline scorer. Historic
reports must remain immutable. Malformed provider response shapes must produce
failed trials instead of aborting the entire scoring pass.

## Evidence and qualifications

Before review changes, all 12 P01 offline tests passed and the retained run
replayed 18/18 passes. An independent SHA-256 check matched all 71 entries in
its artifact inventory. Runtime unit tests plus the S01/S02–S09 suites passed
31 tests and three subtests. A broad repository collection encountered a
concurrent library test whose package was still under construction; that is
outside this checkpoint and is not reported as a passing full-repository run.

No review or regression check made paid inference calls. Raw run artifacts are
Git-ignored; independent reconstruction of the historical live result requires
the retained evidence directory. Shared S01 fixtures are owned by the separate
experiment task and are not staged by this task.

## Demo checkpoint

The reviewed runner passes 17 offline tests. The command below produces
18/18 fidelity passes without credentials or network calls:

```sh
python3 -m experiments.semantic_encoding_v1.run_p01 score --run-id 20260917-p01-002 --report-name result-demo-reviewed.json
```

Review fixes retain HTTP-body errors as sanitized attempt results, bound body
reads, check elapsed deadlines between reads, reject changed frozen artifacts,
and handle malformed choice/message shapes. Live dispatch still requires the
current code to match its prepared snapshot. Replay identifies both runner and
scorer hashes and preserves original reports.

Deferred beyond the offline demo: independently sealing preflight admission
metadata for future live runs, consolidating duplicated budget constants, and
a process-level deadline watchdog (DNS/header operations are not guaranteed by
socket timeouts). No claim of adversarial artifact integrity or resumable live
inference is made. These gaps do not prevent the verified retained-run demo.
