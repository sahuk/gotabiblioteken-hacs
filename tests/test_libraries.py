"""The per-library short name and website table."""

import pytest

from custom_components.gotabiblioteken.libraries import (
    LIBRARIES,
    OPENING_HOURS_URL,
    short_name,
    website_for,
)


@pytest.mark.parametrize(
    ("branch", "url"),
    [
        (
            "Borensbergs bibliotek",
            "https://www.gotabiblioteken.se/borensbergs-bibliotek",
        ),
        # Leading space and case, as the API sometimes sends them.
        (
            " Finspångs huvudbibliotek",
            "https://www.gotabiblioteken.se/finspang-bibliotek",
        ),
        # Names that differ between the API and the website.
        ("Motala bibliotek", "https://www.gotabiblioteken.se/motala-huvudbibliotek"),
        ("Stinsen", "https://www.gotabiblioteken.se/soderkopings-bibliotek"),
    ],
)
def test_website_for_known_branch(branch, url):
    assert website_for(branch) == url


@pytest.mark.parametrize(
    ("branch", "expected"),
    [
        ("Motala bibliotek", "Motala"),
        ("Bibliotek Agora", "Agora"),  # generic word first
        ("Borensbergs bibliotek", "Borensberg"),  # genitive -s dropped
        ("Östra Ryds bibliotek", "Östra Ryd"),
        ("Sturefors bibliotek", "Sturefors"),  # -s is part of the place name
        ("Tranås stadsbibliotek", "Tranås"),
        (" Finspångs huvudbibliotek", "Finspång"),
    ],
)
def test_short_name_known_branch(branch, expected):
    assert short_name(branch) == expected


def test_unknown_branch_falls_back():
    assert website_for("Nytt bibliotek") == OPENING_HOURS_URL
    assert short_name("Nya stadsbiblioteket") == "Nya stadsbiblioteket"
    assert short_name("Bibliotek Nova") == "Nova"
    assert short_name("Bibliotek") == "Bibliotek"


def test_table_is_complete_and_unambiguous():
    assert len(LIBRARIES) == 46
    shorts = [library.short_name for library in LIBRARIES.values()]
    assert len(set(shorts)) == len(shorts), "short names must tell libraries apart"
    for name, library in LIBRARIES.items():
        assert name == name.strip().lower()
        assert "bibliotek" not in library.short_name.lower()
        assert library.website.startswith("https://www.gotabiblioteken.se/")
