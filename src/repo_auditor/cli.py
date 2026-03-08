from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from dotenv import load_dotenv

from repo_auditor.github_client import GitHubClient
from repo_auditor.github_workspace import (
    audit_github_org,
    audit_github_repository,
    audit_github_user,
)
from repo_auditor.local_scanner import scan_local_repository
from repo_auditor.models import RepoFacts, RepoAuditResult
from repo_auditor.portfolio_policy import (
    PortfolioAssessment,
    assess_repo_for_portfolio,
    load_portfolio_policy,
)
from repo_auditor.report import (
    render_github_workspace_report,
    render_markdown_report,
    render_org_health_block,
    render_workspace_report,
)
from repo_auditor.scoring import audit_repo
from repo_auditor.serialization import (
    github_workspace_result_to_dict,
    repo_result_to_dict,
    workspace_result_to_dict,
    write_json_output,
    write_text_output,
)
from repo_auditor.workspace import audit_workspace


def build_demo_repo() -> RepoFacts:
    return RepoFacts(
        name="demo-repo",
        description="A small Python project for repository quality auditing.",
        root_files=["README.md", "pyproject.toml", ".gitignore"],
        root_dirs=["src", "tests", "docs"],
        all_paths=[
            "README.md",
            "pyproject.toml",
            ".gitignore",
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "docs/architecture.md",
        ],
        readme_text="""
# Demo Repo

## Overview
This project audits repositories.

## Installation
pip install -e .

## Usage
repo-auditor --path .

## Structure
- src/
- tests/
- docs/

## Demo
Example output is provided.

## Roadmap
Add GitHub API support.
""",
        file_line_counts={
            "src/main.py": 120,
            "src/utils.py": 80,
            "tests/test_main.py": 60,
        },
        manifest_files=["pyproject.toml"],
        tooling_files=["pytest.ini"],
        has_gitignore=True,
        has_license=False,
        has_env_example=False,
        code_file_count=2,
        test_file_count=1,
        readme_sections=["demo repo", "overview", "installation", "usage", "structure", "demo", "roadmap"],
        github_topics=[],
        homepage_url=None,
        has_ci_config=False,
        is_archived=False,
        recent_push_days=10,
        repo_type="python_project",
    )


def sanitize_stem(value: str) -> str:
    return (
        value.replace("/", "__")
        .replace("\\", "__")
        .replace(" ", "_")
        .replace(":", "_")
    )


def build_output_paths(base_path: str | None, default_stem: str) -> tuple[Path | None, Path | None]:
    if not base_path:
        return None, None

    safe_stem = sanitize_stem(default_stem)
    base = Path(base_path)

    if base.suffix:
        markdown_path = base
        json_path = base.with_suffix(".json")
        return markdown_path, json_path

    markdown_path = base / f"{safe_stem}.md"
    json_path = base / f"{safe_stem}.json"
    return markdown_path, json_path


def parse_github_repo_slug(value: str) -> tuple[str, str]:
    parts = [part.strip() for part in value.split("/") if part.strip()]
    if len(parts) != 2:
        raise ValueError("GitHub repository slug must follow the format owner/repo")
    return parts[0], parts[1]


def render_portfolio_block(assessment: PortfolioAssessment) -> str:
    lines = [
        "## Portfolio assessment",
        "",
        f"- **Decision:** {assessment.decision}",
        f"- **Reason:** {assessment.reason}",
        "",
    ]
    return "\n".join(lines)


def classify_doctor_actions(result: RepoAuditResult) -> tuple[list[str], list[str], list[str]]:
    quick_wins: list[str] = []
    structural_fixes: list[str] = []
    blockers: list[str] = []

    for issue in result.priority_issues:
        if issue.severity == "high":
            blockers.append(f"{issue.title} — {issue.recommendation}")

    for action in result.prioritized_actions:
        line = f"{action.title} — impact={action.impact}, effort={action.effort}, priority={action.priority_score}"
        if action.effort == "low":
            quick_wins.append(line)
        elif action.effort == "high" or action.impact == "high":
            structural_fixes.append(line)
        else:
            quick_wins.append(line)

    return quick_wins[:5], structural_fixes[:5], blockers[:5]


def render_doctor_block(result: RepoAuditResult) -> str:
    quick_wins, structural_fixes, blockers = classify_doctor_actions(result)

    lines: list[str] = []
    lines.append("## Doctor mode")
    lines.append("")
    lines.append("### Top blockers")
    lines.append("")
    if blockers:
        for item in blockers:
            lines.append(f"- {item}")
    else:
        lines.append("- No critical blockers detected.")
    lines.append("")

    lines.append("### Quick wins")
    lines.append("")
    if quick_wins:
        for item in quick_wins:
            lines.append(f"- {item}")
    else:
        lines.append("- No quick wins identified.")
    lines.append("")

    lines.append("### Structural fixes")
    lines.append("")
    if structural_fixes:
        for item in structural_fixes:
            lines.append(f"- {item}")
    else:
        lines.append("- No structural refactor identified.")
    lines.append("")

    return "\n".join(lines)


def enrich_repo_markdown(
    result: RepoAuditResult,
    *,
    include_portfolio: bool,
    include_doctor: bool,
    policy_path: Path | None,
) -> str:
    sections = [render_markdown_report(result).rstrip()]

    if include_portfolio:
        policy = load_portfolio_policy(policy_path)
        assessment = assess_repo_for_portfolio(result, policy)
        sections.append(render_portfolio_block(assessment).rstrip())

    if include_doctor:
        sections.append(render_doctor_block(result).rstrip())

    return "\n\n".join(section for section in sections if section).rstrip() + "\n"


def enrich_repo_payload(
    result: RepoAuditResult,
    *,
    include_portfolio: bool,
    include_doctor: bool,
    policy_path: Path | None,
) -> dict[str, Any]:
    payload = repo_result_to_dict(result)

    if include_portfolio:
        policy = load_portfolio_policy(policy_path)
        assessment = assess_repo_for_portfolio(result, policy)
        payload["portfolio_assessment"] = {
            "decision": assessment.decision,
            "reason": assessment.reason,
        }

    if include_doctor:
        quick_wins, structural_fixes, blockers = classify_doctor_actions(result)
        payload["doctor_summary"] = {
            "top_blockers": blockers,
            "quick_wins": quick_wins,
            "structural_fixes": structural_fixes,
        }

    return payload


def ensure_single_repo_mode_for_enhanced_flags(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not (args.portfolio or args.doctor or args.policy):
        return

    single_repo_mode = bool(args.demo or args.path or args.github_repo)
    if not single_repo_mode:
        parser.error("--portfolio, --doctor, and --policy are currently supported only with --demo, --path, or --github-repo.")

    if args.policy and not args.portfolio:
        parser.error("--policy requires --portfolio.")


def ensure_org_health_mode_is_valid(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not args.org_health:
        return

    valid = bool(args.workspace or args.github_user or args.github_org)
    if not valid:
        parser.error("--org-health is currently supported only with --workspace, --github-user, or --github-org.")


def build_org_health_summary(
    repo_results: list[RepoAuditResult],
    *,
    policy_path: Path | None,
) -> dict[str, Any]:
    policy = load_portfolio_policy(policy_path)
    scores = [repo.total_score for repo in repo_results]
    max_score = repo_results[0].max_score if repo_results else 100

    issue_counter: Counter[str] = Counter()
    issue_titles: dict[str, str] = {}
    decisions: Counter[str] = Counter()

    archived_count = 0
    missing_topics_count = 0
    missing_homepage_count = 0
    missing_ci_count = 0

    for repo in repo_results:
        assessment = assess_repo_for_portfolio(repo, policy)
        decisions[assessment.decision] += 1

        metadata = getattr(repo, "metadata", None)
        if metadata is not None:
            if metadata.is_archived:
                archived_count += 1
            if not metadata.github_topics:
                missing_topics_count += 1
            if not metadata.homepage_url:
                missing_homepage_count += 1
            if not metadata.has_ci_config:
                missing_ci_count += 1
        else:
            missing_topics_count += 1
            missing_homepage_count += 1
            missing_ci_count += 1

        seen_codes: set[str] = set()
        for issue in repo.priority_issues:
            if issue.code in seen_codes:
                continue
            seen_codes.add(issue.code)
            issue_counter[issue.code] += 1
            issue_titles.setdefault(issue.code, issue.title)

    sorted_by_score = sorted(repo_results, key=lambda item: item.total_score)
    best_repo = sorted_by_score[-1] if sorted_by_score else None
    worst_repo = sorted_by_score[0] if sorted_by_score else None

    top_issue_counts = [
        {"code": code, "title": issue_titles.get(code, code), "count": count}
        for code, count in issue_counter.most_common(5)
    ]

    return {
        "repo_count": len(repo_results),
        "max_score": max_score,
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "median_score": round(float(median(scores)), 1) if scores else 0,
        "best_repo_name": best_repo.repo_name if best_repo else None,
        "worst_repo_name": worst_repo.repo_name if worst_repo else None,
        "portfolio_decisions": {
            "keep": decisions.get("keep", 0),
            "improve": decisions.get("improve", 0),
            "rebuild": decisions.get("rebuild", 0),
            "archive": decisions.get("archive", 0),
        },
        "archived_count": archived_count,
        "missing_topics_count": missing_topics_count,
        "missing_homepage_count": missing_homepage_count,
        "missing_ci_count": missing_ci_count,
        "top_issue_counts": top_issue_counts,
    }


def enrich_workspace_markdown(
    markdown: str,
    repo_results: list[RepoAuditResult],
    *,
    include_org_health: bool,
    policy_path: Path | None,
) -> str:
    if not include_org_health:
        return markdown.rstrip() + "\n"

    summary = build_org_health_summary(repo_results, policy_path=policy_path)
    return markdown.rstrip() + "\n\n" + render_org_health_block(summary).rstrip() + "\n"


def enrich_workspace_payload(
    payload: dict[str, Any],
    repo_results: list[RepoAuditResult],
    *,
    include_org_health: bool,
    policy_path: Path | None,
) -> dict[str, Any]:
    if not include_org_health:
        return payload

    enriched = dict(payload)
    enriched["org_health_summary"] = build_org_health_summary(repo_results, policy_path=policy_path)
    return enriched


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Audit repositories and rank them by structural quality.")
    parser.add_argument("--demo", action="store_true", help="Run the demo repository audit.")
    parser.add_argument("--path", type=str, help="Scan a single local repository path.")
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Optional repository description for the audit context.",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        help="Scan a parent directory containing multiple local repositories.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively discover repositories inside a local workspace.",
    )
    parser.add_argument(
        "--github-user",
        type=str,
        help="Audit all public or accessible repositories of a GitHub user.",
    )
    parser.add_argument(
        "--github-org",
        type=str,
        help="Audit all public or accessible repositories of a GitHub organization.",
    )
    parser.add_argument(
        "--github-repo",
        type=str,
        help="Audit a single GitHub repository using the format owner/repo.",
    )
    parser.add_argument(
        "--include-forks",
        action="store_true",
        help="Include forked repositories in GitHub user/org audits.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help=(
            "Output directory or base file path for exported reports. "
            "If a directory/base path is provided, both Markdown and JSON are written."
        ),
    )
    parser.add_argument(
        "--portfolio",
        action="store_true",
        help="Append a portfolio decision block for single-repository audits.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Append an action-oriented doctor block for single-repository audits.",
    )
    parser.add_argument(
        "--policy",
        type=str,
        help="Optional custom portfolio policy JSON file. Requires --portfolio or --org-health.",
    )
    parser.add_argument(
        "--org-health",
        action="store_true",
        help="Append an aggregated organization/workspace health summary.",
    )
    args = parser.parse_args()

    ensure_single_repo_mode_for_enhanced_flags(args, parser)
    ensure_org_health_mode_is_valid(args, parser)

    if args.policy and not (args.portfolio or args.org_health):
        parser.error("--policy requires --portfolio or --org-health.")

    policy_path = Path(args.policy).expanduser().resolve() if args.policy else None

    github_token = os.getenv("GITHUB_TOKEN")
    github_client = GitHubClient(token=github_token)

    if args.demo:
        facts = build_demo_repo()
        result = audit_repo(facts)
        markdown = enrich_repo_markdown(
            result,
            include_portfolio=args.portfolio,
            include_doctor=args.doctor,
            policy_path=policy_path,
        )
        print(markdown)

        md_path, json_path = build_output_paths(args.output, "demo-repo-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(
                json_path,
                enrich_repo_payload(
                    result,
                    include_portfolio=args.portfolio,
                    include_doctor=args.doctor,
                    policy_path=policy_path,
                ),
            )
        return

    if args.path:
        facts = scan_local_repository(Path(args.path), description=args.description)
        result = audit_repo(facts)
        markdown = enrich_repo_markdown(
            result,
            include_portfolio=args.portfolio,
            include_doctor=args.doctor,
            policy_path=policy_path,
        )
        print(markdown)

        md_path, json_path = build_output_paths(args.output, f"{facts.name}-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(
                json_path,
                enrich_repo_payload(
                    result,
                    include_portfolio=args.portfolio,
                    include_doctor=args.doctor,
                    policy_path=policy_path,
                ),
            )
        return

    if args.workspace:
        workspace_result = audit_workspace(Path(args.workspace), recursive=args.recursive)
        base_markdown = render_workspace_report(workspace_result)
        markdown = enrich_workspace_markdown(
            base_markdown,
            workspace_result.sorted_results,
            include_org_health=args.org_health,
            policy_path=policy_path,
        )
        print(markdown)

        md_path, json_path = build_output_paths(args.output, f"{workspace_result.root_path.name}-workspace-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(
                json_path,
                enrich_workspace_payload(
                    workspace_result_to_dict(workspace_result),
                    workspace_result.sorted_results,
                    include_org_health=args.org_health,
                    policy_path=policy_path,
                ),
            )
        return

    if args.github_repo:
        owner, repo = parse_github_repo_slug(args.github_repo)
        result = audit_github_repository(owner, repo, client=github_client)
        markdown = enrich_repo_markdown(
            result,
            include_portfolio=args.portfolio,
            include_doctor=args.doctor,
            policy_path=policy_path,
        )
        print(markdown)

        md_path, json_path = build_output_paths(args.output, f"{owner}__{repo}-github-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(
                json_path,
                enrich_repo_payload(
                    result,
                    include_portfolio=args.portfolio,
                    include_doctor=args.doctor,
                    policy_path=policy_path,
                ),
            )
        return

    if args.github_user:
        github_result = audit_github_user(
            args.github_user,
            client=github_client,
            include_forks=args.include_forks,
        )
        base_markdown = render_github_workspace_report(github_result)
        markdown = enrich_workspace_markdown(
            base_markdown,
            github_result.sorted_results,
            include_org_health=args.org_health,
            policy_path=policy_path,
        )
        print(markdown)

        md_path, json_path = build_output_paths(args.output, f"{args.github_user}-github-user-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(
                json_path,
                enrich_workspace_payload(
                    github_workspace_result_to_dict(github_result),
                    github_result.sorted_results,
                    include_org_health=args.org_health,
                    policy_path=policy_path,
                ),
            )
        return

    if args.github_org:
        github_result = audit_github_org(
            args.github_org,
            client=github_client,
            include_forks=args.include_forks,
        )
        base_markdown = render_github_workspace_report(github_result)
        markdown = enrich_workspace_markdown(
            base_markdown,
            github_result.sorted_results,
            include_org_health=args.org_health,
            policy_path=policy_path,
        )
        print(markdown)

        md_path, json_path = build_output_paths(args.output, f"{args.github_org}-github-org-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(
                json_path,
                enrich_workspace_payload(
                    github_workspace_result_to_dict(github_result),
                    github_result.sorted_results,
                    include_org_health=args.org_health,
                    policy_path=policy_path,
                ),
            )
        return

    parser.error(
        "Use one of: --demo, --path <repo_path>, --workspace <parent_directory>, "
        "--github-repo <owner/repo>, --github-user <username>, or --github-org <org>."
    )


if __name__ == "__main__":
    main()