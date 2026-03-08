from __future__ import annotations

from typing import Any

import requests


class GitHubApiError(RuntimeError):
    """Raised when a GitHub API request fails."""


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        *,
        token: str | None = None,
        timeout: int = 20,
        api_version: str = "2022-11-28",
    ) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": api_version,
                "User-Agent": "repo-auditor/0.8.0",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        url = path_or_url if path_or_url.startswith("http") else f"{self.BASE_URL}{path_or_url}"
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            message = self._extract_error_message(response)
            raise GitHubApiError(
                f"GitHub API error {response.status_code} on {url}: {message}"
            )

        return response

    @staticmethod
    def _extract_error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text.strip() or "Unknown error"

        if isinstance(payload, dict):
            if "message" in payload:
                return str(payload["message"])
            return str(payload)

        return str(payload)

    @staticmethod
    def _is_not_found_error(exc: GitHubApiError) -> bool:
        return "GitHub API error 404" in str(exc)

    def get_json(
        self,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self._request("GET", path_or_url, params=params, headers=headers)
        return response.json()

    def get_text(
        self,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        response = self._request("GET", path_or_url, params=params, headers=headers)
        return response.text

    def paginate_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        next_url = f"{self.BASE_URL}{path}"
        next_params = dict(params or {})

        while next_url:
            response = self._request("GET", next_url, params=next_params)
            payload = response.json()

            if not isinstance(payload, list):
                raise GitHubApiError(
                    f"Expected a paginated list response for {next_url}, got: {type(payload).__name__}"
                )

            results.extend(payload)
            next_url = response.links.get("next", {}).get("url")
            next_params = None

        return results

    def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        return self.get_json(f"/repos/{owner}/{repo}")

    def get_branch(self, owner: str, repo: str, branch: str) -> dict[str, Any]:
        return self.get_json(f"/repos/{owner}/{repo}/branches/{branch}")

    def get_tree(self, owner: str, repo: str, tree_sha: str, *, recursive: bool = True) -> dict[str, Any]:
        params = {"recursive": "1"} if recursive else None
        return self.get_json(f"/repos/{owner}/{repo}/git/trees/{tree_sha}", params=params)

    def get_repository_tree_from_default_branch(self, owner: str, repo: str) -> dict[str, Any]:
        repo_payload = self.get_repository(owner, repo)
        default_branch = repo_payload.get("default_branch")

        if not default_branch:
            return {"tree": []}

        try:
            branch_payload = self.get_branch(owner, repo, str(default_branch))
        except GitHubApiError as exc:
            if self._is_not_found_error(exc):
                return {"tree": []}
            raise

        commit_data = branch_payload.get("commit", {})

        tree_sha = (
            commit_data.get("commit", {})
            .get("tree", {})
            .get("sha")
        )

        if not tree_sha:
            tree_sha = commit_data.get("sha")

        if not tree_sha:
            return {"tree": []}

        return self.get_tree(owner, repo, tree_sha, recursive=True)

    def get_readme(self, owner: str, repo: str) -> str | None:
        try:
            return self.get_text(
                f"/repos/{owner}/{repo}/readme",
                headers={"Accept": "application/vnd.github.raw+json"},
            )
        except GitHubApiError as exc:
            if self._is_not_found_error(exc):
                return None
            raise

    def get_file_text(self, owner: str, repo: str, path: str) -> str | None:
        try:
            return self.get_text(
                f"/repos/{owner}/{repo}/contents/{path}",
                headers={"Accept": "application/vnd.github.raw+json"},
            )
        except GitHubApiError as exc:
            if self._is_not_found_error(exc):
                return None
            raise

    def list_user_repositories(
        self,
        username: str,
        *,
        include_forks: bool = False,
    ) -> list[dict[str, Any]]:
        repos = self.paginate_json(
            f"/users/{username}/repos",
            params={"per_page": 100, "type": "owner", "sort": "updated"},
        )
        if include_forks:
            return repos
        return [repo for repo in repos if not repo.get("fork", False)]

    def list_org_repositories(
        self,
        org: str,
        *,
        include_forks: bool = False,
    ) -> list[dict[str, Any]]:
        repos = self.paginate_json(
            f"/orgs/{org}/repos",
            params={"per_page": 100, "type": "all", "sort": "updated"},
        )
        if include_forks:
            return repos
        return [repo for repo in repos if not repo.get("fork", False)]