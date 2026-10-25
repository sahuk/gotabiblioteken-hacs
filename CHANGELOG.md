# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). The version in
`custom_components/gotabiblioteken/manifest.json` is the source of truth; each
release is tagged `v<version>`.

## [Unreleased]

### Added

- Static checks: ruff (lint + format) and strict mypy, locally and in CI.
- HACS and hassfest validation in CI, plus local repo-convention tests.
- Release workflow that verifies the tag against the manifest and attaches
  `gotabiblioteken.zip`; `scripts/bump_version.py` for version bumps.
- Brand icon (`brand/icon.png`) from the Götabiblioteken logo.
- MIT license.

## [1.0.0] - 2026-10-20

### Added

- GUI-installable custom integration: pick favorite libraries in a config
  flow; each becomes an "opening hours today" sensor with shift-level
  attributes, polled every 3 hours and recomputed locally every minute.
