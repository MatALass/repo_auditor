from __future__ import annotations

import json
from pathlib import Path

from scripts.build_batch_summary import build_batch_summary, render_batch_summary_markdown


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_batch_summary_aggregates_multiple_orgs(tmp_path: Path) -> None:
    batch_dir = tmp_path / "github_orgs_audit_20260308_104154"

    write_json(
        batch_dir / "OrgA" / "OrgA-github-org-audit.json",
        {
            "workspace_type": "github_org",
            "source_name": "OrgA",
            "repo_count": 2,
            "failed_count": 0,
            "worst_repo_name": "OrgA/repo1",
            "results": [
                {
                    "repo_name": "OrgA/repo1",
                    "total_score": 20,
                    "max_score": 100,
                    "level": "very weak",
                    "repo_type": "generic_project",
                    "maturity_band": "bootstrap",
                    "priority_issues": [
                        {"code": "missing_readme", "title": "README missing"},
                    ],
                    "prioritized_actions": [
                        {"code": "write_readme", "title": "Write a complete README"},
                    ],
                },
                {
                    "repo_name": "OrgA/repo2",
                    "total_score": 70,
                    "max_score": 100,
                    "level": "good",
                    "repo_type": "python_project",
                    "maturity_band": "developing",
                    "priority_issues": [],
                    "prioritized_actions": [],
                },
            ],
            "failed_repositories": [],
        },
    )

    write_json(
        batch_dir / "OrgB" / "OrgB-github-org-audit.json",
        {
            "workspace_type": "github_org",
            "source_name": "OrgB",
            "repo_count": 1,
            "failed_count": 1,
            "worst_repo_name": "OrgB/repo3",
            "results": [
                {
                    "repo_name": "OrgB/repo3",
                    "total_score": 40,
                    "max_score": 100,
                    "level": "weak",
                    "repo_type": "web_app",
                    "maturity_band": "foundation",
                    "priority_issues": [
                        {"code": "missing_readme", "title": "README missing"},
                    ],
                    "prioritized_actions": [
                        {"code": "write_readme", "title": "Write a complete README"},
                    ],
                }
            ],
            "failed_repositories": [
                {"owner": "OrgB", "repo_name": "broken-repo", "error": "404"},
            ],
        },
    )

    summary = build_batch_summary(batch_dir)

    assert summary["org_count"] == 2
    assert summary["total_repositories_analyzed"] == 3
    assert summary["total_failed_repositories"] == 1
    assert summary["organizations"][0]["org_name"] == "OrgA"
    assert summary["weakest_repositories"][0]["repo_name"] == "OrgA/repo1"
    assert summary["top_issue_hotspots"][0]["code"] == "missing_readme"
    assert summary["top_action_hotspots"][0]["code"] == "write_readme"

    markdown = render_batch_summary_markdown(summary)
    assert "# GitHub Organizations Batch Audit Summary" in markdown
    assert "## Organization ranking" in markdown
    assert "## Weakest repositories across all organizations" in markdown