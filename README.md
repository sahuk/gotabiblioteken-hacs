# gotabiblioteken-hacs

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Tests](https://github.com/sahuk/gotabiblioteken-hacs/actions/workflows/test.yml/badge.svg)](https://github.com/sahuk/gotabiblioteken-hacs/actions/workflows/test.yml)

Home Assistant integration for **library opening hours** from
[gotabiblioteken.se](https://www.gotabiblioteken.se/) (the Götabiblioteken
consortium), served by the Axiell JSON API.

Pick your favorite libraries from a dropdown and each one becomes an
"opening hours today" sensor — aware of multiple shifts per day and of both
service types (`Bemannat` / staffed and `Meröppet` / self-service).

## Installation

### Install with HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sahuk&repository=gotabiblioteken-hacs&category=integration)

1. Click the button above to open this repository in HACS.
   (Or add it by hand: HACS → ⋮ → **Custom repositories** →
   `https://github.com/sahuk/gotabiblioteken-hacs`, category **Integration**.)
2. Select **Download**.
3. Restart Home Assistant.

### Install manually

1. Copy the `custom_components/gotabiblioteken/` directory into your
   Home Assistant `<config>/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=gotabiblioteken)

Go to **Settings → Devices & services → + Add integration** and search for
**Götabiblioteken** (or use the button above). Then:

1. Select your favorite libraries in the multi-select (all ~46 branches are
   fetched live from the API).
2. Choose whether **Meröppet** (self-service) counts as open.
3. Submit.

Each favorite becomes a `sensor.oppettider_<library>` entity. Change your
favorites any time with the integration's **Configure** button.

## What each sensor gives you

State: today's staffed hours as a short string, e.g. `10:00–13:00, 14:00–19:00`
(or the self-service hours if the branch is self-service only, or `Stängt`).

Attributes:

| Attribute              | Example                                             |
| ---------------------- | --------------------------------------------------- |
| `branch`               | `Linköpings huvudbibliotek`                         |
| `date` / `date_label`  | `2026-10-20` / `Tisdag 20 oktober`                  |
| `weekday`              | `Tisdag`                                            |
| `open_now`             | `true`                                              |
| `status`               | `staffed` \| `self_service` \| `closed`             |
| `staffed_summary`      | `10:00–13:00, 14:00–19:00`                          |
| `self_service_summary` | `07:00–22:00` or `Stängt`                           |
| `shifts`               | list of `{type, service_type, info, from, to}`      |
| `hours_markdown`       | pre-formatted block for a Markdown card             |

`shifts` keeps **every shift** for the day and distinguishes `Bemannat`
(staffed) from `Meröppet` (self-service), so split days and mixed service types
are all preserved. `open_now` recomputes locally every minute; the API itself
is only polled every 3 hours.

## Dashboard cards

**One card for all favorites** (built-in Markdown card, no custom components):

```yaml
type: markdown
title: Öppettider idag
content: |
  {% for e in [
    'sensor.oppettider_linkopings_huvudbibliotek',
    'sensor.oppettider_motala_bibliotek'
  ] %}
  {{ state_attr(e, 'hours_markdown') }}

  {% endfor %}
```

**At a glance** (built-in Entities card — state shows today's hours):

```yaml
type: entities
title: Bibliotek
entities:
  - sensor.oppettider_linkopings_huvudbibliotek
  - sensor.oppettider_motala_bibliotek
```

## API notes

```
https://api.axiell.com/openinghours/customers/637ce8087143292d469b8c9b/openinghours?locale=sv_SE&daysFromNow=0&numOfDays=2
```

```json
{
  "dates": [
    {
      "date": "2026-10-20",
      "branches": [
        {
          "branchName": "Borensbergs bibliotek",
          "openingHours": [
            { "serviceType": "Staffed",     "info": null,       "from": "09:00", "to": "14:00", "openingHoursType": "Regular" },
            { "serviceType": "SelfService", "info": "Meröppet", "from": "14:00", "to": "21:00", "openingHoursType": "Regular" }
          ]
        }
      ]
    }
  ]
}
```

An empty `openingHours` array means the branch is closed that day. Branches are
omitted entirely on days they are closed, so a single day lists ~40 while the
full roster is ~46. The customer id `637ce8087143292d469b8c9b` is
Götabiblioteken's.

## Development

Tooling is managed with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
```

Tests cover the pure opening-hours logic, the config/options flow,
end-to-end entity setup under a real Home Assistant instance, and the HACS /
hassfest repository conventions. Lint, types and tests run in CI
(`.github/workflows/test.yml`) on every push and pull request, alongside the
official HACS and hassfest validators (`.github/workflows/validate.yml`).

### Releasing

Versions follow [SemVer](https://semver.org/); `manifest.json` holds the
version and releases are tagged `v<version>`. Note changes under
`Unreleased` in [CHANGELOG.md](CHANGELOG.md), then:

```bash
uv run scripts/bump_version.py patch   # or minor / major / X.Y.Z
```

and run the git / `gh release create` commands it prints. Publishing the
release runs `.github/workflows/release.yml`, which checks the tag against the
manifest and attaches the `gotabiblioteken.zip` that HACS installs.
