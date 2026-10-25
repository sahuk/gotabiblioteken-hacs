"""Per-library display name and website, keyed by lowercased API name.

Short names are the place without "bibliotek" and without the genitive -s
("Borensbergs bibliotek" -> "Borensberg"), so the device name, and with it
every entity name, starts with the part that tells libraries apart and
survives being cut off on a dashboard card.

Websites come from https://www.gotabiblioteken.se/öppettider (each branch's
"Visa alla öppettider för …" link). Where the site and the API name a
branch differently: "Motala bibliotek" is Motala huvudbibliotek,
"Malmslätts bibliotek" is Malmslätt bibliotek, and "Stinsen" is the
Söderköping library (its hours sit in that section of the page).
"""

from __future__ import annotations

from dataclasses import dataclass
import re

# Fallback for branches the API adds later: the consortium's hours page.
OPENING_HOURS_URL = "https://www.gotabiblioteken.se/%C3%B6ppettider"

_GENERIC = re.compile(
    r"\b(huvudbibliotek|stadsbibliotek|kommunbibliotek|bibliotek)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Library:
    short_name: str
    website: str


LIBRARIES: dict[str, Library] = {
    "berga bibliotek": Library("Berga", "https://www.gotabiblioteken.se/berga"),
    "bibliotek agora": Library(
        "Agora", "https://www.gotabiblioteken.se/bibliotek-agora"
    ),
    "borensbergs bibliotek": Library(
        "Borensberg", "https://www.gotabiblioteken.se/borensbergs-bibliotek"
    ),
    "borghamns bibliotek": Library(
        "Borghamn", "https://www.gotabiblioteken.se/borghamn-bibliotek"
    ),
    "boxholms bibliotek": Library(
        "Boxholm", "https://www.gotabiblioteken.se/boxholms-bibliotek"
    ),
    "ekholmens bibliotek": Library(
        "Ekholmen", "https://www.gotabiblioteken.se/ekholmen"
    ),
    "eneby bibliotek": Library(
        "Eneby", "https://www.gotabiblioteken.se/eneby-bibliotek"
    ),
    "finspångs huvudbibliotek": Library(
        "Finspång", "https://www.gotabiblioteken.se/finspang-bibliotek"
    ),
    "gusums bibliotek": Library(
        "Gusum", "https://www.gotabiblioteken.se/gusums-bibliotek"
    ),
    "hageby bibliotek": Library(
        "Hageby", "https://www.gotabiblioteken.se/hageby-bibliotek"
    ),
    "hestra bibliotek": Library(
        "Hestra", "https://www.gotabiblioteken.se/hestra-bibliotek"
    ),
    "horns bibliotek": Library("Horn", "https://www.gotabiblioteken.se/horn-bibliotek"),
    "hällestad bibliotek": Library(
        "Hällestad", "https://www.gotabiblioteken.se/hallestad-bibliotek"
    ),
    "johannelunds bibliotek": Library(
        "Johannelund", "https://www.gotabiblioteken.se/johannelund"
    ),
    "kisa bibliotek": Library("Kisa", "https://www.gotabiblioteken.se/kisa-bibliotek"),
    "krokeks bibliotek": Library(
        "Krokek", "https://www.gotabiblioteken.se/krokeks-bibliotek"
    ),
    "lambohovs bibliotek": Library(
        "Lambohov", "https://www.gotabiblioteken.se/lambohovs-bibliotek"
    ),
    "linghems bibliotek": Library("Linghem", "https://www.gotabiblioteken.se/linghem"),
    "linköpings huvudbibliotek": Library(
        "Linköping", "https://www.gotabiblioteken.se/linkoping-huvudbibliotek"
    ),
    "ljungsbro bibliotek": Library(
        "Ljungsbro", "https://www.gotabiblioteken.se/ljungsbro"
    ),
    "malmslätts bibliotek": Library(
        "Malmslätt", "https://www.gotabiblioteken.se/malmsl%C3%A4tt-bibliotek"
    ),
    "mantorps bibliotek": Library(
        "Mantorp", "https://www.gotabiblioteken.se/mantorps-bibliotek"
    ),
    "mjölby bibliotek": Library(
        "Mjölby", "https://www.gotabiblioteken.se/mjolby-bibliotek"
    ),
    "mogata bibliotek": Library(
        "Mogata", "https://www.gotabiblioteken.se/mogata-bibliotek"
    ),
    "motala bibliotek": Library(
        "Motala", "https://www.gotabiblioteken.se/motala-huvudbibliotek"
    ),
    "norrköpings stadsbibliotek": Library(
        "Norrköping", "https://www.gotabiblioteken.se/norrkopings-stadsbibliotek"
    ),
    "rejmyre bibliotek": Library(
        "Rejmyre", "https://www.gotabiblioteken.se/rejmyre-bibliotek"
    ),
    "rimforsa bibliotek": Library(
        "Rimforsa", "https://www.gotabiblioteken.se/rimforsa-bibliotek"
    ),
    "ringarums bibliotek": Library(
        "Ringarum", "https://www.gotabiblioteken.se/ringarums-bibliotek"
    ),
    "ryds bibliotek": Library("Ryd", "https://www.gotabiblioteken.se/ryd"),
    "skänninge bibliotek": Library(
        "Skänninge", "https://www.gotabiblioteken.se/skanninge-bibliotek"
    ),
    "skärblacka bibliotek": Library(
        "Skärblacka", "https://www.gotabiblioteken.se/skarblacka-bibliotek"
    ),
    "stinsen": Library(
        "Stinsen", "https://www.gotabiblioteken.se/soderkopings-bibliotek"
    ),
    "sturefors bibliotek": Library(
        "Sturefors", "https://www.gotabiblioteken.se/sturefors"
    ),
    "tjällmo bibliotek": Library(
        "Tjällmo", "https://www.gotabiblioteken.se/tjallmo-bibliotek"
    ),
    "tranås stadsbibliotek": Library(
        "Tranås", "https://www.gotabiblioteken.se/tranas-bibliotek"
    ),
    "vadstena bibliotek": Library(
        "Vadstena", "https://www.gotabiblioteken.se/vadstena-bibliotek"
    ),
    "valdemarsviks bibliotek": Library(
        "Valdemarsvik", "https://www.gotabiblioteken.se/valdemarsviks-bibliotek"
    ),
    "vilbergens bibliotek": Library(
        "Vilbergen", "https://www.gotabiblioteken.se/vilbergens-bibliotek"
    ),
    "väderstads bibliotek": Library(
        "Väderstad", "https://www.gotabiblioteken.se/vaderstad-bibliotek"
    ),
    "ydre kommunbibliotek": Library(
        "Ydre", "https://www.gotabiblioteken.se/ydre-kommunbibliotek"
    ),
    "åby bibliotek": Library(
        "Åby", "https://www.gotabiblioteken.se/%C3%A5by-bibliotek"
    ),
    "åtvidabergs bibliotek": Library(
        "Åtvidaberg", "https://www.gotabiblioteken.se/atvidaberg"
    ),
    "ödeshögs bibliotek": Library(
        "Ödeshög", "https://www.gotabiblioteken.se/%C3%96desh%C3%B6gs-bibliotek"
    ),
    "östra husby bibliotek": Library(
        "Östra Husby", "https://www.gotabiblioteken.se/ostra-husby-bibliotek"
    ),
    "östra ryds bibliotek": Library(
        "Östra Ryd", "https://www.gotabiblioteken.se/ostra-ryds-bibliotek"
    ),
}


def _lookup(branch: str) -> Library | None:
    return LIBRARIES.get(branch.strip().lower())


def short_name(branch: str) -> str:
    """Display name for the device; derived for branches not in the table."""
    if library := _lookup(branch):
        return library.short_name
    return " ".join(_GENERIC.sub("", branch).split()) or branch.strip()


def website_for(branch: str) -> str:
    """The library's own page, or the consortium's hours page if unknown."""
    library = _lookup(branch)
    return library.website if library else OPENING_HOURS_URL
