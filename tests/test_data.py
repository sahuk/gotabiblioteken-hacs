"""Unit tests for the pure opening-hours logic (no Home Assistant)."""

from datetime import datetime

from custom_components.gotabiblioteken.data import branch_names, compute_branch_today

from .const import SAMPLE_PAYLOAD


def _at(hm: str) -> datetime:
    return datetime.strptime(f"2026-10-20 {hm}", "%Y-%m-%d %H:%M")


def test_branch_names_union_and_dedupe():
    # Mjölby only appears on day two; the two Finspång entries collapse to one.
    assert branch_names(SAMPLE_PAYLOAD) == [
        "Borensbergs bibliotek",
        "Finspångs huvudbibliotek",
        "Mjölby bibliotek",
        "Motala bibliotek",
    ]


def test_split_shift_staffed_then_self_service():
    r = compute_branch_today(
        SAMPLE_PAYLOAD, "Borensbergs bibliotek", True, _at("15:00")
    )
    a = r["attributes"]
    assert r["state"] == "09:00–14:00"
    assert a["staffed_summary"] == "09:00–14:00"
    assert a["self_service_summary"] == "14:00–21:00"
    assert a["status"] == "self_service"
    assert a["open_now"] is True
    assert len(a["shifts"]) == 2


def test_self_service_excluded_when_disabled():
    r = compute_branch_today(
        SAMPLE_PAYLOAD, "Borensbergs bibliotek", False, _at("15:00")
    )
    assert r["attributes"]["open_now"] is False  # only self-service open at 15:00


def test_duplicate_branch_merges_and_dedupes_shifts():
    # Leading-space + duplicate entry: one staffed (deduped) + one self-service.
    r = compute_branch_today(
        SAMPLE_PAYLOAD, " Finspångs huvudbibliotek ", True, _at("13:00")
    )
    shifts = r["attributes"]["shifts"]
    assert len(shifts) == 2
    assert r["attributes"]["staffed_summary"] == "12:00–18:00"
    assert r["attributes"]["self_service_summary"] == "09:00–12:00"


def test_missing_branch_is_closed():
    r = compute_branch_today(SAMPLE_PAYLOAD, "Does Not Exist", True, _at("12:00"))
    assert r["state"] == "Stängt"
    assert r["attributes"]["status"] == "closed"
    assert r["attributes"]["shifts"] == []


def test_markdown_and_labels():
    a = compute_branch_today(
        SAMPLE_PAYLOAD, "Borensbergs bibliotek", True, _at("10:00")
    )["attributes"]
    assert a["date"] == "2026-10-20"
    assert a["weekday"] == "Tisdag"
    assert a["date_label"] == "Tisdag 20 oktober"
    assert (
        a["hours_markdown"].splitlines()[0].strip()
        == "**Borensbergs bibliotek** — Tisdag 20 oktober"
    )
    assert "Bemannat: 09:00–14:00" in a["hours_markdown"]
    assert "Meröppet: 14:00–21:00" in a["hours_markdown"]
