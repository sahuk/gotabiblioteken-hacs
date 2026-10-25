# gotabiblioteken-hacs

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Tests](https://github.com/sahuk/gotabiblioteken-hacs/actions/workflows/test.yml/badge.svg)](https://github.com/sahuk/gotabiblioteken-hacs/actions/workflows/test.yml)

Home Assistant integration for **library opening hours** from
[gotabiblioteken.se](https://www.gotabiblioteken.se/) (the Götabiblioteken
consortium), served by the Axiell JSON API.

Pick your favorite libraries from a dropdown and each one becomes a device
that answers, at a glance: what are today's hours, and is the library
**open** right now (`Öppet`), counting both staffed and Meröppet
(self-service) hours? For people who need in-person help, such as kids or
the elderly, each library also has an opt-in **staffed** sensor
(`Bemannat`). There is no mode to choose at setup (see
[docs/ux/personas.md](docs/ux/personas.md)).

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
2. Submit.

Each favorite becomes a device named after the library. Change your favorites
any time with the integration's **Configure** button; libraries you remove
disappear along with their device.

## What each library gives you

Entity IDs below assume Home Assistant is set to Swedish; with another
language the suffixes follow that language (e.g. `_opening_hours`, `_open`,
`_staffed`).

| Entity | State | Attributes |
| --- | --- | --- |
| `sensor.<library>_oppettider` | today's shifts in time order, e.g. `09:00–14:00, Meröppet 14:00–21:00`, or `Stängt` | see below |
| `binary_sensor.<library>_oppet` | open/closed (door): open whenever you can get in, during staffed **or** Meröppet hours | `hours`: the combined opening window, e.g. `09:00–21:00` |
| `binary_sensor.<library>_bemannat` | **disabled by default.** `Ja`/`Nej`: whether staff are working | `hours`: the staffed hours, e.g. `09:00–14:00` |

Each of these is on exactly when the current time falls inside its own
`hours` attribute, so the state never disagrees with the hours shown.

To get the staffed sensor for a library, open the library's device under
**Settings → Devices & services → Götabiblioteken**, select the `Bemannat`
entity, and turn on **Enabled** in its settings.

Attributes of the hours sensor:

| Attribute              | Example                                             |
| ---------------------- | --------------------------------------------------- |
| `branch`               | `Linköpings huvudbibliotek`                         |
| `date` / `date_label`  | `2026-10-20` / `Tisdag 20 oktober`                  |
| `weekday`              | `Tisdag`                                            |
| `status`               | `staffed` \| `self_service` \| `closed`             |
| `staffed_summary`      | `10:00–13:00, 14:00–19:00`                          |
| `self_service_summary` | `07:00–22:00` or `Stängt`                           |
| `shifts`               | list of `{type, service_type, info, from, to}`      |
| `hours_markdown`       | pre-formatted block for a Markdown card             |

`shifts` keeps **every shift** for the day and distinguishes `Bemannat`
(staffed) from `Meröppet` (self-service), so split days and mixed service types
are all preserved. Open/closed states recompute locally every minute; the API
itself is only polled every 3 hours.

## Dashboard cards

**One card for all favorites** (built-in Markdown card, no custom components):

```yaml
type: markdown
title: Öppettider idag
content: |
  {% for e in [
    'sensor.linkopings_huvudbibliotek_oppettider',
    'sensor.motala_bibliotek_oppettider'
  ] %}
  {{ state_attr(e, 'hours_markdown') }}

  {% endfor %}
```

**At a glance** (built-in Entities card, one library):

```yaml
type: entities
title: Motala bibliotek
entities:
  - sensor.motala_bibliotek_oppettider
  - binary_sensor.motala_bibliotek_oppet
  - binary_sensor.motala_bibliotek_bemannat  # once enabled
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
uv run scripts/type_coverage.py   # share of expressions typed (not Any)
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
