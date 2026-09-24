"""GitHub connector — ingests issues, pull requests, and commit comments via GitHub REST API."""

from __future__ import annotations

import os
import urllib.request
import json
from dataclasses import dataclass, field
from typing import Any

from packages.connectors.base_connector import BaseConnector, IngestPayload


@dataclass
class GitHubMemory:
    repo: str
    item_type: str  # "issue", "pull_request", "commit_comment"
    item_id: int | str
    title: str
    body: str
    author: str
    url: str
    extra_tags: list[str] = field(default_factory=list)

    def to_ingest_payload(self) -> IngestPayload:
        tags = ["github", self.item_type, *self.extra_tags]
        header = f"[{self.repo}] {self.title}\n" if self.title else ""
        content = f"{header}{self.body}".strip()
        return IngestPayload(
            content=content,
            source_type="github",
            source_id=f"{self.repo}#{self.item_id}",
            actor=self.author or "github_bot",
            metadata={
                "repo": self.repo,
                "item_type": self.item_type,
                "item_id": self.item_id,
                "url": self.url,
            },
            tags=tags,
        )


class GitHubConnector(BaseConnector):
    """Fetch issues, PRs, or comments from a GitHub repository."""

    def __init__(self, token: str | None = None, api_base: str = "https://api.github.com") -> None:
        self._token = token or os.environ.get("GITHUB_TOKEN", "")
        self._api_base = api_base.rstrip("/")

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Memory-Firewall-Connector",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _request(self, path: str) -> Any:
        url = f"{self._api_base}/{path.lstrip('/')}"
        req = urllib.request.Request(url, headers=self._get_headers())
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"GitHub API error: status {response.status}")
            data = response.read().decode("utf-8")
            return json.loads(data)

    def fetch_issues(self, repo: str, state: str = "open", limit: int = 30) -> list[GitHubMemory]:
        """Fetch issues from a repository."""
        data = self._request(f"/repos/{repo}/issues?state={state}&per_page={limit}")
        results: list[GitHubMemory] = []
        for item in data:
            # Skip PRs in issues endpoint if pull_request key exists
            is_pr = "pull_request" in item
            item_type = "pull_request" if is_pr else "issue"
            results.append(
                GitHubMemory(
                    repo=repo,
                    item_type=item_type,
                    item_id=item.get("number", 0),
                    title=item.get("title", ""),
                    body=item.get("body") or "",
                    author=item.get("user", {}).get("login", "unknown"),
                    url=item.get("html_url", ""),
                    extra_tags=[label.get("name") for label in item.get("labels", []) if isinstance(label, dict)],
                )
            )
        return results

    def fetch_memories(self, repo: str, state: str = "open", limit: int = 30) -> list[IngestPayload]:
        """Fetch memories in standard IngestPayload format."""
        items = self.fetch_issues(repo=repo, state=state, limit=limit)
        return [item.to_ingest_payload() for item in items]
