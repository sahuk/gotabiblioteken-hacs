# gotabiblioteken-hacs

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Tests](https://github.com/sahuk/gotabiblioteken-hacs/actions/workflows/test.yml/badge.svg)](https://github.com/sahuk/gotabiblioteken-hacs/actions/workflows/test.yml)

Home Assistant integration for **library opening hours** from
[gotabiblioteken.se](https://www.gotabiblioteken.se/) (the Götabiblioteken
consortium), served by the Axiell JSON API.

Pick your favorite libraries from a dropdown and each one becomes a device
that answers, at a glance: what are today's hours, and is the library
**open** right now, counting both staffed and Meröppet (self-service) hours?
For people who need in-person help, such as kids or the elderly, each library
also has an opt-in **staffed** sensor. There is no mode to choose at setup (see
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

Each favorite becomes a device named after its place, e.g. **Motala** or
**Östra Ryd** (no "bibliotek"), so every entity name starts with what tells
libraries apart, like "Motala Open", and stays readable when a dashboard card
cuts it off. The device has a **Visit**
link to the library's page on gotabiblioteken.se. Change your favorites
any time with the integration's **Configure** button; libraries you remove
disappear along with their device.

## What each library gives you

Entity names and the text the integration generates (states, weekdays,
labels) follow Home Assistant's language: Swedish, English, the Nordic
languages (Finnish, Norwegian Bokmål and Nynorsk, Danish, Icelandic), the
major continental EU languages (German, French, Spanish, Portuguese,
Italian), and Estonian, Latvian, Lithuanian and Polish, with English for any
other language (see [TRANSLATIONS.md](TRANSLATIONS.md),
including which translations still need native review). Library names are
place names and aren't translated. Entity IDs are created in the language
active at setup, e.g. for English and Swedish:

| Entity (English) | Swedish setup | State | Attributes |
| --- | --- | --- | --- |
| `sensor.<place>_opening_hours` | `…_oppettider` | today's shifts in time order, e.g. `09:00–14:00, Self-service 14:00–21:00`, or `Closed` | see below |
| `binary_sensor.<place>_open` | `…_oppet` | open/closed (door): open whenever you can get in, during staffed **or** Meröppet hours | `hours`: the combined opening window, e.g. `09:00–21:00` |
| `binary_sensor.<place>_staffed` | `…_bemannat` | **disabled by default.** Yes/No: whether staff are working | `hours`: the staffed hours, e.g. `09:00–14:00` |

Each of these is on exactly when the current time falls inside its own
`hours` attribute, so the state never disagrees with the hours shown.

To get the staffed sensor for a library, open the library's device under
**Settings → Devices & services → Götabiblioteken**, select the **Staffed**
entity, and turn on **Enabled** in its settings.

Attributes of the hours sensor:

| Attribute              | Example                                             |
| ---------------------- | --------------------------------------------------- |
| `branch`               | `Linköpings huvudbibliotek`                         |
| `website`              | `https://www.gotabiblioteken.se/linkoping-huvudbibliotek` |
| `date` / `date_label`  | `2026-10-20` / `Tuesday 20 October`                 |
| `weekday`              | `Tuesday`                                           |
| `status`               | `staffed` \| `self_service` \| `closed`             |
| `staffed_summary`      | `10:00–13:00, 14:00–19:00`                          |
| `self_service_summary` | `07:00–22:00` or `Closed`                           |
| `shifts`               | list of `{type, service_type, info, from, to}`      |
| `hours_markdown`       | pre-formatted block for a Markdown card             |

`shifts` keeps **every shift** for the day and distinguishes staffed from
self-service (Meröppet) shifts (`service_type` is the API's `Staffed` /
`SelfService`; `type` is the localized label), so split days and mixed service types
are all preserved. Open/closed states recompute locally every minute; the API
itself is only polled every 3 hours.

## Dashboard cards

**One card for all favorites** (built-in Markdown card, no custom components):

```yaml
type: markdown
title: Opening hours today
content: |
  {% for e in [
    'sensor.linkoping_opening_hours',
    'sensor.motala_opening_hours'
  ] %}
  {{ state_attr(e, 'hours_markdown') }}

  {% endfor %}
```

**At a glance** (built-in Entities card, one library):

```yaml
type: entities
title: Motala bibliotek
entities:
  - sensor.motala_opening_hours
  - binary_sensor.motala_open
  - binary_sensor.motala_staffed  # once enabled
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
