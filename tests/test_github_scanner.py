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


class FakeGameGitHubClient:
    def get_repository(self, owner: str, repo: str) -> dict:
        return {
            "full_name": f"{owner}/{repo}",
            "description": "A simple Tetris game project.",
            "default_branch": "main",
            "pushed_at": "2026-03-01T10:00:00Z",
        }

    def get_repository_tree_from_default_branch(self, owner: str, repo: str) -> dict:
        return {
            "tree": [
                {"path": "README.md", "type": "blob", "size": 500},
                {"path": "main.py", "type": "blob", "size": 250},
                {"path": "board.py", "type": "blob", "size": 220},
                {"path": "pieces.py", "type": "blob", "size": 210},
            ]
        }

    def get_readme(self, owner: str, repo: str) -> str | None:
        return """
# Tetris Game

A small arcade game built in Python.
"""

    def get_file_text(self, owner: str, repo: str, path: str) -> str | None:
        payloads = {
            "main.py": "def run_game():\n    pass\n",
            "board.py": "class Board:\n    pass\n",
            "pieces.py": "class Piece:\n    pass\n",
        }
        return payloads.get(path)


class FakeWebGitHubClient:
    def get_repository(self, owner: str, repo: str) -> dict:
        return {
            "full_name": f"{owner}/{repo}",
            "description": "Personal portfolio website.",
            "default_branch": "main",
            "pushed_at": "2026-03-01T10:00:00Z",
        }

    def get_repository_tree_from_default_branch(self, owner: str, repo: str) -> dict:
        return {
            "tree": [
                {"path": "README.md", "type": "blob", "size": 400},
                {"path": "index.html", "type": "blob", "size": 500},
                {"path": "styles.css", "type": "blob", "size": 300},
                {"path": "app.js", "type": "blob", "size": 250},
            ]
        }

    def get_readme(self, owner: str, repo: str) -> str | None:
        return """
# Portfolio Website

A personal website and portfolio built with HTML, CSS and JavaScript.
"""

    def get_file_text(self, owner: str, repo: str, path: str) -> str | None:
        payloads = {
            "app.js": "function init() { return true; }\n",
        }
        return payloads.get(path)


class FakePythonAppGitHubClient:
    def get_repository(self, owner: str, repo: str) -> dict:
        return {
            "full_name": f"{owner}/{repo}",
            "description": "ECTS grade engine for academic analytics.",
            "default_branch": "main",
            "pushed_at": "2026-03-01T10:00:00Z",
        }

    def get_repository_tree_from_default_branch(self, owner: str, repo: str) -> dict:
        return {
            "tree": [
                {"path": "README.md", "type": "blob", "size": 700},
                {"path": "requirements.txt", "type": "blob", "size": 120},
                {"path": "grade_engine.py", "type": "blob", "size": 320},
                {"path": "rules.py", "type": "blob", "size": 210},
                {"path": "docs/usage.md", "type": "blob", "size": 180},
            ]
        }

    def get_readme(self, owner: str, repo: str) -> str | None:
        return """
# ECTS Grade Engine

Python engine for academic grade analytics and workload calculations.
"""

    def get_file_text(self, owner: str, repo: str, path: str) -> str | None:
        payloads = {
            "grade_engine.py": "def compute_grade():\n    return 1\n",
            "rules.py": "RULES = {}\n",
        }
        return payloads.get(path)


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


def test_scan_github_repository_detects_game_project() -> None:
    client = FakeGameGitHubClient()

    facts = scan_github_repository(
        "example-owner",
        "Tetris_Game",
        client=client,
        options=GitHubScanOptions(max_code_files_for_line_counts=10),
    )

    assert facts.repo_type == "game_project"


def test_scan_github_repository_detects_web_app() -> None:
    client = FakeWebGitHubClient()

    facts = scan_github_repository(
        "example-owner",
        "Atelier_Alassoeur_Website",
        client=client,
        options=GitHubScanOptions(max_code_files_for_line_counts=10),
    )

    assert facts.repo_type == "web_app"


def test_scan_github_repository_detects_python_project_from_engine_signals() -> None:
    client = FakePythonAppGitHubClient()

    facts = scan_github_repository(
        "example-owner",
        "ects-grade-engine",
        client=client,
        options=GitHubScanOptions(max_code_files_for_line_counts=10),
    )

    assert facts.repo_type == "python_project"