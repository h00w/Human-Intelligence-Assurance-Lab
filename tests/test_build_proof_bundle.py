from scripts.build_proof_bundle import dependency_records


def test_dependency_records_include_pyproject_dependencies():
    records = dependency_records()
    pyproject_records = {
        (record["name"], record["version"], record["scope"])
        for record in records
        if record["scope"] == "project.dependencies"
    }

    assert ("pydantic", ">=2.7,<3", "project.dependencies") in pyproject_records
    assert ("PyYAML", ">=6.0,<7", "project.dependencies") in pyproject_records
    assert ("pandas", ">=2.2,<3", "project.dependencies") in pyproject_records
    assert ("streamlit", ">=1.37,<2", "project.dependencies") in pyproject_records
    assert (
        "huggingface_hub",
        ">=1.0,<2",
        "project.dependencies",
    ) in pyproject_records
