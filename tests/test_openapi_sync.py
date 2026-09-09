"""openapi.yaml is a build artefact and must match the running application.

It drifted twice unnoticed: the file still declared 3.9.0 while the API served
3.9.1, and prod reported 3.9.1 while the repository was on 3.9.2. Nothing in CI
compared them, so the only detection was someone happening to look.

The check reuses the generator own ``render()``, so a formatting change in
``scripts/gen_openapi.py`` can never make the test disagree with the file it
guards.
"""

import importlib.util
import pathlib
import sys

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML is a dev dependency")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi.yaml"

_spec_file = importlib.util.spec_from_file_location(
    "_gen_openapi", ROOT / "scripts" / "gen_openapi.py"
)
gen_openapi = importlib.util.module_from_spec(_spec_file)
sys.modules["_gen_openapi"] = gen_openapi
_spec_file.loader.exec_module(gen_openapi)


def test_openapi_yaml_matches_the_application():
    expected = gen_openapi.render(gen_openapi.build_spec())
    actual = SPEC.read_text(encoding="utf-8")
    assert actual == expected, (
        "openapi.yaml is stale. Regenerate it and commit the result:\n"
        "    PYTHONPATH=src python scripts/gen_openapi.py"
    )


def test_openapi_version_matches_pyproject():
    from humandesign.utils.version import get_version

    declared = yaml.safe_load(SPEC.read_text(encoding="utf-8"))["info"]["version"]
    assert declared == get_version(), (
        "openapi.yaml declares %r while the project version is %r"
        % (declared, get_version())
    )
