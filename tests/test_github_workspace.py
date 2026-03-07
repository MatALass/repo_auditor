from __future__ import annotations

from repo_auditor.github_workspace import GitHubWorkspaceAuditResult


def test_github_workspace_properties() -> None:
    result = GitHubWorkspaceAuditResult(
        source_type="github_user",
        source_name="matalass",
        repo_results=[],
    )

    assert result.repo_count == 0
    assert result.worst_repo is None
    assert result.sorted_results == []