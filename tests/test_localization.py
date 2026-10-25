"""Every supported language: translation file, generated text, and in HA."""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.generated.languages import LANGUAGES

from custom_components.gotabiblioteken.data import (
    LABELS,
    LABELS_EN,
    compute_branch_today,
    labels_for,
)

from .const import SAMPLE_PAYLOAD
from .test_entities import _entry, _setup, _state

MJOLBY = "Mjölby bibliotek"

TRANSLATIONS = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "gotabiblioteken"
    / "translations"
)
SUPPORTED = sorted(path.stem for path in TRANSLATIONS.glob("*.json"))


def _translation(language: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (TRANSLATIONS / f"{language}.json").read_text("utf-8")
    )
    return data


def test_expected_languages():
    # Swedish + English, Finnish (also a Swedish minority language), and the
    # main languages of the neighboring Nordic countries.
    assert SUPPORTED == ["da", "en", "fi", "is", "nb", "nn", "sv"]


def test_translation_files_and_labels_cover_the_same_languages():
    assert sorted(LABELS) == SUPPORTED


@pytest.mark.parametrize("language", SUPPORTED)
def test_language_is_selectable_in_home_assistant(language):
    """A translation for a language HA can't be set to would never load."""
    assert language in LANGUAGES


@pytest.mark.parametrize("language", SUPPORTED)
def test_labels_are_complete(language):
    labels = LABELS[language]
    assert len(labels.weekdays) == 7
    assert len(labels.months) == 12
    assert all([labels.closed, labels.closed_today, labels.staffed])
    assert labels.self_service
    labels.date_format.format(weekday="x", day=1, month="y")


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("fi-FI", "fi"),
        ("nb", "nb"),
        ("nn", "nn"),
        ("da", "da"),
        ("is", "is"),
        ("de", "en"),  # not covered: English
        ("fit", "en"),  # Meänkieli; not selectable in HA yet
    ],
)
def test_labels_for(language, expected):
    assert labels_for(language) is LABELS.get(expected, LABELS_EN)


@pytest.mark.parametrize(
    ("language", "date_label", "hours"),
    [
        ("en", "Tuesday 20 October", "09:00–14:00, Self-service 14:00–21:00"),
        ("sv", "Tisdag 20 oktober", "09:00–14:00, Meröppet 14:00–21:00"),
        ("fi", "Tiistai 20. lokakuuta", "09:00–14:00, Omatoimiaika 14:00–21:00"),
        ("nb", "Tirsdag 20. oktober", "09:00–14:00, Meråpent 14:00–21:00"),
        ("nn", "Tysdag 20. oktober", "09:00–14:00, Meirope 14:00–21:00"),
        ("da", "Tirsdag 20. oktober", "09:00–14:00, Åbent bibliotek 14:00–21:00"),
        ("is", "Þriðjudagur 20. október", "09:00–14:00, Sjálfsafgreiðsla 14:00–21:00"),
    ],
)
def test_generated_text(language, date_label, hours):
    r = compute_branch_today(
        SAMPLE_PAYLOAD,
        "Borensbergs bibliotek",
        datetime(2026, 10, 20, 10, 0),
        labels_for(language),
    )
    assert r["attributes"]["date_label"] == date_label
    assert r["hours"] == hours


@pytest.mark.parametrize("language", SUPPORTED)
async def test_home_assistant_in_each_language(
    hass: HomeAssistant, language: str
) -> None:
    # Mjölby has no hours on the sample day, so its state is the closed text.
    hass.config.language = language
    entry = await _setup(hass, _entry([MJOLBY]))

    names = _translation(language)["entity"]
    open_state = _state(hass, entry, MJOLBY, "open")
    assert open_state.attributes["friendly_name"] == (
        f"Mjölby {names['binary_sensor']['open']['name']}"
    )
    hours = _state(hass, entry, MJOLBY, "hours")
    assert hours.attributes["friendly_name"] == (
        f"Mjölby {names['sensor']['hours']['name']}"
    )
    assert hours.state == LABELS[language].closed
