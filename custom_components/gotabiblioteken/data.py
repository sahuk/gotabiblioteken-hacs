"""Pure opening-hours computation.

No Home Assistant imports on purpose: this module is unit-testable on its own.
Merges duplicate branch entries, de-duplicates identical shifts, and splits
staffed from self-service hours.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

WEEKDAYS_SV = [
    "Måndag",
    "Tisdag",
    "Onsdag",
    "Torsdag",
    "Fredag",
    "Lördag",
    "Söndag",
]

MONTHS_SV = [
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
]

CLOSED = "Stängt"


def branch_names(payload: dict[str, Any]) -> list[str]:
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
    payload: dict[str, Any], branch: str, date_str: str
) -> list[dict[str, Any]]:
    """Merged, de-duplicated opening-hour intervals for a branch on a date."""
    norm = branch.strip().lower()
    entry = next(
        (d for d in payload.get("dates", []) if d.get("date") == date_str), None
    )
    if not entry:
        return []

    items: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
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
                items.append(interval)
    return items


def _summary(intervals: list[dict[str, Any]]) -> str:
    parts = [f"{i['from']}–{i['to']}" for i in intervals]
    return ", ".join(parts) if parts else CLOSED


def compute_branch_today(
    payload: dict[str, Any],
    branch: str,
    include_self_service: bool,
    now: datetime,
) -> dict[str, Any]:
    """Compute today's state and attributes for one branch."""
    date_str = now.strftime("%Y-%m-%d")
    now_hm = now.strftime("%H:%M")

    intervals = _intervals_for(payload, branch, date_str)
    staffed = [i for i in intervals if i.get("serviceType") == "Staffed"]
    self_service = [i for i in intervals if i.get("serviceType") == "SelfService"]

    staffed_summary = _summary(staffed)
    self_service_summary = _summary(self_service)

    staffed_now = any(i["from"] <= now_hm < i["to"] for i in staffed)
    self_service_now = any(i["from"] <= now_hm < i["to"] for i in self_service)
    open_now = staffed_now or (include_self_service and self_service_now)
    status = (
        "staffed" if staffed_now else ("self_service" if self_service_now else "closed")
    )

    date_label = f"{WEEKDAYS_SV[now.weekday()]} {now.day} {MONTHS_SV[now.month - 1]}"

    shifts = [
        {
            "type": "Bemannat" if i.get("serviceType") == "Staffed" else "Meröppet",
            "service_type": i.get("serviceType"),
            "info": i.get("info"),
            "from": i.get("from"),
            "to": i.get("to"),
        }
        for i in intervals
    ]

    lines = [f"**{branch.strip()}** — {date_label}"]
    if staffed_summary != CLOSED:
        lines.append(f"Bemannat: {staffed_summary}")
    if self_service_summary != CLOSED:
        lines.append(f"Meröppet: {self_service_summary}")
    if staffed_summary == CLOSED and self_service_summary == CLOSED:
        lines.append("Stängt idag")
    hours_markdown = "  \n".join(lines)

    if staffed:
        state = staffed_summary
    elif self_service:
        state = self_service_summary
    else:
        state = CLOSED

    return {
        "state": state,
        "open_now": open_now,
        "attributes": {
            "branch": branch.strip(),
            "date": date_str,
            "weekday": WEEKDAYS_SV[now.weekday()],
            "date_label": date_label,
            "open_now": open_now,
            "status": status,
            "staffed_summary": staffed_summary,
            "self_service_summary": self_service_summary,
            "shifts": shifts,
            "hours_markdown": hours_markdown,
            "include_self_service": include_self_service,
        },
    }
