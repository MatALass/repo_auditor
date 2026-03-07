from __future__ import annotations

from repo_auditor.models import ActionRecommendation, AuditIssue


SEVERITY_SCORE = {
    "high": 30,
    "medium": 20,
    "low": 10,
}

EFFORT_SCORE = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

ACTION_CATALOG = {
    "missing_readme": {
        "action_code": "write_core_readme",
        "title": "Write a complete README",
        "description": "Create a README covering project purpose, installation, usage, structure, and demo evidence.",
        "rationale": "A missing README destroys repository clarity and portfolio value immediately.",
        "steps": [
            "Add a project overview with the problem solved and the technical scope.",
            "Document installation and execution steps.",
            "Explain the repository structure and key modules.",
            "Add demo material such as screenshots, outputs, or usage examples.",
        ],
        "impact": "high",
        "effort": "medium",
        "base_priority": 95,
    },
    "readme_too_short": {
        "action_code": "expand_readme",
        "title": "Expand the README",
        "description": "Turn the current README into a useful entry point for reviewers and future maintainers.",
        "rationale": "A thin README weakens adoption, reproducibility, and interview readiness.",
        "steps": [
            "Add more project context and scope.",
            "Document setup and usage more explicitly.",
            "Add structure, limitations, and next steps sections.",
        ],
        "impact": "high",
        "effort": "low",
        "base_priority": 82,
    },
    "missing_project_description": {
        "action_code": "clarify_project_scope",
        "title": "Clarify project scope",
        "description": "Add a clear project description in the README.",
        "rationale": "Readers should understand what the repository does in seconds.",
        "steps": [
            "Add a short summary at the top of the README.",
            "State the core objective, users, and technical output.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 70,
    },
    "missing_installation_instructions": {
        "action_code": "document_installation",
        "title": "Document installation steps",
        "description": "Add clear installation instructions with prerequisites and commands.",
        "rationale": "A project that cannot be installed easily loses reproducibility.",
        "steps": [
            "List prerequisites and required versions.",
            "Add install commands.",
            "Document environment setup if needed.",
        ],
        "impact": "high",
        "effort": "low",
        "base_priority": 88,
    },
    "missing_usage_instructions": {
        "action_code": "document_usage",
        "title": "Document execution and usage",
        "description": "Explain how to run the project and what output to expect.",
        "rationale": "A repository is much less convincing when usage is unclear.",
        "steps": [
            "Add run commands.",
            "Describe expected outputs or visible behavior.",
            "Provide one concrete usage example.",
        ],
        "impact": "high",
        "effort": "low",
        "base_priority": 88,
    },
    "missing_project_structure_explanation": {
        "action_code": "document_structure",
        "title": "Explain repository structure",
        "description": "Document the main folders and their responsibilities.",
        "rationale": "Structure explanation accelerates onboarding and maintenance.",
        "steps": [
            "List top-level folders.",
            "Explain the purpose of core modules.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 60,
    },
    "missing_demo_or_examples": {
        "action_code": "add_demo_material",
        "title": "Add demo evidence",
        "description": "Add screenshots, example outputs, or sample runs.",
        "rationale": "Projects become much easier to assess when outputs are visible.",
        "steps": [
            "Capture screenshots or terminal examples.",
            "Add a demo section in the README.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 62,
    },
    "missing_roadmap_or_limitations": {
        "action_code": "add_roadmap_section",
        "title": "Add roadmap and limitations",
        "description": "Document current limitations and future improvements.",
        "rationale": "This shows maturity and helps frame the current state of the project.",
        "steps": [
            "Add known limitations.",
            "Add next steps or roadmap items.",
        ],
        "impact": "low",
        "effort": "low",
        "base_priority": 45,
    },
    "flat_project_structure": {
        "action_code": "restructure_repository",
        "title": "Restructure the repository layout",
        "description": "Move code, tests, docs, and assets into clear dedicated directories.",
        "rationale": "A flat structure quickly becomes hard to maintain and scale.",
        "steps": [
            "Move source code into src/, app/, or equivalent.",
            "Move tests into tests/.",
            "Group docs, assets, and scripts into dedicated folders.",
        ],
        "impact": "high",
        "effort": "medium",
        "base_priority": 92,
    },
    "missing_main_code_directory": {
        "action_code": "create_main_code_directory",
        "title": "Introduce a dedicated source directory",
        "description": "Move core code into a dedicated source folder.",
        "rationale": "A main code directory improves clarity and future scalability.",
        "steps": [
            "Choose src/, app/, or lib/ depending on the stack.",
            "Move main implementation files there.",
            "Update imports and execution entry points.",
        ],
        "impact": "high",
        "effort": "medium",
        "base_priority": 90,
    },
    "missing_tests_directory": {
        "action_code": "create_test_layout",
        "title": "Create a dedicated test layout",
        "description": "Introduce a tests/ directory with a coherent structure.",
        "rationale": "Test organization is part of maintainability and engineering maturity.",
        "steps": [
            "Create tests/.",
            "Move or add tests by feature or module.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 68,
    },
    "missing_supporting_directories": {
        "action_code": "add_support_directories",
        "title": "Add supporting directories where relevant",
        "description": "Separate documentation, assets, scripts, notebooks, or data into dedicated folders.",
        "rationale": "Supporting material should not be mixed randomly with main code.",
        "steps": [
            "Create only the directories relevant to the project.",
            "Move auxiliary files into the right locations.",
        ],
        "impact": "low",
        "effort": "low",
        "base_priority": 40,
    },
    "inconsistent_naming": {
        "action_code": "normalize_naming",
        "title": "Normalize file and folder naming",
        "description": "Rename vague or inconsistent files and folders.",
        "rationale": "Naming quality strongly affects readability and maintainability.",
        "steps": [
            "Rename vague files such as final.py or temp.py.",
            "Adopt one naming convention across the repository.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 72,
    },
    "versioned_junk_files": {
        "action_code": "clean_versioned_junk",
        "title": "Remove junk files from version control",
        "description": "Delete generated or temporary files and reinforce ignore rules.",
        "rationale": "Noise in version control reduces professionalism and clarity.",
        "steps": [
            "Remove generated files from the repository.",
            "Update .gitignore to prevent reintroducing them.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 74,
    },
    "missing_dependency_manifest": {
        "action_code": "formalize_dependencies",
        "title": "Formalize project dependencies",
        "description": "Add the appropriate manifest file for the project stack.",
        "rationale": "Without formal dependencies, the project is not properly reproducible.",
        "steps": [
            "Add pyproject.toml, requirements.txt, package.json, or the relevant manifest.",
            "List runtime and development dependencies explicitly.",
        ],
        "impact": "high",
        "effort": "low",
        "base_priority": 90,
    },
    "missing_gitignore": {
        "action_code": "add_gitignore",
        "title": "Add a proper .gitignore",
        "description": "Create a stack-specific .gitignore file.",
        "rationale": "This avoids polluting the repository with generated files.",
        "steps": [
            "Add a base .gitignore adapted to the tech stack.",
            "Cover environments, caches, build outputs, and editor files.",
        ],
        "impact": "high",
        "effort": "low",
        "base_priority": 86,
    },
    "missing_license": {
        "action_code": "add_license",
        "title": "Add a license",
        "description": "Clarify repository usage rights with a LICENSE file.",
        "rationale": "Licensing matters for portfolio clarity and open-source reuse.",
        "steps": [
            "Choose an appropriate license.",
            "Add the corresponding LICENSE file.",
        ],
        "impact": "low",
        "effort": "low",
        "base_priority": 35,
    },
    "missing_tooling_configuration": {
        "action_code": "configure_tooling",
        "title": "Add tooling configuration",
        "description": "Configure linting, formatting, typing, or test tools explicitly.",
        "rationale": "Tooling configuration signals engineering discipline.",
        "steps": [
            "Choose the relevant tools for the stack.",
            "Add configuration files and document usage.",
        ],
        "impact": "medium",
        "effort": "medium",
        "base_priority": 66,
    },
    "missing_env_example": {
        "action_code": "add_env_template",
        "title": "Add a configuration template",
        "description": "Create a safe example for environment or config variables.",
        "rationale": "Projects depending on secrets or config should remain reproducible safely.",
        "steps": [
            "Add .env.example or equivalent.",
            "Document each variable briefly.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 64,
    },
    "missing_tests": {
        "action_code": "build_core_test_suite",
        "title": "Build a core test suite",
        "description": "Add tests for the repository's main logic and critical flows.",
        "rationale": "No tests is one of the clearest signals of fragility.",
        "steps": [
            "Identify the core business logic or critical flows.",
            "Add a minimal but credible automated test suite.",
            "Cover the most failure-prone paths first.",
        ],
        "impact": "high",
        "effort": "medium",
        "base_priority": 94,
    },
    "insufficient_test_coverage_apparent": {
        "action_code": "expand_test_scope",
        "title": "Expand test coverage on critical paths",
        "description": "Increase test breadth beyond the current minimal footprint.",
        "rationale": "A tiny test surface still leaves the project looking fragile.",
        "steps": [
            "Add tests for core modules.",
            "Cover edge cases and failure paths.",
        ],
        "impact": "high",
        "effort": "medium",
        "base_priority": 78,
    },
    "missing_test_framework_configuration": {
        "action_code": "configure_test_framework",
        "title": "Configure the test framework explicitly",
        "description": "Make the testing strategy and commands explicit.",
        "rationale": "Testing should be reproducible and clearly declared.",
        "steps": [
            "Declare the test framework dependency.",
            "Add config and document the test command.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 69,
    },
    "missing_ci_for_tests": {
        "action_code": "add_test_ci",
        "title": "Add CI for automated tests",
        "description": "Run tests automatically in CI.",
        "rationale": "Automation reinforces quality gates and project credibility.",
        "steps": [
            "Add a CI workflow.",
            "Run install, lint, and test steps automatically.",
        ],
        "impact": "medium",
        "effort": "medium",
        "base_priority": 63,
    },
    "oversized_files": {
        "action_code": "split_large_files",
        "title": "Split oversized files",
        "description": "Break large implementation files into smaller focused modules.",
        "rationale": "Oversized files are a strong maintainability smell.",
        "steps": [
            "Identify oversized files.",
            "Extract related responsibilities into separate modules.",
            "Reduce file size while preserving cohesion.",
        ],
        "impact": "high",
        "effort": "high",
        "base_priority": 84,
    },
    "monolithic_structure": {
        "action_code": "decompose_monolith",
        "title": "Decompose monolithic code structure",
        "description": "Separate logic across multiple focused modules.",
        "rationale": "Monolithic repositories are harder to evolve and reason about.",
        "steps": [
            "Identify major responsibilities currently mixed together.",
            "Create modules by responsibility.",
            "Reduce central file dominance.",
        ],
        "impact": "high",
        "effort": "high",
        "base_priority": 86,
    },
    "vague_file_names": {
        "action_code": "rename_vague_files",
        "title": "Rename vague files",
        "description": "Replace generic file names with responsibility-based names.",
        "rationale": "Precise naming improves readability quickly.",
        "steps": [
            "Rename generic files.",
            "Align file names with their actual function.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 67,
    },
    "poor_separation_of_concerns": {
        "action_code": "separate_responsibilities",
        "title": "Improve separation of concerns",
        "description": "Split mixed responsibilities into explicit layers or modules.",
        "rationale": "Poor separation of concerns slows every future change.",
        "steps": [
            "Define major responsibility boundaries.",
            "Create modules or layers per responsibility.",
            "Move logic accordingly and simplify entry points.",
        ],
        "impact": "high",
        "effort": "high",
        "base_priority": 89,
    },
    "missing_technical_documentation": {
        "action_code": "write_technical_docs",
        "title": "Add technical documentation",
        "description": "Document architecture, conventions, or contribution rules.",
        "rationale": "Technical docs improve maintainability and professional clarity.",
        "steps": [
            "Add architecture notes or a docs/ section.",
            "Document major technical decisions.",
        ],
        "impact": "medium",
        "effort": "medium",
        "base_priority": 58,
    },
    "missing_repository_description": {
        "action_code": "add_github_description",
        "title": "Add a concise repository description",
        "description": "Fill the short repository description for quick GitHub clarity.",
        "rationale": "This improves first-glance understanding in a portfolio context.",
        "steps": [
            "Write a short one-line description that states purpose and scope.",
        ],
        "impact": "low",
        "effort": "low",
        "base_priority": 38,
    },
    "stale_repository": {
        "action_code": "refresh_or_archive_repo",
        "title": "Refresh or explicitly archive the repository",
        "description": "Either update the repository or mark it as intentionally inactive.",
        "rationale": "Stale repositories can look abandoned without explanation.",
        "steps": [
            "Decide whether to continue, archive, or document the current state.",
            "Update the README accordingly.",
        ],
        "impact": "low",
        "effort": "low",
        "base_priority": 36,
    },
    "empty_or_nearly_empty_repo": {
        "action_code": "complete_or_archive_repo",
        "title": "Complete or archive the repository",
        "description": "Either add meaningful implementation or remove/archive the repo from the portfolio.",
        "rationale": "A nearly empty repo hurts portfolio quality more than it helps.",
        "steps": [
            "Decide whether the repo is worth continuing.",
            "Either add real implementation or archive/remove it from showcase use.",
        ],
        "impact": "high",
        "effort": "medium",
        "base_priority": 91,
    },
    "missing_demo_artifacts": {
        "action_code": "add_demo_outputs",
        "title": "Add screenshots or output examples",
        "description": "Make the project easier to evaluate visually or functionally.",
        "rationale": "Demo material increases clarity and interview readiness.",
        "steps": [
            "Add screenshots, GIFs, or sample outputs.",
            "Reference them in the README.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 61,
    },
    "project_promise_not_supported_by_contents": {
        "action_code": "align_scope_and_contents",
        "title": "Align repository scope with actual contents",
        "description": "Make the repository content match the promise made in its description and README.",
        "rationale": "Overpromising damages credibility quickly.",
        "steps": [
            "Review the claimed scope.",
            "Either reduce the promise or add the missing implementation and documentation.",
        ],
        "impact": "high",
        "effort": "medium",
        "base_priority": 80,
    },
    "low_portfolio_clarity": {
        "action_code": "improve_portfolio_positioning",
        "title": "Improve portfolio clarity",
        "description": "Make the repository easier to understand for recruiters and reviewers.",
        "rationale": "Portfolio value depends heavily on clarity and framing.",
        "steps": [
            "Clarify the purpose and value proposition.",
            "Improve README opening and repository description.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 65,
    },
    "low_technical_credibility": {
        "action_code": "increase_engineering_signals",
        "title": "Increase engineering credibility",
        "description": "Strengthen structure, testing, tooling, and documentation signals.",
        "rationale": "Weak engineering signals reduce trust in the project quality.",
        "steps": [
            "Add or improve tests, tooling config, and documentation.",
            "Strengthen project structure and reproducibility.",
        ],
        "impact": "high",
        "effort": "medium",
        "base_priority": 79,
    },
    "hard_to_present_in_interview": {
        "action_code": "improve_interview_readiness",
        "title": "Improve interview readiness",
        "description": "Make the repository easier to demonstrate and discuss quickly.",
        "rationale": "Good interview projects should be easy to show and explain.",
        "steps": [
            "Add examples, demo material, and quickstart usage.",
            "Clarify the key technical decisions and outcomes.",
        ],
        "impact": "medium",
        "effort": "low",
        "base_priority": 57,
    },
}


def action_priority_score(*, base_priority: int, severity: str, effort: str, impact: str) -> int:
    impact_bonus = 10 if impact == "high" else 5 if impact == "medium" else 0
    severity_bonus = SEVERITY_SCORE.get(severity, 0)
    effort_penalty = EFFORT_SCORE.get(effort, 2) * 4
    return base_priority + impact_bonus + severity_bonus - effort_penalty


def build_action_from_issue(issue: AuditIssue) -> ActionRecommendation | None:
    meta = ACTION_CATALOG.get(issue.code)
    if meta is None:
        return None

    priority_score = action_priority_score(
        base_priority=meta["base_priority"],
        severity=issue.severity,
        effort=meta["effort"],
        impact=meta["impact"],
    )

    return ActionRecommendation(
        code=meta["action_code"],
        title=meta["title"],
        description=meta["description"],
        rationale=meta["rationale"],
        steps=list(meta["steps"]),
        impact=meta["impact"],
        effort=meta["effort"],
        priority_score=priority_score,
        source_issue_codes=[issue.code],
    )


def merge_actions(actions: list[ActionRecommendation]) -> list[ActionRecommendation]:
    merged: dict[str, ActionRecommendation] = {}

    for action in actions:
        existing = merged.get(action.code)
        if existing is None:
            merged[action.code] = action
            continue

        existing.priority_score = max(existing.priority_score, action.priority_score)
        existing.source_issue_codes = sorted(
            set(existing.source_issue_codes + action.source_issue_codes)
        )

    return list(merged.values())


def build_action_plan(issues: list[AuditIssue], *, max_actions: int = 5) -> list[ActionRecommendation]:
    raw_actions: list[ActionRecommendation] = []

    for issue in issues:
        action = build_action_from_issue(issue)
        if action is not None:
            raw_actions.append(action)

    merged_actions = merge_actions(raw_actions)
    merged_actions.sort(key=lambda action: (-action.priority_score, action.title.lower()))
    return merged_actions[:max_actions]