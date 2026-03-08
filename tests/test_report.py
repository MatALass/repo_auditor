from __future__ import annotations

from repo_auditor.models import (
    ActionRecommendation,
    AuditIssue,
    CategoryScore,
    RepoAuditMetadata,
    RepoAuditResult,
)
from repo_auditor.report import render_repo_report_markdown


def test_render_repo_report_markdown_includes_metadata_block() -> None:
    result = RepoAuditResult(
        repo_name="octo/repo-auditor",
        total_score=84,
        max_score=100,
        level="good",
        repo_type="cli_tool",
        maturity_band="advanced",
        category_scores=[
            CategoryScore(
                name="Documentation",
                score=17,
                max_score=20,
                issues=[
                    AuditIssue(
                        code="readme_missing_key_sections",
                        title="README missing key sections",
                        why_it_matters="Weak onboarding.",
                        recommendation="Add missing sections.",
                        severity="medium",
                    )
                ],
            )
        ],
        priority_issues=[
            AuditIssue(
                code="missing_project_homepage",
                title="Project homepage missing",
                why_it_matters="Live link helps review.",
                recommendation="Add homepage.",
                severity="low",
            )
        ],
        prioritized_actions=[
            ActionRecommendation(
                code="improve_readme",
                title="Improve README",
                description="Expand README structure.",
                rationale="Better portfolio clarity.",
                steps=["Add usage", "Add roadmap"],
                impact="high",
                effort="medium",
                priority_score=120,
                source_issue_codes=["readme_missing_key_sections"],
            )
        ],
        metadata=RepoAuditMetadata(
            github_topics=["python", "cli", "auditing"],
            homepage_url="https://example.com/repo-auditor",
            has_ci_config=True,
            is_archived=False,
            readme_sections=["overview", "installation", "usage", "demo"],
        ),
    )

    markdown = render_repo_report_markdown(result)

    assert "# Repository Audit Report — octo/repo-auditor" in markdown
    assert "## Repository metadata" in markdown
    assert "**GitHub topics:** python, cli, auditing" in markdown
    assert "**Homepage:** https://example.com/repo-auditor" in markdown
    assert "**CI detected:** yes" in markdown
    assert "**Archived:** no" in markdown
    assert "**README sections detected:** overview, installation, usage, demo" in markdown
    assert "## Category scores" in markdown
    assert "## Top priority issues" in markdown
    assert "## Prioritized action plan" in markdown