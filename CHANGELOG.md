# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). The version in
`custom_components/gotabiblioteken/manifest.json` is the source of truth; each
release is tagged `v<version>`.

## [Unreleased]

### Changed (breaking)

- Each favorite library is now its own device with three entities: today's
  hours (`sensor.<library>_oppettider`), **Bemannat** (Ja/Nej,
  `binary_sensor.<library>_bemannat`) and **Meröppet** (open/closed door,
  `binary_sensor.<library>_meroppet`, open whenever a cardholder can get in).
  Entity IDs change: the old entities are removed on upgrade (their history
  and customizations don't carry over), so update dashboards and automations.
- Setup no longer asks whether Meröppet counts as open; both are always
  shown. The `open_now` and `include_self_service` attributes are gone.
- The hours sensor lists all of today's shifts in time order, marking
  Meröppet ones (`09:00–14:00, Meröppet 14:00–21:00`).

### Fixed

- The door icon could say open while the listed hours said otherwise (e.g.
  during Meröppet with staffed hours shown). Every open/closed state now
  comes from exactly the hours it displays.
- Removing a favorite now removes its device.

### Added

- `scripts/type_coverage.py`: measures how much of the code mypy types
  precisely (no `Any`), gated at 97% in CI. The API payload and computed
  results are now `TypedDict`s.
- UX persona and user story for families using both staffed and Meröppet
  hours (`docs/ux/personas.md`).
- Static checks: ruff (lint + format) and strict mypy, locally and in CI.
- HACS and hassfest validation in CI, plus local repo-convention tests.
- Release workflow that verifies the tag against the manifest and attaches
  `gotabiblioteken.zip`; `scripts/bump_version.py` for version bumps.
- Brand icon (`brand/icon.png`) from the Götabiblioteken logo.
- MIT license.
- Dev dependencies managed with uv (`pyproject.toml` + `uv.lock`).

## [1.0.0] - 2026-10-20

### Added

- GUI-installable custom integration: pick favorite libraries in a config
  flow; each becomes an "opening hours today" sensor with shift-level
  attributes, polled every 3 hours and recomputed locally every minute.
