"""Build review packets for the translation-review skill, one per language.

Usage: uv run scripts/translation_review_packets.py OUT_DIR
           [--since REF] [--all] [--lang CODE ...]

A packet holds what a reviewer of one human language needs: the strings that
changed since REF (default: the latest v* tag) next to their English source,
real generated output on three sample days, a glossary of the concepts, and
the full translation file and generated-text labels for consistency checks.
Also writes OUT_DIR/index.json listing the languages with something to review.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import dataclasses
from datetime import datetime
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from custom_components.gotabiblioteken.data import (  # noqa: E402
    LABELS,
    ApiPayload,
    Labels,
    compute_branch_today,
)
from custom_components.gotabiblioteken.libraries import short_name  # noqa: E402

INTEGRATION = "custom_components/gotabiblioteken"

# English name and native name per reviewed language (en is the source).
LANGUAGE_NAMES: dict[str, tuple[str, str]] = {
    "sv": ("Swedish", "svenska"),
    "fi": ("Finnish", "suomi"),
    "nb": ("Norwegian Bokmål", "norsk bokmål"),
    "nn": ("Norwegian Nynorsk", "norsk nynorsk"),
    "da": ("Danish", "dansk"),
    "is": ("Icelandic", "íslenska"),
    "de": ("German", "Deutsch"),
    "fr": ("French", "français"),
    "es": ("Spanish (Spain)", "español"),
    "pt": ("Portuguese (Portugal)", "português europeu"),
    "it": ("Italian", "italiano"),
    "et": ("Estonian", "eesti"),
    "lv": ("Latvian", "latviešu"),
    "lt": ("Lithuanian", "lietuvių"),
    "pl": ("Polish", "polski"),
}

# One day, three libraries: staffed then Meröppet, Meröppet only, closed.
REVIEW_DAY = datetime(2026, 10, 20, 10, 0)
STAFFED, SELF_SERVICE_ONLY, CLOSED = (
    "Borensbergs bibliotek",
    "Ekholmens bibliotek",
    "Mjölby bibliotek",
)
REVIEW_PAYLOAD: ApiPayload = {
    "dates": [
        {
            "date": "2026-10-20",
            "branches": [
                {
                    "branchName": STAFFED,
                    "openingHours": [
                        {"serviceType": "Staffed", "from": "09:00", "to": "14:00"},
                        {"serviceType": "SelfService", "from": "14:00", "to": "21:00"},
                    ],
                },
                {
                    "branchName": SELF_SERVICE_ONLY,
                    "openingHours": [
                        {"serviceType": "SelfService", "from": "07:00", "to": "22:00"}
                    ],
                },
            ],
        }
    ]
}

GLOSSARY = """\
- The integration shows the opening hours of the Götabiblioteken libraries
  (Östergötland, Sweden) in Home Assistant, a smart-home app. Each library is
  a device; its entity names start with the library's short place name.
- **Staffed**: library staff are on site (help desk, story hour, homework help).
- **Self-service** (Swedish "Meröppet"): open with library card + PIN, no
  staff on site. The library is *open*, just unstaffed.
- **Open** (binary sensor): you can get in now, staffed or self-service.
- **Staffed** (binary sensor) and **Staffed hours** (sensor) are created
  disabled; people who need in-person help (kids, the elderly) enable them.
- **Not staffed**: the Staffed hours value on a day the library is open for
  self-service only. It must not read as "closed".
- Dashboard cards cut names off from the right, so the distinguishing word
  should come early; short is better.
- Follow Home Assistant's style in the language (usually: capital letter only
  at the start). Place names (Borensberg, Motala, ...) are never translated.
"""


class IndexEntry(TypedDict):
    code: str
    english: str
    native: str
    packet: str
    changed: list[str]


class Index(TypedDict):
    since: str
    languages: list[IndexEntry]


# (ref, repo-relative path) -> file text at that ref, or None if absent.
Show = Callable[[str, str], str | None]


def git_show(ref: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def latest_tag() -> str:
    return subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v*"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def flatten(value: object, prefix: str = "") -> dict[str, str]:
    """Translation JSON as {"entity.sensor.hours.name": "Opening hours", ...}."""
    if isinstance(value, dict):
        flat: dict[str, str] = {}
        for key, child in value.items():
            flat |= flatten(child, f"{prefix}{key}.")
        return flat
    return {prefix.rstrip("."): str(value)}


def label_fields(labels: object) -> dict[str, str]:
    """A Labels instance (current or loaded from an old ref) as text per field."""
    if not dataclasses.is_dataclass(labels) or isinstance(labels, type):
        return {}
    return {
        f"labels.{field.name}": json.dumps(
            getattr(labels, field.name), ensure_ascii=False
        )
        for field in dataclasses.fields(labels)
    }


def old_label_fields(ref: str, show: Show) -> dict[str, dict[str, str]]:
    """Each language's label fields as of `ref`, from that ref's data.py."""
    files = {
        name: show(ref, f"{INTEGRATION}/{name}") for name in ("data.py", "libraries.py")
    }
    if any(text is None for text in files.values()):
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        package = Path(tmp) / "_translation_review_old"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        for name, text in files.items():
            (package / name).write_text(text or "", encoding="utf-8")
        sys.path.insert(0, tmp)
        try:
            module = importlib.import_module("_translation_review_old.data")
            labels: object = getattr(module, "LABELS", {})
        finally:
            sys.path.remove(tmp)
            for name in [
                m for m in sys.modules if m.startswith("_translation_review_old")
            ]:
                del sys.modules[name]
    if not isinstance(labels, dict):
        return {}
    return {str(code): label_fields(value) for code, value in labels.items()}


def translation(code: str, ref: str | None, show: Show) -> dict[str, str]:
    path = f"{INTEGRATION}/translations/{code}.json"
    text = (ROOT / path).read_text(encoding="utf-8") if ref is None else show(ref, path)
    return flatten(json.loads(text)) if text else {}


def current_strings(code: str) -> dict[str, str]:
    return translation(code, None, git_show) | label_fields(LABELS[code])


def changed_keys(
    code: str, ref: str, show: Show, old_labels: dict[str, dict[str, str]]
) -> list[str]:
    """Keys whose text changed since `ref`, in this language or in English."""
    changed: set[str] = set()
    for lang in (code, "en"):
        now = current_strings(lang)
        before = translation(lang, ref, show) | old_labels.get(lang, {})
        changed |= {k for k, v in now.items() if before.get(k) != v}
    return sorted(k for k in changed if k in current_strings(code))


def sample_output(code: str) -> str:
    """Dashboard rows and Markdown cards as a user of `code` sees them."""
    labels: Labels = LABELS[code]
    names = translation(code, None, git_show)

    def name(platform: str, key: str) -> str:
        return names.get(f"entity.{platform}.{key}.name", "?")

    staffed_state = {
        True: names.get("entity.binary_sensor.staffed.state.on", "on"),
        False: names.get("entity.binary_sensor.staffed.state.off", "off"),
    }
    rows: list[str] = []
    cards: list[str] = []
    for branch, case in (
        (STAFFED, "staffed 09:00–14:00, then self-service until 21:00"),
        (SELF_SERVICE_ONLY, "self-service only, no staff all day"),
        (CLOSED, "closed all day"),
    ):
        today = compute_branch_today(REVIEW_PAYLOAD, branch, REVIEW_DAY, labels)
        place = short_name(branch)
        rows += [
            f"\n*{case}* (at 10:00):",
            f"- `{place} {name('sensor', 'hours')}` → `{today['hours']}`",
            f"- `{place} {name('binary_sensor', 'open')}` → door "
            f"{'open' if today['open']['is_on'] else 'closed'}",
            f"- `{place} {name('binary_sensor', 'staffed')}` → "
            f"`{staffed_state[today['staffed']['is_on']]}`",
            f"- `{place} {name('sensor', 'staffed_hours')}` → "
            f"`{today['staffed']['hours']}`",
        ]
        cards.append(today["attributes"]["hours_markdown"])
    card_blocks = "\n".join(f"```\n{card}\n```" for card in cards)
    return (
        "\n".join(rows).lstrip()
        + "\n\nMarkdown card (`hours_markdown`):\n\n"
        + card_blocks
    )


def packet(code: str, since: str, changed: list[str]) -> str:
    english, native = LANGUAGE_NAMES[code]
    en = current_strings("en")
    mine = current_strings(code)
    table = "\n".join(
        f"| `{key}` | {en.get(key, '')} | **{mine[key]}** |" for key in changed
    )
    full = json.dumps(
        json.loads(
            (ROOT / INTEGRATION / "translations" / f"{code}.json").read_text(
                encoding="utf-8"
            )
        ),
        indent=2,
        ensure_ascii=False,
    )
    labels = json.dumps(dataclasses.asdict(LABELS[code]), indent=2, ensure_ascii=False)
    return f"""\
# Translation review packet: {english} ({native}, `{code}`)

## Strings to review (changed since `{since}`)

| key | English source | {english} |
| --- | --- | --- |
{table}

`labels.*` is text the integration generates (states, attributes, the
Markdown card); the other keys are entity names and the setup dialog.

## How it looks (real output, {REVIEW_DAY:%A %Y-%m-%d})

{sample_output(code)}

## Concepts

{GLOSSARY}
## Full translation file

```json
{full}
```

## Generated-text labels

```json
{labels}
```
"""


def build(
    out_dir: Path,
    since: str,
    languages: list[str],
    *,
    review_all: bool = False,
    show: Show = git_show,
) -> Index:
    old_labels = {} if review_all else old_label_fields(since, show)
    index: Index = {"since": "everything" if review_all else since, "languages": []}
    out_dir.mkdir(parents=True, exist_ok=True)
    for code in languages:
        changed = (
            sorted(current_strings(code))
            if review_all
            else changed_keys(code, since, show, old_labels)
        )
        if not changed:
            continue
        path = out_dir / f"{code}.md"
        path.write_text(packet(code, index["since"], changed), encoding="utf-8")
        english, native = LANGUAGE_NAMES[code]
        index["languages"].append(
            {
                "code": code,
                "english": english,
                "native": native,
                "packet": str(path),
                "changed": changed,
            }
        )
    (out_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path)
    parser.add_argument(
        "--since", help="git ref to compare with (default: latest v* tag)"
    )
    parser.add_argument("--all", action="store_true", help="review every string")
    parser.add_argument("--lang", nargs="+", default=list(LANGUAGE_NAMES))
    args = parser.parse_args()
    unknown = [code for code in args.lang if code not in LANGUAGE_NAMES]
    if unknown:
        raise SystemExit(f"unknown language(s): {', '.join(unknown)}")
    since: str = args.since or latest_tag()
    index = build(args.out_dir, since, args.lang, review_all=args.all)
    if not index["languages"]:
        print(f"nothing to review since {since}")
        return 0
    for entry in index["languages"]:
        print(f"{entry['code']}: {len(entry['changed'])} string(s) → {entry['packet']}")
    print(f"index: {args.out_dir / 'index.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
