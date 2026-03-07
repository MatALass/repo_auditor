from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class RepoFacts:
    name: str
    description: str
    root_files: List[str]
    root_dirs: List[str]
    all_paths: List[str]
    readme_text: str | None
    file_line_counts: Dict[str, int]
    manifest_files: List[str]
    tooling_files: List[str]
    has_gitignore: bool
    has_license: bool
    has_env_example: bool
    code_file_count: int
    test_file_count: int
    recent_push_days: int | None = None
    repo_type: str = "generic_project"


@dataclass(slots=True)
class AuditIssue:
    code: str
    title: str
    why_it_matters: str
    recommendation: str
    severity: str  # low, medium, high


@dataclass(slots=True)
class ActionRecommendation:
    code: str
    title: str
    description: str
    rationale: str
    steps: List[str]
    impact: str  # low, medium, high
    effort: str  # low, medium, high
    priority_score: int
    source_issue_codes: List[str] = field(default_factory=list)


@dataclass(slots=True)
class CategoryScore:
    name: str
    score: int
    max_score: int
    issues: List[AuditIssue] = field(default_factory=list)


@dataclass(slots=True)
class RepoAuditResult:
    repo_name: str
    total_score: int
    max_score: int
    level: str
    repo_type: str
    category_scores: List[CategoryScore]
    priority_issues: List[AuditIssue] = field(default_factory=list)
    prioritized_actions: List[ActionRecommendation] = field(default_factory=list)