# gotabiblioteken-hacs

Home Assistant custom integration (`custom_components/gotabiblioteken/`)
distributed through HACS. See README.md for what it does.

## Dev loop

Setup: `python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt`

Before every commit, all of these must pass (CI runs the same):

```bash
./.venv/bin/ruff check --fix . && ./.venv/bin/ruff format . && ./.venv/bin/mypy && ./.venv/bin/pytest
```

- mypy is `strict` for the integration and scripts; tests only relax
  untyped defs and `State | None` attribute access.
- `tests/test_hacs_conventions.py` enforces the HACS/hassfest file rules
  (single integration dir, manifest keys and order, SemVer, translations in
  sync with `strings.json`, changelog entry for the manifest version). CI also
  runs the real `hacs/action` and `hassfest` (`.github/workflows/validate.yml`).
- When editing `strings.json`, copy it to `translations/en.json` and mirror
  the keys in `translations/sv.json`.

## Skills in the loop

- `/grill-me`: before starting a non-trivial feature or design change, to
  settle the design tree before writing code.
- `/code-review`: on the diff before committing or opening a PR.
- `/security-review` on pending changes; the `security-audit` skill (full
  audit mode) before a release or after touching `api.py`, the config flow, or
  anything that handles API input.

## Versioning and releases

- `manifest.json` `version` (SemVer) is the single source of truth; tags are
  `v<version>`. HACS offers versions from GitHub releases, so every user-facing
  change ships as a release.
- Add changes under `## [Unreleased]` in `CHANGELOG.md` as you go.
- Release: `./.venv/bin/python scripts/bump_version.py <major|minor|patch>`,
  then run the commands it prints. Publishing the GitHub release triggers
  `.github/workflows/release.yml`, which fails if the tag doesn't match the
  manifest, reruns all checks, and attaches `gotabiblioteken.zip` (HACS
  installs that zip, per `zip_release` in `hacs.json`).
- Tagging, pushing and publishing releases are outward-facing: confirm with
  the user first.
