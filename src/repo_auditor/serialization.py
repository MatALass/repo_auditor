from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

from repo_auditor.models import RepoAuditResult
from repo_auditor.workspace import WorkspaceAuditResult


def repo_result_to_dict(result: RepoAuditResult) -> dict:
    return asdict(result)


def workspace_result_to_dict(result: WorkspaceAuditResult) -> dict:
    worst_repo = result.worst_repo

    return {
        "root_path": str(result.root_path),
        "repo_count": result.repo_count,
        "worst_repo_name": worst_repo.repo_name if worst_repo else None,
        "results": [repo_result_to_dict(repo_result) for repo_result in result.sorted_results],
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