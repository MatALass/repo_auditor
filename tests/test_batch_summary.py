from __future__ import annotations

import json
from pathlib import Path

from scripts.build_batch_summary import build_batch_summary, render_batch_summary_markdown


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_batch_summary_aggregates_multiple_targets(tmp_path: Path) -> None:
    batch_dir = tmp_path / "github_targets_audit_20260308_104154"

    write_json(
        batch_dir / "OrgA" / "OrgA-github-org-audit.json",
        {
            "workspace_type": "github_org",
            "source_name": "OrgA",
            "repo_count": 2,
            "failed_count": 0,
            "results": [
                {
                    "repo_name": "OrgA/repo1",
                    "total_score": 20,
                    "max_score": 100,
                    "level": "very weak",
                    "repo_type": "generic_project",
                    "maturity_band": "bootstrap",
                    "priority_issues": [
                        {"code": "repo_empty", "title": "Repository is empty or nearly empty"},
                        {"code": "missing_readme", "title": "README missing"},
                    ],
                    "prioritized_actions": [
                        {"code": "archive_repo", "title": "Complete or archive the repository"},
                        {"code": "write_readme", "title": "Write a complete README"},
                    ],
                },
                {
                    "repo_name": "OrgA/repo2",
                    "total_score": 78,
                    "max_score": 100,
                    "level": "good",
                    "repo_type": "python_project",
                    "maturity_band": "advanced",
                    "priority_issues": [],
                    "prioritized_actions": [],
                },
            ],
            "failed_repositories": [],
        },
    )

    write_json(
        batch_dir / "UserA" / "UserA-github-user-audit.json",
        {
            "workspace_type": "github_user",
            "source_name": "UserA",
            "repo_count": 2,
            "failed_count": 1,
            "results": [
                {
                    "repo_name": "UserA/repo3",
                    "total_score": 38,
                    "max_score": 100,
                    "level": "very weak",
                    "repo_type": "cli_tool",
                    "maturity_band": "foundation",
                    "priority_issues": [
                        {"code": "monolith", "title": "Monolithic structure detected"},
                    ],
                    "prioritized_actions": [
                        {"code": "separate_concerns", "title": "Improve separation of concerns"},
                    ],
                },
                {
                    "repo_name": "UserA/repo4",
                    "total_score": 55,
                    "max_score": 100,
                    "level": "average",
                    "repo_type": "web_app",
                    "maturity_band": "developing",
                    "priority_issues": [
                        {"code": "missing_gitignore", "title": ".gitignore missing"},
                        {"code": "missing_usage", "title": "Usage instructions missing"},
                    ],
                    "prioritized_actions": [
                        {"code": "add_gitignore", "title": "Add a proper .gitignore"},
                        {"code": "document_usage", "title": "Document execution and usage"},
                    ],
                },
            ],
            "failed_repositories": [
                {"owner": "UserA", "repo_name": "broken-repo", "error": "404"},
            ],
        },
    )

    summary = build_batch_summary(batch_dir)

    assert summary["batch_type"] == "github_targets_audit"
    assert summary["target_count"] == 2
    assert summary["total_repositories_analyzed"] == 4
    assert summary["total_failed_repositories"] == 1

    assert summary["targets"][0]["target_name"] == "OrgA"
    assert summary["targets"][0]["target_kind"] == "org"
    assert summary["targets"][1]["target_kind"] == "user"

    assert summary["weakest_repositories"][0]["repo_name"] == "OrgA/repo1"
    assert summary["weakest_repositories"][0]["decision"] == "archive"

    decisions = summary["decision_distribution"]
    assert decisions["archive"] >= 1
    assert decisions["rebuild"] >= 1
    assert decisions["improve"] >= 1
    assert decisions["keep"] >= 1

    remediation = summary["global_remediation_priorities"]
    assert "quick_wins" in remediation
    assert "medium_refactors" in remediation
    assert "heavy_refactors" in remediation

    markdown = render_batch_summary_markdown(summary)
    assert "# GitHub Targets Batch Audit Summary" in markdown
    assert "## Target ranking" in markdown
    assert "## Portfolio decision distribution" in markdown
    assert "## Priority repositories to treat next" in markdown
    assert "## Archive candidates" in markdown
    assert "## Showcase candidates to protect and strengthen" in markdown