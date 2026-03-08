# repo-auditor

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Tests](https://img.shields.io/badge/tests-78%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-94%25-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

**repo-auditor** is a Python CLI tool that audits software repositories
(local or GitHub) and generates a **structured engineering evaluation**
with scoring, prioritized issues, and an actionable improvement roadmap.

It is designed to help developers, data engineers, and teams quickly
identify weaknesses in repositories and transform them into **clean,
production‑grade portfolio projects**.

------------------------------------------------------------------------

# Key Features

### Repository auditing

-   Analyze **local repositories**
-   Analyze **GitHub repositories**
-   Analyze **GitHub users**
-   Analyze **GitHub organizations**
-   Analyze **local workspaces with multiple repositories**

### Engineering scoring system

Each repository is scored **out of 100** across multiple engineering
dimensions:

-   Documentation quality
-   Project structure
-   Testing coverage
-   Dependency management
-   Code organization
-   Portfolio readiness
-   Maintainability

### Issue detection

The auditor detects structural issues such as:

-   Missing README
-   Missing license
-   Missing dependency manifest
-   Lack of tests
-   Poor project structure
-   Missing documentation
-   Portfolio anti‑patterns

Each issue includes:

-   severity
-   explanation
-   recommendation

### Action roadmap generation

For every repository the tool generates:

-   **Prioritized improvement plan**
-   Action descriptions
-   Impact vs effort evaluation
-   Implementation steps

### Multi‑repository batch analysis

You can audit:

-   a full GitHub organization
-   a GitHub user
-   a workspace with many local repositories

The tool then generates:

-   **batch summary**
-   **worst repositories first**
-   **review queue CSV**
-   **consolidated reporting**

### Export formats

Reports can be exported as:

-   Markdown
-   JSON
-   CSV review queue

------------------------------------------------------------------------

# Example Output

Example report structure:

    GitHub Audit Report — github_org:example-org

    Repositories analyzed successfully: 12
    Repositories failed to scan: 1

    Worst repository
    ----------------
    Name: example-org/bad-repo
    Score: 22/100

    Top priority issues
    -------------------
    - Repository is empty or nearly empty
    - Dependency manifest missing
    - Tests missing

    Recommended actions
    -------------------
    1. Add project structure
    2. Add dependency management
    3. Add basic test suite

------------------------------------------------------------------------

# Architecture Overview

The project follows a modular architecture:

    repo-auditor
    │
    ├─ cli.py
    │   CLI entrypoint
    │
    ├─ github_client.py
    │   GitHub API client wrapper
    │
    ├─ github_scanner.py
    │   Extracts repository facts from GitHub
    │
    ├─ local_scanner.py
    │   Extracts repository facts locally
    │
    ├─ scoring.py
    │   Core scoring engine
    │
    ├─ rules.py
    │   Repository evaluation rules
    │
    ├─ planner.py
    │   Generates prioritized improvement plans
    │
    ├─ report.py
    │   Markdown and JSON reporting
    │
    ├─ workspace.py
    │   Local workspace batch auditing
    │
    └─ github_workspace.py
        GitHub user / org batch auditing

Design principles:

-   strict separation between **data extraction** and **evaluation**
-   deterministic scoring
-   composable reporting layer
-   batch‑safe execution

------------------------------------------------------------------------

# Installation

Clone the repository:

    git clone https://github.com/YOUR_USERNAME/repo-auditor.git
    cd repo-auditor

Install dependencies:

    pip install -e .

Or:

    pip install -r requirements.txt

Python requirement:

    Python >= 3.11

------------------------------------------------------------------------

# Configuration

Create a `.env` file for GitHub API access:

    GITHUB_TOKEN=your_token_here

Using a token is recommended to avoid GitHub rate limits.

------------------------------------------------------------------------

# CLI Usage

## Audit a local repository

    repo-auditor audit-repo ./my-project

## Audit a local workspace

    repo-auditor audit-workspace ./projects-folder

## Audit a GitHub repository

    repo-auditor audit-github-repo owner repo

Example:

    repo-auditor audit-github-repo octocat hello-world

## Audit a GitHub user

    repo-auditor audit-github-user username

## Audit a GitHub organization

    repo-auditor audit-github-org orgname

------------------------------------------------------------------------

# Batch Mode

You can run multiple audits in one command using batch targets.

Example targets file:

    github_org:my-company
    github_user:myusername
    local_workspace:./projects

Run batch audit:

    repo-auditor batch targets.txt

Generated outputs:

-   batch summary
-   markdown reports
-   JSON reports
-   review queue CSV

------------------------------------------------------------------------

# Review Queue

The tool can generate a **review queue CSV** listing repositories
ordered by priority.

Fields include:

-   repository name
-   score
-   issue severity
-   recommended actions

This allows teams to **triage improvements across many repositories**.

------------------------------------------------------------------------

# Testing

The project includes a comprehensive test suite.

Current metrics:

    78 tests
    94% coverage

Modules tested:

-   CLI
-   scoring engine
-   GitHub client
-   GitHub workspace orchestration
-   reporting layer
-   serialization
-   repository scanning

Run tests:

    PYTHONPATH=src python -m pytest --cov=repo_auditor --cov-report=term-missing

------------------------------------------------------------------------

# Project Goals

repo-auditor aims to become a powerful tool for:

-   developer portfolio auditing
-   repository quality analysis
-   engineering best‑practice enforcement
-   large GitHub organization reviews

Potential future capabilities:

-   GitHub PR integration
-   CI pipeline checks
-   automatic repository upgrade suggestions
-   architecture linting
-   dependency risk detection

------------------------------------------------------------------------

# License

MIT License

------------------------------------------------------------------------

# Author

Mathieu Alassoeur

Computer Engineering Student\
Data Analytics & Software Engineering

GitHub: https://github.com/MatALass
