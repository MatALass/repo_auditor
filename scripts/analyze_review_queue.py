from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


VALID_REVIEW_STATUSES = {
    "validated",
    "adjust_policy",
    "adjust_detection",
    "needs_context",
}


def normalize(value: str | None) -> str:
    return (value or "").strip()


def lower_normalize(value: str | None) -> str:
    return normalize(value).lower()


def load_review_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def is_reviewed_row(row: dict[str, str]) -> bool:
    status = lower_normalize(row.get("review_status"))
    return status in VALID_REVIEW_STATUSES


def type_matches(row: dict[str, str]) -> bool | None:
    detected = lower_normalize(row.get("repo_type_detected"))
    expected = lower_normalize(row.get("expected_repo_type"))

    if not expected:
        return None
    return detected == expected


def decision_matches(row: dict[str, str]) -> bool | None:
    detected = lower_normalize(row.get("decision_detected"))
    expected = lower_normalize(row.get("expected_decision"))

    if not expected:
        return None
    return detected == expected


def mismatch_entry(row: dict[str, str], field: str) -> dict[str, Any]:
    return {
        "repo_name": normalize(row.get("repo_name")),
        "target_name": normalize(row.get("target_name")),
        "target_kind": normalize(row.get("target_kind")),
        "score": int(normalize(row.get("score")) or 0),
        "level": normalize(row.get("level")),
        "review_status": lower_normalize(row.get("review_status")),
        "review_comment": normalize(row.get("review_comment")),
        "field": field,
        "detected": normalize(row.get(f"{field}_detected")),
        "expected": normalize(row.get(f"expected_{field}")),
    }


def summarize_review_queue(rows: list[dict[str, str]]) -> dict[str, Any]:
    reviewed_rows = [row for row in rows if is_reviewed_row(row)]
    reviewed_count = len(reviewed_rows)

    type_total = 0
    type_match_count = 0
    decision_total = 0
    decision_match_count = 0

    type_mismatches: list[dict[str, Any]] = []
    decision_mismatches: list[dict[str, Any]] = []

    review_status_counter: Counter[str] = Counter()
    detected_type_counter: Counter[str] = Counter()
    expected_type_counter: Counter[str] = Counter()
    detected_decision_counter: Counter[str] = Counter()
    expected_decision_counter: Counter[str] = Counter()

    type_pairs_counter: Counter[str] = Counter()
    decision_pairs_counter: Counter[str] = Counter()

    for row in reviewed_rows:
        review_status = lower_normalize(row.get("review_status"))
        review_status_counter[review_status] += 1

        detected_type = normalize(row.get("repo_type_detected"))
        expected_type = normalize(row.get("expected_repo_type"))
        detected_decision = normalize(row.get("decision_detected"))
        expected_decision = normalize(row.get("expected_decision"))

        if detected_type:
            detected_type_counter[detected_type] += 1
        if expected_type:
            expected_type_counter[expected_type] += 1

        if detected_decision:
            detected_decision_counter[detected_decision] += 1
        if expected_decision:
            expected_decision_counter[expected_decision] += 1

        type_match = type_matches(row)
        if type_match is not None:
            type_total += 1
            if type_match:
                type_match_count += 1
            else:
                type_mismatches.append(mismatch_entry(row, "repo_type"))
                type_pairs_counter[f"{detected_type} -> {expected_type}"] += 1

        decision_match = decision_matches(row)
        if decision_match is not None:
            decision_total += 1
            if decision_match:
                decision_match_count += 1
            else:
                decision_mismatches.append(mismatch_entry(row, "decision"))
                decision_pairs_counter[f"{detected_decision} -> {expected_decision}"] += 1

    overall_reviewed_with_any_expectation = sum(
        1
        for row in reviewed_rows
        if normalize(row.get("expected_repo_type")) or normalize(row.get("expected_decision"))
    )

    return {
        "review_queue_size": len(rows),
        "reviewed_rows": reviewed_count,
        "reviewed_rows_with_expectations": overall_reviewed_with_any_expectation,
        "review_status_distribution": dict(review_status_counter.most_common()),
        "repo_type_analysis": {
            "compared_rows": type_total,
            "matches": type_match_count,
            "mismatches": len(type_mismatches),
            "accuracy": round(type_match_count / type_total, 4) if type_total else None,
            "top_mismatch_patterns": [
                {"pattern": pattern, "count": count}
                for pattern, count in type_pairs_counter.most_common(10)
            ],
            "detected_distribution": dict(detected_type_counter.most_common()),
            "expected_distribution": dict(expected_type_counter.most_common()),
            "mismatch_rows": sorted(
                type_mismatches,
                key=lambda item: (item["score"], item["repo_name"].lower()),
            ),
        },
        "decision_analysis": {
            "compared_rows": decision_total,
            "matches": decision_match_count,
            "mismatches": len(decision_mismatches),
            "accuracy": round(decision_match_count / decision_total, 4) if decision_total else None,
            "top_mismatch_patterns": [
                {"pattern": pattern, "count": count}
                for pattern, count in decision_pairs_counter.most_common(10)
            ],
            "detected_distribution": dict(detected_decision_counter.most_common()),
            "expected_distribution": dict(expected_decision_counter.most_common()),
            "mismatch_rows": sorted(
                decision_mismatches,
                key=lambda item: (item["score"], item["repo_name"].lower()),
            ),
        },
    }


def render_markdown_report(summary: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append("# Review Queue Analysis Report")
    lines.append("")
    lines.append(f"**Rows in review queue:** {summary['review_queue_size']}")
    lines.append(f"**Reviewed rows:** {summary['reviewed_rows']}")
    lines.append(f"**Reviewed rows with expectations:** {summary['reviewed_rows_with_expectations']}")
    lines.append("")

    repo_type_analysis = summary["repo_type_analysis"]
    decision_analysis = summary["decision_analysis"]

    lines.append("## Repo type detection quality")
    lines.append("")
    lines.append(f"- **Compared rows:** {repo_type_analysis['compared_rows']}")
    lines.append(f"- **Matches:** {repo_type_analysis['matches']}")
    lines.append(f"- **Mismatches:** {repo_type_analysis['mismatches']}")
    lines.append(f"- **Accuracy:** {repo_type_analysis['accuracy']}")
    lines.append("")

    lines.append("### Top repo type mismatch patterns")
    lines.append("")
    if not repo_type_analysis["top_mismatch_patterns"]:
        lines.append("- No repo type mismatches recorded.")
    else:
        for item in repo_type_analysis["top_mismatch_patterns"]:
            lines.append(f"- **{item['pattern']}** — {item['count']}")
    lines.append("")

    lines.append("### Repo type mismatches")
    lines.append("")
    if not repo_type_analysis["mismatch_rows"]:
        lines.append("- No repo type mismatches recorded.")
    else:
        for item in repo_type_analysis["mismatch_rows"]:
            lines.append(
                f"- **{item['repo_name']}** — detected `{item['detected']}` vs expected `{item['expected']}` "
                f"(score {item['score']}, status {item['review_status']})"
            )
    lines.append("")

    lines.append("## Portfolio decision quality")
    lines.append("")
    lines.append(f"- **Compared rows:** {decision_analysis['compared_rows']}")
    lines.append(f"- **Matches:** {decision_analysis['matches']}")
    lines.append(f"- **Mismatches:** {decision_analysis['mismatches']}")
    lines.append(f"- **Accuracy:** {decision_analysis['accuracy']}")
    lines.append("")

    lines.append("### Top decision mismatch patterns")
    lines.append("")
    if not decision_analysis["top_mismatch_patterns"]:
        lines.append("- No decision mismatches recorded.")
    else:
        for item in decision_analysis["top_mismatch_patterns"]:
            lines.append(f"- **{item['pattern']}** — {item['count']}")
    lines.append("")

    lines.append("### Decision mismatches")
    lines.append("")
    if not decision_analysis["mismatch_rows"]:
        lines.append("- No decision mismatches recorded.")
    else:
        for item in decision_analysis["mismatch_rows"]:
            lines.append(
                f"- **{item['repo_name']}** — detected `{item['detected']}` vs expected `{item['expected']}` "
                f"(score {item['score']}, status {item['review_status']})"
            )
    lines.append("")

    lines.append("## Review status distribution")
    lines.append("")
    for status, count in summary["review_status_distribution"].items():
        lines.append(f"- **{status}** — {count}")
    lines.append("")

    return "\n".join(lines)


def write_outputs(summary: dict[str, Any], json_output: Path, md_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.parent.mkdir(parents=True, exist_ok=True)

    json_output.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    md_output.write_text(
        render_markdown_report(summary),
        encoding="utf-8",
    )


def analyze_review_queue_file(review_queue_path: Path, json_output: Path, md_output: Path) -> dict[str, Any]:
    rows = load_review_rows(review_queue_path)
    summary = summarize_review_queue(rows)
    write_outputs(summary, json_output, md_output)
    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze a manually reviewed review-queue.csv and produce mismatch reports."
    )
    parser.add_argument(
        "review_queue_csv",
        help="Path to review-queue.csv",
    )
    parser.add_argument(
        "--json-output",
        help="Output JSON path. Defaults to review-analysis.json next to the CSV.",
    )
    parser.add_argument(
        "--md-output",
        help="Output Markdown path. Defaults to review-analysis.md next to the CSV.",
    )
    args = parser.parse_args()

    review_queue_path = Path(args.review_queue_csv).expanduser().resolve()
    if not review_queue_path.exists():
        raise FileNotFoundError(f"Review queue CSV not found: {review_queue_path}")

    json_output = (
        Path(args.json_output).expanduser().resolve()
        if args.json_output
        else review_queue_path.with_name("review-analysis.json")
    )
    md_output = (
        Path(args.md_output).expanduser().resolve()
        if args.md_output
        else review_queue_path.with_name("review-analysis.md")
    )

    analyze_review_queue_file(review_queue_path, json_output, md_output)
    print(f"Review analysis written to: {json_output}")
    print(f"Review analysis written to: {md_output}")


if __name__ == "__main__":
    main()