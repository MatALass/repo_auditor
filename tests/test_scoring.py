from repo_auditor.cli import build_demo_repo
from repo_auditor.models import RepoFacts
from repo_auditor.scoring import audit_repo


def make_remote_repo(*, topics: list[str], homepage_url: str | None, is_archived: bool) -> RepoFacts:
    return RepoFacts(
        name="octo/repo-auditor",
        description="CLI tool to audit repositories and produce prioritized action plans.",
        root_files=["README.md", "pyproject.toml", ".gitignore"],
        root_dirs=["src", "tests", "docs"],
        all_paths=[
            "README.md",
            "pyproject.toml",
            ".gitignore",
            ".github/workflows/ci.yml",
            "src/main.py",
            "src/core.py",
            "tests/test_main.py",
            "docs/architecture.md",
        ],
        readme_text="""
# Repo Auditor

## Overview
Audit repositories.

## Installation
pip install -e .

## Usage
repo-auditor audit

## Structure
src tests docs

## Demo
Sample report.

## Roadmap
Doctor mode.
""",
        file_line_counts={"src/main.py": 120, "src/core.py": 100},
        manifest_files=["pyproject.toml"],
        tooling_files=["pytest.ini"],
        has_gitignore=True,
        has_license=True,
        has_env_example=True,
        code_file_count=2,
        test_file_count=1,
        readme_sections=["repo auditor", "overview", "installation", "usage", "structure", "demo", "roadmap"],
        github_topics=topics,
        homepage_url=homepage_url,
        has_ci_config=True,
        is_archived=is_archived,
        recent_push_days=10,
        repo_type="cli_tool",
    )


def test_demo_repo_scores_reasonably() -> None:
    facts = build_demo_repo()
    result = audit_repo(facts)

    assert result.repo_name == "demo-repo"
    assert result.total_score > 0
    assert result.max_score == 100
    assert result.level in {"strong", "good", "average", "weak", "very weak"}
    assert len(result.category_scores) == 7
    assert len(result.prioritized_actions) >= 1
    assert result.repo_type == "python_project"


def test_prioritized_actions_are_sorted_descending() -> None:
    facts = build_demo_repo()
    result = audit_repo(facts)

    scores = [action.priority_score for action in result.prioritized_actions]
    assert scores == sorted(scores, reverse=True)


def test_github_metadata_signals_improve_portfolio_score() -> None:
    weak = audit_repo(make_remote_repo(topics=[], homepage_url=None, is_archived=False))
    strong = audit_repo(
        make_remote_repo(
            topics=["python", "cli", "github", "auditing"],
            homepage_url="https://example.com",
            is_archived=False,
        )
    )

    weak_portfolio = next(category for category in weak.category_scores if category.name == "Portfolio value")
    strong_portfolio = next(category for category in strong.category_scores if category.name == "Portfolio value")

    assert strong_portfolio.score > weak_portfolio.score
    weak_issue_codes = {issue.code for issue in weak_portfolio.issues}
    assert "missing_github_topics" in weak_issue_codes


def test_archived_repository_gets_portfolio_issue() -> None:
    result = audit_repo(
        make_remote_repo(
            topics=["python", "cli"],
            homepage_url="https://example.com",
            is_archived=True,
        )
    )

    portfolio = next(category for category in result.category_scores if category.name == "Portfolio value")
    assert any(issue.code == "repository_archived" for issue in portfolio.issues)