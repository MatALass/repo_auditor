from __future__ import annotations

from repo_auditor.models import RepoAuditResult
from repo_auditor.workspace import WorkspaceAuditResult


def render_markdown_report(result: RepoAuditResult) -> str:
    lines: list[str] = []
    lines.append(f"# Repository Audit Report — {result.repo_name}")
    lines.append("")
    lines.append(f"**Global score:** {result.total_score}/{result.max_score}")
    lines.append(f"**Level:** {result.level}")
    lines.append("")

    lines.append("## Category scores")
    lines.append("")
    for category in result.category_scores:
        lines.append(f"- **{category.name}**: {category.score}/{category.max_score}")
    lines.append("")

    lines.append("## Priority issues")
    lines.append("")
    if not result.priority_issues:
        lines.append("- No major issue detected.")
    else:
        for issue in result.priority_issues:
            lines.append(f"### {issue.title}")
            lines.append(f"- Severity: **{issue.severity}**")
            lines.append(f"- Why it matters: {issue.why_it_matters}")
            lines.append(f"- Recommendation: {issue.recommendation}")
            lines.append("")

    lines.append("## Detailed category issues")
    lines.append("")
    for category in result.category_scores:
        lines.append(f"### {category.name}")
        if not category.issues:
            lines.append("- No issue detected.")
        else:
            for issue in category.issues:
                lines.append(f"- **{issue.title}** ({issue.severity}) — {issue.recommendation}")
        lines.append("")

    return "\n".join(lines)


def render_workspace_report(workspace_result: WorkspaceAuditResult) -> str:
    lines: list[str] = []

    lines.append(f"# Workspace Audit Report — {workspace_result.root_path.name}")
    lines.append("")
    lines.append(f"**Workspace path:** `{workspace_result.root_path}`")
    lines.append(f"**Repositories analyzed:** {workspace_result.repo_count}")
    lines.append("")

    if workspace_result.repo_count == 0:
        lines.append("No repositories detected in the workspace.")
        return "\n".join(lines)

    worst_repo = workspace_result.worst_repo
    if worst_repo is not None:
        lines.append("## Worst repository")
        lines.append("")
        lines.append(f"- **Name:** {worst_repo.repo_name}")
        lines.append(f"- **Score:** {worst_repo.total_score}/{worst_repo.max_score}")
        lines.append(f"- **Level:** {worst_repo.level}")
        lines.append("")

        lines.append("### Top priority issues")
        lines.append("")
        if not worst_repo.priority_issues:
            lines.append("- No major issue detected.")
        else:
            for issue in worst_repo.priority_issues:
                lines.append(f"- **{issue.title}** ({issue.severity}) — {issue.recommendation}")
        lines.append("")

    lines.append("## Repository ranking")
    lines.append("")
    for index, repo_result in enumerate(workspace_result.sorted_results, start=1):
        lines.append(
            f"{index}. **{repo_result.repo_name}** — "
            f"{repo_result.total_score}/{repo_result.max_score} ({repo_result.level})"
        )
    lines.append("")

    lines.append("## Per-repository summaries")
    lines.append("")
    for repo_result in workspace_result.sorted_results:
        lines.append(f"### {repo_result.repo_name}")
        lines.append(f"- Score: **{repo_result.total_score}/{repo_result.max_score}**")
        lines.append(f"- Level: **{repo_result.level}**")
        if repo_result.priority_issues:
            lines.append("- Top issues:")
            for issue in repo_result.priority_issues:
                lines.append(f"  - {issue.title} ({issue.severity})")
        else:
            lines.append("- Top issues: none")
        lines.append("")

    return "\n".join(lines)