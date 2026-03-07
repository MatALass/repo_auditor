from pathlib import Path

from repo_auditor.workspace import audit_workspace, discover_repository_directories


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_good_repo(root: Path) -> None:
    write_text(
        root / "README.md",
        """
# Good Repo

## Overview
A clean repository.

## Installation
pip install -r requirements.txt

## Usage
python -m src.main

## Structure
src tests docs

## Demo
Example output included.

## Roadmap
Add more features.
""",
    )
    write_text(root / "requirements.txt", "pytest\n")
    write_text(root / ".gitignore", "__pycache__/\n")
    write_text(root / "src" / "main.py", "def run():\n    return 1\n")
    write_text(root / "src" / "utils.py", "def helper():\n    return 2\n")
    write_text(root / "tests" / "test_main.py", "def test_run():\n    assert True\n")
    write_text(root / "docs" / "architecture.md", "# Architecture\n")


def create_bad_repo(root: Path) -> None:
    write_text(root / "main.py", "print('bad repo')\n")
    write_text(root / "final.py", "print('final')\n")
    write_text(root / "notes.txt", "unfinished\n")


def test_discover_repository_directories(tmp_path: Path) -> None:
    create_good_repo(tmp_path / "repo_one")
    create_bad_repo(tmp_path / "repo_two")
    (tmp_path / "random_folder").mkdir()

    repos = discover_repository_directories(tmp_path)
    repo_names = [repo.name for repo in repos]

    assert "repo_one" in repo_names
    assert "repo_two" in repo_names
    assert "random_folder" not in repo_names


def test_audit_workspace_returns_ranked_results(tmp_path: Path) -> None:
    create_good_repo(tmp_path / "good_repo")
    create_bad_repo(tmp_path / "bad_repo")

    workspace_result = audit_workspace(tmp_path)

    assert workspace_result.repo_count == 2
    assert workspace_result.worst_repo is not None
    assert workspace_result.worst_repo.repo_name == "bad_repo"

    ranked_names = [result.repo_name for result in workspace_result.sorted_results]
    assert ranked_names[0] == "bad_repo"
    assert ranked_names[1] == "good_repo"