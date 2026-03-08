from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from repo_auditor.github_workspace import GitHubWorkspaceAuditResult
from repo_auditor.models import (
    ActionRecommendation,
    AuditIssue,
    CategoryScore,
    RepoAuditMetadata,
    RepoAuditResult,
)
from repo_auditor.serialization import (
    github_workspace_result_to_dict,
    repo_audit_result_to_dict,
    write_json_output,
    write_repo_audit_json,
    write_text_output,
    workspace_result_to_dict,
)
from repo_auditor.workspace import WorkspaceAuditResult


@dataclass
class DummyGitHubFailure:
    owner: str
    repo_name: str
    error: str


def make_issue(code: str, title: str, severity: str = "medium") -> AuditIssue:
    return AuditIssue(
        code=code,
        title=title,
        why_it_matters=f"Why {title} matters.",
        recommendation=f"Fix {title}.",
        severity=severity,
    )


def make_action(
    code: str,
    title: str,
    *,
    priority_score: int = 100,
    impact: str = "high",
    effort: str = "medium",
) -> ActionRecommendation:
    return ActionRecommendation(
        code=code,
        title=title,
        description=f"Description for {title}.",
        rationale=f"Rationale for {title}.",
        steps=["step 1", "step 2"],
        impact=impact,
        effort=effort,
        priority_score=priority_score,
        source_issue_codes=["issue_1"],
    )


def make_repo_result(
    repo_name: str = "octo/repo-auditor",
    *,
    score: int = 82,
    repo_type: str = "cli_tool",
    maturity_band: str = "advanced",
) -> RepoAuditResult:
    issue = make_issue("issue_1", "README missing key sections")
    action = make_action("action_1", "Improve README", priority_score=120)

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
                score=17,
                max_score=20,
                issues=[issue],
            )
        ],
        priority_issues=[issue],
        prioritized_actions=[action],
        metadata=RepoAuditMetadata(
            github_topics=["python", "cli", "auditing"],
            homepage_url="https://example.com/repo-auditor",
            has_ci_config=True,
            is_archived=False,
            readme_sections=["overview", "installation", "usage", "demo"],
        ),
    )


def test_repo_audit_result_to_dict_includes_metadata() -> None:
    result = make_repo_result()

    payload = repo_audit_result_to_dict(result)

    assert payload["repo_name"] == "octo/repo-auditor"
    assert payload["total_score"] == 82
    assert payload["repo_type"] == "cli_tool"
    assert payload["metadata"]["github_topics"] == ["python", "cli", "auditing"]
    assert payload["metadata"]["homepage_url"] == "https://example.com/repo-auditor"
    assert payload["metadata"]["has_ci_config"] is True
    assert payload["metadata"]["is_archived"] is False
    assert payload["metadata"]["readme_sections"] == ["overview", "installation", "usage", "demo"]
    json.dumps(payload)


def test_workspace_result_to_dict_serializes_sorted_results_and_worst_repo() -> None:
    weaker = make_repo_result("repo-b", score=41, repo_type="web_app", maturity_band="foundation")
    stronger = make_repo_result("repo-a", score=78)

    result = WorkspaceAuditResult(
        root_path=Path("/tmp/workspace"),
        repo_results=[stronger, weaker],
    )

    payload = workspace_result_to_dict(result)

    assert payload["workspace_type"] == "local_workspace"
    assert payload["root_path"] == str(Path("/tmp/workspace"))
    assert payload["repo_count"] == 2
    assert payload["worst_repo_name"] == "repo-b"
    assert [item["repo_name"] for item in payload["results"]] == ["repo-b", "repo-a"]


def test_github_workspace_result_to_dict_serializes_failures() -> None:
    weaker = make_repo_result("acme/repo-b", score=33, repo_type="python_project", maturity_band="foundation")
    stronger = make_repo_result("acme/repo-a", score=74)

    result = GitHubWorkspaceAuditResult(
        source_type="github_org",
        source_name="acme",
        repo_results=[stronger, weaker],
        failed_repositories=[
            DummyGitHubFailure(
                owner="acme",
                repo_name="repo-c",
                error="default branch not found",
            )
        ],
    )

    payload = github_workspace_result_to_dict(result)

    assert payload["workspace_type"] == "github_org"
    assert payload["source_name"] == "acme"
    assert payload["repo_count"] == 2
    assert payload["failed_count"] == 1
    assert payload["worst_repo_name"] == "acme/repo-b"
    assert [item["repo_name"] for item in payload["results"]] == ["acme/repo-b", "acme/repo-a"]
    assert payload["failed_repositories"] == [
        {
            "owner": "acme",
            "repo_name": "repo-c",
            "error": "default branch not found",
        }
    ]


def test_write_text_output_creates_parent_dirs_and_writes_content(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "report.md"

    write_text_output(output_path, "# Hello\n\ncontent\n")

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "# Hello\n\ncontent\n"


def test_write_json_output_creates_parent_dirs_and_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "report.json"
    payload = {
        "repo_name": "octo/repo-auditor",
        "score": 82,
        "metadata": {"ci": True},
    }

    write_json_output(output_path, payload)

    assert output_path.exists()
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded == payload


def test_write_repo_audit_json_writes_serialized_repo_payload(tmp_path: Path) -> None:
    result = make_repo_result()
    output_path = tmp_path / "exports" / "repo_audit.json"

    returned_path = write_repo_audit_json(result, output_path)

    assert returned_path == output_path
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["repo_name"] == "octo/repo-auditor"
    assert payload["metadata"]["homepage_url"] == "https://example.com/repo-auditor"
    assert payload["prioritized_actions"][0]["title"] == "Improve README"