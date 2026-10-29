# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). The version in
`custom_components/gotabiblioteken/manifest.json` is the source of truth; each
release is tagged `v<version>`.

## [Unreleased]

### Changed

- `hacs.json` declares `"country": "SE"`, so HACS lists the integration
  under Sweden when users filter by country.

## [1.1.1] - 2026-10-27

### Security

- Library names in `hours_markdown` also escape `:` and `.`, so a name
  containing a bare URL can't be turned into a link.
- Release workflow: checks and the build run with a read-only token in a
  separate job from publishing, and the release is published only once its
  zip is attached. Releases are now made by pushing the tag. GitHub Actions
  updated to Node 24 versions (`actions/checkout` v7).
- Release workflow: the zip and release notes are built from the tagged
  commit (`git archive`), not the working tree the checks ran in; the build
  asserts it checked out the tagged commit, and publishing stops if the tag
  was moved to another commit after the build.

## [1.1.0] - 2026-10-25

### Added

- **Staffed hours** sensor (`sensor.<place>_staffed_hours`), created disabled
  like the Staffed sensor: today's staffed hours only (`09:00–14:00`).

### Changed

- On a Meröppet-only day the staffed hours (the new sensor, the Staffed
  sensor's `hours` and `staffed_summary`) read **Not staffed** instead of
  **Closed**, since the library is open for self-service.

### Security

- API responses over 1 MiB are refused before parsing, and the response
  must be a JSON object.
- Malformed opening hours from the API (missing, mistyped or non-`HH:MM`
  times, entries of the wrong type) are skipped and treated as closed
  instead of raising errors in the entities.
- Library names are Markdown-escaped in `hours_markdown`, so a name can't
  inject links, images or HTML into a dashboard Markdown card.
- CI: actions pinned to commit SHAs; read-only token for test and validate
  workflows; the release workflow keeps the release tag out of shell
  interpolation, doesn't persist its write token during checks, and only
  releases commits that are on `master`.

## [1.0.0] - 2026-10-25

First release.

### Added

- GUI setup: pick your favorite Götabiblioteken libraries; change them later
  with **Configure** (removing a favorite removes its device). Opening hours
  are fetched from the Axiell API every 3 hours and states are recomputed
  locally every minute.
- One device per library, named by its short place name ("Motala",
  "Borensberg", "Söderköping") so entity names start with what tells
  libraries apart on a dashboard ("Motala Open"):
  - **Opening hours** (`sensor.<place>_opening_hours`): today's shifts in
    time order, self-service ones marked
    (`09:00–14:00, Self-service 14:00–21:00`), or `Closed`.
  - **Open** (`binary_sensor.<place>_open`): an open/closed door, open
    whenever you can get in, staffed or Meröppet.
  - **Staffed** (`binary_sensor.<place>_staffed`, Yes/No): created disabled,
    for people who need in-person support to enable per library.
  - Every open/closed state comes from exactly the hours it displays.
  - Attributes with shifts, summaries, a date label, the full branch name,
    and `hours_markdown` for a Markdown card; a **Visit** link and `website`
    attribute to the library's page on gotabiblioteken.se.
- 16 languages, following Home Assistant's language: Swedish, English,
  Finnish, Norwegian (Bokmål and Nynorsk), Danish, Icelandic, German,
  French, Spanish, Portuguese, Italian, Estonian, Latvian, Lithuanian and
  Polish, with English for any other language. Entity names, setup dialog
  and generated text (closed, weekdays, months, date format, self-service
  label) follow each language's conventions. Non-Swedish translations are
  flagged for native review in `TRANSLATIONS.md`, which also tracks
  Sweden's other minority languages (waiting on Home Assistant support).
- HACS distribution with a brand icon and MIT license; releases attach
  `gotabiblioteken.zip`.
- Development: uv-managed dev tools, pytest, ruff, strict mypy with a type
  coverage gate, HACS/hassfest validation and repo-convention tests in CI,
  a UX persona spec (`docs/ux/personas.md`) and `scripts/bump_version.py`.
