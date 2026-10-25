"""Measure type coverage: the share of expressions mypy can type precisely.

Usage: uv run scripts/type_coverage.py [--fail-under PERCENT] [--per-file]

Runs mypy's any-exprs report and counts, per module group, how many expressions
have a real type rather than `Any`. Strict mypy already guarantees every
function is annotated; this catches `Any` leaking in through untyped data
(e.g. JSON payloads or `dict[str, Any]`). Fails if the shipped code (the
integration and scripts) drops below the threshold. Tests are reported but
not gated: they lean on untyped pytest/HA fixtures by design.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
GATED = ("custom_components", "scripts")
DEFAULT_FAIL_UNDER = 97.0


@dataclass
class Count:
    anys: int = 0
    exprs: int = 0

    def add(self, other: Count) -> None:
        self.anys += other.anys
        self.exprs += other.exprs

    @property
    def percent(self) -> float:
        return 100.0 if not self.exprs else 100.0 * (1 - self.anys / self.exprs)


def any_exprs_report() -> dict[str, Count]:
    """Run mypy and return {module: Count} from its any-exprs report."""
    with tempfile.TemporaryDirectory() as out:
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--any-exprs-report", out],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            sys.stdout.write(result.stdout)
            raise SystemExit("mypy failed; fix type errors before measuring")
        lines = (Path(out) / "any-exprs.txt").read_text().splitlines()

    counts: dict[str, Count] = {}
    for line in lines[2:]:  # skip header + rule
        parts = line.split()
        if len(parts) == 4 and parts[0] != "Total":
            counts[parts[0]] = Count(int(parts[1]), int(parts[2]))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--fail-under",
        type=float,
        default=DEFAULT_FAIL_UNDER,
        help=f"minimum %% for {', '.join(GATED)} (default {DEFAULT_FAIL_UNDER})",
    )
    parser.add_argument("--per-file", action="store_true", help="show each module")
    args = parser.parse_args()

    counts = any_exprs_report()
    groups: dict[str, Count] = {}
    for module, count in counts.items():
        groups.setdefault(module.split(".")[0], Count()).add(count)
        if args.per_file:
            print(f"  {module:<50} {count.percent:6.2f}%  ({count.anys} Any)")

    gated = Count()
    print(f"{'group':<20} {'typed':>8} {'Any':>6} {'exprs':>7}")
    for name, count in sorted(groups.items()):
        if name in GATED:
            gated.add(count)
        label = name if name in GATED else f"{name} (not gated)"
        print(f"{label:<20} {count.percent:7.2f}% {count.anys:>6} {count.exprs:>7}")
    print(f"\nshipped code: {gated.percent:.2f}% typed (fail under {args.fail_under}%)")

    if gated.percent < args.fail_under:
        print("Type coverage dropped. Run with --per-file to find where Any leaks in.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
