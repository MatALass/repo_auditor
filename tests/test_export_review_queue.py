from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.export_review_queue import export_review_queue


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_export_review_queue_creates_csv_with_expected_columns(tmp_path: Path) -> None:
    summary_path = tmp_path / "batch-summary.json"
    output_path = tmp_path / "review-queue.csv"

    payload = {
        "weakest_repositories": [
            {
                "repo_name": "OrgA/repo1",
                "target_name": "OrgA",
                "target_kind": "org",
                "total_score": 18,
                "level": "very weak",
                "repo_type": "generic_project",
                "maturity_band": "bootstrap",
                "decision": "archive",
                "decision_reason": "Low score and weak repository.",
                "priority_issues": [
                    {"title": "Repository is empty or nearly empty"},
                    {"title": "README missing"},
                ],
                "prioritized_actions": [
                    {"title": "Complete or archive the repository"},
                    {"title": "Write a complete README"},
                ],
            }
        ],
        "strongest_repositories": [
            {
                "repo_name": "UserA/repo2",
                "target_name": "UserA",
                "target_kind": "user",
                "total_score": 82,
                "level": "strong",
                "repo_type": "cli_tool",
                "maturity_band": "advanced",
                "decision": "keep",
                "decision_reason": "High score.",
                "priority_issues": [],
                "prioritized_actions": [],
            }
        ],
        "portfolio_decisions": {
            "priority_repositories": [
                {
                    "repo_name": "UserA/repo3",
                    "target_name": "UserA",
                    "target_kind": "user",
                    "total_score": 41,
                    "level": "weak",
                    "repo_type": "web_app",
                    "maturity_band": "developing",
                    "decision": "improve",
                    "decision_reason": "Recoverable repository.",
                    "priority_issues": [{"title": "Usage instructions missing"}],
                    "prioritized_actions": [{"title": "Document execution and usage"}],
                }
            ],
            "archive_candidates": [],
            "showcase_candidates": [],
        },
    }

    write_json(summary_path, payload)
    exported_path = export_review_queue(summary_path, output_path)

    assert exported_path.exists()

    with exported_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert len(rows) == 3
    assert rows[0]["repo_name"] == "OrgA/repo1"
    assert rows[0]["repo_type_detected"] == "generic_project"
    assert rows[0]["decision_detected"] == "archive"
    assert rows[0]["expected_repo_type"] == ""
    assert rows[0]["expected_decision"] == ""
    assert rows[0]["review_status"] == "todo"

    repo_names = {row["repo_name"] for row in rows}
    assert "UserA/repo2" in repo_names
    assert "UserA/repo3" in repo_names