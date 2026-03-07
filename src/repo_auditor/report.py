from __future__ import annotations

from repo_auditor.github_workspace import GitHubWorkspaceAuditResult
from repo_auditor.models import RepoAuditResult
from repo_auditor.workspace import WorkspaceAuditResult


def render_markdown_report(result: RepoAuditResult) -> str:
    lines: list[str] = []
    lines.append(f"# Repository Audit Report — {result.repo_name}")
    lines.append("")
    lines.append(f"**Global score:** {result.total_score}/{result.max_score}")
    lines.append(f"**Level:** {result.level}")
    lines.append(f"**Detected project type:** {result.repo_type}")
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

    lines.append("## Prioritized action plan")
    lines.append("")
    if not result.prioritized_actions:
        lines.append("- No action plan generated.")
    else:
        for index, action in enumerate(result.prioritized_actions, start=1):
            lines.append(f"### {index}. {action.title}")
            lines.append(f"- Priority score: **{action.priority_score}**")
            lines.append(f"- Impact: **{action.impact}**")
            lines.append(f"- Effort: **{action.effort}**")
            lines.append(f"- Why this matters: {action.rationale}")
            lines.append(f"- Description: {action.description}")
            lines.append("- Recommended steps:")
            for step in action.steps:
                lines.append(f"  - {step}")
            if action.source_issue_codes:
                lines.append(f"- Linked issues: {', '.join(action.source_issue_codes)}")
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
        lines.append(f"- **Type:** {worst_repo.repo_type}")
        lines.append("")

        lines.append("### Top priority issues")
        lines.append("")
        if not worst_repo.priority_issues:
            lines.append("- No major issue detected.")
        else:
            for issue in worst_repo.priority_issues:
                lines.append(f"- **{issue.title}** ({issue.severity}) — {issue.recommendation}")
        lines.append("")

        lines.append("### Recommended action plan")
        lines.append("")
        if not worst_repo.prioritized_actions:
            lines.append("- No action plan generated.")
        else:
            for index, action in enumerate(worst_repo.prioritized_actions, start=1):
                lines.append(
                    f"{index}. **{action.title}** — "
                    f"priority {action.priority_score}, impact {action.impact}, effort {action.effort}"
                )
        lines.append("")

    lines.append("## Repository ranking")
    lines.append("")
    for index, repo_result in enumerate(workspace_result.sorted_results, start=1):
        lines.append(
            f"{index}. **{repo_result.repo_name}** — "
            f"{repo_result.total_score}/{repo_result.max_score} ({repo_result.level}, {repo_result.repo_type})"
        )
    lines.append("")

    lines.append("## Per-repository summaries")
    lines.append("")
    for repo_result in workspace_result.sorted_results:
        lines.append(f"### {repo_result.repo_name}")
        lines.append(f"- Score: **{repo_result.total_score}/{repo_result.max_score}**")
        lines.append(f"- Level: **{repo_result.level}**")
        lines.append(f"- Type: **{repo_result.repo_type}**")
        if repo_result.priority_issues:
            lines.append("- Top issues:")
            for issue in repo_result.priority_issues:
                lines.append(f"  - {issue.title} ({issue.severity})")
        else:
            lines.append("- Top issues: none")

        if repo_result.prioritized_actions:
            lines.append("- Top actions:")
            for action in repo_result.prioritized_actions[:3]:
                lines.append(
                    f"  - {action.title} "
                    f"[priority={action.priority_score}, impact={action.impact}, effort={action.effort}]"
                )
        else:
            lines.append("- Top actions: none")
        lines.append("")

    return "\n".join(lines)


def render_github_workspace_report(result: GitHubWorkspaceAuditResult) -> str:
    lines: list[str] = []

    lines.append(f"# GitHub Audit Report — {result.source_type}:{result.source_name}")
    lines.append("")
    lines.append(f"**Source type:** {result.source_type}")
    lines.append(f"**Source name:** {result.source_name}")
    lines.append(f"**Repositories analyzed successfully:** {result.repo_count}")
    lines.append(f"**Repositories failed to scan:** {result.failed_count}")
    lines.append("")

    if result.repo_count == 0 and result.failed_count == 0:
        lines.append("No repositories found for this GitHub source.")
        return "\n".join(lines)

    worst_repo = result.worst_repo
    if worst_repo is not None:
        lines.append("## Worst repository")
        lines.append("")
        lines.append(f"- **Name:** {worst_repo.repo_name}")
        lines.append(f"- **Score:** {worst_repo.total_score}/{worst_repo.max_score}")
        lines.append(f"- **Level:** {worst_repo.level}")
        lines.append(f"- **Type:** {worst_repo.repo_type}")
        lines.append("")

        lines.append("### Top priority issues")
        lines.append("")
        if not worst_repo.priority_issues:
            lines.append("- No major issue detected.")
        else:
            for issue in worst_repo.priority_issues:
                lines.append(f"- **{issue.title}** ({issue.severity}) — {issue.recommendation}")
        lines.append("")

        lines.append("### Recommended action plan")
        lines.append("")
        if not worst_repo.prioritized_actions:
            lines.append("- No action plan generated.")
        else:
            for index, action in enumerate(worst_repo.prioritized_actions, start=1):
                lines.append(
                    f"{index}. **{action.title}** — "
                    f"priority {action.priority_score}, impact {action.impact}, effort {action.effort}"
                )
        lines.append("")

    if result.repo_count > 0:
        lines.append("## Repository ranking")
        lines.append("")
        for index, repo_result in enumerate(result.sorted_results, start=1):
            lines.append(
                f"{index}. **{repo_result.repo_name}** — "
                f"{repo_result.total_score}/{repo_result.max_score} ({repo_result.level}, {repo_result.repo_type})"
            )
        lines.append("")

        lines.append("## Per-repository summaries")
        lines.append("")
        for repo_result in result.sorted_results:
            lines.append(f"### {repo_result.repo_name}")
            lines.append(f"- Score: **{repo_result.total_score}/{repo_result.max_score}**")
            lines.append(f"- Level: **{repo_result.level}**")
            lines.append(f"- Type: **{repo_result.repo_type}**")

            if repo_result.priority_issues:
                lines.append("- Top issues:")
                for issue in repo_result.priority_issues:
                    lines.append(f"  - {issue.title} ({issue.severity})")
            else:
                lines.append("- Top issues: none")

            if repo_result.prioritized_actions:
                lines.append("- Top actions:")
                for action in repo_result.prioritized_actions[:3]:
                    lines.append(
                        f"  - {action.title} "
                        f"[priority={action.priority_score}, impact={action.impact}, effort={action.effort}]"
                    )
            else:
                lines.append("- Top actions: none")

            lines.append("")

    if result.failed_repositories:
        lines.append("## Failed repositories")
        lines.append("")
        for failure in result.failed_repositories:
            lines.append(f"- **{failure.owner}/{failure.repo_name}** — {failure.error}")
        lines.append("")

    return "\n".join(lines)