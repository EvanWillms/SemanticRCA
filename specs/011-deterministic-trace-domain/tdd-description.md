# Description boundary TDD notes

The baseline standalone package had 20 passing tests before this slice.

The context/qualification regression was completed first. The next three
regressions were present together in an intermediate run (28 passed, 3 failed),
then their fixes were verified. This departed from the skill's prescribed
one-test-at-a-time cadence; the failures preceded the corresponding fixes:

1. The context and shared qualification test first failed because descriptions
   had no structured context or qualification record. The implementation then
   exposed source context and one trace-scoped qualification carrying the
   description schema version, caller policy version, claim kinds, scope,
   evidence IDs, applies-to sections and explicit limitations.
2. The forged coverage/evidence-reference test first failed because arbitrary
   coverage and unknown occurrence evidence were accepted. The implementation
   then validated evidence identity, occurrence membership, coverage counts,
   conflict/occurrence counts, resolved edge endpoints, deferred references and
   conflicting node claims.
3. The cycle/non-finite boundary test first failed because ignored cyclic or
   non-finite top-level values were not inspected. The implementation then
   detached and validated the complete partition, detecting recursive values
   and rejecting non-JSON inputs with caller-facing `TypeError`s.
4. The lone-surrogate canonicalization test first failed because canonical JSON
   retained an unescaped surrogate. Canonical serialization now escapes such
   JSON strings, so digest encoding remains deterministic and UTF-8 safe.

Focused description tests pass with the absolute Python 3.14.3 runtime. A
typed identifier smoke check keeps JSON `1` and `1.0` distinct, and a 3,000
node resolved chain completes in linear-time boundary validation. The package
suite is also green once the concurrent partition slice is settled; its
temporary timing-context assertion changed while this slice was in progress.
