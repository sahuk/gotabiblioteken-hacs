"""Repo-shape checks for HACS distribution and hassfest manifest rules.

These are the file-level rules that `hacs/action` and `hassfest` enforce in CI,
duplicated here so a plain `pytest` run catches them before a push.
"""

import json
from pathlib import Path
import re
from typing import Any

from awesomeversion import AwesomeVersion
from PIL import Image
import pytest

from homeassistant.const import __version__ as HA_VERSION

ROOT = Path(__file__).resolve().parent.parent
COMPONENTS = ROOT / "custom_components"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
REQUIRED_MANIFEST_KEYS = {
    "domain",
    "name",
    "codeowners",
    "config_flow",
    "documentation",
    "integration_type",
    "iot_class",
    "issue_tracker",
    "requirements",
    "version",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _key_paths(obj: Any, prefix: str = "") -> set[str]:
    if not isinstance(obj, dict):
        return {prefix}
    paths: set[str] = set()
    for key, value in obj.items():
        paths |= _key_paths(value, f"{prefix}.{key}" if prefix else key)
    return paths


@pytest.fixture(scope="module")
def integration_dir() -> Path:
    dirs = [p for p in COMPONENTS.iterdir() if p.is_dir() and p.name != "__pycache__"]
    assert len(dirs) == 1, f"HACS expects exactly one integration, found {dirs}"
    return dirs[0]


@pytest.fixture(scope="module")
def manifest(integration_dir: Path) -> dict[str, Any]:
    data: dict[str, Any] = _load(integration_dir / "manifest.json")
    return data


@pytest.fixture(scope="module")
def hacs() -> dict[str, Any]:
    data: dict[str, Any] = _load(ROOT / "hacs.json")
    return data


def test_domain_matches_directory(
    integration_dir: Path, manifest: dict[str, Any]
) -> None:
    assert manifest["domain"] == integration_dir.name


def test_manifest_required_keys(manifest: dict[str, Any]) -> None:
    missing = REQUIRED_MANIFEST_KEYS - manifest.keys()
    assert not missing, f"manifest.json is missing {sorted(missing)}"


def test_manifest_key_order(manifest: dict[str, Any]) -> None:
    keys = list(manifest)
    assert keys[:2] == ["domain", "name"], "hassfest wants domain, name first"
    assert keys[2:] == sorted(keys[2:]), "hassfest wants remaining keys sorted"


def test_manifest_version_is_semver(manifest: dict[str, Any]) -> None:
    assert SEMVER.match(manifest["version"]), manifest["version"]


def test_manifest_urls_point_at_same_repo(manifest: dict[str, Any]) -> None:
    docs = manifest["documentation"].rstrip("/")
    assert docs.startswith("https://github.com/")
    assert manifest["issue_tracker"] == f"{docs}/issues"


def test_hacs_json(hacs: dict[str, Any], manifest: dict[str, Any]) -> None:
    assert hacs["name"]
    assert hacs["content_in_root"] is False
    if hacs.get("zip_release"):
        assert hacs["filename"] == f"{manifest['domain']}.zip"


def test_hacs_min_ha_version_is_tested(hacs: dict[str, Any]) -> None:
    """The HA version the tests run on must satisfy the declared minimum."""
    assert AwesomeVersion(hacs["homeassistant"]) <= AwesomeVersion(HA_VERSION)


def test_translations_match_strings(integration_dir: Path) -> None:
    expected = _key_paths(_load(integration_dir / "strings.json"))
    for path in sorted((integration_dir / "translations").glob("*.json")):
        assert _key_paths(_load(path)) == expected, f"{path.name} keys drift"
    assert _load(integration_dir / "translations" / "en.json") == _load(
        integration_dir / "strings.json"
    ), "en.json must be a copy of strings.json"


def test_changelog_has_current_version(manifest: dict[str, Any]) -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    heading = f"## [{manifest['version']}]"
    assert heading in changelog, f"CHANGELOG.md has no '{heading}' entry"


def test_brand_icon(integration_dir: Path) -> None:
    """HA 2026.3+ and HACS read brand images from the integration's brand/ dir."""
    with Image.open(integration_dir / "brand" / "icon.png") as icon:
        assert icon.format == "PNG"
        assert icon.size == (256, 256)
