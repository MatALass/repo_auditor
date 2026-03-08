from repo_auditor.local_scanner import detect_repo_type


def test_detects_data_science_project() -> None:
    repo_type = detect_repo_type(
        all_paths=[
            "README.md",
            "notebooks/exploration.ipynb",
            "src/features.py",
            "data/raw/sample.csv",
            "requirements.txt",
        ],
        file_names=[
            "README.md",
            "exploration.ipynb",
            "features.py",
            "sample.csv",
            "requirements.txt",
        ],
    )

    assert repo_type == "data_science_project"


def test_detects_ml_project() -> None:
    repo_type = detect_repo_type(
        all_paths=[
            "README.md",
            "src/train.py",
            "src/model.py",
            "models/baseline.pkl",
            "requirements.txt",
        ],
        file_names=[
            "README.md",
            "train.py",
            "model.py",
            "baseline.pkl",
            "requirements.txt",
            "scikit-learn",
        ],
    )

    assert repo_type == "ml_project"


def test_detects_cli_tool() -> None:
    repo_type = detect_repo_type(
        all_paths=[
            "README.md",
            "src/repo_auditor/cli.py",
            "src/repo_auditor/__main__.py",
            "pyproject.toml",
        ],
        file_names=[
            "README.md",
            "cli.py",
            "__main__.py",
            "pyproject.toml",
        ],
    )

    assert repo_type == "cli_tool"


def test_detects_documentation_project() -> None:
    repo_type = detect_repo_type(
        all_paths=[
            "README.md",
            "docs/index.md",
            "docs/architecture.md",
            "docs/usage.md",
            "mkdocs.yml",
        ],
        file_names=[
            "README.md",
            "index.md",
            "architecture.md",
            "usage.md",
            "mkdocs.yml",
        ],
    )

    assert repo_type == "documentation_project"


def test_detects_config_or_infra_project() -> None:
    repo_type = detect_repo_type(
        all_paths=[
            "README.md",
            "terraform/main.tf",
            "terraform/variables.tf",
            ".github/workflows/deploy.yml",
        ],
        file_names=[
            "README.md",
            "main.tf",
            "variables.tf",
            "deploy.yml",
        ],
    )

    assert repo_type == "config_or_infra_project"