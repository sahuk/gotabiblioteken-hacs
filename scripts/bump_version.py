"""Bump the integration version in manifest.json and roll CHANGELOG.md.

Usage: python scripts/bump_version.py <major|minor|patch|X.Y.Z> [--dry-run]

Edits files only; prints the git/gh commands to finish the release.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "custom_components" / "gotabiblioteken" / "manifest.json"
CHANGELOG = ROOT / "CHANGELOG.md"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
UNRELEASED = "## [Unreleased]"


def next_version(current: str, bump: str) -> str:
    match = SEMVER.match(current)
    if not match:
        raise SystemExit(f"manifest version {current!r} is not X.Y.Z")
    major, minor, patch = map(int, match.groups())
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if not SEMVER.match(bump):
        raise SystemExit(f"{bump!r} is not major/minor/patch or X.Y.Z")
    return bump


def roll_changelog(text: str, version: str, today: date) -> str:
    if UNRELEASED not in text:
        raise SystemExit(f"CHANGELOG.md has no '{UNRELEASED}' section")
    if f"## [{version}]" in text:
        raise SystemExit(f"CHANGELOG.md already has an entry for {version}")
    body = text.split(UNRELEASED, 1)[1].split("\n## [", 1)[0]
    if not body.strip():
        raise SystemExit("the Unreleased section is empty; describe the changes")
    return text.replace(
        UNRELEASED, f"{UNRELEASED}\n\n## [{version}] - {today.isoformat()}", 1
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bump", help="major, minor, patch, or an explicit X.Y.Z")
    parser.add_argument("--dry-run", action="store_true", help="print, don't write")
    args = parser.parse_args()

    manifest_text = MANIFEST.read_text(encoding="utf-8")
    current = json.loads(manifest_text)["version"]
    version = next_version(current, args.bump)
    if version == current:
        raise SystemExit(f"version is already {current}")
    # Replace only the version string, keeping the file's own formatting.
    manifest_text, count = re.subn(
        r'("version"\s*:\s*")[^"]*(")', rf"\g<1>{version}\g<2>", manifest_text
    )
    if count != 1:
        raise SystemExit("manifest.json must have exactly one version key")
    changelog = roll_changelog(
        CHANGELOG.read_text(encoding="utf-8"), version, date.today()
    )

    print(f"{current} -> {version}")
    if args.dry_run:
        print("(dry run, nothing written)")
        return 0

    MANIFEST.write_text(manifest_text, encoding="utf-8")
    CHANGELOG.write_text(changelog, encoding="utf-8")
    print(
        "\nNext:\n"
        f"  git commit -am 'Release v{version}'\n"
        f"  git tag v{version}\n"
        "  git push && git push --tags\n"
        f"  gh release create v{version} --generate-notes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
