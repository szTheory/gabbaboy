# Changelog

Notable GabbaBoy changes are recorded here. The protected release-please version
pull request creates the numbered release section from merged commits; that
reviewed file and the release notes attached to the matching draft are the
source for the tagged release. Do not edit or publish a numbered entry outside
that version pull request.

## Unreleased

### Added

- A limited DMG-CPU-B software preview with a relocatable native C/C++ package,
  a macOS SDL3 player, and exact-byte release qualification.
- A versioned support ledger and release evidence that identify the scoped
  model, fixture/corpus revisions, tested runner combinations, and known limits.
- Consumer guidance for package use, host-owned battery data, recovery, and a
  future Playstead adapter seam.

### Scope and limitations

- The boot ROM is skipped. The preview does not claim physical DMG qualification,
  CGB support, broad game compatibility, minimum OS versions, or a stable ABI.
- The macOS player is distributed as a CLI tar archive. It is unsigned and not
  notarized unless the exact final artifact is separately verified otherwise.
- See [the release guide](docs/release.md) and the versioned
  [support ledger](docs/support/v0.1.0.md) for downloads, provenance, evidence,
  and exclusions.
