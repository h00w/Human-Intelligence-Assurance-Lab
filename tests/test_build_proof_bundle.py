import re

import tomllib

from scripts import build_proof_bundle
from scripts.build_proof_bundle import dependency_records


def test_dependency_records_include_pyproject_dependencies():
    records = dependency_records()
    pyproject_records = {
        (record["name"], record["version"], record["scope"])
        for record in records
        if record["scope"] == "project.dependencies"
    }
    pyproject = tomllib.loads(
        (build_proof_bundle.ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    expected_records = set()
    for dep in pyproject["project"]["dependencies"]:
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*(.*)$", dep)
        assert match is not None
        name, version = match.groups()
        expected_records.add((name, version.strip() or "unspecified", "project.dependencies"))

    assert expected_records <= pyproject_records
