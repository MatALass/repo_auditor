from pathlib import Path
import json

from repo_auditor.cli import build_demo_repo
from repo_auditor.scoring import audit_repo
from repo_auditor.serialization import (
    repo_result_to_dict,
    write_json_output,
    write_text_output,
)


def test_repo_result_to_dict_contains_expected_keys() -> None:
    facts = build_demo_repo()
    result = audit_repo(facts)

    payload = repo_result_to_dict(result)

    assert payload["repo_name"] == "demo-repo"
    assert "category_scores" in payload
    assert "priority_issues" in payload
    assert "prioritized_actions" in payload


def test_write_text_output_creates_file(tmp_path: Path) -> None:
    output_path = tmp_path / "reports" / "report.md"

    write_text_output(output_path, "# Report\n")

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "# Report\n"


def test_write_json_output_creates_valid_json(tmp_path: Path) -> None:
    output_path = tmp_path / "reports" / "report.json"
    payload = {"name": "demo", "score": 42}

    write_json_output(output_path, payload)

    assert output_path.exists()
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded == payload