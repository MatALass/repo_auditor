from __future__ import annotations

from repo_auditor.github_scanner import (
    GitHubScanOptions,
    parse_github_datetime_to_age_days,
    scan_github_repository,
)


class FakeGitHubClient:
    def get_repository(self, owner: str, repo: str) -> dict:
        return {
            "full_name": f"{owner}/{repo}",
            "description": "Remote repository used for testing.",
            "default_branch": "main",
            "pushed_at": "2026-03-01T10:00:00Z",
        }

    def get_repository_tree_from_default_branch(self, owner: str, repo: str) -> dict:
        return {
            "tree": [
                {"path": "README.md", "type": "blob", "size": 1200},
                {"path": "pyproject.toml", "type": "blob", "size": 300},
                {"path": ".gitignore", "type": "blob", "size": 80},
                {"path": "src/main.py", "type": "blob", "size": 180},
                {"path": "src/utils.py", "type": "blob", "size": 120},
                {"path": "tests/test_main.py", "type": "blob", "size": 90},
                {"path": "docs/architecture.md", "type": "blob", "size": 200},
            ]
        }

    def get_readme(self, owner: str, repo: str) -> str | None:
        return """
# Sample Remote Repo

## Overview
A remote repo.

## Installation
pip install -e .

## Usage
python -m src.main

## Structure
src tests docs

## Demo
Example output.

## Roadmap
More features.
"""

    def get_file_text(self, owner: str, repo: str, path: str) -> str | None:
        payloads = {
            "src/main.py": "def main():\n    return 1\n",
            "src/utils.py": "def helper():\n    return 2\n",
            "tests/test_main.py": "def test_main():\n    assert True\n",
        }
        return payloads.get(path)


class FakeEmptyGitHubClient:
    def get_repository(self, owner: str, repo: str) -> dict:
        return {
            "full_name": f"{owner}/{repo}",
            "description": "",
            "default_branch": None,
            "pushed_at": "2026-03-01T10:00:00Z",
        }

    def get_repository_tree_from_default_branch(self, owner: str, repo: str) -> dict:
        return {"tree": []}

    def get_readme(self, owner: str, repo: str) -> str | None:
        return None

    def get_file_text(self, owner: str, repo: str, path: str) -> str | None:
        return None


def test_parse_github_datetime_to_age_days() -> None:
    age = parse_github_datetime_to_age_days("2026-03-01T10:00:00Z")
    assert age is not None
    assert age >= 0


def test_scan_github_repository_builds_repofacts() -> None:
    client = FakeGitHubClient()

    facts = scan_github_repository(
        "example-owner",
        "example-repo",
        client=client,
        options=GitHubScanOptions(max_code_files_for_line_counts=10),
    )

    assert facts.name == "example-owner/example-repo"
    assert facts.readme_text is not None
    assert facts.has_gitignore is True
    assert facts.code_file_count >= 2
    assert facts.test_file_count >= 1
    assert "pyproject.toml" in facts.manifest_files
    assert "src" in facts.root_dirs
    assert "tests" in facts.root_dirs


def test_scan_github_repository_handles_empty_repo() -> None:
    client = FakeEmptyGitHubClient()

    facts = scan_github_repository(
        "example-owner",
        "empty-repo",
        client=client,
        options=GitHubScanOptions(max_code_files_for_line_counts=10),
    )

    assert facts.name == "example-owner/empty-repo"
    assert facts.readme_text is None
    assert facts.code_file_count == 0
    assert facts.test_file_count == 0
    assert facts.root_dirs == []
    assert facts.root_files == []
    assert facts.manifest_files == []