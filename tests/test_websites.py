"""The per-library website mapping."""

import pytest

from custom_components.gotabiblioteken.websites import (
    OPENING_HOURS_URL,
    WEBSITES,
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


def test_unknown_branch_falls_back_to_hours_page():
    assert website_for("Nytt bibliotek") == OPENING_HOURS_URL


def test_all_websites_are_gotabiblioteken_https():
    assert len(WEBSITES) == 46
    for name, url in WEBSITES.items():
        assert name == name.strip().lower()
        assert url.startswith("https://www.gotabiblioteken.se/"), url
