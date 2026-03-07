from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from repo_auditor.github_workspace import GitHubWorkspaceAuditResult
from repo_auditor.models import RepoAuditResult
from repo_auditor.workspace import WorkspaceAuditResult


def repo_result_to_dict(result: RepoAuditResult) -> dict:
    return asdict(result)


def workspace_result_to_dict(result: WorkspaceAuditResult) -> dict:
    worst_repo = result.worst_repo

    return {
        "workspace_type": "local_workspace",
        "root_path": str(result.root_path),
        "repo_count": result.repo_count,
        "worst_repo_name": worst_repo.repo_name if worst_repo else None,
        "results": [repo_result_to_dict(repo_result) for repo_result in result.sorted_results],
    }


def github_workspace_result_to_dict(result: GitHubWorkspaceAuditResult) -> dict:
    worst_repo = result.worst_repo

    return {
        "workspace_type": result.source_type,
        "source_name": result.source_name,
        "repo_count": result.repo_count,
        "failed_count": result.failed_count,
        "worst_repo_name": worst_repo.repo_name if worst_repo else None,
        "results": [repo_result_to_dict(repo_result) for repo_result in result.sorted_results],
        "failed_repositories": [asdict(failure) for failure in result.failed_repositories],
    }


def write_text_output(path: Path | str, content: str) -> None:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def write_json_output(path: Path | str, payload: dict) -> None:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )