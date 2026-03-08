from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.analyze_review_queue import analyze_review_queue_file


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "repo_name",
        "target_name",
        "target_kind",
        "score",
        "level",
        "repo_type_detected",
        "maturity_detected",
        "decision_detected",
        "decision_reason",
        "review_risk",
        "review_sources",
        "top_issues",
        "top_actions",
        "expected_repo_type",
        "expected_decision",
        "review_status",
        "review_comment",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_analyze_review_queue_generates_reports(tmp_path: Path) -> None:
    review_queue_path = tmp_path / "review-queue.csv"
    json_output = tmp_path / "review-analysis.json"
    md_output = tmp_path / "review-analysis.md"

    write_csv(
        review_queue_path,
        [
            {
                "repo_name": "OrgA/repo1",
                "target_name": "OrgA",
                "target_kind": "org",
                "score": "20",
                "level": "very weak",
                "repo_type_detected": "generic_project",
                "maturity_detected": "bootstrap",
                "decision_detected": "archive",
                "decision_reason": "Low score.",
                "review_risk": "medium",
                "review_sources": "weakest,archive_candidate",
                "top_issues": "Repository is empty or nearly empty",
                "top_actions": "Complete or archive the repository",
                "expected_repo_type": "generic_project",
                "expected_decision": "archive",
                "review_status": "validated",
                "review_comment": "Correct as is.",
            },
            {
                "repo_name": "UserA/repo2",
                "target_name": "UserA",
                "target_kind": "user",
                "score": "70",
                "level": "good",
                "repo_type_detected": "cli_tool",
                "maturity_detected": "advanced",
                "decision_detected": "keep",
                "decision_reason": "High enough.",
                "review_risk": "high",
                "review_sources": "strongest,showcase_candidate",
                "top_issues": "No tests detected",
                "top_actions": "Build a core test suite",
                "expected_repo_type": "cli_tool",
                "expected_decision": "improve",
                "review_status": "adjust_policy",
                "review_comment": "Keep is too optimistic.",
            },
            {
                "repo_name": "UserA/repo3",
                "target_name": "UserA",
                "target_kind": "user",
                "score": "73",
                "level": "good",
                "repo_type_detected": "config_or_infra_project",
                "maturity_detected": "advanced",
                "decision_detected": "keep",
                "decision_reason": "Strong enough.",
                "review_risk": "high",
                "review_sources": "strongest,showcase_candidate",
                "top_issues": "Dependency manifest missing",
                "top_actions": "Formalize project dependencies",
                "expected_repo_type": "python_project",
                "expected_decision": "keep",
                "review_status": "adjust_detection",
                "review_comment": "Detection is wrong, decision is fine.",
            },
            {
                "repo_name": "UserA/repo4",
                "target_name": "UserA",
                "target_kind": "user",
                "score": "35",
                "level": "very weak",
                "repo_type_detected": "web_app",
                "maturity_detected": "foundation",
                "decision_detected": "rebuild",
                "decision_reason": "Structurally weak.",
                "review_risk": "medium",
                "review_sources": "priority",
                "top_issues": "README missing",
                "top_actions": "Write a complete README",
                "expected_repo_type": "",
                "expected_decision": "",
                "review_status": "todo",
                "review_comment": "",
            },
        ],
    )

    summary = analyze_review_queue_file(review_queue_path, json_output, md_output)

    assert summary["review_queue_size"] == 4
    assert summary["reviewed_rows"] == 3
    assert summary["reviewed_rows_with_expectations"] == 3

    repo_type_analysis = summary["repo_type_analysis"]
    assert repo_type_analysis["compared_rows"] == 3
    assert repo_type_analysis["matches"] == 2
    assert repo_type_analysis["mismatches"] == 1
    assert repo_type_analysis["accuracy"] == 0.6667

    decision_analysis = summary["decision_analysis"]
    assert decision_analysis["compared_rows"] == 3
    assert decision_analysis["matches"] == 2
    assert decision_analysis["mismatches"] == 1
    assert decision_analysis["accuracy"] == 0.6667

    assert json_output.exists()
    assert md_output.exists()

    payload = json.loads(json_output.read_text(encoding="utf-8"))
    assert payload["repo_type_analysis"]["top_mismatch_patterns"][0]["pattern"] == "config_or_infra_project -> python_project"
    assert payload["decision_analysis"]["top_mismatch_patterns"][0]["pattern"] == "keep -> improve"

    markdown = md_output.read_text(encoding="utf-8")
    assert "# Review Queue Analysis Report" in markdown
    assert "## Repo type detection quality" in markdown
    assert "## Portfolio decision quality" in markdown