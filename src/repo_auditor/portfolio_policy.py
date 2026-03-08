from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repo_auditor.models import RepoAuditResult


DEFAULT_POLICY: dict[str, Any] = {
    "thresholds": {
        "keep_min_score": 78,
        "improve_min_score": 45,
        "archive_max_score": 24,
        "soft_keep_min_score": 76,
        "web_improve_floor": 25,
    },
    "archive_repo_types": [
        "generic_project",
        "documentation_project",
    ],
    "rebuild_repo_types": [
        "cli_tool",
        "game_project",
        "web_app",
        "python_project",
        "data_science_project",
        "ml_project",
        "streamlit_app",
        "django_app",
        "config_or_infra_project",
    ],
    "archive_maturity_bands": [
        "bootstrap",
        "foundation",
    ],
    "structure_debt_keywords": [
        "monolithic structure",
        "poor separation of concerns",
        "main code directory missing",
        "flat project structure",
        "dedicated source directory",
        "decompose monolithic code structure",
        "improve separation of concerns",
        "restructure the repository layout",
    ],
    "missing_basics_keywords": [
        ".gitignore missing",
        "dependency manifest missing",
        "readme missing",
        "installation instructions missing",
        "usage instructions missing",
        "environment example missing",
    ],
    "empty_like_keywords": [
        "empty or nearly empty",
        "empty",
    ],
    "repo_overrides": {
        "MatALass-ISM/ects-grade-engine": {
            "decision": "keep",
            "reason": "Repository is strategically important and already strong enough to remain a showcase candidate."
        }
    },
    "repo_type_overrides": {
        "config_or_infra_project": {
            "keep_min_score": 70,
            "improve_min_score": 50,
        },
        "documentation_project": {
            "keep_min_score": 72,
            "improve_min_score": 40,
        },
        "ml_project": {
            "keep_min_score": 75,
            "improve_min_score": 50,
        },
        "data_science_project": {
            "keep_min_score": 72,
            "improve_min_score": 48,
        },
    },
}


@dataclass(slots=True)
class PortfolioPolicy:
    raw: dict[str, Any]

    @property
    def thresholds(self) -> dict[str, int]:
        raw_thresholds = self.raw.get("thresholds", {})
        return {
            "keep_min_score": int(raw_thresholds.get("keep_min_score", 78)),
            "improve_min_score": int(raw_thresholds.get("improve_min_score", 45)),
            "archive_max_score": int(raw_thresholds.get("archive_max_score", 24)),
            "soft_keep_min_score": int(raw_thresholds.get("soft_keep_min_score", 76)),
            "web_improve_floor": int(raw_thresholds.get("web_improve_floor", 25)),
        }

    @property
    def archive_repo_types(self) -> set[str]:
        return set(self.raw.get("archive_repo_types", []))

    @property
    def rebuild_repo_types(self) -> set[str]:
        return set(self.raw.get("rebuild_repo_types", []))

    @property
    def archive_maturity_bands(self) -> set[str]:
        return set(self.raw.get("archive_maturity_bands", []))

    @property
    def structure_debt_keywords(self) -> list[str]:
        return list(self.raw.get("structure_debt_keywords", []))

    @property
    def missing_basics_keywords(self) -> list[str]:
        return list(self.raw.get("missing_basics_keywords", []))

    @property
    def empty_like_keywords(self) -> list[str]:
        return list(self.raw.get("empty_like_keywords", []))

    @property
    def repo_overrides(self) -> dict[str, dict[str, str]]:
        return dict(self.raw.get("repo_overrides", {}))

    @property
    def repo_type_overrides(self) -> dict[str, dict[str, int]]:
        return dict(self.raw.get("repo_type_overrides", {}))

    def thresholds_for_repo_type(self, repo_type: str) -> dict[str, int]:
        thresholds = dict(self.thresholds)
        overrides = self.repo_type_overrides.get(repo_type, {})
        for key in (
            "keep_min_score",
            "improve_min_score",
            "archive_max_score",
            "soft_keep_min_score",
            "web_improve_floor",
        ):
            if key in overrides:
                thresholds[key] = int(overrides[key])
        return thresholds


@dataclass(slots=True)
class PortfolioAssessment:
    decision: str
    reason: str


def deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_portfolio_policy(policy_path: Path | None = None) -> PortfolioPolicy:
    merged = dict(DEFAULT_POLICY)

    if policy_path is not None and policy_path.exists():
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
        merged = deep_merge_dicts(merged, payload)

    return PortfolioPolicy(raw=merged)


def _issue_title_text(result: RepoAuditResult) -> str:
    return " | ".join(issue.title.strip().lower() for issue in result.priority_issues)


def _action_title_text(result: RepoAuditResult) -> str:
    return " | ".join(action.title.strip().lower() for action in result.prioritized_actions)


def _text_contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def _has_empty_like_signal(result: RepoAuditResult, policy: PortfolioPolicy) -> bool:
    return _text_contains_any(_issue_title_text(result), policy.empty_like_keywords)


def _has_structure_debt_signal(result: RepoAuditResult, policy: PortfolioPolicy) -> bool:
    return _text_contains_any(
        _issue_title_text(result) + " | " + _action_title_text(result),
        policy.structure_debt_keywords,
    )


def _has_missing_basics_signal(result: RepoAuditResult, policy: PortfolioPolicy) -> bool:
    return _text_contains_any(_issue_title_text(result), policy.missing_basics_keywords)


def determine_portfolio_decision(result: RepoAuditResult, policy: PortfolioPolicy) -> str:
    repo_name = str(result.repo_name)
    repo_type = str(result.repo_type)
    maturity = str(result.maturity_band)
    score = int(result.total_score)

    repo_override = policy.repo_overrides.get(repo_name)
    if repo_override and "decision" in repo_override:
        return str(repo_override["decision"])

    thresholds = policy.thresholds_for_repo_type(repo_type)
    keep_min_score = thresholds["keep_min_score"]
    improve_min_score = thresholds["improve_min_score"]
    archive_max_score = thresholds["archive_max_score"]
    soft_keep_min_score = thresholds.get("soft_keep_min_score", keep_min_score)
    web_improve_floor = thresholds.get("web_improve_floor", 25)

    empty_like = _has_empty_like_signal(result, policy)
    structure_debt = _has_structure_debt_signal(result, policy)
    missing_basics = _has_missing_basics_signal(result, policy)

    if score >= keep_min_score:
        return "keep"

    if (
        score >= soft_keep_min_score
        and maturity == "advanced"
        and repo_type in {"web_app", "streamlit_app", "cli_tool", "ml_project", "data_science_project"}
    ):
        return "keep"

    if score <= archive_max_score:
        if empty_like or (repo_type in policy.archive_repo_types and maturity in policy.archive_maturity_bands):
            return "archive"
        if repo_type in policy.rebuild_repo_types:
            return "rebuild"
        return "archive"

    if score < improve_min_score:
        if empty_like and maturity in policy.archive_maturity_bands and repo_type in policy.archive_repo_types:
            return "archive"

        if repo_type in {"web_app", "streamlit_app"} and score >= web_improve_floor and not empty_like:
            return "improve"

        if structure_debt or repo_type in policy.rebuild_repo_types:
            return "rebuild"

        return "improve"

    if missing_basics or structure_debt:
        return "improve"

    return "improve"


def portfolio_decision_reason(result: RepoAuditResult, decision: str, policy: PortfolioPolicy) -> str:
    repo_name = str(result.repo_name)
    repo_override = policy.repo_overrides.get(repo_name)
    if repo_override and "reason" in repo_override:
        return str(repo_override["reason"])

    score = int(result.total_score)
    maturity = str(result.maturity_band)

    if decision == "keep":
        return f"Score is high enough ({score}/100) to keep this repository as a portfolio asset."
    if decision == "archive":
        return (
            f"Low score ({score}/100) with limited portfolio upside relative to cleanup effort, "
            f"especially for a {maturity} repository."
        )
    if decision == "rebuild":
        return (
            f"Score remains too low ({score}/100) and the repository appears structurally weak, "
            f"so a rebuild is more defensible than incremental cleanup."
        )
    return f"Repository is still recoverable ({score}/100) through targeted incremental improvements."


def assess_repo_for_portfolio(result: RepoAuditResult, policy: PortfolioPolicy) -> PortfolioAssessment:
    decision = determine_portfolio_decision(result, policy)
    reason = portfolio_decision_reason(result, decision, policy)
    return PortfolioAssessment(decision=decision, reason=reason)