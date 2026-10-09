---
phase: "01"
slug: "portable-foundation-and-original-rom-tracer"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-09"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Host to native core | Public C API accepts caller-owned ROM bytes and bounded execution options. | ROM bytes, sizes, model, budget, and trace capacity |
| Core instance to guest execution | Guest instructions operate on isolated instance state and caller-provided trace storage. | CPU, memory, diagnostics, timing, trace records |
| Repository to CI | Untrusted pull requests invoke workflows with limited permissions and pinned actions. | Source, build scripts, test inventory, fixture inputs |
| Build to package consumer | Installed metadata and artifacts cross into independent C/C++ consumers. | Headers, libraries, runner, package metadata, digests |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| 01 / T-GB01-01 | Tampering | ROM/header parsing | high | mitigate | Validate pointer, size, type, declared length, and checksum before state replacement; malformed-loader tests. | closed |
| 01 / T-GB01-02 | Denial of Service | Guest execution and trace | high | mitigate | Strict half-dot budget, instruction-cost preflight, fixed trace capacity, and explicit stop reasons. | closed |
| 01 / T-GB01-03 | Repudiation | Fixture and trace result | medium | mitigate | Manifest binds authored source, rights, digest, profile, protocol, timeout, and reachable opcodes. | closed |
| 01 / T-GB01-04 | Elevation of Privilege | CI workflows | high | mitigate | Pull-request triggers, read-only permissions, and SHA-pinned actions. | closed |
| 01 / T-GB01-05 | Security controls outside native scope | Local native core | low | accept | No web service or authentication surface exists; this ASVS web-control scope is inapplicable. | closed — accepted |
| 02 / T-GB01-01 | Tampering | ROM loader | high | mitigate | Checked arithmetic, size/type validation, parse-to-temporary-state, and non-destructive failure tests. | closed |
| 02 / T-GB01-02 | Denial of Service | Guest execution and host runner | high | mitigate | Guest budget and trace bounds plus CTest `TIMEOUT 30` host watchdog on tracer, runner, and Mooneye processes. | closed |
| 02 / T-GB01-03 | Information Disclosure | Instance lifecycle | medium | mitigate | State and diagnostics are per instance; reset, independent-instance, and concurrent-instance tests. | closed |
| 02 / T-GB01-04 | Elevation of Privilege | Native core API | low | accept | There is no web route, identity, session, or database in the native core; repository permissions are separately minimized. | closed — accepted |
| 03 / T-GB01-01 | Tampering | Installed package metadata | medium | mitigate | Relocated-prefix checks reject private path leakage; independent C and C++ consumers exercise installed files. | closed |
| 03 / T-GB01-02 | Repudiation | README support claims | medium | mitigate | Publish only toolchain and OS floors supported by named local and hosted consumer evidence. | closed |
| 03 / T-GB01-03 | Elevation of Privilege | Package consumption | low | accept | Package consumption introduces no web identity or session surface; repository access remains the applicable boundary. | closed — accepted |
| 04 / T-GB01-01 | Elevation of Privilege | Pull-request workflows | high | mitigate | Pull-request triggers, least token permissions, pinned action SHAs, and no privileged fork execution. | closed |
| 04 / T-GB01-02 | Repudiation | Test inventory and aggregate gate | high | mitigate | Explicit expected-case inventory rejects missing, failed, or skipped tests; aggregate requires all required jobs. | closed |
| 04 / T-GB01-03 | Tampering | Fixture regeneration | medium | mitigate | Pin RGBDS, verify its archive digest, compare generated ROM bytes, and check fixture digest. | closed |
| 04 / T-GB01-04 | Security controls outside native scope | Web authentication/session | low | accept | No application authentication surface exists; repository workflow permissions are independently minimized. | closed — accepted |
| 04 / T-GB01-05 | Tampering | CMake floor toolchain archive | high | mitigate | Verify the official checksum listing and downloaded CMake 3.25.3 archive SHA-256 before extraction. | closed |
| 05 / T-GB01-01 | Tampering | Preview package artifact | high | mitigate | Gate package creation on exact-revision CI and extracted-package smoke; verify source SHA, archive digest, and smoke marker. | closed |
| 05 / T-GB01-02 | Repudiation | Artifact/support claims | medium | mitigate | Sidecar records smoke, limits, revision, and retention; verifier reads actual artifact API expiry. | closed |
| 05 / T-GB01-03 | Elevation of Privilege | Preview workflow | high | mitigate | Pull-request trigger, limited permissions, and SHA-pinned actions. | closed |
| 05 / T-GB01-04 | Web access controls | Native core | low | accept | Web authentication/session controls are inapplicable; hosted repository permissions define the relevant boundary. | closed — accepted |

*Only open threats at or above the configured high threshold count toward `threats_open`.*

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | 01 / T-GB01-05 | The local native core has no web service or authentication surface, so web session controls do not apply. | Project owner, per approved plan disposition | 2026-10-09 |
| AR-02 | 02 / T-GB01-04 | The native core has no web route, identity, session, or database; repository permissions remain separately minimized. | Project owner, per approved plan disposition | 2026-10-09 |
| AR-03 | 03 / T-GB01-03 | Standalone package consumption adds no web identity or session boundary. | Project owner, per approved plan disposition | 2026-10-09 |
| AR-04 | 04 / T-GB01-04 | The project has no application authentication surface; repository workflow permissions are separately minimized. | Project owner, per approved plan disposition | 2026-10-09 |
| AR-05 | 05 / T-GB01-04 | The shipped native core has no web access-control surface; hosted repository permissions are the relevant boundary. | Project owner, per approved plan disposition | 2026-10-09 |

These five low-severity dispositions were marked `accept` in the phase plans. This log records those existing decisions; no high-severity threat is accepted.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-09 | 21 | 21 | 0 | gsd-security-auditor; orchestrator |

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-09

## Security Audit 2026-10-09

| Metric | Count |
|---|---|
| Threats found | 21 |
| Closed | 21 |
| Open | 0 |
