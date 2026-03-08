from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_MAX_WEAKEST = 20
DEFAULT_MAX_STRONGEST = 10
DEFAULT_MAX_PRIORITY = 15
DEFAULT_MAX_ARCHIVE = 10
DEFAULT_MAX_SHOWCASE = 10


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_identity(repo: dict[str, Any]) -> str:
    return str(repo.get("repo_name", "")).strip()


def repo_sort_key(repo: dict[str, Any]) -> tuple[int, str]:
    return (
        int(repo.get("total_score", 0)),
        repo_identity(repo).lower(),
    )


def deduplicate_repositories(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []

    for repo in repos:
        identity = repo_identity(repo)
        if not identity or identity in seen:
            continue
        seen.add(identity)
        unique.append(repo)

    return unique


def select_review_candidates(
    summary: dict[str, Any],
    *,
    max_weakest: int = DEFAULT_MAX_WEAKEST,
    max_strongest: int = DEFAULT_MAX_STRONGEST,
    max_priority: int = DEFAULT_MAX_PRIORITY,
    max_archive: int = DEFAULT_MAX_ARCHIVE,
    max_showcase: int = DEFAULT_MAX_SHOWCASE,
) -> list[dict[str, Any]]:
    weakest = list(summary.get("weakest_repositories", []))[:max_weakest]
    strongest = list(summary.get("strongest_repositories", []))[:max_strongest]

    portfolio_decisions = summary.get("portfolio_decisions", {})
    priority = list(portfolio_decisions.get("priority_repositories", []))[:max_priority]
    archive = list(portfolio_decisions.get("archive_candidates", []))[:max_archive]
    showcase = list(portfolio_decisions.get("showcase_candidates", []))[:max_showcase]

    merged = weakest + strongest + priority + archive + showcase
    merged = deduplicate_repositories(merged)
    merged.sort(key=repo_sort_key)
    return merged


def review_risk_level(repo: dict[str, Any]) -> str:
    score = int(repo.get("total_score", 0))
    decision = str(repo.get("decision", ""))
    repo_type = str(repo.get("repo_type", ""))
    maturity = str(repo.get("maturity_band", ""))

    if decision in {"archive", "rebuild"} and score >= 60:
        return "high"
    if decision == "keep" and score < 75:
        return "high"
    if repo_type == "config_or_infra_project" and decision != "keep" and score >= 70:
        return "high"
    if repo_type in {"ml_project", "data_science_project"} and decision == "archive":
        return "high"
    if maturity == "advanced" and decision in {"archive", "rebuild"}:
        return "medium"
    if score <= 35 or score >= 75:
        return "medium"
    return "low"


def review_source_tags(repo: dict[str, Any], summary: dict[str, Any]) -> str:
    tags: list[str] = []
    name = repo_identity(repo)

    for key, label in [
        ("weakest_repositories", "weakest"),
        ("strongest_repositories", "strongest"),
    ]:
        if any(repo_identity(item) == name for item in summary.get(key, [])):
            tags.append(label)

    portfolio_decisions = summary.get("portfolio_decisions", {})
    for key, label in [
        ("priority_repositories", "priority"),
        ("archive_candidates", "archive_candidate"),
        ("showcase_candidates", "showcase_candidate"),
    ]:
        if any(repo_identity(item) == name for item in portfolio_decisions.get(key, [])):
            tags.append(label)

    return ",".join(tags)


def to_review_row(repo: dict[str, Any], summary: dict[str, Any]) -> dict[str, str]:
    issues = " | ".join(
        str(issue.get("title", "")).strip()
        for issue in repo.get("priority_issues", [])[:5]
    )
    actions = " | ".join(
        str(action.get("title", "")).strip()
        for action in repo.get("prioritized_actions", [])[:5]
    )

    return {
        "repo_name": repo_identity(repo),
        "target_name": str(repo.get("target_name", "")),
        "target_kind": str(repo.get("target_kind", "")),
        "score": str(repo.get("total_score", "")),
        "level": str(repo.get("level", "")),
        "repo_type_detected": str(repo.get("repo_type", "")),
        "maturity_detected": str(repo.get("maturity_band", "")),
        "decision_detected": str(repo.get("decision", "")),
        "decision_reason": str(repo.get("decision_reason", "")),
        "review_risk": review_risk_level(repo),
        "review_sources": review_source_tags(repo, summary),
        "top_issues": issues,
        "top_actions": actions,
        "expected_repo_type": "",
        "expected_decision": "",
        "review_status": "todo",
        "review_comment": "",
    }


def export_review_queue(summary_path: Path, output_path: Path) -> Path:
    summary = load_summary(summary_path)
    candidates = select_review_candidates(summary)
    rows = [to_review_row(repo, summary) for repo in candidates]

    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Export a manual review queue from batch-summary.json."
    )
    parser.add_argument(
        "summary_json",
        help="Path to batch-summary.json",
    )
    parser.add_argument(
        "--output",
        help="Output CSV path. Defaults to review-queue.csv next to the summary JSON.",
    )
    args = parser.parse_args()

    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary JSON not found: {summary_path}")

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else summary_path.with_name("review-queue.csv")
    )

    exported = export_review_queue(summary_path, output_path)
    print(f"Review queue exported to: {exported}")


if __name__ == "__main__":
    main()