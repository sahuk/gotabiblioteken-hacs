"""The translation-review packet builder finds changed strings and real output."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from custom_components.gotabiblioteken.data import LABELS

ROOT = Path(__file__).resolve().parent.parent
INTEGRATION = "custom_components/gotabiblioteken"

_spec = importlib.util.spec_from_file_location(
    "translation_review_packets", ROOT / "scripts" / "translation_review_packets.py"
)
assert _spec and _spec.loader
packets = importlib.util.module_from_spec(_spec)
sys.modules["translation_review_packets"] = packets
_spec.loader.exec_module(packets)


def _show(overrides: dict[str, str | None]):
    """A `git show` stand-in: the working tree, except `overrides` (path: text)."""

    def show(ref: str, path: str) -> str | None:
        if path in overrides:
            return overrides[path]
        file = ROOT / path
        return file.read_text(encoding="utf-8") if file.exists() else None

    return show


def _current(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _changed(tmp_path: Path, overrides: dict[str, str | None]) -> dict[str, list[str]]:
    index = packets.build(
        tmp_path, "vX", list(packets.LANGUAGE_NAMES), show=_show(overrides)
    )
    return {entry["code"]: entry["changed"] for entry in index["languages"]}


def test_every_reviewed_language_has_names():
    assert set(packets.LANGUAGE_NAMES) == set(LABELS) - {"en"}


def test_nothing_changed(tmp_path):
    assert _changed(tmp_path, {}) == {}
    assert not list(tmp_path.glob("*.md"))


def test_changed_translation_and_label_in_one_language(tmp_path):
    sv = f"{INTEGRATION}/translations/sv.json"
    data = f"{INTEGRATION}/data.py"
    old_data = _current(data).replace('not_staffed="Obemannat"', 'not_staffed="X"')
    assert old_data != _current(data)
    changed = _changed(
        tmp_path,
        {
            sv: _current(sv).replace('"Bemannade tider"', '"Gammalt namn"'),
            data: old_data,
        },
    )
    assert changed == {"sv": ["entity.sensor.staffed_hours.name", "labels.not_staffed"]}


def test_changed_english_source_flags_every_language(tmp_path):
    en = f"{INTEGRATION}/translations/en.json"
    changed = _changed(
        tmp_path, {en: _current(en).replace('"Staffed hours"', '"Old name"')}
    )
    assert set(changed) == set(packets.LANGUAGE_NAMES)
    assert all(
        keys == ["entity.sensor.staffed_hours.name"] for keys in changed.values()
    )


def test_new_language_is_reviewed_in_full(tmp_path):
    changed = _changed(tmp_path, {f"{INTEGRATION}/translations/fi.json": None})
    assert set(changed) == {"fi"}
    assert "config.step.user.description" in changed["fi"]


@pytest.mark.parametrize(
    "row",
    [
        "`Borensberg Bemannade tider` → `09:00–14:00`",
        "`Ekholmen Bemannade tider` → `Obemannat`",
        "`Mjölby Öppettider` → `Stängt`",
    ],
)
def test_packet_shows_real_output(tmp_path, row):
    packets.build(tmp_path, "vX", ["sv"], review_all=True)
    text = (tmp_path / "sv.md").read_text(encoding="utf-8")
    assert row in text
    assert '| `labels.not_staffed` | "Not staffed" | **"Obemannat"** |' in text


def test_parsed_old_labels_match_the_runtime_labels():
    # Old labels are parsed from data.py, never imported; at HEAD the parse
    # must agree with the real Labels objects.
    parsed = packets.old_label_fields("HEAD", _show({}))
    assert parsed == {code: packets.label_fields(lab) for code, lab in LABELS.items()}


@pytest.mark.parametrize("ref", ["--output=/tmp/x", "no-such-ref"])
def test_unresolvable_ref_is_refused(ref):
    with pytest.raises(SystemExit):
        packets.resolve_ref(ref)
