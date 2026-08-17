"""The reported version must track pyproject.toml, not a copy pinned in the test."""

import pathlib
import tomllib

from humandesign.utils.version import get_version

PYPROJECT = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"


def test_get_version_matches_pyproject():
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert get_version() == declared


def test_get_version_is_a_release_number():
    version = get_version()
    assert version != "0.0.0", "version lookup fell back to its sentinel"
    major, minor, patch = version.split(".")
    assert all(part.isdigit() for part in (major, minor, patch)), version
