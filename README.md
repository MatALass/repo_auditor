# repo-auditor

A structured repository auditing tool focused on project quality, maintainability, and portfolio value.

## Goals

This project aims to:
- score repositories with a transparent rule-based system
- identify the weakest repositories in a portfolio
- explain the main issues clearly
- propose prioritized improvements

## Current status

Version `0.4.0` includes:
- repository scoring engine
- issue catalog
- markdown report generation
- demo CLI mode
- local repository scanner
- workspace scanning across multiple repositories
- Markdown and JSON export

## Run locally

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .