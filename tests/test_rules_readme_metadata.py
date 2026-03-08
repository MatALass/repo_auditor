from __future__ import annotations

from repo_auditor.models import RepoFacts
from repo_auditor.rules import extract_readme_sections, has_ci_signal, has_keyword_section


def make_facts(*, readme_text: str | None, readme_sections: list[str], has_ci_config: bool = False) -> RepoFacts:
    return RepoFacts(
        name="demo",
        description="Demo repository for tests.",
        root_files=["README.md"],
        root_dirs=["src"],
        all_paths=["README.md", "src/main.py"],
        readme_text=readme_text,
        file_line_counts={"src/main.py": 10},
        manifest_files=["pyproject.toml"],
        tooling_files=[],
        has_gitignore=True,
        has_license=False,
        has_env_example=False,
        code_file_count=1,
        test_file_count=0,
        readme_sections=readme_sections,
        github_topics=[],
        homepage_url=None,
        has_ci_config=has_ci_config,
        is_archived=False,
        repo_type="python_project",
    )


def test_extract_readme_sections_normalizes_common_section_names() -> None:
    readme = """
# Demo Project

## Getting Started
Text.

## Quick Start
Text.

## Architecture
Text.

### Screenshots
Text.

## Next Steps
Text.
"""

    assert extract_readme_sections(readme) == [
        "demo project",
        "installation",
        "usage",
        "structure",
        "demo",
        "roadmap",
    ]


def test_has_keyword_section_uses_structured_readme_sections_first() -> None:
    facts = make_facts(readme_text="# Demo\n", readme_sections=["installation", "usage", "structure"])

    assert has_keyword_section(facts, ["setup", "getting started"])
    assert has_keyword_section(facts, ["how to run", "quickstart"])
    assert has_keyword_section(facts, ["architecture", "project structure"])


def test_has_ci_signal_uses_cached_fact_field() -> None:
    facts = make_facts(readme_text=None, readme_sections=[], has_ci_config=True)
    assert has_ci_signal(facts) is True