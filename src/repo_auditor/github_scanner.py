from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from repo_auditor.github_client import GitHubClient
from repo_auditor.local_scanner import (
    ENV_EXAMPLE_NAMES,
    LICENSE_NAMES,
    MANIFEST_NAMES,
    TOOLING_NAMES,
    count_lines,
    detect_repo_type,
    is_code_file,
    is_test_file,
)
from repo_auditor.models import RepoFacts


@dataclass(slots=True)
class GitHubScanOptions:
    max_remote_file_size_bytes: int = 200_000
    max_code_files_for_line_counts: int = 40


def parse_github_datetime_to_age_days(value: str | None) -> int | None:
    if not value:
        return None

    parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - parsed
    return max(delta.days, 0)


def build_root_entries(all_paths: list[str]) -> tuple[list[str], list[str]]:
    root_files: set[str] = set()
    root_dirs: set[str] = set()

    for path in all_paths:
        parts = PurePosixPath(path).parts
        if len(parts) == 1:
            root_files.add(parts[0])
        elif len(parts) > 1:
            root_dirs.add(parts[0])

    return sorted(root_files), sorted(root_dirs)


def extract_blob_paths(tree_payload: dict[str, Any]) -> list[str]:
    entries = tree_payload.get("tree", [])
    paths: list[str] = []

    for entry in entries:
        if entry.get("type") == "blob" and entry.get("path"):
            paths.append(str(entry["path"]))

    return sorted(paths)


def select_code_files_for_content_fetch(
    tree_payload: dict[str, Any],
    *,
    max_file_size_bytes: int,
    limit: int,
) -> list[str]:
    candidates: list[tuple[int, str]] = []

    for entry in tree_payload.get("tree", []):
        if entry.get("type") != "blob":
            continue

        path = str(entry.get("path", ""))
        size = int(entry.get("size", 0) or 0)

        if not path:
            continue
        if size > max_file_size_bytes:
            continue
        if not is_code_file(PurePosixPath(path)):
            continue

        candidates.append((size, path))

    candidates.sort(key=lambda item: (-item[0], item[1].lower()))
    return [path for _, path in candidates[:limit]]


def build_manifest_files(all_paths: list[str]) -> list[str]:
    return [path for path in all_paths if PurePosixPath(path).name in MANIFEST_NAMES]


def build_tooling_files(all_paths: list[str]) -> list[str]:
    return [path for path in all_paths if PurePosixPath(path).name in TOOLING_NAMES]


def has_any_named_path(all_paths: list[str], names: set[str]) -> bool:
    return any(PurePosixPath(path).name in names for path in all_paths)


def scan_github_repository(
    owner: str,
    repo: str,
    *,
    client: GitHubClient,
    options: GitHubScanOptions | None = None,
) -> RepoFacts:
    options = options or GitHubScanOptions()

    repo_payload = client.get_repository(owner, repo)
    tree_payload = client.get_repository_tree_from_default_branch(owner, repo)
    readme_text = client.get_readme(owner, repo)

    all_paths = extract_blob_paths(tree_payload)
    root_files, root_dirs = build_root_entries(all_paths)

    manifest_files = build_manifest_files(all_paths)
    tooling_files = build_tooling_files(all_paths)

    has_gitignore = ".gitignore" in all_paths or ".gitignore" in root_files
    has_license = has_any_named_path(all_paths, LICENSE_NAMES) or any(name in root_files for name in LICENSE_NAMES)
    has_env_example = has_any_named_path(all_paths, ENV_EXAMPLE_NAMES) or any(
        name in root_files for name in ENV_EXAMPLE_NAMES
    )

    code_file_count = 0
    test_file_count = 0

    for path in all_paths:
        path_obj = PurePosixPath(path)
        if is_code_file(path_obj):
            code_file_count += 1
        if is_test_file(path_obj):
            test_file_count += 1

    file_line_counts: dict[str, int] = {}
    code_paths_for_content = select_code_files_for_content_fetch(
        tree_payload,
        max_file_size_bytes=options.max_remote_file_size_bytes,
        limit=options.max_code_files_for_line_counts,
    )

    for path in code_paths_for_content:
        text = client.get_file_text(owner, repo, path)
        file_line_counts[path] = count_lines(text)

    repo_type = detect_repo_type(
        all_paths=all_paths,
        file_names=root_files + [PurePosixPath(path).name for path in all_paths],
    )

    return RepoFacts(
        name=str(repo_payload.get("full_name") or f"{owner}/{repo}"),
        description=str(repo_payload.get("description") or ""),
        root_files=root_files,
        root_dirs=root_dirs,
        all_paths=all_paths,
        readme_text=readme_text,
        file_line_counts=file_line_counts,
        manifest_files=manifest_files,
        tooling_files=tooling_files,
        has_gitignore=has_gitignore,
        has_license=has_license,
        has_env_example=has_env_example,
        code_file_count=code_file_count,
        test_file_count=test_file_count,
        recent_push_days=parse_github_datetime_to_age_days(repo_payload.get("pushed_at")),
        repo_type=repo_type,
    )