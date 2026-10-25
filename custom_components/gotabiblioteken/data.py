"""Pure opening-hours computation.

No Home Assistant imports on purpose: this module is unit-testable on its own.
Generated text is Swedish or English (`labels_for`); entity names are not set
here but come from the translation files.
Merges duplicate branch entries, de-duplicates identical shifts, and splits
staffed from self-service hours.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypedDict

from .websites import website_for

# Shape of the Axiell payload. Every key is optional: the API is external,
# so the code reads it with .get() and treats missing data as closed.
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
    """Generated text (states, attributes) in one language."""

    closed: str
    closed_today: str
    staffed: str
    self_service: str
    weekdays: tuple[str, ...]
    months: tuple[str, ...]


LABELS_SV = Labels(
    closed="Stängt",
    closed_today="Stängt idag",
    staffed="Bemannat",
    self_service="Meröppet",
    weekdays=("Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"),
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

LABELS_EN = Labels(
    closed="Closed",
    closed_today="Closed today",
    staffed="Staffed",
    self_service="Self-service",
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


def labels_for(language: str) -> Labels:
    """Swedish for a Swedish Home Assistant, English for everything else."""
    return LABELS_SV if language.lower().split("-")[0] == "sv" else LABELS_EN


def branch_names(payload: ApiPayload) -> list[str]:
    """Return the sorted, de-duplicated list of branch display names."""
    names: list[str] = []
    seen: set[str] = set()
    for day in payload.get("dates", []):
        for branch in day.get("branches", []):
            name = (branch.get("branchName") or "").strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                names.append(name)
    return sorted(names, key=str.lower)


def _intervals_for(
    payload: ApiPayload, branch: str, date_str: str
) -> list[ApiInterval]:
    """Merged, de-duplicated opening-hour intervals for a branch on a date."""
    norm = branch.strip().lower()
    entry = next(
        (d for d in payload.get("dates", []) if d.get("date") == date_str), None
    )
    if not entry:
        return []

    items: list[ApiInterval] = []
    seen: set[tuple[str | None, ...]] = set()
    for branch_entry in entry.get("branches", []):
        if (branch_entry.get("branchName") or "").strip().lower() != norm:
            continue
        for interval in branch_entry.get("openingHours", []):
            key = (
                interval.get("serviceType"),
                interval.get("from"),
                interval.get("to"),
                interval.get("info"),
            )
            if key not in seen:
                seen.add(key)
                if interval.get("to") == "00:00":
                    # Ends at midnight; keep "HH:MM" string comparisons valid.
                    interval = {**interval, "to": "24:00"}
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
    return ", ".join(parts) if parts else labels.closed


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

    staffed_summary = _summary(staffed, labels)
    self_service_summary = _summary(self_service, labels)

    staffed_now = _is_on(staffed, now_hm)
    accessible_now = _is_on(accessible, now_hm)
    status = (
        "staffed" if staffed_now else ("self_service" if accessible_now else "closed")
    )

    weekday = labels.weekdays[now.weekday()]
    date_label = f"{weekday} {now.day} {labels.months[now.month - 1]}"

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

    lines = [f"**{branch.strip()}** — {date_label}"]
    if staffed:
        lines.append(f"{labels.staffed}: {staffed_summary}")
    if self_service:
        lines.append(f"{labels.self_service}: {self_service_summary}")
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
            "weekday": weekday,
            "date_label": date_label,
            "status": status,
            "staffed_summary": staffed_summary,
            "self_service_summary": self_service_summary,
            "shifts": shifts,
            "hours_markdown": hours_markdown,
        },
    }
