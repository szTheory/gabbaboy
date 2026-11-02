# Deferred Items

- `test_budget` still rejects `phase21_fixture_admission_contract` (120 s) and `phase21_fixture_admission_controls` (180 s) because their existing timeouts exceed the 60-second policy without allowlist entries. These tests are outside Plan 21-02's file and behavior scope; their owning plan should bound the runs or resolve the policy before the phase-wide verification.
