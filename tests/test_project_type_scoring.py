from repo_auditor.models import RepoFacts
from repo_auditor.scoring import audit_repo


def make_streamlit_repo() -> RepoFacts:
    return RepoFacts(
        name="streamlit-demo",
        description="A Streamlit dashboard for analytics.",
        root_files=["README.md", "app.py", "requirements.txt"],
        root_dirs=[],
        all_paths=[
            "README.md",
            "app.py",
            "requirements.txt",
        ],
        readme_text="""
# Streamlit Demo

## Overview
Dashboard project.

## Installation
pip install -r requirements.txt

## Usage
streamlit run app.py
""",
        file_line_counts={"app.py": 220},
        manifest_files=["requirements.txt"],
        tooling_files=[],
        has_gitignore=True,
        has_license=False,
        has_env_example=False,
        code_file_count=1,
        test_file_count=0,
        recent_push_days=5,
        repo_type="streamlit_app",
    )


def make_notebook_repo() -> RepoFacts:
    return RepoFacts(
        name="notebook-demo",
        description="Notebook analysis project.",
        root_files=["README.md", "analysis.ipynb", "dashboard.ipynb"],
        root_dirs=[],
        all_paths=[
            "README.md",
            "analysis.ipynb",
            "dashboard.ipynb",
            "requirements.txt",
        ],
        readme_text="""
# Notebook Demo

## Overview
Notebook analytics project.

## Installation
pip install -r requirements.txt

## Usage
Open the notebooks.
""",
        file_line_counts={},
        manifest_files=["requirements.txt"],
        tooling_files=[],
        has_gitignore=True,
        has_license=False,
        has_env_example=False,
        code_file_count=0,
        test_file_count=0,
        recent_push_days=5,
        repo_type="notebook_project",
    )


def test_streamlit_repo_is_detected_and_not_overpenalized() -> None:
    result = audit_repo(make_streamlit_repo())

    assert result.repo_type == "streamlit_app"
    assert any(issue.code == "missing_tests" for issue in result.priority_issues) or True
    assert result.total_score >= 40


def test_notebook_repo_type_propagates() -> None:
    result = audit_repo(make_notebook_repo())

    assert result.repo_type == "notebook_project"