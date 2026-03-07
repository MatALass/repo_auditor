from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from repo_auditor.models import RepoFacts
from repo_auditor.rules import README_NAMES


CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".scala",
    ".sql",
    ".r",
    ".lua",
    ".dart",
}

MANIFEST_NAMES = {
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "package.json",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "go.mod",
}

TOOLING_NAMES = {
    "pytest.ini",
    "tox.ini",
    "ruff.toml",
    ".ruff.toml",
    "mypy.ini",
    ".flake8",
    "tsconfig.json",
    ".prettierrc",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.cjs",
    ".eslintrc.json",
    "vite.config.ts",
    "vitest.config.ts",
    "jest.config.js",
    "jest.config.ts",
}

LICENSE_NAMES = {"LICENSE", "LICENSE.md", "LICENSE.txt"}
ENV_EXAMPLE_NAMES = {
    ".env.example",
    "sample.env",
    "config.example.json",
    "config.example.yaml",
    "config.example.yml",
    "example.config.json",
    "example.config.yaml",
    "example.config.yml",
}
TEST_FILE_MARKERS = (
    "test_",
    "_test.",
    ".test.",
    ".spec.",
)
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
}


@dataclass(slots=True)
class ScanOptions:
    max_file_size_bytes: int = 1_000_000
    max_readme_size_bytes: int = 500_000


def is_ignored_path(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def is_code_file(path: Path) -> bool:
    return path.suffix.lower() in CODE_EXTENSIONS


def is_test_file(path: Path) -> bool:
    path_str = path.as_posix().lower()
    name = path.name.lower()

    if "tests/" in path_str or "/test/" in path_str or "__tests__" in path_str:
        return True

    return any(marker in name for marker in TEST_FILE_MARKERS)


def safe_read_text(path: Path, max_bytes: int) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def count_lines(text: str | None) -> int:
    if text is None or text == "":
        return 0
    return len(text.splitlines())


def discover_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if is_ignored_path(path.relative_to(root)):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def collect_root_entries(root: Path) -> tuple[list[str], list[str]]:
    root_files: list[str] = []
    root_dirs: list[str] = []

    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if child.name in IGNORED_DIRS:
            continue
        if child.is_file():
            root_files.append(child.name)
        elif child.is_dir():
            root_dirs.append(child.name)

    return root_files, root_dirs


def find_first_existing(paths: Iterable[str], all_paths: set[str]) -> str | None:
    for candidate in paths:
        if candidate in all_paths:
            return candidate
    return None


def detect_repo_type(all_paths: list[str], file_names: list[str]) -> str:
    lower_paths = [path.lower() for path in all_paths]
    lower_names = [name.lower() for name in file_names]

    notebook_count = sum(1 for path in lower_paths if path.endswith(".ipynb"))
    if notebook_count >= 2:
        return "notebook_project"

    if "package.json" in lower_names:
        return "javascript_project"

    if "pyproject.toml" in lower_names or "requirements.txt" in lower_names:
        if any("streamlit" in path for path in lower_paths):
            return "data_app"
        return "python_project"

    return "generic_project"


def scan_local_repository(
    root: Path | str,
    *,
    description: str = "",
    options: ScanOptions | None = None,
) -> RepoFacts:
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root_path}")

    options = options or ScanOptions()

    root_files, root_dirs = collect_root_entries(root_path)
    files = discover_files(root_path)
    all_paths = [relative_posix(path, root_path) for path in files]
    all_paths_set = set(all_paths)

    readme_rel_path = find_first_existing(README_NAMES, all_paths_set)
    readme_text = None
    if readme_rel_path is not None:
        readme_text = safe_read_text(root_path / readme_rel_path, options.max_readme_size_bytes)

    manifest_files = [path for path in all_paths if Path(path).name in MANIFEST_NAMES]
    tooling_files = [path for path in all_paths if Path(path).name in TOOLING_NAMES]

    has_gitignore = ".gitignore" in all_paths_set or ".gitignore" in root_files
    has_license = any(name in all_paths_set or name in root_files for name in LICENSE_NAMES)
    has_env_example = any(name in all_paths_set or name in root_files for name in ENV_EXAMPLE_NAMES)

    file_line_counts: dict[str, int] = {}
    code_file_count = 0
    test_file_count = 0

    for rel_path in all_paths:
        file_path = root_path / rel_path
        path_obj = Path(rel_path)

        if is_code_file(path_obj):
            code_file_count += 1
            text = safe_read_text(file_path, options.max_file_size_bytes)
            file_line_counts[rel_path] = count_lines(text)

        if is_test_file(path_obj):
            test_file_count += 1

    repo_type = detect_repo_type(all_paths=all_paths, file_names=root_files + [Path(p).name for p in all_paths])

    return RepoFacts(
        name=root_path.name,
        description=description,
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
        recent_push_days=None,
        repo_type=repo_type,
    )