from __future__ import annotations

from pathlib import Path

from repo_auditor.github_workspace import GitHubRepoFailure, GitHubWorkspaceAuditResult
from repo_auditor.models import (
    ActionRecommendation,
    AuditIssue,
    CategoryScore,
    RepoAuditResult,
)
from repo_auditor.report import (
    render_github_workspace_report,
    render_markdown_report,
    render_workspace_report,
)
from repo_auditor.workspace import WorkspaceAuditResult


def make_issue(code: str, title: str, severity: str = "high") -> AuditIssue:
    return AuditIssue(
        code=code,
        title=title,
        why_it_matters=f"Why {title} matters.",
        recommendation=f"Fix {title}.",
        severity=severity,
    )


def make_action(code: str, title: str, priority_score: int = 120) -> ActionRecommendation:
    return ActionRecommendation(
        code=code,
        title=title,
        description=f"Description for {title}.",
        rationale=f"Rationale for {title}.",
        impact="high",
        effort="medium",
        priority_score=priority_score,
        source_issue_codes=["issue_1"],
        steps=["step 1", "step 2"],
    )


def make_repo_result(
    repo_name: str = "demo-repo",
    score: int = 78,
    repo_type: str = "python_project",
    maturity_band: str = "advanced",
) -> RepoAuditResult:
    issue = make_issue("issue_1", "README missing")
    action = make_action("action_1", "Write a complete README")

    return RepoAuditResult(
        repo_name=repo_name,
        total_score=score,
        max_score=100,
        level="good",
        repo_type=repo_type,
        maturity_band=maturity_band,
        category_scores=[
            CategoryScore(
                name="Documentation",
                score=12,
                max_score=20,
                issues=[issue],
            ),
            CategoryScore(
                name="Testing",
                score=8,
                max_score=20,
                issues=[],
            ),
        ],
        priority_issues=[issue],
        prioritized_actions=[action],
    )


def test_render_markdown_report_with_content() -> None:
    result = make_repo_result()

    markdown = render_markdown_report(result)

    assert "# Repository Audit Report — demo-repo" in markdown
    assert "**Global score:** 78/100" in markdown
    assert "## Category scores" in markdown
    assert "### README missing" in markdown
    assert "## Prioritized action plan" in markdown
    assert "### 1. Write a complete README" in markdown
    assert "- Linked issues: issue_1" in markdown
    assert "## Detailed category issues" in markdown
    assert "### Testing" in markdown
    assert "- No issue detected." in markdown


def test_render_markdown_report_without_issues_or_actions() -> None:
    result = RepoAuditResult(
        repo_name="empty-repo",
        total_score=100,
        max_score=100,
        level="strong",
        repo_type="generic_project",
        maturity_band="advanced",
        category_scores=[
            CategoryScore(name="Documentation", score=20, max_score=20, issues=[]),
        ],
        priority_issues=[],
        prioritized_actions=[],
    )

    markdown = render_markdown_report(result)

    assert "# Repository Audit Report — empty-repo" in markdown
    assert "- No major issue detected." in markdown
    assert "- No action plan generated." in markdown


def test_render_workspace_report_with_results() -> None:
    repo_result = make_repo_result(repo_name="repo-one", score=42, repo_type="web_app", maturity_band="foundation")
    workspace_result = WorkspaceAuditResult(
        root_path=Path("/tmp/workspace"),
        repo_results=[repo_result],
    )

    markdown = render_workspace_report(workspace_result)

    assert "# Workspace Audit Report — workspace" in markdown
    assert "**Repositories analyzed:** 1" in markdown
    assert "## Worst repository" in markdown
    assert "- **Name:** repo-one" in markdown
    assert "## Repository ranking" in markdown
    assert "1. **repo-one** — 42/100 (good, web_app, foundation)" in markdown
    assert "## Per-repository summaries" in markdown
    assert "- Top actions:" in markdown


def test_render_workspace_report_without_repositories() -> None:
    workspace_result = WorkspaceAuditResult(
        root_path=Path("/tmp/empty-workspace"),
        repo_results=[],
    )

    markdown = render_workspace_report(workspace_result)

    assert "# Workspace Audit Report — empty-workspace" in markdown
    assert "No repositories detected in the workspace." in markdown


def test_render_github_workspace_report_with_results_and_failures() -> None:
    repo_result = make_repo_result(
        repo_name="example-org/repo-one",
        score=44,
        repo_type="cli_tool",
        maturity_band="developing",
    )
    github_result = GitHubWorkspaceAuditResult(
        source_type="github_org",
        source_name="example-org",
        repo_results=[repo_result],
        failed_repositories=[
            GitHubRepoFailure(
                owner="example-org",
                repo_name="broken-repo",
                error="404",
            )
        ],
    )

    markdown = render_github_workspace_report(github_result)

    assert "# GitHub Audit Report — github_org:example-org" in markdown
    assert "**Repositories analyzed successfully:** 1" in markdown
    assert "**Repositories failed to scan:** 1" in markdown
    assert "## Worst repository" in markdown
    assert "- **Name:** example-org/repo-one" in markdown
    assert "## Failed repositories" in markdown
    assert "- **example-org/broken-repo** — 404" in markdown


def test_render_github_workspace_report_without_repositories() -> None:
    github_result = GitHubWorkspaceAuditResult(
        source_type="github_user",
        source_name="empty-user",
        repo_results=[],
        failed_repositories=[],
    )

    markdown = render_github_workspace_report(github_result)

    assert "# GitHub Audit Report — github_user:empty-user" in markdown
    assert "No repositories found for this GitHub source." in markdown