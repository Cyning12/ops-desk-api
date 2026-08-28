"""GitHub REST 客户端：Issue/PR 分页拉取与重试（httpx · 对齐旧 github_client.py）。"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

REPO_OWNER = "MoonshotAI"
REPO_NAME = "kimi-code"
API_BASE = "https://api.github.com"

# 401/422 立即失败，不重试
FAIL_FAST_STATUS = frozenset({401, 422})
# 403/502/504 指数退避，最多 5 次
RETRYABLE_STATUS = frozenset({403, 502, 504})
MAX_RETRIES = 5
INITIAL_BACKOFF_S = 2.0


class GitHubSyncError(Exception):
    """GitHub 同步不可恢复错误。"""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        fail_fast: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.fail_fast = fail_fast


@dataclass
class GitHubClient:
    token: str
    owner: str = REPO_OWNER
    name: str = REPO_NAME
    http_client: httpx.Client | None = None
    _owns_client: bool = field(default=False, repr=False)

    @classmethod
    def from_env(cls, *, http_client: httpx.Client | None = None) -> GitHubClient:
        token = (os.getenv("GITHUB_TOKEN") or "").strip()
        if not token:
            raise GitHubSyncError("缺少 GITHUB_TOKEN", fail_fast=True)
        repo = (os.getenv("OPS_SYNC_REPO") or f"{REPO_OWNER}/{REPO_NAME}").strip()
        owner, sep, name = repo.partition("/")
        if not sep or not owner or not name:
            raise GitHubSyncError(f"无效 OPS_SYNC_REPO: {repo}", fail_fast=True)
        return cls(token=token, owner=owner, name=name, http_client=http_client)

    def _ensure_client(self) -> httpx.Client:
        if self.http_client is None:
            self.http_client = httpx.Client(timeout=60.0)
            self._owns_client = True
        return self.http_client

    def close(self) -> None:
        if self._owns_client and self.http_client is not None:
            self.http_client.close()
            self.http_client = None
            self._owns_client = False

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = path if path.startswith("http") else f"{API_BASE}{path}"
        client = self._ensure_client()
        last_status: int | None = None
        last_body = ""

        for attempt in range(MAX_RETRIES):
            resp = client.request(
                method,
                url,
                headers=self._headers(),
                params=params,
            )
            last_status = resp.status_code
            last_body = (resp.text or "")[:500]

            if resp.status_code < 400:
                return resp.json()

            if resp.status_code in FAIL_FAST_STATUS:
                raise GitHubSyncError(
                    f"GitHub {resp.status_code}: {last_body}",
                    status_code=resp.status_code,
                    fail_fast=True,
                )

            if resp.status_code in RETRYABLE_STATUS and attempt < MAX_RETRIES - 1:
                delay = INITIAL_BACKOFF_S * (2**attempt)
                time.sleep(delay)
                continue

            raise GitHubSyncError(
                f"GitHub {resp.status_code} after {attempt + 1} attempt(s): {last_body}",
                status_code=last_status,
                fail_fast=False,
            )

        raise GitHubSyncError(
            f"GitHub exhausted retries (last={last_status}): {last_body}",
            status_code=last_status,
            fail_fast=False,
        )

    def _paginate(self, path: str, *, params: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            page_params = {**params, "page": page, "per_page": 100}
            batch = self._request_json("GET", path, params=page_params)
            if not isinstance(batch, list) or not batch:
                break
            items.extend([row for row in batch if isinstance(row, dict)])
            if len(batch) < 100:
                break
            page += 1
        return items

    def fetch_issues(self, since: datetime | None) -> list[dict[str, Any]]:
        """拉取 Issue（排除含 pull_request 键的行）。"""
        params: dict[str, Any] = {"state": "all", "sort": "updated", "direction": "desc"}
        if since is not None:
            params["since"] = since.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        path = f"/repos/{self.owner}/{self.name}/issues"
        raw = self._paginate(path, params=params)
        return [row for row in raw if "pull_request" not in row]

    def fetch_pull_requests(self, since: datetime | None) -> list[dict[str, Any]]:
        """拉取 PR；GitHub pulls 无 since，按 updated_at 客户端过滤。

        已按 updated desc 排序：遇到第一条不新于 since 即可停分页，避免增量仍拉全量 PR。
        """
        path = f"/repos/{self.owner}/{self.name}/pulls"
        params: dict[str, Any] = {"state": "all", "sort": "updated", "direction": "desc"}
        if since is None:
            return self._paginate(path, params=params)

        since_ts = since.timestamp()
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self._request_json(
                "GET", path, params={**params, "page": page, "per_page": 100}
            )
            if not isinstance(batch, list) or not batch:
                break
            stop = False
            for row in batch:
                if not isinstance(row, dict):
                    continue
                updated = self.parse_github_ts(
                    str(row["updated_at"]) if row.get("updated_at") else None
                )
                if updated is None:
                    continue
                if updated.timestamp() > since_ts:
                    items.append(row)
                else:
                    stop = True
                    break
            if stop or len(batch) < 100:
                break
            page += 1
        return items

    @staticmethod
    def parse_github_ts(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def next_link_url(link_header: str | None) -> str | None:
        if not link_header:
            return None
        for part in link_header.split(","):
            chunk = part.strip()
            if 'rel="next"' in chunk:
                start = chunk.find("<") + 1
                end = chunk.find(">")
                if start > 0 and end > start:
                    return chunk[start:end]
        return None
