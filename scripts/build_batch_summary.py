from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_github_audit_json_files(batch_dir: Path) -> list[Path]:
    candidates: set[Path] = set()
    candidates.update(batch_dir.rglob("*-github-org-audit.json"))
    candidates.update(batch_dir.rglob("*-github-user-audit.json"))
    return sorted(candidates)


def infer_target_kind(payload: dict[str, Any]) -> str:
    raw = str(
        payload.get("source_type")
        or payload.get("workspace_type")
        or payload.get("batch_item_type")
        or ""
    ).strip().lower()

    if raw == "github_org":
        return "org"
    if raw == "github_user":
        return "user"
    return "unknown"


def collect_repo_rows(target_payload: dict[str, Any]) -> list[dict[str, Any]]:
    source_name = str(target_payload.get("source_name", "unknown"))
    source_kind = infer_target_kind(target_payload)
    rows: list[dict[str, Any]] = []

    for repo in target_payload.get("results", []):
        row = {
            "target_name": source_name,
            "target_kind": source_kind,
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


def summarize_target(target_payload: dict[str, Any]) -> dict[str, Any]:
    target_name = str(target_payload.get("source_name", "unknown"))
    target_kind = infer_target_kind(target_payload)
    repos = target_payload.get("results", [])
    failed_repositories = target_payload.get("failed_repositories", [])

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
        "target_name": target_name,
        "target_kind": target_kind,
        "repo_count": int(target_payload.get("repo_count", len(repos))),
        "failed_count": int(target_payload.get("failed_count", len(failed_repositories))),
        "average_score": average_score,
        "worst_repo_name": worst_repo.get("repo_name") if worst_repo else None,
        "worst_repo_score": worst_repo.get("total_score") if worst_repo else None,
        "best_repo_name": best_repo.get("repo_name") if best_repo else None,
        "best_repo_score": best_repo.get("total_score") if best_repo else None,
    }


def issue_code_set(repo: dict[str, Any]) -> set[str]:
    return {
        str(issue.get("code", "")).strip().lower()
        for issue in repo.get("priority_issues", [])
        if str(issue.get("code", "")).strip()
    }


def issue_title_text(repo: dict[str, Any]) -> str:
    return " | ".join(
        str(issue.get("title", "")).strip().lower()
        for issue in repo.get("priority_issues", [])
    )


def action_title_text(repo: dict[str, Any]) -> str:
    return " | ".join(
        str(action.get("title", "")).strip().lower()
        for action in repo.get("prioritized_actions", [])
    )


def has_empty_like_signal(repo: dict[str, Any]) -> bool:
    text = issue_title_text(repo)
    return "empty or nearly empty" in text or "empty" in text


def has_structure_debt_signal(repo: dict[str, Any]) -> bool:
    text = issue_title_text(repo)
    action_text = action_title_text(repo)
    return any(
        fragment in text or fragment in action_text
        for fragment in [
            "monolithic structure",
            "poor separation of concerns",
            "main code directory missing",
            "flat project structure",
            "dedicated source directory",
            "decompose monolithic code structure",
            "improve separation of concerns",
        ]
    )


def has_missing_basics_signal(repo: dict[str, Any]) -> bool:
    text = issue_title_text(repo)
    return any(
        fragment in text
        for fragment in [
            ".gitignore missing",
            "dependency manifest missing",
            "readme missing",
            "installation instructions missing",
            "usage instructions missing",
        ]
    )


def determine_repo_decision(repo: dict[str, Any]) -> str:
    score = int(repo["total_score"])
    repo_type = str(repo["repo_type"])
    maturity = str(repo["maturity_band"])
    empty_like = has_empty_like_signal(repo)
    structure_debt = has_structure_debt_signal(repo)
    missing_basics = has_missing_basics_signal(repo)

    if score >= 75:
        return "keep"

    if score < 25:
        if empty_like or repo_type in {"generic_project", "documentation_project"}:
            return "archive"
        return "rebuild"

    if score < 40:
        if empty_like and maturity in {"bootstrap", "foundation"}:
            return "archive"
        if structure_debt:
            return "rebuild"
        return "improve"

    if score < 75:
        if structure_debt and maturity in {"developing", "advanced"}:
            return "rebuild"
        if missing_basics or structure_debt:
            return "improve"
        return "improve"

    return "keep"


def decision_reason(repo: dict[str, Any], decision: str) -> str:
    score = int(repo["total_score"])
    maturity = str(repo["maturity_band"])

    if decision == "keep":
        return f"High score ({score}/100) and already credible as a showcase repository."
    if decision == "archive":
        return (
            f"Very weak score ({score}/100) with low portfolio value relative to cleanup effort, "
            f"especially for a {maturity} repository."
        )
    if decision == "rebuild":
        return (
            f"Low-to-mid score ({score}/100) with structural debt that likely makes incremental cleanup inefficient."
        )
    return f"Recoverable score ({score}/100) with improvements that are still worth implementing incrementally."


def classify_action_bucket(action_title: str) -> str:
    title = action_title.lower()

    quick_keywords = [
        ".gitignore",
        "readme",
        "installation",
        "usage",
        "dependencies",
        "manifest",
        "test framework",
        "environment example",
        "license",
    ]
    heavy_keywords = [
        "decompose monolithic",
        "improve separation of concerns",
        "introduce a dedicated source directory",
        "restructure the repository layout",
        "complete or archive the repository",
        "align repository scope with actual contents",
    ]

    if any(keyword in title for keyword in heavy_keywords):
        return "heavy_refactors"
    if any(keyword in title for keyword in quick_keywords):
        return "quick_wins"
    return "medium_refactors"


def build_global_remediation_priorities(all_repos: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, Counter[str]] = {
        "quick_wins": Counter(),
        "medium_refactors": Counter(),
        "heavy_refactors": Counter(),
    }
    action_titles: dict[str, str] = {}

    for repo in all_repos:
        for action in repo.get("prioritized_actions", []):
            code = str(action.get("code", "unknown_action"))
            title = str(action.get("title", code))
            bucket = classify_action_bucket(title)
            buckets[bucket][code] += 1
            action_titles[code] = title

    return {
        bucket_name: [
            {
                "code": code,
                "title": action_titles.get(code, code),
                "count": count,
            }
            for code, count in counter.most_common(10)
        ]
        for bucket_name, counter in buckets.items()
    }


def select_priority_repositories(all_repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [repo for repo in all_repos if repo["decision"] in {"improve", "rebuild"}]
    ranked = sorted(
        candidates,
        key=lambda repo: (
            0 if repo["decision"] == "rebuild" else 1,
            repo["total_score"],
            repo["target_name"].lower(),
            str(repo["repo_name"]).lower(),
        ),
    )
    return ranked[:12]


def select_archive_candidates(all_repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [repo for repo in all_repos if repo["decision"] == "archive"]
    ranked = sorted(
        candidates,
        key=lambda repo: (
            repo["total_score"],
            repo["target_name"].lower(),
            str(repo["repo_name"]).lower(),
        ),
    )
    return ranked[:12]


def select_showcase_candidates(all_repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [repo for repo in all_repos if repo["decision"] == "keep"]
    ranked = sorted(
        candidates,
        key=lambda repo: (
            -repo["total_score"],
            repo["target_name"].lower(),
            str(repo["repo_name"]).lower(),
        ),
    )
    return ranked[:12]


def decision_distribution(all_repos: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for repo in all_repos:
        counter[str(repo["decision"])] += 1
    return dict(counter.most_common())


def build_batch_summary(batch_dir: Path) -> dict[str, Any]:
    json_files = find_github_audit_json_files(batch_dir)
    if not json_files:
        raise FileNotFoundError(f"No GitHub audit JSON files found under: {batch_dir}")

    target_payloads = [load_json(path) for path in json_files]
    target_summaries = [summarize_target(payload) for payload in target_payloads]

    all_repos: list[dict[str, Any]] = []
    failed_repositories: list[dict[str, Any]] = []

    issue_counter: Counter[str] = Counter()
    issue_title_by_code: dict[str, str] = {}

    action_counter: Counter[str] = Counter()
    action_title_by_code: dict[str, str] = {}

    repo_type_counter: Counter[str] = Counter()
    maturity_counter: Counter[str] = Counter()
    level_counter: Counter[str] = Counter()
    target_kind_counter: Counter[str] = Counter()

    for payload in target_payloads:
        all_repos.extend(collect_repo_rows(payload))
        failed_repositories.extend(payload.get("failed_repositories", []))

    for repo in all_repos:
        repo["decision"] = determine_repo_decision(repo)
        repo["decision_reason"] = decision_reason(repo, repo["decision"])

        repo_type_counter[str(repo["repo_type"])] += 1
        maturity_counter[str(repo["maturity_band"])] += 1
        level_counter[str(repo["level"])] += 1
        target_kind_counter[str(repo["target_kind"])] += 1

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

    sorted_targets = sorted(
        target_summaries,
        key=lambda row: (
            row["average_score"],
            row["failed_count"],
            row["target_name"].lower(),
        ),
    )

    weakest_repos = sorted(
        all_repos,
        key=lambda repo: (
            repo["total_score"],
            repo["target_name"].lower(),
            str(repo["repo_name"]).lower(),
        ),
    )

    strongest_repos = sorted(
        all_repos,
        key=lambda repo: (
            -repo["total_score"],
            repo["target_name"].lower(),
            str(repo["repo_name"]).lower(),
        ),
    )

    average_score_all = round(mean([repo["total_score"] for repo in all_repos]), 2) if all_repos else 0.0
    remediation = build_global_remediation_priorities(all_repos)

    return {
        "batch_type": "github_targets_audit",
        "batch_directory": str(batch_dir),
        "target_count": len(target_payloads),
        "target_kind_distribution": dict(target_kind_counter.most_common()),
        "total_repositories_analyzed": len(all_repos),
        "total_failed_repositories": len(failed_repositories),
        "average_score_all_repositories": average_score_all,
        "targets": sorted_targets,
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
        "decision_distribution": decision_distribution(all_repos),
        "portfolio_decisions": {
            "priority_repositories": select_priority_repositories(all_repos),
            "archive_candidates": select_archive_candidates(all_repos),
            "showcase_candidates": select_showcase_candidates(all_repos),
        },
        "global_remediation_priorities": remediation,
        "failed_repositories": failed_repositories,
    }


def render_batch_summary_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append("# GitHub Targets Batch Audit Summary")
    lines.append("")
    lines.append(f"**GitHub targets audited:** {summary['target_count']}")
    lines.append(f"**Repositories analyzed:** {summary['total_repositories_analyzed']}")
    lines.append(f"**Repositories failed to scan:** {summary['total_failed_repositories']}")
    lines.append(f"**Average score across all repositories:** {summary['average_score_all_repositories']}/100")
    lines.append("")

    lines.append("## Target ranking")
    lines.append("")
    for index, target in enumerate(summary["targets"], start=1):
        lines.append(
            f"{index}. **{target['target_name']}** "
            f"({target['target_kind']}) — "
            f"avg {target['average_score']}/100, "
            f"repos {target['repo_count']}, "
            f"failed {target['failed_count']}, "
            f"worst repo: {target['worst_repo_name']} ({target['worst_repo_score']}/100)"
        )
    lines.append("")

    lines.append("## Weakest repositories across all targets")
    lines.append("")
    for index, repo in enumerate(summary["weakest_repositories"], start=1):
        lines.append(
            f"{index}. **{repo['repo_name']}** — "
            f"{repo['total_score']}/{repo['max_score']} "
            f"({repo['target_name']}, {repo['level']}, {repo['repo_type']}, {repo['maturity_band']}, decision: {repo['decision']})"
        )
    lines.append("")

    lines.append("## Strongest repositories across all targets")
    lines.append("")
    for index, repo in enumerate(summary["strongest_repositories"], start=1):
        lines.append(
            f"{index}. **{repo['repo_name']}** — "
            f"{repo['total_score']}/{repo['max_score']} "
            f"({repo['target_name']}, {repo['level']}, {repo['repo_type']}, {repo['maturity_band']}, decision: {repo['decision']})"
        )
    lines.append("")

    lines.append("## Portfolio decision distribution")
    lines.append("")
    for decision, count in summary["decision_distribution"].items():
        lines.append(f"- **{decision}** — {count}")
    lines.append("")

    lines.append("## Priority repositories to treat next")
    lines.append("")
    priority_repos = summary["portfolio_decisions"]["priority_repositories"]
    if not priority_repos:
        lines.append("- No priority repositories identified.")
    else:
        for index, repo in enumerate(priority_repos, start=1):
            lines.append(
                f"{index}. **{repo['repo_name']}** — "
                f"{repo['total_score']}/{repo['max_score']} "
                f"({repo['decision']}) — {repo['decision_reason']}"
            )
    lines.append("")

    lines.append("## Archive candidates")
    lines.append("")
    archive_candidates = summary["portfolio_decisions"]["archive_candidates"]
    if not archive_candidates:
        lines.append("- No archive candidates identified.")
    else:
        for index, repo in enumerate(archive_candidates, start=1):
            lines.append(
                f"{index}. **{repo['repo_name']}** — "
                f"{repo['total_score']}/{repo['max_score']} "
                f"({repo['decision']}) — {repo['decision_reason']}"
            )
    lines.append("")

    lines.append("## Showcase candidates to protect and strengthen")
    lines.append("")
    showcase_candidates = summary["portfolio_decisions"]["showcase_candidates"]
    if not showcase_candidates:
        lines.append("- No showcase candidates identified.")
    else:
        for index, repo in enumerate(showcase_candidates, start=1):
            lines.append(
                f"{index}. **{repo['repo_name']}** — "
                f"{repo['total_score']}/{repo['max_score']} "
                f"({repo['decision']}) — {repo['decision_reason']}"
            )
    lines.append("")

    lines.append("## Global remediation priorities — quick wins")
    lines.append("")
    quick_wins = summary["global_remediation_priorities"]["quick_wins"]
    if not quick_wins:
        lines.append("- No quick wins detected.")
    else:
        for item in quick_wins:
            lines.append(f"- **{item['title']}** — {item['count']} repositories")
    lines.append("")

    lines.append("## Global remediation priorities — medium refactors")
    lines.append("")
    medium_refactors = summary["global_remediation_priorities"]["medium_refactors"]
    if not medium_refactors:
        lines.append("- No medium refactors detected.")
    else:
        for item in medium_refactors:
            lines.append(f"- **{item['title']}** — {item['count']} repositories")
    lines.append("")

    lines.append("## Global remediation priorities — heavy refactors")
    lines.append("")
    heavy_refactors = summary["global_remediation_priorities"]["heavy_refactors"]
    if not heavy_refactors:
        lines.append("- No heavy refactors detected.")
    else:
        for item in heavy_refactors:
            lines.append(f"- **{item['title']}** — {item['count']} repositories")
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

    parser = argparse.ArgumentParser(
        description="Build a consolidated summary from multiple GitHub target audit JSON files."
    )
    parser.add_argument("batch_dir", help="Directory containing per-target audit outputs")
    args = parser.parse_args()

    batch_dir = Path(args.batch_dir).expanduser().resolve()
    summary = build_batch_summary(batch_dir)
    write_outputs(batch_dir, summary)

    print(f"Batch summary written to: {batch_dir}")


if __name__ == "__main__":
    main()