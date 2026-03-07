# repo-auditor

A structured repository auditing tool focused on project quality, maintainability, and portfolio value.

## Goals

This project aims to:
- score repositories with a transparent rule-based system
- identify the weakest repositories in a portfolio
- explain the main issues clearly
- propose prioritized improvements
- audit GitHub repositories directly without manual cloning

## Current status

Version `0.6.0` includes:
- repository scoring engine
- issue catalog
- prioritized action planning
- local repository scanner
- workspace scanning across multiple local repositories
- Markdown and JSON export
- GitHub REST API integration for:
  - a single remote repository
  - all repositories of a GitHub user
  - all repositories of a GitHub organization

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## Local usage

### Demo

```bash
repo-auditor --demo
```

### Audit one local repository

```bash
repo-auditor --path /absolute/or/relative/path/to/repo
```

### Audit a local workspace

```bash
repo-auditor --workspace /absolute/or/relative/path/to/workspace
```

### Recursive local workspace audit

```bash
repo-auditor --workspace /absolute/or/relative/path/to/workspace --recursive
```

## GitHub usage

For public repositories, authentication is optional but strongly discouraged for repeated use because unauthenticated requests are more rate-limited.

For private repositories, or for a more reliable rate limit, set a token:

```powershell
$env:GITHUB_TOKEN="ghp_xxx"
```

or on macOS/Linux:

```bash
export GITHUB_TOKEN="ghp_xxx"
```

### Audit one remote repository

```bash
repo-auditor --github-repo owner/repository
```

### Audit all repositories of a GitHub user

```bash
repo-auditor --github-user some-username
```

### Audit all repositories of a GitHub organization

```bash
repo-auditor --github-org some-organization
```

### Include forks

```bash
repo-auditor --github-user some-username --include-forks
```

## Export reports

### Export a local repository audit

```bash
repo-auditor --path /path/to/repo --output ./reports
```

### Export a local workspace audit

```bash
repo-auditor --workspace /path/to/workspace --output ./reports
```

### Export a GitHub user audit

```bash
repo-auditor --github-user some-username --output ./reports
```

### Export a GitHub organization audit

```bash
repo-auditor --github-org some-organization --output ./reports
```

### Export a single GitHub repository audit

```bash
repo-auditor --github-repo owner/repository --output ./reports
```

This writes both Markdown and JSON artifacts.

## What GitHub integration currently does

The remote scanner currently collects:
- repository metadata
- default branch information
- recursive file tree
- README content
- dependency manifests
- tooling/config files
- license and environment template signals
- code file counts
- test file counts
- limited remote file content reads for line-count heuristics

## Current limitations

- remote line counts are still heuristic and intentionally capped to avoid excessive API calls
- some very large repositories may be partially assessed if Git tree traversal is truncated by GitHub
- action planning is rule-based, not semantic
- no deep AST/code-smell analysis yet
- no historical comparison yet

## Recommended token model

Use a fine-grained personal access token with the minimum repository read permissions needed for the endpoints you use. For read-only auditing, a token scoped to repository contents read access is the correct baseline.

## Next steps

- project-type-aware scoring adjustments
- historical scoring and diffing
- scheduled daily audit
- GitHub Actions / webhook integration
- richer action deduplication and grouping
