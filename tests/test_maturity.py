from repo_auditor.maturity import apply_maturity_adjustments, maturity_band_for_score
from repo_auditor.models import ActionRecommendation


def make_action(code: str, priority_score: int) -> ActionRecommendation:
    return ActionRecommendation(
        code=code,
        title=code,
        description="desc",
        rationale="why",
        steps=["step 1"],
        impact="high",
        effort="medium",
        priority_score=priority_score,
        source_issue_codes=[],
    )


def test_maturity_band_for_score() -> None:
    assert maturity_band_for_score(12) == "bootstrap"
    assert maturity_band_for_score(30) == "foundation"
    assert maturity_band_for_score(55) == "developing"
    assert maturity_band_for_score(75) == "advanced"


def test_bootstrap_demotes_test_actions() -> None:
    actions = [
        make_action("build_core_test_suite", 120),
        make_action("write_core_readme", 110),
    ]

    adjusted = apply_maturity_adjustments(actions, total_score=12)

    assert adjusted[0].code == "write_core_readme"


def test_developing_promotes_engineering_actions() -> None:
    actions = [
        make_action("add_gitignore", 100),
        make_action("build_core_test_suite", 95),
    ]

    adjusted = apply_maturity_adjustments(actions, total_score=55)

    assert adjusted[0].code == "build_core_test_suite"