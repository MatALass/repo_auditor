from __future__ import annotations

from repo_auditor.models import CategoryScore, RepoAuditResult, RepoFacts
from repo_auditor.rules import (
    apparent_test_volume_points,
    count_useful_root_files,
    has_ci_signal,
    has_demo_signal,
    has_inconsistent_naming,
    has_junk_files,
    has_keyword_section,
    has_main_code_directory,
    has_manifest,
    has_readme,
    has_repo_description,
    has_separation_of_concerns_signal,
    has_support_directory,
    has_technical_docs,
    has_test_framework_signal,
    has_tests,
    has_tests_directory,
    has_tooling_config,
    interview_ready_signal,
    make_issue,
    modularity_status,
    oversized_file_status,
    portfolio_clarity_signal,
    project_promise_supported,
    readme_length,
    recent_activity_points,
    repo_is_nearly_empty,
    technical_credibility_signal,
)


def evaluate_documentation(facts: RepoFacts) -> CategoryScore:
    score = 0
    issues = []

    if has_readme(facts):
        score += 5
    else:
        issues.append(make_issue("missing_readme"))
        return CategoryScore("Documentation", score, 20, issues)

    length = readme_length(facts)
    if length >= 300:
        score += 1
    else:
        issues.append(make_issue("readme_too_short"))

    if length >= 800:
        score += 1

    if has_keyword_section(facts, ["overview", "about", "description", "project", "goal", "purpose"]):
        score += 3
    else:
        issues.append(make_issue("missing_project_description"))

    if has_keyword_section(facts, ["install", "installation", "setup", "requirements", "getting started"]):
        score += 3
    else:
        issues.append(make_issue("missing_installation_instructions"))

    if has_keyword_section(facts, ["usage", "run", "how to run", "quickstart", "example usage"]):
        score += 3
    else:
        issues.append(make_issue("missing_usage_instructions"))

    if has_keyword_section(facts, ["architecture", "structure", "project structure", "folders", "modules"]):
        score += 2
    else:
        issues.append(make_issue("missing_project_structure_explanation"))

    if has_keyword_section(facts, ["demo", "example", "screenshot", "preview", "sample output"]):
        score += 2
    else:
        issues.append(make_issue("missing_demo_or_examples"))

    if has_keyword_section(facts, ["roadmap", "limitations", "future improvements", "todo", "next steps"]):
        score += 2
    else:
        issues.append(make_issue("missing_roadmap_or_limitations"))

    return CategoryScore("Documentation", min(score, 20), 20, issues)


def evaluate_structure(facts: RepoFacts) -> CategoryScore:
    score = 0
    issues = []

    root_file_count = count_useful_root_files(facts)
    if root_file_count <= 8:
        score += 5
    elif root_file_count <= 15:
        score += 2
    else:
        issues.append(make_issue("flat_project_structure"))

    if has_main_code_directory(facts):
        score += 5
    else:
        issues.append(make_issue("missing_main_code_directory"))

    if has_tests_directory(facts):
        score += 3
    else:
        issues.append(make_issue("missing_tests_directory"))

    if has_support_directory(facts):
        score += 2
    else:
        issues.append(make_issue("missing_supporting_directories"))

    if not has_inconsistent_naming(facts):
        score += 3
    else:
        issues.append(make_issue("inconsistent_naming"))

    if not has_junk_files(facts):
        score += 2
    else:
        issues.append(make_issue("versioned_junk_files"))

    return CategoryScore("Structure", min(score, 20), 20, issues)


def evaluate_packaging(facts: RepoFacts) -> CategoryScore:
    score = 0
    issues = []

    if has_manifest(facts):
        score += 4
    else:
        issues.append(make_issue("missing_dependency_manifest"))

    if facts.has_gitignore:
        score += 3
    else:
        issues.append(make_issue("missing_gitignore"))

    if facts.has_license:
        score += 2
    else:
        issues.append(make_issue("missing_license"))

    if has_tooling_config(facts):
        score += 3
    else:
        issues.append(make_issue("missing_tooling_configuration"))

    if facts.has_env_example:
        score += 3
    else:
        issues.append(make_issue("missing_env_example"))

    return CategoryScore("Packaging", min(score, 15), 15, issues)


def evaluate_tests(facts: RepoFacts) -> CategoryScore:
    score = 0
    issues = []

    if has_tests(facts):
        score += 5
    else:
        issues.append(make_issue("missing_tests"))

    volume_points = apparent_test_volume_points(facts)
    score += volume_points
    if volume_points < 4:
        issues.append(make_issue("insufficient_test_coverage_apparent"))

    if has_test_framework_signal(facts):
        score += 3
    else:
        issues.append(make_issue("missing_test_framework_configuration"))

    if has_ci_signal(facts):
        score += 3
    else:
        issues.append(make_issue("missing_ci_for_tests"))

    return CategoryScore("Tests", min(score, 15), 15, issues)


def evaluate_maintainability(facts: RepoFacts) -> CategoryScore:
    score = 0
    issues = []

    size_status = oversized_file_status(facts)
    if size_status == "ok":
        score += 4
    elif size_status == "warning":
        score += 2
        issues.append(make_issue("oversized_files"))
    else:
        issues.append(make_issue("oversized_files"))

    mod_status = modularity_status(facts)
    if mod_status == "good":
        score += 4
    elif mod_status == "weak":
        score += 2
        issues.append(make_issue("monolithic_structure"))
    else:
        issues.append(make_issue("monolithic_structure"))

    if not has_inconsistent_naming(facts):
        score += 2
    else:
        issues.append(make_issue("vague_file_names"))

    if has_separation_of_concerns_signal(facts) or has_main_code_directory(facts):
        score += 3
    else:
        issues.append(make_issue("poor_separation_of_concerns"))

    if has_technical_docs(facts):
        score += 2
    else:
        issues.append(make_issue("missing_technical_documentation"))

    return CategoryScore("Maintainability", min(score, 15), 15, issues)


def evaluate_completeness(facts: RepoFacts) -> CategoryScore:
    score = 0
    issues = []

    if has_repo_description(facts):
        score += 2
    else:
        issues.append(make_issue("missing_repository_description"))

    activity_points = recent_activity_points(facts)
    score += activity_points
    if activity_points == 0 and facts.recent_push_days is not None and facts.recent_push_days > 365:
        issues.append(make_issue("stale_repository"))

    if not repo_is_nearly_empty(facts):
        score += 2
    else:
        issues.append(make_issue("empty_or_nearly_empty_repo"))

    if has_demo_signal(facts):
        score += 2
    else:
        issues.append(make_issue("missing_demo_artifacts"))

    if project_promise_supported(facts):
        score += 2
    else:
        issues.append(make_issue("project_promise_not_supported_by_contents"))

    return CategoryScore("Completeness", min(score, 10), 10, issues)


def evaluate_portfolio_value(facts: RepoFacts) -> CategoryScore:
    score = 0
    issues = []

    if portfolio_clarity_signal(facts):
        score += 2
    else:
        issues.append(make_issue("low_portfolio_clarity"))

    if technical_credibility_signal(facts):
        score += 2
    else:
        issues.append(make_issue("low_technical_credibility"))

    if interview_ready_signal(facts):
        score += 1
    else:
        issues.append(make_issue("hard_to_present_in_interview"))

    return CategoryScore("Portfolio value", min(score, 5), 5, issues)


def score_to_level(score: int) -> str:
    if score >= 85:
        return "strong"
    if score >= 70:
        return "good"
    if score >= 55:
        return "average"
    if score >= 40:
        return "weak"
    return "very weak"


def deduplicate_issues(category_scores: list[CategoryScore]) -> list:
    seen = set()
    unique = []
    for category in category_scores:
        for issue in category.issues:
            if issue.code not in seen:
                seen.add(issue.code)
                unique.append(issue)
    return unique


def issue_sort_key(issue) -> tuple[int, str]:
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    return (severity_rank.get(issue.severity, 3), issue.code)


def audit_repo(facts: RepoFacts) -> RepoAuditResult:
    categories = [
        evaluate_documentation(facts),
        evaluate_structure(facts),
        evaluate_packaging(facts),
        evaluate_tests(facts),
        evaluate_maintainability(facts),
        evaluate_completeness(facts),
        evaluate_portfolio_value(facts),
    ]

    total_score = sum(category.score for category in categories)
    max_score = sum(category.max_score for category in categories)

    issues = deduplicate_issues(categories)
    issues.sort(key=issue_sort_key)

    return RepoAuditResult(
        repo_name=facts.name,
        total_score=total_score,
        max_score=max_score,
        level=score_to_level(total_score),
        category_scores=categories,
        priority_issues=issues[:5],
    )