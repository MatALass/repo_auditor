from __future__ import annotations

from pathlib import Path

import pytest

from repo_auditor import cli
from repo_auditor.github_workspace import GitHubWorkspaceAuditResult
from repo_auditor.models import (
    ActionRecommendation,
    AuditIssue,
    CategoryScore,
    RepoAuditMetadata,
    RepoAuditResult,
)
from repo_auditor.workspace import WorkspaceAuditResult


def make_issue(code: str, title: str, severity: str = "high") -> AuditIssue:
    return AuditIssue(
        code=code,
        title=title,
        why_it_matters=f"Why {title} matters.",
        recommendation=f"Fix {title}.",
        severity=severity,
    )


def make_action(code: str, title: str, priority_score: int = 120, effort: str = "medium", impact: str = "high") -> ActionRecommendation:
    return ActionRecommendation(
        code=code,
        title=title,
        description=f"Description for {title}.",
        rationale=f"Rationale for {title}.",
        impact=impact,
        effort=effort,
        priority_score=priority_score,
        source_issue_codes=["issue_1"],
        steps=["step 1", "step 2"],
    )


def make_repo_result(
    repo_name: str = "demo-repo",
    score: int = 78,
    repo_type: str = "python_project",
    maturity_band: str = "advanced",
) -> RepoAuditResult:
    issue = make_issue("issue_1", "README missing")
    action = make_action("action_1", "Write a complete README", effort="low", impact="medium")

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
        metadata=RepoAuditMetadata(
            github_topics=["python", "cli"],
            homepage_url="https://example.com",
            has_ci_config=True,
            is_archived=False,
            readme_sections=["overview", "installation", "usage"],
        ),
    )


def make_workspace_result() -> WorkspaceAuditResult:
    repo_result = make_repo_result(repo_name="repo-one", score=42, repo_type="web_app", maturity_band="foundation")
    return WorkspaceAuditResult(
        root_path=Path("/tmp/workspace"),
        repo_results=[repo_result],
    )


def make_github_workspace_result(source_type: str, source_name: str) -> GitHubWorkspaceAuditResult:
    repo_result = make_repo_result(
        repo_name=f"{source_name}/repo-one",
        score=44,
        repo_type="cli_tool",
        maturity_band="developing",
    )
    return GitHubWorkspaceAuditResult(
        source_type=source_type,
        source_name=source_name,
        repo_results=[repo_result],
        failed_repositories=[],
    )


def test_sanitize_stem_replaces_unsafe_characters() -> None:
    assert cli.sanitize_stem("owner/repo name:test") == "owner__repo_name_test"


def test_build_output_paths_returns_none_when_missing_base_path() -> None:
    markdown_path, json_path = cli.build_output_paths(None, "demo")
    assert markdown_path is None
    assert json_path is None


def test_build_output_paths_with_directory() -> None:
    markdown_path, json_path = cli.build_output_paths("reports", "owner/repo-audit")
    assert markdown_path == Path("reports") / "owner__repo-audit.md"
    assert json_path == Path("reports") / "owner__repo-audit.json"


def test_build_output_paths_with_file_path() -> None:
    markdown_path, json_path = cli.build_output_paths("reports/output.md", "ignored")
    assert markdown_path == Path("reports/output.md")
    assert json_path == Path("reports/output.json")


def test_parse_github_repo_slug_valid() -> None:
    owner, repo = cli.parse_github_repo_slug("owner/repo")
    assert owner == "owner"
    assert repo == "repo"


def test_parse_github_repo_slug_invalid() -> None:
    with pytest.raises(ValueError, match="owner/repo"):
        cli.parse_github_repo_slug("invalid-slug")


def test_main_demo_writes_outputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_result = make_repo_result(repo_name="demo-repo")

    monkeypatch.setattr(cli, "audit_repo", lambda facts: repo_result)
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)

    written: dict[str, object] = {}

    def fake_write_text_output(path: Path, content: str) -> None:
        written["text_path"] = path
        written["text_content"] = content

    def fake_write_json_output(path: Path, payload: dict) -> None:
        written["json_path"] = path
        written["json_payload"] = payload

    monkeypatch.setattr(cli, "write_text_output", fake_write_text_output)
    monkeypatch.setattr(cli, "write_json_output", fake_write_json_output)

    monkeypatch.setattr("sys.argv", ["repo-auditor", "--demo", "--output", str(tmp_path)])
    cli.main()

    out = capsys.readouterr().out
    assert "# Repository Audit Report — demo-repo" in out
    assert written["text_path"] == tmp_path / "demo-repo-audit.md"
    assert written["json_path"] == tmp_path / "demo-repo-audit.json"
    assert isinstance(written["json_payload"], dict)


def test_main_demo_with_portfolio_and_doctor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_result = make_repo_result(repo_name="demo-repo", score=82, repo_type="cli_tool", maturity_band="advanced")

    monkeypatch.setattr(cli, "audit_repo", lambda facts: repo_result)
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)

    written: dict[str, object] = {}

    def fake_write_text_output(path: Path, content: str) -> None:
        written["text_path"] = path
        written["text_content"] = content

    def fake_write_json_output(path: Path, payload: dict) -> None:
        written["json_path"] = path
        written["json_payload"] = payload

    monkeypatch.setattr(cli, "write_text_output", fake_write_text_output)
    monkeypatch.setattr(cli, "write_json_output", fake_write_json_output)

    monkeypatch.setattr(
        "sys.argv",
        ["repo-auditor", "--demo", "--portfolio", "--doctor", "--output", str(tmp_path)],
    )
    cli.main()

    out = capsys.readouterr().out
    assert "## Portfolio assessment" in out
    assert "## Doctor mode" in out
    assert isinstance(written["json_payload"], dict)
    assert "portfolio_assessment" in written["json_payload"]
    assert "doctor_summary" in written["json_payload"]


def test_main_path_branch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_result = make_repo_result(repo_name="local-repo", score=64, repo_type="web_app", maturity_band="developing")

    class FakeFacts:
        name = "local-repo"

    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(cli, "scan_local_repository", lambda path, description="": FakeFacts())
    monkeypatch.setattr(cli, "audit_repo", lambda facts: repo_result)

    written: dict[str, object] = {}
    monkeypatch.setattr(cli, "write_text_output", lambda path, content: written.setdefault("text_path", path))
    monkeypatch.setattr(cli, "write_json_output", lambda path, payload: written.setdefault("json_path", path))

    monkeypatch.setattr("sys.argv", ["repo-auditor", "--path", ".", "--output", str(tmp_path)])
    cli.main()

    out = capsys.readouterr().out
    assert "# Repository Audit Report — local-repo" in out
    assert written["text_path"] == tmp_path / "local-repo-audit.md"
    assert written["json_path"] == tmp_path / "local-repo-audit.json"


def test_main_workspace_branch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace_result = make_workspace_result()

    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(cli, "audit_workspace", lambda path, recursive=False: workspace_result)

    written: dict[str, object] = {}
    monkeypatch.setattr(cli, "write_text_output", lambda path, content: written.setdefault("text_path", path))
    monkeypatch.setattr(cli, "write_json_output", lambda path, payload: written.setdefault("json_path", path))

    monkeypatch.setattr("sys.argv", ["repo-auditor", "--workspace", ".", "--output", str(tmp_path)])
    cli.main()

    out = capsys.readouterr().out
    assert "# Workspace Audit Report — workspace" in out
    assert written["text_path"] == tmp_path / "workspace-workspace-audit.md"
    assert written["json_path"] == tmp_path / "workspace-workspace-audit.json"


def test_main_github_repo_branch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_result = make_repo_result(repo_name="owner/repo", score=70, repo_type="cli_tool", maturity_band="advanced")

    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(cli, "audit_github_repository", lambda owner, repo, client: repo_result)

    written: dict[str, object] = {}
    monkeypatch.setattr(cli, "write_text_output", lambda path, content: written.setdefault("text_path", path))
    monkeypatch.setattr(cli, "write_json_output", lambda path, payload: written.setdefault("json_path", path))

    monkeypatch.setattr("sys.argv", ["repo-auditor", "--github-repo", "owner/repo", "--output", str(tmp_path)])
    cli.main()

    out = capsys.readouterr().out
    assert "# Repository Audit Report — owner/repo" in out
    assert written["text_path"] == tmp_path / "owner__repo-github-audit.md"
    assert written["json_path"] == tmp_path / "owner__repo-github-audit.json"


def test_main_github_repo_with_portfolio_custom_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_result = make_repo_result(repo_name="owner/repo", score=60, repo_type="python_project", maturity_band="developing")
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        '{"thresholds":{"keep_min_score":90,"improve_min_score":55,"archive_max_score":20,"soft_keep_min_score":88,"web_improve_floor":25}}',
        encoding="utf-8",
    )

    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(cli, "audit_github_repository", lambda owner, repo, client: repo_result)

    written: dict[str, object] = {}

    def fake_write_json_output(path: Path, payload: dict) -> None:
        written["json_payload"] = payload

    monkeypatch.setattr(cli, "write_text_output", lambda path, content: written.setdefault("text_path", path))
    monkeypatch.setattr(cli, "write_json_output", fake_write_json_output)

    monkeypatch.setattr(
        "sys.argv",
        [
            "repo-auditor",
            "--github-repo",
            "owner/repo",
            "--portfolio",
            "--policy",
            str(policy_path),
            "--output",
            str(tmp_path),
        ],
    )
    cli.main()

    out = capsys.readouterr().out
    assert "## Portfolio assessment" in out
    assert written["json_payload"]["portfolio_assessment"]["decision"] in {"improve", "rebuild", "keep", "archive"}


def test_main_github_user_branch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    github_result = make_github_workspace_result("github_user", "example-user")

    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(cli, "audit_github_user", lambda username, client, include_forks=False: github_result)

    written: dict[str, object] = {}
    monkeypatch.setattr(cli, "write_text_output", lambda path, content: written.setdefault("text_path", path))
    monkeypatch.setattr(cli, "write_json_output", lambda path, payload: written.setdefault("json_path", path))

    monkeypatch.setattr("sys.argv", ["repo-auditor", "--github-user", "example-user", "--output", str(tmp_path)])
    cli.main()

    out = capsys.readouterr().out
    assert "# GitHub Audit Report — github_user:example-user" in out
    assert written["text_path"] == tmp_path / "example-user-github-user-audit.md"
    assert written["json_path"] == tmp_path / "example-user-github-user-audit.json"


def test_main_github_org_branch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    github_result = make_github_workspace_result("github_org", "example-org")

    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(cli, "audit_github_org", lambda org, client, include_forks=False: github_result)

    written: dict[str, object] = {}
    monkeypatch.setattr(cli, "write_text_output", lambda path, content: written.setdefault("text_path", path))
    monkeypatch.setattr(cli, "write_json_output", lambda path, payload: written.setdefault("json_path", path))

    monkeypatch.setattr("sys.argv", ["repo-auditor", "--github-org", "example-org", "--output", str(tmp_path)])
    cli.main()

    out = capsys.readouterr().out
    assert "# GitHub Audit Report — github_org:example-org" in out
    assert written["text_path"] == tmp_path / "example-org-github-org-audit.md"
    assert written["json_path"] == tmp_path / "example-org-github-org-audit.json"


def test_main_rejects_portfolio_for_workspace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr("sys.argv", ["repo-auditor", "--workspace", ".", "--portfolio"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 2


def test_main_rejects_policy_without_portfolio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr("sys.argv", ["repo-auditor", "--demo", "--policy", "config/portfolio_policy.json"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 2


def test_main_without_mode_exits_with_parser_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr("sys.argv", ["repo-auditor"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 2