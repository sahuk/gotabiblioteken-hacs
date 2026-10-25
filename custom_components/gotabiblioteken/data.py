"""Pure opening-hours computation.

No Home Assistant imports on purpose: this module is unit-testable on its own.
Generated text follows Home Assistant's language (`labels_for`); entity names are not set
here but come from the translation files.
Merges duplicate branch entries, de-duplicates identical shifts, and splits
staffed from self-service hours.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Literal, TypedDict

from .libraries import website_for

# Shape of the Axiell payload. Every key is optional: the API is external,
# so the code reads it with .get(), skips entries of the wrong type and
# treats missing or malformed data as closed.
ApiInterval = TypedDict(
    "ApiInterval",
    {
        "serviceType": str,
        "info": str | None,
        "from": str,
        "to": str,
        "openingHoursType": str,
    },
    total=False,
)


class ApiBranch(TypedDict, total=False):
    branchName: str
    openingHours: list[ApiInterval]


class ApiDay(TypedDict, total=False):
    date: str
    branches: list[ApiBranch]


class ApiPayload(TypedDict, total=False):
    dates: list[ApiDay]


Shift = TypedDict(
    "Shift",
    {
        "type": str,
        "service_type": str | None,
        "info": str | None,
        "from": str | None,
        "to": str | None,
    },
)


class Access(TypedDict):
    """One open/closed answer and exactly the hours it is derived from."""

    is_on: bool
    hours: str


class BranchAttributes(TypedDict):
    branch: str
    website: str
    date: str
    weekday: str
    date_label: str
    status: str
    staffed_summary: str
    self_service_summary: str
    shifts: list[Shift]
    hours_markdown: str


class BranchToday(TypedDict):
    hours: str
    staffed: Access
    open: Access
    attributes: BranchAttributes


AccessKey = Literal["staffed", "open"]


@dataclass(frozen=True)
class Labels:
    """Generated text (states, attributes) in one language.

    Labels and weekdays are written as they look at the start of a text
    ("Tisdag", "Meröppet"). Mid-line (after "—" or ", ") they get a lowercase
    first letter unless `lowercase_inline` is off, as in English and German.
    """

    closed: str
    closed_today: str
    staffed: str
    self_service: str
    # No staffed hours today, but open for self-service: not "closed".
    not_staffed: str
    # Placeholders: {weekday}, {day}, {month}.
    date_format: str
    weekdays: tuple[str, ...]
    # In the form the date label uses (genitive/partitive where the
    # language needs it: Finnish "lokakuuta", Polish "października").
    months: tuple[str, ...]
    lowercase_inline: bool = True
    # How the 1st of the month is written where it isn't plain "1" (French "1er").
    first_day: str = "1"
    # Label/value separator (French typography: no-break space before ":").
    colon: str = ": "

    def inline(self, text: str) -> str:
        """`text` as written in the middle of a line."""
        return text[:1].lower() + text[1:] if self.lowercase_inline else text

    def date_label(self, now: datetime) -> str:
        """The date as it reads at the start of a text, e.g. "Tisdag 20 oktober"."""
        return self.date_format.format(
            weekday=self.weekdays[now.weekday()],
            day=self.first_day if now.day == 1 else now.day,
            month=self.months[now.month - 1],
        )


LABELS_EN = Labels(
    closed="Closed",
    closed_today="Closed today",
    staffed="Staffed",
    self_service="Self-service",
    not_staffed="Not staffed",
    date_format="{weekday} {day} {month}",
    lowercase_inline=False,
    weekdays=(
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ),
    months=(
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ),
)

LABELS_SV = Labels(
    closed="Stängt",
    closed_today="Stängt i dag",
    staffed="Bemannat",
    self_service="Meröppet",
    not_staffed="Obemannat",
    date_format="{weekday} {day} {month}",
    weekdays=(
        "Måndag",
        "Tisdag",
        "Onsdag",
        "Torsdag",
        "Fredag",
        "Lördag",
        "Söndag",
    ),
    months=(
        "januari",
        "februari",
        "mars",
        "april",
        "maj",
        "juni",
        "juli",
        "augusti",
        "september",
        "oktober",
        "november",
        "december",
    ),
)

# Finnish is also a national minority language of Sweden.
LABELS_FI = Labels(
    closed="Suljettu",
    closed_today="Suljettu tänään",
    staffed="Palveluaika",
    self_service="Omatoimiaika",
    not_staffed="Ei palveluaikaa",
    date_format="{weekday} {day}. {month}",
    weekdays=(
        "Maanantai",
        "Tiistai",
        "Keskiviikko",
        "Torstai",
        "Perjantai",
        "Lauantai",
        "Sunnuntai",
    ),
    months=(
        "tammikuuta",
        "helmikuuta",
        "maaliskuuta",
        "huhtikuuta",
        "toukokuuta",
        "kesäkuuta",
        "heinäkuuta",
        "elokuuta",
        "syyskuuta",
        "lokakuuta",
        "marraskuuta",
        "joulukuuta",
    ),
)

LABELS_NB = Labels(
    closed="Stengt",
    closed_today="Stengt i dag",
    staffed="Betjent",
    self_service="Meråpent",
    not_staffed="Ubetjent",
    date_format="{weekday} {day}. {month}",
    weekdays=(
        "Mandag",
        "Tirsdag",
        "Onsdag",
        "Torsdag",
        "Fredag",
        "Lørdag",
        "Søndag",
    ),
    months=(
        "januar",
        "februar",
        "mars",
        "april",
        "mai",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "desember",
    ),
)

LABELS_NN = Labels(
    closed="Stengt",
    closed_today="Stengt i dag",
    staffed="Bemanna",
    self_service="Meirope",
    not_staffed="Ubemanna",
    date_format="{weekday} {day}. {month}",
    weekdays=(
        "Måndag",
        "Tysdag",
        "Onsdag",
        "Torsdag",
        "Fredag",
        "Laurdag",
        "Søndag",
    ),
    months=(
        "januar",
        "februar",
        "mars",
        "april",
        "mai",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "desember",
    ),
)

LABELS_DA = Labels(
    closed="Lukket",
    closed_today="Lukket i dag",
    # "Betjent" alone also means "police officer".
    staffed="Bemandet",
    self_service="Åbent bibliotek",
    not_staffed="Ubemandet",
    date_format="{weekday} {day}. {month}",
    weekdays=(
        "Mandag",
        "Tirsdag",
        "Onsdag",
        "Torsdag",
        "Fredag",
        "Lørdag",
        "Søndag",
    ),
    months=(
        "januar",
        "februar",
        "marts",
        "april",
        "maj",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "december",
    ),
)

LABELS_IS = Labels(
    closed="Lokað",
    closed_today="Lokað í dag",
    staffed="Mannað",
    self_service="Sjálfsafgreiðsla",
    not_staffed="Ómannað",
    date_format="{weekday} {day}. {month}",
    weekdays=(
        "Mánudagur",
        "Þriðjudagur",
        "Miðvikudagur",
        "Fimmtudagur",
        "Föstudagur",
        "Laugardagur",
        "Sunnudagur",
    ),
    months=(
        "janúar",
        "febrúar",
        "mars",
        "apríl",
        "maí",
        "júní",
        "júlí",
        "ágúst",
        "september",
        "október",
        "nóvember",
        "desember",
    ),
)

LABELS_DE = Labels(
    closed="Geschlossen",
    closed_today="Heute geschlossen",
    staffed="Mit Personal",
    # The term libraries in German-speaking countries use for staff-free hours.
    self_service="Open Library",
    not_staffed="Ohne Personal",
    date_format="{weekday}, {day}. {month}",
    lowercase_inline=False,
    weekdays=(
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ),
    months=(
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ),
)

LABELS_FR = Labels(
    closed="Fermé",
    closed_today="Fermé aujourd'hui",
    staffed="Avec personnel",
    # "Libre-service" reads as self-checkout machines in French libraries.
    self_service="Accès autonome",
    not_staffed="Sans personnel",
    date_format="{weekday} {day} {month}",
    first_day="1er",
    colon="\u00a0: ",
    weekdays=(
        "Lundi",
        "Mardi",
        "Mercredi",
        "Jeudi",
        "Vendredi",
        "Samedi",
        "Dimanche",
    ),
    months=(
        "janvier",
        "février",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "août",
        "septembre",
        "octobre",
        "novembre",
        "décembre",
    ),
)

LABELS_ES = Labels(
    closed="Cerrado",
    closed_today="Cerrado hoy",
    staffed="Con personal",
    self_service="Autoservicio",
    not_staffed="Sin personal",
    date_format="{weekday}, {day} de {month}",
    weekdays=(
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ),
    months=(
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ),
)

LABELS_PT = Labels(
    closed="Fechado",
    closed_today="Fechado hoje",
    staffed="Com pessoal",
    self_service="Autosserviço",
    not_staffed="Sem pessoal",
    date_format="{weekday}, {day} de {month}",
    weekdays=(
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ),
    months=(
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    ),
)

LABELS_IT = Labels(
    closed="Chiuso",
    closed_today="Chiuso oggi",
    staffed="Con personale",
    self_service="Self-service",
    not_staffed="Senza personale",
    date_format="{weekday} {day} {month}",
    first_day="1º",
    weekdays=(
        "Lunedì",
        "Martedì",
        "Mercoledì",
        "Giovedì",
        "Venerdì",
        "Sabato",
        "Domenica",
    ),
    months=(
        "gennaio",
        "febbraio",
        "marzo",
        "aprile",
        "maggio",
        "giugno",
        "luglio",
        "agosto",
        "settembre",
        "ottobre",
        "novembre",
        "dicembre",
    ),
)

LABELS_ET = Labels(
    closed="Suletud",
    closed_today="Täna suletud",
    staffed="Teenindus",
    self_service="Iseteenindus",
    not_staffed="Teeninduseta",
    date_format="{weekday}, {day}. {month}",
    weekdays=(
        "Esmaspäev",
        "Teisipäev",
        "Kolmapäev",
        "Neljapäev",
        "Reede",
        "Laupäev",
        "Pühapäev",
    ),
    months=(
        "jaanuar",
        "veebruar",
        "märts",
        "aprill",
        "mai",
        "juuni",
        "juuli",
        "august",
        "september",
        "oktoober",
        "november",
        "detsember",
    ),
)

LABELS_LV = Labels(
    closed="Slēgts",
    closed_today="Šodien slēgts",
    staffed="Ar personālu",
    self_service="Bez personāla",
    not_staffed="Bez personāla",
    date_format="{weekday}, {day}. {month}",
    weekdays=(
        "Pirmdiena",
        "Otrdiena",
        "Trešdiena",
        "Ceturtdiena",
        "Piektdiena",
        "Sestdiena",
        "Svētdiena",
    ),
    months=(
        "janvāris",
        "februāris",
        "marts",
        "aprīlis",
        "maijs",
        "jūnijs",
        "jūlijs",
        "augusts",
        "septembris",
        "oktobris",
        "novembris",
        "decembris",
    ),
)

LABELS_LT = Labels(
    closed="Uždaryta",
    closed_today="Šiandien uždaryta",
    staffed="Su personalu",
    self_service="Savitarna",
    not_staffed="Be personalo",
    date_format="{weekday}, {month} {day} d.",
    weekdays=(
        "Pirmadienis",
        "Antradienis",
        "Trečiadienis",
        "Ketvirtadienis",
        "Penktadienis",
        "Šeštadienis",
        "Sekmadienis",
    ),
    months=(
        "sausio",
        "vasario",
        "kovo",
        "balandžio",
        "gegužės",
        "birželio",
        "liepos",
        "rugpjūčio",
        "rugsėjo",
        "spalio",
        "lapkričio",
        "gruodžio",
    ),
)

LABELS_PL = Labels(
    closed="Zamknięte",
    closed_today="Dziś zamknięte",
    staffed="Z obsługą",
    self_service="Samoobsługa",
    not_staffed="Bez obsługi",
    date_format="{weekday}, {day} {month}",
    weekdays=(
        "Poniedziałek",
        "Wtorek",
        "Środa",
        "Czwartek",
        "Piątek",
        "Sobota",
        "Niedziela",
    ),
    months=(
        "stycznia",
        "lutego",
        "marca",
        "kwietnia",
        "maja",
        "czerwca",
        "lipca",
        "sierpnia",
        "września",
        "października",
        "listopada",
        "grudnia",
    ),
)

# Keyed by Home Assistant language code. Sweden's other national minority
# languages (Meänkieli, Sami, Romani, Yiddish) can't be selected as Home
# Assistant's language yet; see TRANSLATIONS.md.
LABELS: dict[str, Labels] = {
    "en": LABELS_EN,
    "sv": LABELS_SV,
    "fi": LABELS_FI,
    "nb": LABELS_NB,
    "nn": LABELS_NN,
    "da": LABELS_DA,
    "is": LABELS_IS,
    "de": LABELS_DE,
    "fr": LABELS_FR,
    "es": LABELS_ES,
    "pt": LABELS_PT,
    "it": LABELS_IT,
    "et": LABELS_ET,
    "lv": LABELS_LV,
    "lt": LABELS_LT,
    "pl": LABELS_PL,
}


def labels_for(language: str) -> Labels:
    """Labels for Home Assistant's language; English when it isn't covered.

    Exact match only, like Home Assistant's own translation lookup: a
    regional variant without its own file ("pt-BR", "es-419") gets English
    entity names, so its generated text is English too, not a mix.
    """
    return LABELS.get(language, LABELS_EN)


_HM = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")
# Markdown/HTML syntax a name must not inject into `hours_markdown`.
_MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]()<>!|~&#])")


def _entries[T](value: list[T] | None) -> list[T]:
    """The dict entries of an API list; a non-list or non-dict entry is skipped."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _name(branch: ApiBranch) -> str:
    name = branch.get("branchName")
    return name.strip() if isinstance(name, str) else ""


def _escape_markdown(text: str) -> str:
    """`text` as literal Markdown: on one line, no links, images or HTML."""
    return _MARKDOWN_SPECIAL.sub(r"\\\1", " ".join(text.split()))


def branch_names(payload: ApiPayload) -> list[str]:
    """Return the sorted, de-duplicated list of branch display names."""
    names: list[str] = []
    seen: set[str] = set()
    for day in _entries(payload.get("dates")):
        for branch in _entries(day.get("branches")):
            name = _name(branch)
            if name and name.lower() not in seen:
                seen.add(name.lower())
                names.append(name)
    return sorted(names, key=str.lower)


def _clean_interval(interval: ApiInterval) -> ApiInterval | None:
    """The interval with only well-typed fields, or None if its times are bad.

    Times must be 24-hour "HH:MM"; an end of "00:00" (midnight) becomes
    "24:00" so "HH:MM" string comparisons stay valid.
    """
    start, end = interval.get("from"), interval.get("to")
    if end == "00:00":
        end = "24:00"
    # Inline isinstance checks narrow for mypy; typing.TypeIs needs Python
    # 3.13, newer than the oldest supported Home Assistant (hacs.json).
    if not (
        isinstance(start, str)
        and _HM.fullmatch(start)
        and isinstance(end, str)
        and (end == "24:00" or _HM.fullmatch(end))
    ):
        return None
    clean: ApiInterval = {"from": start, "to": end}
    service_type, info = interval.get("serviceType"), interval.get("info")
    if isinstance(service_type, str):
        clean["serviceType"] = service_type
    clean["info"] = info if isinstance(info, str) else None
    return clean


def _intervals_for(
    payload: ApiPayload, branch: str, date_str: str
) -> list[ApiInterval]:
    """Merged, de-duplicated opening-hour intervals for a branch on a date."""
    norm = branch.strip().lower()
    entry = next(
        (d for d in _entries(payload.get("dates")) if d.get("date") == date_str),
        None,
    )
    if not entry:
        return []

    items: list[ApiInterval] = []
    seen: set[tuple[str | None, ...]] = set()
    for branch_entry in _entries(entry.get("branches")):
        if _name(branch_entry).lower() != norm:
            continue
        for raw in _entries(branch_entry.get("openingHours")):
            interval = _clean_interval(raw)
            if interval is None:
                continue
            key = (
                interval.get("serviceType"),
                interval["from"],
                interval["to"],
                interval.get("info"),
            )
            if key not in seen:
                seen.add(key)
                items.append(interval)
    return items


def _summary(intervals: Sequence[ApiInterval], labels: Labels) -> str:
    parts = [f"{i['from']}–{i['to']}" for i in intervals]
    return ", ".join(parts) if parts else labels.closed


def _merge(intervals: Sequence[ApiInterval]) -> list[ApiInterval]:
    """Sort intervals and join the ones that overlap or touch."""
    merged: list[ApiInterval] = []
    for i in sorted(intervals, key=lambda i: (i["from"], i["to"])):
        if merged and i["from"] <= merged[-1]["to"]:
            merged[-1]["to"] = max(merged[-1]["to"], i["to"])
        else:
            merged.append({"from": i["from"], "to": i["to"]})
    return merged


def _is_on(intervals: Sequence[ApiInterval], now_hm: str) -> bool:
    return any(i["from"] <= now_hm < i["to"] for i in intervals)


def _day_summary(intervals: Sequence[ApiInterval], labels: Labels) -> str:
    """All of today's shifts in time order, self-service ones labelled."""
    parts = [
        f"{'' if i.get('serviceType') == 'Staffed' else labels.self_service + ' '}"
        f"{i['from']}–{i['to']}"
        for i in sorted(intervals, key=lambda i: (i["from"], i["to"]))
    ]
    if not parts:
        return labels.closed
    return ", ".join([parts[0], *(labels.inline(p) for p in parts[1:])])


def compute_branch_today(
    payload: ApiPayload,
    branch: str,
    now: datetime,
    labels: Labels = LABELS_EN,
) -> BranchToday:
    """Compute today's hours and open/closed states for one branch.

    Each open/closed block is derived from exactly the intervals its `hours`
    string lists, so the two can never disagree. `open` answers "can I get
    in", which is true during staffed and Meröppet hours alike; `staffed` is
    the narrower "is someone working there". Generated text uses `labels`.
    """
    date_str = now.strftime("%Y-%m-%d")
    now_hm = now.strftime("%H:%M")

    intervals = _intervals_for(payload, branch, date_str)
    staffed = [i for i in intervals if i.get("serviceType") == "Staffed"]
    self_service = [i for i in intervals if i.get("serviceType") == "SelfService"]
    accessible = _merge(staffed + self_service)

    # A Meröppet-only day isn't closed for the staffed view either: you can
    # get in, there's just nobody working.
    staffed_summary = (
        _summary(staffed, labels) if staffed or not self_service else labels.not_staffed
    )
    self_service_summary = _summary(self_service, labels)

    staffed_now = _is_on(staffed, now_hm)
    accessible_now = _is_on(accessible, now_hm)
    status = (
        "staffed" if staffed_now else ("self_service" if accessible_now else "closed")
    )

    date_label = labels.date_label(now)

    shifts: list[Shift] = [
        {
            "type": (
                labels.staffed
                if i.get("serviceType") == "Staffed"
                else labels.self_service
            ),
            "service_type": i.get("serviceType"),
            "info": i.get("info"),
            "from": i.get("from"),
            "to": i.get("to"),
        }
        for i in intervals
    ]

    lines = [f"**{_escape_markdown(branch)}** — {labels.inline(date_label)}"]
    if staffed:
        lines.append(f"{labels.staffed}{labels.colon}{staffed_summary}")
    if self_service:
        lines.append(f"{labels.self_service}{labels.colon}{self_service_summary}")
    if not staffed and not self_service:
        lines.append(labels.closed_today)
    hours_markdown = "  \n".join(lines)

    return {
        "hours": _day_summary(staffed + self_service, labels),
        "staffed": {"is_on": staffed_now, "hours": staffed_summary},
        "open": {"is_on": accessible_now, "hours": _summary(accessible, labels)},
        "attributes": {
            "branch": branch.strip(),
            "website": website_for(branch),
            "date": date_str,
            "weekday": labels.weekdays[now.weekday()],
            "date_label": date_label,
            "status": status,
            "staffed_summary": staffed_summary,
            "self_service_summary": self_service_summary,
            "shifts": shifts,
            "hours_markdown": hours_markdown,
        },
    }
