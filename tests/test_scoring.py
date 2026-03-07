from repo_auditor.cli import build_demo_repo
from repo_auditor.scoring import audit_repo


def test_demo_repo_scores_reasonably() -> None:
    facts = build_demo_repo()
    result = audit_repo(facts)

    assert result.repo_name == "demo-repo"
    assert result.total_score > 0
    assert result.max_score == 100
    assert result.level in {"strong", "good", "average", "weak", "very weak"}
    assert len(result.category_scores) == 7