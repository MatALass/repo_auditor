from __future__ import annotations

import json

from repo_auditor.models import (
    ActionRecommendation,
    AuditIssue,
    CategoryScore,
    RepoAuditMetadata,
    RepoAuditResult,
)
from repo_auditor.serialization import repo_audit_result_to_dict


def test_repo_audit_result_to_dict_includes_metadata() -> None:
    result = RepoAuditResult(
        repo_name="octo/repo-auditor",
        total_score=82,
        max_score=100,
        level="good",
        repo_type="cli_tool",
        maturity_band="advanced",
        category_scores=[
            CategoryScore(
                name="Documentation",
                score=18,
                max_score=20,
                issues=[
                    AuditIssue(
                        code="missing_project_homepage",
                        title="Project homepage missing",
                        why_it_matters="Demo link is useful.",
                        recommendation="Add homepage.",
                        severity="low",
                    )
                ],
            )
        ],
        priority_issues=[],
        prioritized_actions=[
            ActionRecommendation(
                code="add_homepage",
                title="Add homepage",
                description="Add a live link or docs URL.",
                rationale="Improves project evaluation.",
                steps=["Add homepage in GitHub repo settings"],
                impact="medium",
                effort="low",
                priority_score=90,
                source_issue_codes=["missing_project_homepage"],
            )
        ],
        metadata=RepoAuditMetadata(
            github_topics=["python", "cli", "github", "auditing"],
            homepage_url="https://example.com",
            has_ci_config=True,
            is_archived=False,
            readme_sections=["overview", "installation", "usage", "structure", "demo", "roadmap"],
        ),
    )

    payload = repo_audit_result_to_dict(result)

    assert payload["repo_name"] == "octo/repo-auditor"
    assert payload["metadata"]["github_topics"] == ["python", "cli", "github", "auditing"]
    assert payload["metadata"]["homepage_url"] == "https://example.com"
    assert payload["metadata"]["has_ci_config"] is True
    assert payload["metadata"]["is_archived"] is False
    assert payload["metadata"]["readme_sections"] == [
        "overview",
        "installation",
        "usage",
        "structure",
        "demo",
        "roadmap",
    ]
    json.dumps(payload)