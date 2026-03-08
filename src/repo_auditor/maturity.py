from __future__ import annotations

from repo_auditor.models import ActionRecommendation


MATURITY_ADJUSTMENTS = {
    "bootstrap": {
        "write_core_readme": 26,
        "complete_or_archive_repo": 24,
        "formalize_dependencies": 22,
        "add_gitignore": 18,
        "document_installation": 16,
        "document_usage": 16,
        "restructure_repository": 14,
        "create_main_code_directory": 10,
        "build_core_test_suite": -30,
        "expand_test_scope": -35,
        "configure_test_framework": -22,
        "add_test_ci": -30,
        "write_technical_docs": -12,
        "decompose_monolith": -12,
        "separate_responsibilities": -12,
    },
    "foundation": {
        "write_core_readme": 18,
        "formalize_dependencies": 16,
        "add_gitignore": 14,
        "document_installation": 12,
        "document_usage": 12,
        "restructure_repository": 10,
        "create_main_code_directory": 10,
        "build_core_test_suite": -8,
        "expand_test_scope": -12,
        "configure_test_framework": -8,
        "add_test_ci": -14,
    },
    "developing": {
        "build_core_test_suite": 16,
        "expand_test_scope": 12,
        "configure_test_framework": 8,
        "configure_tooling": 10,
        "write_technical_docs": 10,
        "separate_responsibilities": 10,
        "decompose_monolith": 8,
        "add_env_template": 8,
        "add_test_ci": 8,
        "complete_or_archive_repo": -16,
    },
    "advanced": {
        "add_test_ci": 14,
        "configure_tooling": 12,
        "write_technical_docs": 12,
        "add_demo_outputs": 10,
        "improve_interview_readiness": 8,
        "add_license": 6,
        "complete_or_archive_repo": -20,
        "write_core_readme": -6,
    },
}


def maturity_band_for_score(score: int) -> str:
    if score < 25:
        return "bootstrap"
    if score < 45:
        return "foundation"
    if score < 65:
        return "developing"
    return "advanced"


def apply_maturity_adjustments(
    actions: list[ActionRecommendation],
    *,
    total_score: int,
) -> list[ActionRecommendation]:
    band = maturity_band_for_score(total_score)
    adjustments = MATURITY_ADJUSTMENTS.get(band, {})

    for action in actions:
        action.priority_score += adjustments.get(action.code, 0)

    actions.sort(key=lambda action: (-action.priority_score, action.title.lower()))
    return actions