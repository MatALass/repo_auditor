from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_POLICY: dict[str, Any] = {
    "thresholds": {
        "keep_min_score": 78,
        "improve_min_score": 45,
        "archive_max_score": 24,
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
        return {
            "keep_min_score": int(self.raw.get("thresholds", {}).get("keep_min_score", 78)),
            "improve_min_score": int(self.raw.get("thresholds", {}).get("improve_min_score", 45)),
            "archive_max_score": int(self.raw.get("thresholds", {}).get("archive_max_score", 24)),
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
        for key in ("keep_min_score", "improve_min_score", "archive_max_score"):
            if key in overrides:
                thresholds[key] = int(overrides[key])
        return thresholds


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