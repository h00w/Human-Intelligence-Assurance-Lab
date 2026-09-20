import tomllib
from packaging.requirements import Requirement

from scripts import build_proof_bundle
from scripts.build_proof_bundle import dependency_records


def test_dependency_records_include_pyproject_dependencies():
    records = dependency_records()
    pyproject_records = [record for record in records if record["scope"] == "project.dependencies"]
    pyproject = tomllib.loads(
        (build_proof_bundle.ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    expected_names = set()
    for dep in pyproject["project"]["dependencies"]:
        expected_names.add(Requirement(dep).name)

    observed_names = {record["name"] for record in pyproject_records}
    assert expected_names <= observed_names
    assert all(record["version"] for record in pyproject_records)
