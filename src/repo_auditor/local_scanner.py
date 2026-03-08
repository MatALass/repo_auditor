from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
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

DOC_EXTENSIONS = {".md", ".rst", ".txt"}
INFRA_FILE_NAMES = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "terraform.tfvars",
}
INFRA_EXTENSIONS = {".tf", ".tfvars", ".hcl"}
INFRA_PATH_MARKERS = {".github/workflows", "terraform", "helm", "k8s", "kubernetes", "ansible"}
DATA_DIR_MARKERS = {"data", "datasets", "notebooks", "models", "experiments"}
CLI_FILE_NAMES = {"cli.py", "main.py", "__main__.py"}
CLI_PATH_MARKERS = {"bin/", "cli/", "commands/"}
ML_FILE_MARKERS = {
    "train.py",
    "trainer.py",
    "predict.py",
    "inference.py",
    "model.py",
    "pipeline.py",
}
ML_PATH_MARKERS = {"models/", "training/", "experiments/", "pipelines/"}
ML_KEYWORDS = {
    "sklearn",
    "scikit-learn",
    "xgboost",
    "lightgbm",
    "catboost",
    "tensorflow",
    "keras",
    "pytorch",
    "torch",
}


@dataclass(slots=True)
class ScanOptions:
    max_file_size_bytes: int = 1_000_000
    max_readme_size_bytes: int = 500_000


def is_ignored_path(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def is_code_file(path: Path | PurePosixPath) -> bool:
    return path.suffix.lower() in CODE_EXTENSIONS


def is_test_file(path: Path | PurePosixPath) -> bool:
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


def _has_any_path_marker(lower_paths: list[str], markers: set[str]) -> bool:
    return any(marker in path for marker in markers for path in lower_paths)


def _has_any_name_fragment(lower_names: list[str], fragments: set[str]) -> bool:
    joined = " ".join(lower_names)
    return any(fragment in joined for fragment in fragments)


def detect_repo_type(all_paths: list[str], file_names: list[str]) -> str:
    lower_paths = [path.lower() for path in all_paths]
    lower_names = [name.lower() for name in file_names]
    lower_root_names = {name.lower() for name in file_names if "/" not in name and "\\" not in name}

    notebook_count = sum(1 for path in lower_paths if path.endswith(".ipynb"))
    python_count = sum(1 for path in lower_paths if path.endswith(".py"))
    js_count = sum(1 for path in lower_paths if path.endswith((".js", ".ts", ".jsx", ".tsx")))
    html_count = sum(1 for path in lower_paths if path.endswith((".html", ".css")))
    markdown_count = sum(1 for path in lower_paths if PurePosixPath(path).suffix in DOC_EXTENSIONS)
    infra_count = sum(
        1
        for path in lower_paths
        if PurePosixPath(path).name in INFRA_FILE_NAMES or PurePosixPath(path).suffix in INFRA_EXTENSIONS
    )

    has_streamlit = any("streamlit" in path for path in lower_paths) or "streamlit" in " ".join(lower_names)
    has_django = "manage.py" in lower_names
    has_package_json = "package.json" in lower_names
    has_python_manifest = "pyproject.toml" in lower_names or "requirements.txt" in lower_names or "setup.py" in lower_names
    has_rendered_front = has_package_json and html_count > 0
    has_game_hint = any(
        keyword in " ".join(lower_names)
        for keyword in ["tetris", "game", "jumper", "maze", "pygame", "arcade", "unity"]
    )

    has_docs_dir = any(path.startswith("docs/") for path in lower_paths)
    has_docsite_config = any(name in lower_names for name in {"mkdocs.yml", "docusaurus.config.js", "docusaurus.config.ts"})
    has_infra_signal = infra_count > 0 or _has_any_path_marker(lower_paths, INFRA_PATH_MARKERS)
    has_data_signal = notebook_count >= 1 or any(part in DATA_DIR_MARKERS for part in lower_root_names)
    has_cli_signal = (
        any(name in CLI_FILE_NAMES for name in lower_names)
        or any(path.startswith(marker) for marker in CLI_PATH_MARKERS for path in lower_paths)
        or "argparse" in " ".join(lower_names)
    )
    has_ml_signal = (
        any(name in ML_FILE_MARKERS for name in lower_names)
        or _has_any_path_marker(lower_paths, ML_PATH_MARKERS)
        or _has_any_name_fragment(lower_names, ML_KEYWORDS)
    )

    if has_streamlit:
        return "streamlit_app"

    if has_django:
        return "django_app"

    if has_package_json and has_rendered_front:
        return "web_app"

    if has_game_hint and (python_count > 0 or js_count > 0):
        return "game_project"

    if has_ml_signal and (python_count > 0 or notebook_count > 0):
        return "ml_project"

    if has_data_signal and (python_count > 0 or notebook_count >= 2):
        return "data_science_project"

    if has_cli_signal and (python_count > 0 or js_count > 0):
        return "cli_tool"

    if has_infra_signal and python_count == 0 and js_count == 0:
        return "config_or_infra_project"

    if (has_docs_dir or has_docsite_config) and markdown_count >= max(3, python_count + js_count + 1):
        return "documentation_project"

    if notebook_count >= 2:
        return "notebook_project"

    if has_python_manifest and python_count > 0:
        return "python_project"

    if has_package_json and js_count > 0:
        return "javascript_project"

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

    repo_type = detect_repo_type(
        all_paths=all_paths,
        file_names=root_files + [Path(path).name for path in all_paths],
    )

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
        repo_type=repo_type,
    )