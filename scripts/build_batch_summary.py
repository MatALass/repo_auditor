from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_org_audit_json_files(batch_dir: Path) -> list[Path]:
    return sorted(batch_dir.rglob("*-github-org-audit.json"))


def collect_repo_rows(org_payload: dict[str, Any]) -> list[dict[str, Any]]:
    source_name = str(org_payload.get("source_name", "unknown"))
    rows: list[dict[str, Any]] = []

    for repo in org_payload.get("results", []):
        row = {
            "org_name": source_name,
            "repo_name": repo.get("repo_name"),
            "total_score": int(repo.get("total_score", 0)),
            "max_score": int(repo.get("max_score", 100)),
            "level": repo.get("level", "unknown"),
            "repo_type": repo.get("repo_type", "generic_project"),
            "maturity_band": repo.get("maturity_band", "unknown"),
            "priority_issues": repo.get("priority_issues", []),
            "prioritized_actions": repo.get("prioritized_actions", []),
        }
        rows.append(row)

    return rows


def summarize_org(org_payload: dict[str, Any]) -> dict[str, Any]:
    org_name = str(org_payload.get("source_name", "unknown"))
    repos = org_payload.get("results", [])
    failed_repositories = org_payload.get("failed_repositories", [])

    scores = [int(repo.get("total_score", 0)) for repo in repos]
    average_score = round(mean(scores), 2) if scores else 0.0

    sorted_repos = sorted(
        repos,
        key=lambda repo: (
            int(repo.get("total_score", 0)),
            str(repo.get("repo_name", "")).lower(),
        ),
    )

    worst_repo = sorted_repos[0] if sorted_repos else None
    best_repo = sorted(
        repos,
        key=lambda repo: (
            -int(repo.get("total_score", 0)),
            str(repo.get("repo_name", "")).lower(),
        ),
    )[0] if repos else None

    return {
        "org_name": org_name,
        "repo_count": int(org_payload.get("repo_count", len(repos))),
        "failed_count": int(org_payload.get("failed_count", len(failed_repositories))),
        "average_score": average_score,
        "worst_repo_name": worst_repo.get("repo_name") if worst_repo else None,
        "worst_repo_score": worst_repo.get("total_score") if worst_repo else None,
        "best_repo_name": best_repo.get("repo_name") if best_repo else None,
        "best_repo_score": best_repo.get("total_score") if best_repo else None,
    }


def build_batch_summary(batch_dir: Path) -> dict[str, Any]:
    json_files = find_org_audit_json_files(batch_dir)
    if not json_files:
        raise FileNotFoundError(f"No *-github-org-audit.json files found under: {batch_dir}")

    org_payloads = [load_json(path) for path in json_files]
    org_summaries = [summarize_org(payload) for payload in org_payloads]

    all_repos: list[dict[str, Any]] = []
    failed_repositories: list[dict[str, Any]] = []

    issue_counter: Counter[str] = Counter()
    issue_title_by_code: dict[str, str] = {}

    action_counter: Counter[str] = Counter()
    action_title_by_code: dict[str, str] = {}

    repo_type_counter: Counter[str] = Counter()
    maturity_counter: Counter[str] = Counter()
    level_counter: Counter[str] = Counter()

    for payload in org_payloads:
        all_repos.extend(collect_repo_rows(payload))
        failed_repositories.extend(payload.get("failed_repositories", []))

    for repo in all_repos:
        repo_type_counter[str(repo["repo_type"])] += 1
        maturity_counter[str(repo["maturity_band"])] += 1
        level_counter[str(repo["level"])] += 1

        for issue in repo.get("priority_issues", []):
            code = str(issue.get("code", "unknown_issue"))
            title = str(issue.get("title", code))
            issue_counter[code] += 1
            issue_title_by_code[code] = title

        for action in repo.get("prioritized_actions", []):
            code = str(action.get("code", "unknown_action"))
            title = str(action.get("title", code))
            action_counter[code] += 1
            action_title_by_code[code] = title

    sorted_orgs = sorted(
        org_summaries,
        key=lambda row: (
            row["average_score"],
            row["failed_count"],
            row["org_name"].lower(),
        ),
    )

    weakest_repos = sorted(
        all_repos,
        key=lambda repo: (
            repo["total_score"],
            repo["org_name"].lower(),
            str(repo["repo_name"]).lower(),
        ),
    )

    strongest_repos = sorted(
        all_repos,
        key=lambda repo: (
            -repo["total_score"],
            repo["org_name"].lower(),
            str(repo["repo_name"]).lower(),
        ),
    )

    average_score_all = round(mean([repo["total_score"] for repo in all_repos]), 2) if all_repos else 0.0

    return {
        "batch_type": "github_orgs_audit",
        "batch_directory": str(batch_dir),
        "org_count": len(org_payloads),
        "total_repositories_analyzed": len(all_repos),
        "total_failed_repositories": len(failed_repositories),
        "average_score_all_repositories": average_score_all,
        "organizations": sorted_orgs,
        "weakest_repositories": weakest_repos[:15],
        "strongest_repositories": strongest_repos[:10],
        "top_issue_hotspots": [
            {
                "code": code,
                "title": issue_title_by_code.get(code, code),
                "count": count,
            }
            for code, count in issue_counter.most_common(10)
        ],
        "top_action_hotspots": [
            {
                "code": code,
                "title": action_title_by_code.get(code, code),
                "count": count,
            }
            for code, count in action_counter.most_common(10)
        ],
        "repo_type_distribution": dict(repo_type_counter.most_common()),
        "maturity_distribution": dict(maturity_counter.most_common()),
        "level_distribution": dict(level_counter.most_common()),
        "failed_repositories": failed_repositories,
    }


def render_batch_summary_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append("# GitHub Organizations Batch Audit Summary")
    lines.append("")
    lines.append(f"**Organizations audited:** {summary['org_count']}")
    lines.append(f"**Repositories analyzed:** {summary['total_repositories_analyzed']}")
    lines.append(f"**Repositories failed to scan:** {summary['total_failed_repositories']}")
    lines.append(f"**Average score across all repositories:** {summary['average_score_all_repositories']}/100")
    lines.append("")

    lines.append("## Organization ranking")
    lines.append("")
    for index, org in enumerate(summary["organizations"], start=1):
        lines.append(
            f"{index}. **{org['org_name']}** — "
            f"avg {org['average_score']}/100, "
            f"repos {org['repo_count']}, "
            f"failed {org['failed_count']}, "
            f"worst repo: {org['worst_repo_name']} ({org['worst_repo_score']}/100)"
        )
    lines.append("")

    lines.append("## Weakest repositories across all organizations")
    lines.append("")
    for index, repo in enumerate(summary["weakest_repositories"], start=1):
        lines.append(
            f"{index}. **{repo['repo_name']}** — "
            f"{repo['total_score']}/{repo['max_score']} "
            f"({repo['org_name']}, {repo['level']}, {repo['repo_type']}, {repo['maturity_band']})"
        )
    lines.append("")

    lines.append("## Strongest repositories across all organizations")
    lines.append("")
    for index, repo in enumerate(summary["strongest_repositories"], start=1):
        lines.append(
            f"{index}. **{repo['repo_name']}** — "
            f"{repo['total_score']}/{repo['max_score']} "
            f"({repo['org_name']}, {repo['level']}, {repo['repo_type']}, {repo['maturity_band']})"
        )
    lines.append("")

    lines.append("## Most common issue hotspots")
    lines.append("")
    if not summary["top_issue_hotspots"]:
        lines.append("- No issue hotspot detected.")
    else:
        for hotspot in summary["top_issue_hotspots"]:
            lines.append(f"- **{hotspot['title']}** — {hotspot['count']} repositories")
    lines.append("")

    lines.append("## Most common recommended actions")
    lines.append("")
    if not summary["top_action_hotspots"]:
        lines.append("- No action hotspot detected.")
    else:
        for hotspot in summary["top_action_hotspots"]:
            lines.append(f"- **{hotspot['title']}** — {hotspot['count']} repositories")
    lines.append("")

    lines.append("## Repository type distribution")
    lines.append("")
    for repo_type, count in summary["repo_type_distribution"].items():
        lines.append(f"- **{repo_type}** — {count}")
    lines.append("")

    lines.append("## Maturity distribution")
    lines.append("")
    for maturity, count in summary["maturity_distribution"].items():
        lines.append(f"- **{maturity}** — {count}")
    lines.append("")

    lines.append("## Level distribution")
    lines.append("")
    for level, count in summary["level_distribution"].items():
        lines.append(f"- **{level}** — {count}")
    lines.append("")

    if summary["failed_repositories"]:
        lines.append("## Failed repositories")
        lines.append("")
        for failure in summary["failed_repositories"]:
            owner = failure.get("owner", "unknown")
            repo_name = failure.get("repo_name", "unknown")
            error = failure.get("error", "unknown error")
            lines.append(f"- **{owner}/{repo_name}** — {error}")
        lines.append("")

    return "\n".join(lines)


def write_outputs(batch_dir: Path, summary: dict[str, Any]) -> None:
    json_path = batch_dir / "batch-summary.json"
    md_path = batch_dir / "batch-summary.md"

    json_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    md_path.write_text(
        render_batch_summary_markdown(summary),
        encoding="utf-8",
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build a consolidated summary from multiple GitHub org audit JSON files.")
    parser.add_argument("batch_dir", help="Directory containing per-organization audit outputs")
    args = parser.parse_args()

    batch_dir = Path(args.batch_dir).expanduser().resolve()
    summary = build_batch_summary(batch_dir)
    write_outputs(batch_dir, summary)

    print(f"Batch summary written to: {batch_dir}")


if __name__ == "__main__":
    main()