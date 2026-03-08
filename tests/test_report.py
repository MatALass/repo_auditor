from __future__ import annotations

from repo_auditor.models import (
    ActionRecommendation,
    AuditIssue,
    CategoryScore,
    RepoAuditMetadata,
    RepoAuditResult,
)
from repo_auditor.report import render_org_health_block, render_repo_report_markdown


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


def test_render_org_health_block_includes_aggregated_metrics() -> None:
    summary = {
        "repo_count": 4,
        "max_score": 100,
        "average_score": 63.5,
        "median_score": 61.0,
        "best_repo_name": "acme/repo-best",
        "worst_repo_name": "acme/repo-worst",
        "portfolio_decisions": {
            "keep": 1,
            "improve": 2,
            "rebuild": 1,
            "archive": 0,
        },
        "archived_count": 1,
        "missing_topics_count": 2,
        "missing_homepage_count": 3,
        "missing_ci_count": 1,
        "top_issue_counts": [
            {"code": "missing_project_homepage", "title": "Project homepage missing", "count": 3},
            {"code": "missing_github_topics", "title": "GitHub topics missing", "count": 2},
        ],
    }

    markdown = render_org_health_block(summary)

    assert "## Organization health summary" in markdown
    assert "**Repositories considered:** 4" in markdown
    assert "**Average score:** 63.5/100" in markdown
    assert "**Median score:** 61.0/100" in markdown
    assert "**Best repository:** acme/repo-best" in markdown
    assert "**Worst repository:** acme/repo-worst" in markdown
    assert "**keep**: 1" in markdown
    assert "**improve**: 2" in markdown
    assert "**rebuild**: 1" in markdown
    assert "**archive**: 0" in markdown
    assert "**Archived repositories:** 1" in markdown
    assert "**Missing GitHub topics:** 2" in markdown
    assert "**Missing homepage:** 3" in markdown
    assert "**Missing CI:** 1" in markdown
    assert "**Project homepage missing**: 3" in markdown