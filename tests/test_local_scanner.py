from pathlib import Path

from repo_auditor.local_scanner import scan_local_repository


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_local_repository_detects_core_signals(tmp_path: Path) -> None:
    write_text(
        tmp_path / "README.md",
        """
# Sample Repo

## Overview
A sample repo.

## Installation
pip install -r requirements.txt

## Usage
python -m src.main

## Demo
Screenshot available.
""",
    )
    write_text(tmp_path / "requirements.txt", "pytest\n")
    write_text(tmp_path / ".gitignore", "__pycache__/\n")
    write_text(tmp_path / ".env.example", "API_KEY=\n")
    write_text(tmp_path / "src" / "main.py", "print('hello')\n")
    write_text(tmp_path / "tests" / "test_main.py", "def test_ok():\n    assert True\n")
    write_text(tmp_path / "docs" / "architecture.md", "# Architecture\n")

    facts = scan_local_repository(tmp_path, description="Sample local repository for testing.")

    assert facts.name == tmp_path.name
    assert facts.readme_text is not None
    assert facts.has_gitignore is True
    assert facts.has_env_example is True
    assert facts.code_file_count >= 1
    assert facts.test_file_count >= 1
    assert "requirements.txt" in facts.manifest_files
    assert "src" in facts.root_dirs
    assert "tests" in facts.root_dirs


def test_scan_local_repository_handles_missing_readme(tmp_path: Path) -> None:
    write_text(tmp_path / "src" / "main.py", "print('x')\n")

    facts = scan_local_repository(tmp_path)

    assert facts.readme_text is None
    assert facts.code_file_count == 1