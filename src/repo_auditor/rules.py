from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Iterable

from repo_auditor.issue_catalog import ISSUE_CATALOG
from repo_auditor.models import AuditIssue, RepoFacts


README_NAMES = {"README.md", "readme.md", "README.rst", "README.txt"}
CODE_DIR_NAMES = {"src", "app", "lib", "backend", "frontend"}
TEST_DIR_NAMES = {"tests", "test", "__tests__"}
SUPPORT_DIR_NAMES = {"docs", "assets", "data", "notebooks", "scripts"}
JUNK_PATTERNS = {
    ".DS_Store",
    "Thumbs.db",
    "__pycache__",
    ".ipynb_checkpoints",
}
VAGUE_NAMES = {
    "final.py",
    "new.py",
    "test2.py",
    "temp.py",
    "aaa.py",
    "script1.py",
}
README_SECTION_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE)
README_SECTION_NORMALIZATIONS = {
    "getting started": "installation",
    "setup": "installation",
    "install": "installation",
    "how to run": "usage",
    "quickstart": "usage",
    "quick start": "usage",
    "examples": "demo",
    "screenshots": "demo",
    "preview": "demo",
    "project structure": "structure",
    "architecture": "structure",
    "folder structure": "structure",
    "next steps": "roadmap",
    "future improvements": "roadmap",
    "limitations": "roadmap",
}
README_SECTION_ALIASES = {
    "overview": {"overview", "introduction", "description", "about"},
    "installation": {"installation", "setup", "getting started", "install", "requirements"},
    "usage": {"usage", "run", "how to run", "quickstart", "quick start", "example usage"},
    "structure": {"architecture", "structure", "project structure", "folders", "modules", "folder structure"},
    "demo": {"demo", "example", "examples", "screenshot", "screenshots", "preview", "sample output"},
    "roadmap": {"roadmap", "limitations", "future improvements", "todo", "next steps"},
}


def make_issue(code: str) -> AuditIssue:
    meta = ISSUE_CATALOG[code]
    return AuditIssue(
        code=code,
        title=meta["title"],
        why_it_matters=meta["why_it_matters"],
        recommendation=meta["recommendation"],
        severity=meta["severity"],
    )


def issue_severity_rank(severity: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(severity, 3)


def normalize_text(text: str | None) -> str:
    return (text or "").lower()


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def normalize_readme_section_name(title: str) -> str:
    normalized = re.sub(r"[`*_#:]", " ", title.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip(" -\t\n\r")
    return README_SECTION_NORMALIZATIONS.get(normalized, normalized)


def extract_readme_sections(readme_text: str | None) -> list[str]:
    if not readme_text:
        return []

    sections: list[str] = []
    seen: set[str] = set()

    for match in README_SECTION_PATTERN.finditer(readme_text):
        section = normalize_readme_section_name(match.group(1))
        if not section or section in seen:
            continue
        seen.add(section)
        sections.append(section)

    return sections


def _normalized_readme_keywords(keywords: Iterable[str]) -> set[str]:
    normalized_keywords: set[str] = set()
    for keyword in keywords:
        normalized = normalize_readme_section_name(keyword)
        normalized_keywords.add(normalized)
        normalized_keywords.update(README_SECTION_ALIASES.get(normalized, set()))
    return {normalize_readme_section_name(keyword) for keyword in normalized_keywords}


def has_readme(facts: RepoFacts) -> bool:
    return facts.readme_text is not None


def readme_length(facts: RepoFacts) -> int:
    return len((facts.readme_text or "").strip())


def has_keyword_section(facts: RepoFacts, keywords: Iterable[str]) -> bool:
    normalized_keywords = _normalized_readme_keywords(keywords)
    if any(section in normalized_keywords for section in facts.readme_sections):
        return True
    return contains_any(normalize_text(facts.readme_text), keywords)


def count_useful_root_files(facts: RepoFacts) -> int:
    return len([name for name in facts.root_files if not name.startswith(".")])


def has_main_code_directory(facts: RepoFacts) -> bool:
    return any(directory in CODE_DIR_NAMES for directory in facts.root_dirs)


def has_tests_directory(facts: RepoFacts) -> bool:
    return any(directory in TEST_DIR_NAMES for directory in facts.root_dirs)


def has_support_directory(facts: RepoFacts) -> bool:
    return any(directory in SUPPORT_DIR_NAMES for directory in facts.root_dirs)


def has_inconsistent_naming(facts: RepoFacts) -> bool:
    for path in facts.all_paths:
        name = PurePosixPath(path).name
        if " " in name or name in VAGUE_NAMES:
            return True
    return False


def has_junk_files(facts: RepoFacts) -> bool:
    for path in facts.all_paths:
        name = PurePosixPath(path).name
        if name in JUNK_PATTERNS or name.endswith(".log") or name.endswith(".tmp"):
            return True
    return False


def has_manifest(facts: RepoFacts) -> bool:
    return len(facts.manifest_files) > 0


def has_tooling_config(facts: RepoFacts) -> bool:
    return len(facts.tooling_files) > 0


def has_tests(facts: RepoFacts) -> bool:
    return facts.test_file_count > 0 or has_tests_directory(facts)


def apparent_test_volume_points(facts: RepoFacts) -> int:
    if facts.test_file_count >= 3:
        return 4
    if facts.test_file_count >= 1:
        return 2
    return 0


def has_test_framework_signal(facts: RepoFacts) -> bool:
    text = normalize_text(facts.readme_text)
    combined = " ".join(facts.manifest_files + facts.tooling_files + facts.all_paths).lower()
    return contains_any(
        text + " " + combined,
        ["pytest", "unittest", "jest", "vitest", "mocha", "cypress", "playwright"],
    )


def has_ci_signal(facts: RepoFacts) -> bool:
    return facts.has_ci_config or any(path.startswith(".github/workflows/") for path in facts.all_paths)


def oversized_file_status(facts: RepoFacts) -> str:
    if not facts.file_line_counts:
        return "none"
    max_lines = max(facts.file_line_counts.values(), default=0)
    if max_lines > 1000:
        return "critical"
    if max_lines > 600:
        return "warning"
    return "ok"


def modularity_status(facts: RepoFacts) -> str:
    if facts.code_file_count <= 1:
        return "monolithic"
    if facts.code_file_count <= 3:
        return "weak"
    return "good"


def has_separation_of_concerns_signal(facts: RepoFacts) -> bool:
    concern_dirs = {"core", "api", "services", "models", "components", "utils"}
    for path in facts.all_paths:
        parts = PurePosixPath(path).parts
        if any(part in concern_dirs for part in parts):
            return True
    return False


def has_technical_docs(facts: RepoFacts) -> bool:
    targets = {"ARCHITECTURE.md", "CONTRIBUTING.md", "docs/architecture.md"}
    return any(path in targets or path.startswith("docs/") for path in facts.all_paths)


def repo_is_nearly_empty(facts: RepoFacts) -> bool:
    return len(facts.all_paths) < 5 or facts.code_file_count < 1


def has_demo_signal(facts: RepoFacts) -> bool:
    text = normalize_text(facts.readme_text)
    return "demo" in facts.readme_sections or contains_any(
        text,
        ["demo", "example", "screenshot", "preview", "sample output"],
    )


def has_repo_description(facts: RepoFacts) -> bool:
    return len(facts.description.strip()) > 15


def recent_activity_points(facts: RepoFacts) -> int:
    if facts.recent_push_days is None:
        return 0
    if facts.recent_push_days < 90:
        return 2
    if facts.recent_push_days <= 365:
        return 1
    return 0


def has_github_topics(facts: RepoFacts) -> bool:
    return len([topic for topic in facts.github_topics if topic.strip()]) > 0


def github_topic_count_points(facts: RepoFacts) -> int:
    count = len([topic for topic in facts.github_topics if topic.strip()])
    if count >= 4:
        return 2
    if count >= 2:
        return 1
    return 0


def has_homepage_signal(facts: RepoFacts) -> bool:
    return bool((facts.homepage_url or "").strip())


def is_archived_repo(facts: RepoFacts) -> bool:
    return facts.is_archived


def missing_readme_sections(facts: RepoFacts) -> list[str]:
    missing: list[str] = []
    for key in ["overview", "installation", "usage", "structure", "demo", "roadmap"]:
        if not has_keyword_section(facts, README_SECTION_ALIASES[key]):
            missing.append(key)
    return missing


def has_minimum_readme_sections(facts: RepoFacts) -> bool:
    return len(missing_readme_sections(facts)) <= 2


def project_promise_supported(facts: RepoFacts) -> bool:
    return has_repo_description(facts) and has_readme(facts) and facts.code_file_count > 0


def portfolio_clarity_signal(facts: RepoFacts) -> bool:
    return has_repo_description(facts) and has_readme(facts) and has_minimum_readme_sections(facts)


def technical_credibility_signal(facts: RepoFacts) -> bool:
    quality_signals = [
        has_tests(facts),
        has_tooling_config(facts),
        has_technical_docs(facts),
        has_ci_signal(facts),
    ]
    return has_manifest(facts) and (
        has_main_code_directory(facts) or is_lightweight_app_type(facts.repo_type)
    ) and any(quality_signals)


def interview_ready_signal(facts: RepoFacts) -> bool:
    return has_demo_signal(facts) or has_keyword_section(
        facts,
        ["usage", "run", "quickstart", "how to run"],
    )


def is_notebook_like_type(repo_type: str) -> bool:
    return repo_type in {"notebook_project", "data_science_project", "ml_project"}


def is_lightweight_app_type(repo_type: str) -> bool:
    return repo_type in {"streamlit_app", "game_project", "web_app", "cli_tool"}


def is_small_project_type(repo_type: str) -> bool:
    return repo_type in {
        "game_project",
        "streamlit_app",
        "web_app",
        "generic_project",
        "documentation_project",
        "config_or_infra_project",
    }


def is_empty_like_repo_type(repo_type: str) -> bool:
    return repo_type in {"generic_project", "documentation_project"}