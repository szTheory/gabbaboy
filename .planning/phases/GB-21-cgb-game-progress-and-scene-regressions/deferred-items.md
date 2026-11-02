# Deferred Items

- `test_budget` still rejects `phase21_fixture_admission_contract` (120 s) and `phase21_fixture_admission_controls` (180 s) because their existing timeouts exceed the 60-second policy without allowlist entries. Plan 21-07 owns resolution during final integration; keep this finding open until the phase-wide budget check passes.
