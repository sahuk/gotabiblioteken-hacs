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
    ApiPayload,
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
    nordic = ["sv", "en", "fi", "nb", "nn", "da", "is"]  # fi: also a minority language
    continental_eu = ["de", "fr", "es", "pt", "it"]
    baltic_and_poland = ["et", "lv", "lt", "pl"]
    assert sorted(nordic + continental_eu + baltic_and_poland) == SUPPORTED


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
        ("fi", "fi"),
        ("pt", "pt"),
        # Regional variants without their own file get English entity names
        # from Home Assistant, so the generated text is English as well.
        ("pt-BR", "en"),
        ("es-419", "en"),
        ("ja", "en"),  # not covered
        ("fit", "en"),  # Meänkieli; not selectable in HA yet
    ],
)
def test_labels_for(language, expected):
    assert labels_for(language) is LABELS.get(expected, LABELS_EN)


@pytest.mark.parametrize(
    ("language", "date_label", "hours"),
    [
        ("en", "Tuesday 20 October", "09:00–14:00, Self-service 14:00–21:00"),
        ("sv", "Tisdag 20 oktober", "09:00–14:00, meröppet 14:00–21:00"),
        ("fi", "Tiistai 20. lokakuuta", "09:00–14:00, omatoimiaika 14:00–21:00"),
        ("nb", "Tirsdag 20. oktober", "09:00–14:00, meråpent 14:00–21:00"),
        ("nn", "Tysdag 20. oktober", "09:00–14:00, meirope 14:00–21:00"),
        ("da", "Tirsdag 20. oktober", "09:00–14:00, åbent bibliotek 14:00–21:00"),
        ("is", "Þriðjudagur 20. október", "09:00–14:00, sjálfsafgreiðsla 14:00–21:00"),
        ("de", "Dienstag, 20. Oktober", "09:00–14:00, Open Library 14:00–21:00"),
        ("fr", "Mardi 20 octobre", "09:00–14:00, accès autonome 14:00–21:00"),
        ("es", "Martes, 20 de octubre", "09:00–14:00, autoservicio 14:00–21:00"),
        ("pt", "Terça-feira, 20 de outubro", "09:00–14:00, autosserviço 14:00–21:00"),
        ("it", "Martedì 20 ottobre", "09:00–14:00, self-service 14:00–21:00"),
        ("et", "Teisipäev, 20. oktoober", "09:00–14:00, iseteenindus 14:00–21:00"),
        ("lv", "Otrdiena, 20. oktobris", "09:00–14:00, bez personāla 14:00–21:00"),
        ("lt", "Antradienis, spalio 20 d.", "09:00–14:00, savitarna 14:00–21:00"),
        ("pl", "Wtorek, 20 października", "09:00–14:00, samoobsługa 14:00–21:00"),
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


@pytest.mark.parametrize(
    ("language", "markdown"),
    [
        # Weekday mid-line in lowercase except where the language capitalizes it.
        (
            "sv",
            "**Borensbergs bibliotek** — tisdag 20 oktober  \nBemannat: 09:00–14:00",
        ),
        (
            "de",
            "**Borensbergs bibliotek** — Dienstag, 20. Oktober  \nMit Personal: 09:00–14:00",
        ),
        (
            "en",
            "**Borensbergs bibliotek** — Tuesday 20 October  \nStaffed: 09:00–14:00",
        ),
        # French typography: no-break space before the colon.
        (
            "fr",
            "**Borensbergs bibliotek** — mardi 20 octobre  \nAvec personnel\u00a0: 09:00–14:00",
        ),
    ],
)
def test_markdown_case_and_typography(language, markdown):
    r = compute_branch_today(
        SAMPLE_PAYLOAD,
        "Borensbergs bibliotek",
        datetime(2026, 10, 20, 10, 0),
        labels_for(language),
    )
    assert r["attributes"]["hours_markdown"].startswith(markdown)
    assert r["attributes"]["weekday"] == r["attributes"]["date_label"].split()[
        0
    ].rstrip(",")


@pytest.mark.parametrize(
    ("language", "date_label"),
    [
        ("fr", "Jeudi 1er janvier"),
        ("it", "Giovedì 1º gennaio"),
        ("sv", "Torsdag 1 januari"),
    ],
)
def test_first_of_the_month(language, date_label):
    r = compute_branch_today(
        SAMPLE_PAYLOAD, "x", datetime(2026, 1, 1), labels_for(language)
    )
    assert r["attributes"]["date_label"] == date_label


@pytest.mark.parametrize(
    ("language", "hours"),
    [("sv", "Meröppet 07:00–22:00"), ("de", "Open Library 07:00–22:00")],
)
def test_self_service_first_keeps_its_capital(language, hours):
    payload: ApiPayload = {
        "dates": [
            {
                "date": "2026-10-20",
                "branches": [
                    {
                        "branchName": "x",
                        "openingHours": [
                            {
                                "serviceType": "SelfService",
                                "from": "07:00",
                                "to": "22:00",
                            }
                        ],
                    }
                ],
            }
        ]
    }
    r = compute_branch_today(
        payload, "x", datetime(2026, 10, 20, 12, 0), labels_for(language)
    )
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
