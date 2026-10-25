"""Each library's page on gotabiblioteken.se, keyed by lowercased API name.

Collected from https://www.gotabiblioteken.se/öppettider (each branch's
"Visa alla öppettider för …" link). Where the site and the API name a
branch differently: "Motala bibliotek" is Motala huvudbibliotek,
"Malmslätts bibliotek" is Malmslätt bibliotek, and "Stinsen" is the
Söderköping library (its hours sit in that section of the page).
"""

from __future__ import annotations

# Fallback for branches the API adds later: the consortium's hours page.
OPENING_HOURS_URL = "https://www.gotabiblioteken.se/%C3%B6ppettider"

WEBSITES: dict[str, str] = {
    "berga bibliotek": "https://www.gotabiblioteken.se/berga",
    "bibliotek agora": "https://www.gotabiblioteken.se/bibliotek-agora",
    "borensbergs bibliotek": "https://www.gotabiblioteken.se/borensbergs-bibliotek",
    "borghamns bibliotek": "https://www.gotabiblioteken.se/borghamn-bibliotek",
    "boxholms bibliotek": "https://www.gotabiblioteken.se/boxholms-bibliotek",
    "ekholmens bibliotek": "https://www.gotabiblioteken.se/ekholmen",
    "eneby bibliotek": "https://www.gotabiblioteken.se/eneby-bibliotek",
    "finspångs huvudbibliotek": "https://www.gotabiblioteken.se/finspang-bibliotek",
    "gusums bibliotek": "https://www.gotabiblioteken.se/gusums-bibliotek",
    "hageby bibliotek": "https://www.gotabiblioteken.se/hageby-bibliotek",
    "hestra bibliotek": "https://www.gotabiblioteken.se/hestra-bibliotek",
    "horns bibliotek": "https://www.gotabiblioteken.se/horn-bibliotek",
    "hällestad bibliotek": "https://www.gotabiblioteken.se/hallestad-bibliotek",
    "johannelunds bibliotek": "https://www.gotabiblioteken.se/johannelund",
    "kisa bibliotek": "https://www.gotabiblioteken.se/kisa-bibliotek",
    "krokeks bibliotek": "https://www.gotabiblioteken.se/krokeks-bibliotek",
    "lambohovs bibliotek": "https://www.gotabiblioteken.se/lambohovs-bibliotek",
    "linghems bibliotek": "https://www.gotabiblioteken.se/linghem",
    "linköpings huvudbibliotek": "https://www.gotabiblioteken.se/linkoping-huvudbibliotek",
    "ljungsbro bibliotek": "https://www.gotabiblioteken.se/ljungsbro",
    "malmslätts bibliotek": "https://www.gotabiblioteken.se/malmsl%C3%A4tt-bibliotek",
    "mantorps bibliotek": "https://www.gotabiblioteken.se/mantorps-bibliotek",
    "mjölby bibliotek": "https://www.gotabiblioteken.se/mjolby-bibliotek",
    "mogata bibliotek": "https://www.gotabiblioteken.se/mogata-bibliotek",
    "motala bibliotek": "https://www.gotabiblioteken.se/motala-huvudbibliotek",
    "norrköpings stadsbibliotek": "https://www.gotabiblioteken.se/norrkopings-stadsbibliotek",
    "rejmyre bibliotek": "https://www.gotabiblioteken.se/rejmyre-bibliotek",
    "rimforsa bibliotek": "https://www.gotabiblioteken.se/rimforsa-bibliotek",
    "ringarums bibliotek": "https://www.gotabiblioteken.se/ringarums-bibliotek",
    "ryds bibliotek": "https://www.gotabiblioteken.se/ryd",
    "skänninge bibliotek": "https://www.gotabiblioteken.se/skanninge-bibliotek",
    "skärblacka bibliotek": "https://www.gotabiblioteken.se/skarblacka-bibliotek",
    "stinsen": "https://www.gotabiblioteken.se/soderkopings-bibliotek",
    "sturefors bibliotek": "https://www.gotabiblioteken.se/sturefors",
    "tjällmo bibliotek": "https://www.gotabiblioteken.se/tjallmo-bibliotek",
    "tranås stadsbibliotek": "https://www.gotabiblioteken.se/tranas-bibliotek",
    "vadstena bibliotek": "https://www.gotabiblioteken.se/vadstena-bibliotek",
    "valdemarsviks bibliotek": "https://www.gotabiblioteken.se/valdemarsviks-bibliotek",
    "vilbergens bibliotek": "https://www.gotabiblioteken.se/vilbergens-bibliotek",
    "väderstads bibliotek": "https://www.gotabiblioteken.se/vaderstad-bibliotek",
    "ydre kommunbibliotek": "https://www.gotabiblioteken.se/ydre-kommunbibliotek",
    "åby bibliotek": "https://www.gotabiblioteken.se/%C3%A5by-bibliotek",
    "åtvidabergs bibliotek": "https://www.gotabiblioteken.se/atvidaberg",
    "ödeshögs bibliotek": "https://www.gotabiblioteken.se/%C3%96desh%C3%B6gs-bibliotek",
    "östra husby bibliotek": "https://www.gotabiblioteken.se/ostra-husby-bibliotek",
    "östra ryds bibliotek": "https://www.gotabiblioteken.se/ostra-ryds-bibliotek",
}


def website_for(branch: str) -> str:
    """The library's own page, or the consortium's hours page if unknown."""
    return WEBSITES.get(branch.strip().lower(), OPENING_HOURS_URL)
