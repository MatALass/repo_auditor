from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repo_auditor.local_scanner import is_code_file, scan_local_repository
from repo_auditor.models import RepoAuditResult
from repo_auditor.scoring import audit_repo


@dataclass(slots=True)
class WorkspaceAuditResult:
    root_path: Path
    repo_results: list[RepoAuditResult]

    @property
    def repo_count(self) -> int:
        return len(self.repo_results)

    @property
    def sorted_results(self) -> list[RepoAuditResult]:
        return sorted(self.repo_results, key=repo_rank_key)

    @property
    def worst_repo(self) -> RepoAuditResult | None:
        ranked = self.sorted_results
        return ranked[0] if ranked else None


def severity_weight(issue_severity: str) -> int:
    mapping = {"high": 3, "medium": 2, "low": 1}
    return mapping.get(issue_severity, 0)


def repo_rank_key(result: RepoAuditResult) -> tuple[int, int, int, int, str]:
    high_issue_count = sum(1 for issue in result.priority_issues if issue.severity == "high")
    total_issue_weight = sum(severity_weight(issue.severity) for issue in result.priority_issues)
    total_issue_count = len(result.priority_issues)

    return (
        result.total_score,
        -high_issue_count,
        -total_issue_weight,
        -total_issue_count,
        result.repo_name.lower(),
    )


def has_code_like_children(path: Path) -> bool:
    for child in path.iterdir():
        if child.is_file() and is_code_file(child):
            return True
    return False


def is_repo_directory(path: Path) -> bool:
    if not path.is_dir():
        return False

    if (path / ".git").exists():
        return True

    repo_markers = {
        "README.md",
        "readme.md",
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
    }

    child_names = {child.name for child in path.iterdir()}
    if child_names.intersection(repo_markers):
        return True

    common_code_dirs = {"src", "app", "lib", "tests"}
    if child_names.intersection(common_code_dirs):
        return True

    if has_code_like_children(path):
        return True

    return False


def discover_repository_directories(root: Path, *, recursive: bool = False) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(f"Workspace path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Workspace path is not a directory: {root}")

    repos: list[Path] = []

    if recursive:
        candidates = [path for path in root.rglob("*") if path.is_dir()]
    else:
        candidates = [path for path in root.iterdir() if path.is_dir()]

    for candidate in sorted(candidates, key=lambda p: p.name.lower()):
        if candidate.name.startswith("."):
            continue
        if is_repo_directory(candidate):
            repos.append(candidate)

    return repos


def audit_workspace(
    root: Path | str,
    *,
    recursive: bool = False,
) -> WorkspaceAuditResult:
    root_path = Path(root).expanduser().resolve()
    repo_dirs = discover_repository_directories(root_path, recursive=recursive)

    repo_results: list[RepoAuditResult] = []
    for repo_dir in repo_dirs:
        facts = scan_local_repository(repo_dir)
        result = audit_repo(facts)
        repo_results.append(result)

    return WorkspaceAuditResult(
        root_path=root_path,
        repo_results=repo_results,
    )