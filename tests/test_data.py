"""Unit tests for the pure opening-hours logic (no Home Assistant)."""

from datetime import datetime, timedelta

import pytest

from custom_components.gotabiblioteken.data import (
    ApiPayload,
    _merge,
    branch_names,
    compute_branch_today,
)

from .const import SAMPLE_PAYLOAD

SELF_SERVICE_ONLY: ApiPayload = {
    "dates": [
        {
            "date": "2026-10-20",
            "branches": [
                {
                    "branchName": "Ekängens bibliotek",
                    "openingHours": [
                        {
                            "serviceType": "SelfService",
                            "info": "Meröppet",
                            "from": "07:00",
                            "to": "22:00",
                        }
                    ],
                }
            ],
        }
    ]
}


def _at(hm: str) -> datetime:
    return datetime.strptime(f"2026-10-20 {hm}", "%Y-%m-%d %H:%M")


def _iv(start: str, end: str) -> dict[str, str]:
    return {"from": start, "to": end}


def test_branch_names_union_and_dedupe():
    # Mjölby only appears on day two; the two Finspång entries collapse to one.
    assert branch_names(SAMPLE_PAYLOAD) == [
        "Borensbergs bibliotek",
        "Finspångs huvudbibliotek",
        "Mjölby bibliotek",
        "Motala bibliotek",
    ]


@pytest.mark.parametrize(
    ("intervals", "expected"),
    [
        ([_iv("14:00", "21:00"), _iv("09:00", "14:00")], [_iv("09:00", "21:00")]),
        ([_iv("09:00", "15:00"), _iv("12:00", "18:00")], [_iv("09:00", "18:00")]),
        ([_iv("09:00", "18:00"), _iv("10:00", "12:00")], [_iv("09:00", "18:00")]),
        (
            [_iv("09:00", "12:00"), _iv("13:00", "18:00")],
            [_iv("09:00", "12:00"), _iv("13:00", "18:00")],
        ),
        ([], []),
    ],
    ids=["adjacent", "overlapping", "contained", "gap", "empty"],
)
def test_merge(intervals, expected):
    assert _merge(intervals) == expected


def test_split_shift_staffed_then_self_service():
    r = compute_branch_today(SAMPLE_PAYLOAD, "Borensbergs bibliotek", _at("15:00"))
    assert r["hours"] == "09:00–14:00, Meröppet 14:00–21:00"
    assert r["staffed"] == {"is_on": False, "hours": "09:00–14:00"}
    assert r["self_service"] == {"is_on": True, "hours": "09:00–21:00"}
    a = r["attributes"]
    assert a["staffed_summary"] == "09:00–14:00"
    assert a["self_service_summary"] == "14:00–21:00"
    assert a["status"] == "self_service"
    assert len(a["shifts"]) == 2


def test_staffed_hours_count_as_cardholder_access():
    r = compute_branch_today(SAMPLE_PAYLOAD, "Borensbergs bibliotek", _at("10:00"))
    assert r["staffed"]["is_on"] is True
    assert r["self_service"]["is_on"] is True
    assert r["attributes"]["status"] == "staffed"


def test_self_service_only_branch():
    r = compute_branch_today(SELF_SERVICE_ONLY, "Ekängens bibliotek", _at("20:00"))
    assert r["hours"] == "Meröppet 07:00–22:00"
    assert r["staffed"] == {"is_on": False, "hours": "Stängt"}
    assert r["self_service"] == {"is_on": True, "hours": "07:00–22:00"}


def test_shift_ending_at_midnight():
    payload: ApiPayload = {
        "dates": [
            {
                "date": "2026-10-20",
                "branches": [
                    {
                        "branchName": "Sent bibliotek",
                        "openingHours": [
                            {"serviceType": "Staffed", "from": "10:00", "to": "19:00"},
                            {
                                "serviceType": "SelfService",
                                "from": "19:00",
                                "to": "00:00",
                            },
                        ],
                    }
                ],
            }
        ]
    }
    r = compute_branch_today(payload, "Sent bibliotek", _at("23:30"))
    assert r["self_service"] == {"is_on": True, "hours": "10:00–24:00"}


def test_hours_listed_in_time_order():
    # Finspång opens for Meröppet before staff arrive.
    r = compute_branch_today(SAMPLE_PAYLOAD, "Finspångs huvudbibliotek", _at("08:00"))
    assert r["hours"] == "Meröppet 09:00–12:00, 12:00–18:00"


def test_duplicate_branch_merges_and_dedupes_shifts():
    # Leading-space + duplicate entry: one staffed (deduped) + one self-service.
    r = compute_branch_today(SAMPLE_PAYLOAD, " Finspångs huvudbibliotek ", _at("13:00"))
    shifts = r["attributes"]["shifts"]
    assert len(shifts) == 2
    assert r["attributes"]["staffed_summary"] == "12:00–18:00"
    assert r["attributes"]["self_service_summary"] == "09:00–12:00"


def test_missing_branch_is_closed_everywhere():
    r = compute_branch_today(SAMPLE_PAYLOAD, "Does Not Exist", _at("12:00"))
    assert r["hours"] == "Stängt"
    assert r["staffed"] == {"is_on": False, "hours": "Stängt"}
    assert r["self_service"] == {"is_on": False, "hours": "Stängt"}
    assert r["attributes"]["status"] == "closed"
    assert r["attributes"]["shifts"] == []


def test_markdown_and_labels():
    a = compute_branch_today(SAMPLE_PAYLOAD, "Borensbergs bibliotek", _at("10:00"))[
        "attributes"
    ]
    assert a["date"] == "2026-10-20"
    assert a["weekday"] == "Tisdag"
    assert a["date_label"] == "Tisdag 20 oktober"
    assert (
        a["hours_markdown"].splitlines()[0].strip()
        == "**Borensbergs bibliotek** — Tisdag 20 oktober"
    )
    assert "Bemannat: 09:00–14:00" in a["hours_markdown"]
    assert "Meröppet: 14:00–21:00" in a["hours_markdown"]


def _within(hours: str, hm: str) -> bool:
    """Is `hm` inside the hours as displayed, e.g. "09:00–14:00, 15:00–18:00"?"""
    if hours == "Stängt":
        return False
    return any(
        start <= hm < end
        for start, end in (part.split("–") for part in hours.split(", "))
    )


@pytest.mark.parametrize(
    ("payload", "branch"),
    [
        (SAMPLE_PAYLOAD, "Borensbergs bibliotek"),
        (SAMPLE_PAYLOAD, "Finspångs huvudbibliotek"),
        (SAMPLE_PAYLOAD, "Motala bibliotek"),
        (SAMPLE_PAYLOAD, "Does Not Exist"),
        (SELF_SERVICE_ONLY, "Ekängens bibliotek"),
    ],
)
def test_open_state_always_matches_displayed_hours(payload, branch):
    """Acceptance criterion 3: the door never disagrees with its listed hours."""
    now = _at("00:00")
    for _ in range(24 * 60):
        r = compute_branch_today(payload, branch, now)
        hm = now.strftime("%H:%M")
        for key in ("staffed", "self_service"):
            block = r[key]
            assert block["is_on"] is _within(block["hours"], hm), (key, hm)
        now += timedelta(minutes=1)
