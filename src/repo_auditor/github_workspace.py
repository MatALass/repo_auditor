from __future__ import annotations

from dataclasses import dataclass, field

from repo_auditor.github_client import GitHubApiError, GitHubClient
from repo_auditor.github_scanner import scan_github_repository
from repo_auditor.models import RepoAuditResult
from repo_auditor.scoring import audit_repo
from repo_auditor.workspace import repo_rank_key


@dataclass(slots=True)
class GitHubRepoFailure:
    owner: str
    repo_name: str
    error: str


@dataclass(slots=True)
class GitHubWorkspaceAuditResult:
    source_type: str  # github_user, github_org
    source_name: str
    repo_results: list[RepoAuditResult]
    failed_repositories: list[GitHubRepoFailure] = field(default_factory=list)

    @property
    def repo_count(self) -> int:
        return len(self.repo_results)

    @property
    def failed_count(self) -> int:
        return len(self.failed_repositories)

    @property
    def sorted_results(self) -> list[RepoAuditResult]:
        return sorted(self.repo_results, key=repo_rank_key)

    @property
    def worst_repo(self) -> RepoAuditResult | None:
        ranked = self.sorted_results
        return ranked[0] if ranked else None


def audit_github_repository(
    owner: str,
    repo: str,
    *,
    client: GitHubClient,
) -> RepoAuditResult:
    facts = scan_github_repository(owner, repo, client=client)
    return audit_repo(facts)


def audit_github_user(
    username: str,
    *,
    client: GitHubClient,
    include_forks: bool = False,
) -> GitHubWorkspaceAuditResult:
    repo_payloads = client.list_user_repositories(username, include_forks=include_forks)
    results: list[RepoAuditResult] = []
    failures: list[GitHubRepoFailure] = []

    for repo_payload in repo_payloads:
        owner = str(repo_payload["owner"]["login"])
        repo_name = str(repo_payload["name"])

        try:
            results.append(audit_github_repository(owner, repo_name, client=client))
        except Exception as exc:
            failures.append(
                GitHubRepoFailure(
                    owner=owner,
                    repo_name=repo_name,
                    error=str(exc),
                )
            )

    return GitHubWorkspaceAuditResult(
        source_type="github_user",
        source_name=username,
        repo_results=results,
        failed_repositories=failures,
    )


def audit_github_org(
    org: str,
    *,
    client: GitHubClient,
    include_forks: bool = False,
) -> GitHubWorkspaceAuditResult:
    repo_payloads = client.list_org_repositories(org, include_forks=include_forks)
    results: list[RepoAuditResult] = []
    failures: list[GitHubRepoFailure] = []

    for repo_payload in repo_payloads:
        owner = str(repo_payload["owner"]["login"])
        repo_name = str(repo_payload["name"])

        try:
            results.append(audit_github_repository(owner, repo_name, client=client))
        except Exception as exc:
            failures.append(
                GitHubRepoFailure(
                    owner=owner,
                    repo_name=repo_name,
                    error=str(exc),
                )
            )

    return GitHubWorkspaceAuditResult(
        source_type="github_org",
        source_name=org,
        repo_results=results,
        failed_repositories=failures,
    )