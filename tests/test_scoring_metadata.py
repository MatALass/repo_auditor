from repo_auditor.models import RepoFacts
from repo_auditor.scoring import evaluate_documentation, evaluate_portfolio_value


def make_repo(*, readme_sections: list[str], github_topics: list[str], homepage_url: str | None) -> RepoFacts:
    return RepoFacts(
        name="octo/demo",
        description="Demo repository for metadata scoring.",
        root_files=["README.md"],
        root_dirs=["src", "tests"],
        all_paths=["README.md", "src/main.py", "tests/test_main.py", ".github/workflows/ci.yml"],
        readme_text="# Demo\n",
        file_line_counts={"src/main.py": 20},
        manifest_files=["pyproject.toml"],
        tooling_files=["pytest.ini"],
        has_gitignore=True,
        has_license=True,
        has_env_example=True,
        code_file_count=1,
        test_file_count=1,
        readme_sections=readme_sections,
        github_topics=github_topics,
        homepage_url=homepage_url,
        has_ci_config=True,
        is_archived=False,
        recent_push_days=30,
        repo_type="python_project",
    )


def test_documentation_adds_aggregated_issue_when_many_sections_missing() -> None:
    facts = make_repo(
        readme_sections=["demo"],
        github_topics=["python", "cli"],
        homepage_url="https://example.com",
    )
    category = evaluate_documentation(facts)

    issue_codes = {issue.code for issue in category.issues}
    assert "readme_missing_key_sections" in issue_codes


def test_portfolio_value_rewards_topics_and_homepage() -> None:
    weak = evaluate_portfolio_value(
        make_repo(
            readme_sections=["overview", "installation", "usage", "demo"],
            github_topics=[],
            homepage_url=None,
        )
    )
    strong = evaluate_portfolio_value(
        make_repo(
            readme_sections=["overview", "installation", "usage", "demo"],
            github_topics=["python", "cli", "github", "auditing"],
            homepage_url="https://example.com",
        )
    )

    assert strong.score > weak.score
    assert any(issue.code == "missing_github_topics" for issue in weak.issues)