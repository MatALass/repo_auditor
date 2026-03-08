from __future__ import annotations

import pytest

from repo_auditor.github_workspace import (
    GitHubWorkspaceAuditResult,
    audit_github_org,
    audit_github_repository,
    audit_github_user,
)
from repo_auditor.models import (
    ActionRecommendation,
    AuditIssue,
    CategoryScore,
    RepoAuditResult,
)


class DummyClient:
    def __init__(self) -> None:
        self.user_include_forks: list[bool] = []
        self.org_include_forks: list[bool] = []

    def list_user_repositories(self, username: str, *, include_forks: bool = False) -> list[dict]:
        self.user_include_forks.append(include_forks)
        return [
            {"name": "repo-a", "owner": {"login": username}},
            {"name": "repo-b", "owner": {"login": username}},
            {"name": "repo-c", "owner": {"login": username}},
        ]

    def list_org_repositories(self, org: str, *, include_forks: bool = False) -> list[dict]:
        self.org_include_forks.append(include_forks)
        return [
            {"name": "repo-1", "owner": {"login": org}},
            {"name": "repo-2", "owner": {"login": org}},
        ]


def make_issue(code: str, title: str, severity: str = "high") -> AuditIssue:
    return AuditIssue(
        code=code,
        title=title,
        why_it_matters=f"Why {title} matters.",
        recommendation=f"Fix {title}.",
        severity=severity,
    )


def make_action(code: str, title: str, priority_score: int = 120) -> ActionRecommendation:
    return ActionRecommendation(
        code=code,
        title=title,
        description=f"Description for {title}.",
        rationale=f"Rationale for {title}.",
        impact="high",
        effort="medium",
        priority_score=priority_score,
        source_issue_codes=["issue_1"],
        steps=["step 1", "step 2"],
    )


def make_repo_result(
    repo_name: str,
    score: int,
    *,
    severity: str = "high",
    repo_type: str = "python_project",
    maturity_band: str = "advanced",
) -> RepoAuditResult:
    issue = make_issue("issue_1", f"Issue for {repo_name}", severity=severity)
    action = make_action("action_1", f"Action for {repo_name}")

    return RepoAuditResult(
        repo_name=repo_name,
        total_score=score,
        max_score=100,
        level="good",
        repo_type=repo_type,
        maturity_band=maturity_band,
        category_scores=[
            CategoryScore(
                name="Documentation",
                score=12,
                max_score=20,
                issues=[issue],
            )
        ],
        priority_issues=[issue],
        prioritized_actions=[action],
    )


def test_github_workspace_properties() -> None:
    result = GitHubWorkspaceAuditResult(
        source_type="github_user",
        source_name="matalass",
        repo_results=[],
    )

    assert result.repo_count == 0
    assert result.failed_count == 0
    assert result.worst_repo is None
    assert result.sorted_results == []


def test_github_workspace_sorted_results_and_worst_repo() -> None:
    weaker = make_repo_result("owner/repo-weaker", 42, severity="high")
    stronger = make_repo_result("owner/repo-stronger", 78, severity="low")

    result = GitHubWorkspaceAuditResult(
        source_type="github_org",
        source_name="acme",
        repo_results=[stronger, weaker],
    )

    assert [repo.repo_name for repo in result.sorted_results] == [
        "owner/repo-weaker",
        "owner/repo-stronger",
    ]
    assert result.worst_repo == weaker


def test_audit_github_repository_calls_scan_then_scoring(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = DummyClient()
    expected_facts = object()
    expected_result = make_repo_result("octo/demo", 65)

    def fake_scan(owner: str, repo: str, *, client) -> object:
        assert owner == "octo"
        assert repo == "demo"
        assert client is fake_client
        return expected_facts

    def fake_audit_repo(facts: object) -> RepoAuditResult:
        assert facts is expected_facts
        return expected_result

    monkeypatch.setattr("repo_auditor.github_workspace.scan_github_repository", fake_scan)
    monkeypatch.setattr("repo_auditor.github_workspace.audit_repo", fake_audit_repo)

    result = audit_github_repository("octo", "demo", client=fake_client)

    assert result == expected_result


def test_audit_github_user_collects_results_and_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DummyClient()

    def fake_audit_github_repository(owner: str, repo: str, *, client) -> RepoAuditResult:
        if repo == "repo-b":
            raise RuntimeError("branch API timeout")
        scores = {"repo-a": 71, "repo-c": 39}
        return make_repo_result(f"{owner}/{repo}", scores[repo])

    monkeypatch.setattr("repo_auditor.github_workspace.audit_github_repository", fake_audit_github_repository)

    result = audit_github_user("matalass", client=client, include_forks=True)

    assert client.user_include_forks == [True]
    assert result.source_type == "github_user"
    assert result.source_name == "matalass"
    assert result.repo_count == 2
    assert result.failed_count == 1
    assert [repo.repo_name for repo in result.sorted_results] == [
        "matalass/repo-c",
        "matalass/repo-a",
    ]
    assert result.worst_repo is not None
    assert result.worst_repo.repo_name == "matalass/repo-c"
    assert len(result.failed_repositories) == 1
    failure = result.failed_repositories[0]
    assert failure.owner == "matalass"
    assert failure.repo_name == "repo-b"
    assert failure.error == "branch API timeout"


def test_audit_github_org_collects_results_and_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DummyClient()

    def fake_audit_github_repository(owner: str, repo: str, *, client) -> RepoAuditResult:
        if repo == "repo-2":
            raise ValueError("missing default branch")
        return make_repo_result(f"{owner}/{repo}", 58)

    monkeypatch.setattr("repo_auditor.github_workspace.audit_github_repository", fake_audit_github_repository)

    result = audit_github_org("acme", client=client)

    assert client.org_include_forks == [False]
    assert result.source_type == "github_org"
    assert result.source_name == "acme"
    assert result.repo_count == 1
    assert result.failed_count == 1
    assert result.worst_repo is not None
    assert result.worst_repo.repo_name == "acme/repo-1"
    assert result.failed_repositories[0].owner == "acme"
    assert result.failed_repositories[0].repo_name == "repo-2"
    assert result.failed_repositories[0].error == "missing default branch"