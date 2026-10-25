# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). The version in
`custom_components/gotabiblioteken/manifest.json` is the source of truth; each
release is tagged `v<version>`.

## [Unreleased]

### Changed (breaking)

- Each favorite library is now its own device with **Opening hours**
  (`sensor.<place>_opening_hours`) and **Open**
  (`binary_sensor.<place>_open`, an open/closed door that is open during
  staffed or Meröppet hours). A **Staffed** sensor
  (`binary_sensor.<place>_staffed`, Yes/No) is created disabled, for people
  who need in-person support to enable per library. On a Swedish Home
  Assistant the names and IDs are Swedish (Öppettider, Öppet, Bemannat).
  Entity IDs change: the old entities are removed on upgrade (their history
  and customizations don't carry over), so update dashboards and automations.
- Setup no longer asks whether Meröppet counts as open: it always does. The
  `open_now` and `include_self_service` attributes are gone.
- The hours sensor lists all of today's shifts in time order, marking
  self-service ones (`09:00–14:00, Self-service 14:00–21:00`).
- States and attributes (closed, weekday, date label, shift labels, Markdown
  block) follow Home Assistant's language: Swedish for Swedish, English
  otherwise. They were always Swedish before.

### Fixed

- The door icon could say open while the listed hours said otherwise (e.g.
  during Meröppet with staffed hours shown). Every open/closed state now
  comes from exactly the hours it displays.
- Removing a favorite now removes its device.

### Added

- 14 more languages: Finnish, Norwegian (Bokmål and Nynorsk), Danish,
  Icelandic, German, French, Spanish, Portuguese, Italian, Estonian, Latvian,
  Lithuanian and Polish. Each covers entity names, the setup dialog, and
  generated text (closed, weekdays, months, date format, self-service label). Drafts flagged for native review in
  `TRANSLATIONS.md`, which also tracks Sweden's other minority languages
  (waiting on Home Assistant support).
- Library devices use a short place name ("Motala", "Borensberg",
  "Agora") so entity names start with what tells libraries apart and stay
  readable when a dashboard card cuts them off ("Motala Open"). The full name
  stays in the `branch` attribute.
- Each library links to its page on gotabiblioteken.se: the device's
  **Visit** link and a `website` attribute on the hours sensor.
- `scripts/type_coverage.py`: measures how much of the code mypy types
  precisely (no `Any`), gated at 97% in CI. The API payload and computed
  results are now `TypedDict`s.
- UX persona and user story: open-by-default, with staffed hours as opt-in
  for people who need in-person support (`docs/ux/personas.md`).
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
