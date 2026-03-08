from __future__ import annotations

from typing import Any

import pytest

from repo_auditor.github_client import GitHubApiError, GitHubClient


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        json_data: Any = None,
        text: str = "",
        links: dict[str, Any] | None = None,
        json_raises: bool = False,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.links = links or {}
        self._json_raises = json_raises

    def json(self) -> Any:
        if self._json_raises:
            raise ValueError("invalid json")
        return self._json_data


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.headers: dict[str, str] = {}
        self._responses = responses
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int,
    ) -> FakeResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if not self._responses:
            raise AssertionError("No fake responses left for request")
        return self._responses.pop(0)


@pytest.fixture
def client_factory(monkeypatch: pytest.MonkeyPatch):
    def _build(responses: list[FakeResponse], **kwargs: Any) -> tuple[GitHubClient, FakeSession]:
        session = FakeSession(responses)
        monkeypatch.setattr("repo_auditor.github_client.requests.Session", lambda: session)
        client = GitHubClient(**kwargs)
        return client, session

    return _build


def test_client_sets_default_headers_and_optional_token(client_factory) -> None:
    client, session = client_factory([], token="secret-token", timeout=33)

    assert client.timeout == 33
    assert session.headers["Accept"] == "application/vnd.github+json"
    assert session.headers["X-GitHub-Api-Version"] == "2022-11-28"
    assert session.headers["User-Agent"] == "repo-auditor/0.8.0"
    assert session.headers["Authorization"] == "Bearer secret-token"


def test_extract_error_message_prefers_message_field() -> None:
    response = FakeResponse(status_code=404, json_data={"message": "Not Found"})
    assert GitHubClient._extract_error_message(response) == "Not Found"


def test_extract_error_message_returns_dict_string_when_message_missing() -> None:
    response = FakeResponse(status_code=500, json_data={"error": "boom"})
    assert GitHubClient._extract_error_message(response) == "{'error': 'boom'}"


def test_extract_error_message_returns_list_string_for_non_dict_json() -> None:
    response = FakeResponse(status_code=500, json_data=["boom"])
    assert GitHubClient._extract_error_message(response) == "['boom']"


def test_extract_error_message_falls_back_to_text_when_json_invalid() -> None:
    response = FakeResponse(status_code=500, text="server exploded", json_raises=True)
    assert GitHubClient._extract_error_message(response) == "server exploded"


def test_extract_error_message_returns_unknown_error_when_empty_text() -> None:
    response = FakeResponse(status_code=500, text="   ", json_raises=True)
    assert GitHubClient._extract_error_message(response) == "Unknown error"


def test_is_not_found_error_detects_404_only() -> None:
    assert GitHubClient._is_not_found_error(GitHubApiError("GitHub API error 404 on x: Not Found")) is True
    assert GitHubClient._is_not_found_error(GitHubApiError("GitHub API error 500 on x: Boom")) is False


def test_request_builds_full_url_for_relative_path_and_passes_timeout(client_factory) -> None:
    client, session = client_factory([FakeResponse(status_code=200, json_data={"ok": True})], timeout=12)

    response = client._request("GET", "/repos/octo/demo", params={"a": 1}, headers={"X-Test": "1"})

    assert response.status_code == 200
    assert session.calls == [
        {
            "method": "GET",
            "url": "https://api.github.com/repos/octo/demo",
            "params": {"a": 1},
            "headers": {"X-Test": "1"},
            "timeout": 12,
        }
    ]


def test_request_keeps_absolute_url_unchanged(client_factory) -> None:
    client, session = client_factory([FakeResponse(status_code=200, text="ok")])

    client._request("GET", "https://next-page.example/api?page=2")

    assert session.calls[0]["url"] == "https://next-page.example/api?page=2"


def test_request_raises_github_api_error_with_message(client_factory) -> None:
    client, _ = client_factory([FakeResponse(status_code=403, json_data={"message": "Forbidden"})])

    with pytest.raises(GitHubApiError, match=r"GitHub API error 403 .* Forbidden"):
        client._request("GET", "/repos/octo/demo")


def test_get_json_returns_payload(client_factory) -> None:
    client, _ = client_factory([FakeResponse(status_code=200, json_data={"name": "demo"})])
    assert client.get_json("/repos/octo/demo") == {"name": "demo"}


def test_get_text_returns_response_text(client_factory) -> None:
    client, _ = client_factory([FakeResponse(status_code=200, text="README")])
    assert client.get_text("/repos/octo/demo/readme") == "README"


def test_paginate_json_collects_multiple_pages_and_clears_params_after_first_call(client_factory) -> None:
    client, session = client_factory(
        [
            FakeResponse(
                status_code=200,
                json_data=[{"name": "repo-1"}],
                links={"next": {"url": "https://api.github.com/page/2"}},
            ),
            FakeResponse(status_code=200, json_data=[{"name": "repo-2"}]),
        ]
    )

    result = client.paginate_json("/users/octo/repos", params={"per_page": 100, "type": "owner"})

    assert result == [{"name": "repo-1"}, {"name": "repo-2"}]
    assert session.calls[0]["url"] == "https://api.github.com/users/octo/repos"
    assert session.calls[0]["params"] == {"per_page": 100, "type": "owner"}
    assert session.calls[1]["url"] == "https://api.github.com/page/2"
    assert session.calls[1]["params"] is None


def test_paginate_json_rejects_non_list_payload(client_factory) -> None:
    client, _ = client_factory([FakeResponse(status_code=200, json_data={"items": []})])

    with pytest.raises(GitHubApiError, match="Expected a paginated list response"):
        client.paginate_json("/users/octo/repos")


def test_get_repository_tree_from_default_branch_returns_empty_tree_without_default_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = GitHubClient()
    monkeypatch.setattr(client, "get_repository", lambda owner, repo: {"default_branch": None})

    assert client.get_repository_tree_from_default_branch("octo", "demo") == {"tree": []}


def test_get_repository_tree_from_default_branch_returns_empty_tree_on_missing_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = GitHubClient()
    monkeypatch.setattr(client, "get_repository", lambda owner, repo: {"default_branch": "main"})

    def fake_get_branch(owner: str, repo: str, branch: str) -> dict[str, Any]:
        raise GitHubApiError("GitHub API error 404 on https://api.github.com/x: Not Found")

    monkeypatch.setattr(client, "get_branch", fake_get_branch)

    assert client.get_repository_tree_from_default_branch("octo", "demo") == {"tree": []}


def test_get_repository_tree_from_default_branch_uses_nested_tree_sha(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GitHubClient()
    monkeypatch.setattr(client, "get_repository", lambda owner, repo: {"default_branch": "main"})
    monkeypatch.setattr(
        client,
        "get_branch",
        lambda owner, repo, branch: {"commit": {"commit": {"tree": {"sha": "tree-123"}}, "sha": "commit-123"}},
    )
    monkeypatch.setattr(
        client,
        "get_tree",
        lambda owner, repo, tree_sha, recursive=True: {"tree": [{"path": tree_sha}], "recursive": recursive},
    )

    result = client.get_repository_tree_from_default_branch("octo", "demo")

    assert result == {"tree": [{"path": "tree-123"}], "recursive": True}


def test_get_repository_tree_from_default_branch_falls_back_to_commit_sha(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GitHubClient()
    monkeypatch.setattr(client, "get_repository", lambda owner, repo: {"default_branch": "main"})
    monkeypatch.setattr(client, "get_branch", lambda owner, repo, branch: {"commit": {"sha": "commit-456"}})
    monkeypatch.setattr(
        client,
        "get_tree",
        lambda owner, repo, tree_sha, recursive=True: {"tree": [{"path": tree_sha}]},
    )

    assert client.get_repository_tree_from_default_branch("octo", "demo") == {"tree": [{"path": "commit-456"}]}


def test_get_repository_tree_from_default_branch_returns_empty_tree_when_no_sha(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = GitHubClient()
    monkeypatch.setattr(client, "get_repository", lambda owner, repo: {"default_branch": "main"})
    monkeypatch.setattr(client, "get_branch", lambda owner, repo, branch: {"commit": {}})

    assert client.get_repository_tree_from_default_branch("octo", "demo") == {"tree": []}


def test_get_readme_returns_text_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GitHubClient()

    def fake_get_text(path_or_url: str, *, params=None, headers=None) -> str:
        assert path_or_url == "/repos/octo/demo/readme"
        assert headers == {"Accept": "application/vnd.github.raw+json"}
        return "# Demo"

    monkeypatch.setattr(client, "get_text", fake_get_text)

    assert client.get_readme("octo", "demo") == "# Demo"


def test_get_readme_returns_none_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GitHubClient()

    def fake_get_text(path_or_url: str, *, params=None, headers=None) -> str:
        raise GitHubApiError("GitHub API error 404 on https://api.github.com/x: Not Found")

    monkeypatch.setattr(client, "get_text", fake_get_text)

    assert client.get_readme("octo", "demo") is None


def test_get_file_text_returns_none_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GitHubClient()

    def fake_get_text(path_or_url: str, *, params=None, headers=None) -> str:
        raise GitHubApiError("GitHub API error 404 on https://api.github.com/x: Not Found")

    monkeypatch.setattr(client, "get_text", fake_get_text)

    assert client.get_file_text("octo", "demo", "README.md") is None


def test_get_file_text_re_raises_non_404(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GitHubClient()

    def fake_get_text(path_or_url: str, *, params=None, headers=None) -> str:
        raise GitHubApiError("GitHub API error 500 on https://api.github.com/x: Boom")

    monkeypatch.setattr(client, "get_text", fake_get_text)

    with pytest.raises(GitHubApiError, match="500"):
        client.get_file_text("octo", "demo", "README.md")


def test_list_user_repositories_filters_forks(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GitHubClient()
    repos = [
        {"name": "repo-a", "fork": False},
        {"name": "repo-b", "fork": True},
        {"name": "repo-c"},
    ]

    def fake_paginate_json(path: str, *, params=None) -> list[dict[str, Any]]:
        assert path == "/users/octo/repos"
        assert params == {"per_page": 100, "type": "owner", "sort": "updated"}
        return repos

    monkeypatch.setattr(client, "paginate_json", fake_paginate_json)

    assert client.list_user_repositories("octo") == [repos[0], repos[2]]
    assert client.list_user_repositories("octo", include_forks=True) == repos


def test_list_org_repositories_filters_forks(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GitHubClient()
    repos = [
        {"name": "repo-a", "fork": False},
        {"name": "repo-b", "fork": True},
    ]

    def fake_paginate_json(path: str, *, params=None) -> list[dict[str, Any]]:
        assert path == "/orgs/acme/repos"
        assert params == {"per_page": 100, "type": "all", "sort": "updated"}
        return repos

    monkeypatch.setattr(client, "paginate_json", fake_paginate_json)

    assert client.list_org_repositories("acme") == [repos[0]]
    assert client.list_org_repositories("acme", include_forks=True) == repos