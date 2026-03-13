# Changelog

## 0.2.0 - 2026-03-12

- packaged the repo with `pyproject.toml`
- added installable CLI entry points for download, chunk, normalize, scan, update, audit, and doctor
- moved runtime writes onto a configurable workspace model instead of assuming repo-relative execution
- added packaged example data for doctor smoke checks
- improved the updater to preserve successful transcript files and append in source order
- added cross-platform bootstrap scripts
- added GitHub Actions workflows for offline CI and live YouTube smoke testing
