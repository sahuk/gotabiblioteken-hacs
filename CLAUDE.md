# gotabiblioteken-hacs

Home Assistant custom integration (`custom_components/gotabiblioteken/`)
distributed through HACS. See README.md for what it does.

## Dev loop

Dependencies and tooling are managed with uv: dev tools live in the `dev`
dependency group in `pyproject.toml`, locked in `uv.lock`. Runtime
requirements of the integration go in `manifest.json` `requirements` (Home
Assistant installs those), never in `pyproject.toml`. Tests are pytest only.

Setup: `uv sync`. Add a dev tool with `uv add --dev <pkg>`.

Before every commit, all of these must pass (CI runs the same):

```bash
uv run ruff check --fix . && uv run ruff format . && uv run mypy \
  && uv run scripts/type_coverage.py && uv run pytest
```

- mypy is `strict` for the integration and scripts; tests only relax
  untyped defs and `State | None` attribute access.
- `scripts/type_coverage.py` measures the share of expressions with a real
  type (not `Any`) and fails below 97% for `custom_components` + `scripts`.
  Model external data with `TypedDict`s (see `data.py`'s `ApiPayload`) instead
  of `dict[str, Any]`; use `--per-file` to find where `Any` leaks in. Don't
  lower the threshold to make a change pass.
- `tests/test_hacs_conventions.py` enforces the HACS/hassfest file rules
  (single integration dir, manifest keys and order, SemVer, translations in
  sync with `strings.json`, changelog entry for the manifest version). CI also
  runs the real `hacs/action` and `hassfest` (`.github/workflows/validate.yml`).
- When editing `strings.json`, copy it to `translations/en.json` and mirror
  the keys in `translations/sv.json`.
- Language: entity names come from translation keys (`translation_key` +
  `entity.*` in the translation files), never hard-coded. Text the
  integration generates (states, attributes) goes through `data.Labels` /
  `labels_for(hass.config.language)`, with English for uncovered languages.
  When in doubt, use English. Every user-facing string must exist in all
  languages listed in TRANSLATIONS.md (follow its "Adding a language" steps;
  `tests/test_localization.py` and the convention tests enforce it).
- Library display names come from `libraries.py` (short place name, e.g.
  "Motala", used as the device name so entity names start with it). If the
  API adds a branch, add its short name and website there; a test keeps the
  table complete and the short names unique.

## Skills in the loop

`docs/ux/personas.md` holds the personas, user stories and acceptance
criteria: treat it as the spec for `/grill-me` and the Spec axis of reviews,
and update it when a design decision changes what users get.

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
- Before a release, finish the work first: run the `security-audit` skill on
  the changes since the last tag, then fix its findings **and** its
  hardening notes (and any open review or translation-review items) in a PR
  merged to `master`. Only bump the version once nothing is left; an item
  is deferred only if the user explicitly says so, and then it is noted in
  the changelog. Fixes never go in as a follow-up to a release that was
  already cut.
- Release: `uv run scripts/bump_version.py <major|minor|patch>`,
  then run the commands it prints. Pushing the `v<version>` tag triggers
  `.github/workflows/release.yml`, which fails if the tag doesn't match the
  manifest, reruns all checks with a read-only token, and then publishes the
  GitHub release with `gotabiblioteken.zip` attached (HACS installs that zip,
  per `zip_release` in `hacs.json`) and the changelog section as notes. Don't
  create the release by hand.
- Release tags must point at a commit on `master` (`release.yml` fails otherwise).
- Tagging, pushing and publishing releases are outward-facing: confirm with
  the user first.
