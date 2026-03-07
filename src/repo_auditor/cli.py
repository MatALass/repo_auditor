from __future__ import annotations

import argparse
from pathlib import Path

from repo_auditor.local_scanner import scan_local_repository
from repo_auditor.models import RepoFacts
from repo_auditor.report import render_markdown_report, render_workspace_report
from repo_auditor.scoring import audit_repo
from repo_auditor.serialization import (
    repo_result_to_dict,
    workspace_result_to_dict,
    write_json_output,
    write_text_output,
)
from repo_auditor.workspace import audit_workspace


def build_demo_repo() -> RepoFacts:
    return RepoFacts(
        name="demo-repo",
        description="A small Python project for repository quality auditing.",
        root_files=["README.md", "pyproject.toml", ".gitignore"],
        root_dirs=["src", "tests", "docs"],
        all_paths=[
            "README.md",
            "pyproject.toml",
            ".gitignore",
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "docs/architecture.md",
        ],
        readme_text="""
# Demo Repo

## Overview
This project audits repositories.

## Installation
pip install -e .

## Usage
repo-auditor --path .

## Structure
- src/
- tests/
- docs/

## Demo
Example output is provided.

## Roadmap
Add GitHub API support.
""",
        file_line_counts={
            "src/main.py": 120,
            "src/utils.py": 80,
            "tests/test_main.py": 60,
        },
        manifest_files=["pyproject.toml"],
        tooling_files=["pytest.ini"],
        has_gitignore=True,
        has_license=False,
        has_env_example=False,
        code_file_count=2,
        test_file_count=1,
        recent_push_days=10,
        repo_type="python_project",
    )


def build_output_paths(base_path: str | None, default_stem: str) -> tuple[Path | None, Path | None]:
    if not base_path:
        return None, None

    base = Path(base_path)
    if base.suffix:
        markdown_path = base
        json_path = base.with_suffix(".json")
        return markdown_path, json_path

    markdown_path = base / f"{default_stem}.md"
    json_path = base / f"{default_stem}.json"
    return markdown_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit repositories and rank them by structural quality.")
    parser.add_argument("--demo", action="store_true", help="Run the demo repository audit.")
    parser.add_argument("--path", type=str, help="Scan a single local repository path.")
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Optional repository description for the audit context.",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        help="Scan a parent directory containing multiple repositories.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively discover repositories inside the workspace.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help=(
            "Output directory or base file path for exported reports. "
            "If a directory/base path is provided, both Markdown and JSON are written."
        ),
    )
    args = parser.parse_args()

    if args.demo:
        facts = build_demo_repo()
        result = audit_repo(facts)
        markdown = render_markdown_report(result)
        print(markdown)

        md_path, json_path = build_output_paths(args.output, "demo-repo-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(json_path, repo_result_to_dict(result))
        return

    if args.path:
        facts = scan_local_repository(Path(args.path), description=args.description)
        result = audit_repo(facts)
        markdown = render_markdown_report(result)
        print(markdown)

        md_path, json_path = build_output_paths(args.output, f"{facts.name}-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(json_path, repo_result_to_dict(result))
        return

    if args.workspace:
        workspace_result = audit_workspace(Path(args.workspace), recursive=args.recursive)
        markdown = render_workspace_report(workspace_result)
        print(markdown)

        md_path, json_path = build_output_paths(args.output, f"{workspace_result.root_path.name}-workspace-audit")
        if md_path and json_path:
            write_text_output(md_path, markdown)
            write_json_output(json_path, workspace_result_to_dict(workspace_result))
        return

    parser.error("Use one of: --demo, --path <repo_path>, or --workspace <parent_directory>.")


if __name__ == "__main__":
    main()