"""启动期 NO_PROXY/no_proxy 方括号 IPv6 清洗单测（fix-no-proxy-bracket-ipv6-sanitize）。

钉案：NO_PROXY 含 '[::1]' 时 httpx(trust_env) 构造 client 抛
InvalidURL("Invalid port: ':1]'")（lg_rag.worker_failed · run 0fbebc8e seq19）。
"""

import asyncio
import os

import httpx
import pytest

from app.main import _sanitize_no_proxy_env

PROXY = "http://127.0.0.1:7890"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """隔离 NO_PROXY/no_proxy/http_proxy/https_proxy，避免宿主 env 污染。"""
    for key in ("NO_PROXY", "no_proxy", "http_proxy", "https_proxy"):
        monkeypatch.delenv(key, raising=False)
    yield


def test_bracket_ipv6_stripped_uppercase(monkeypatch):
    """验收 1：大写 NO_PROXY 剥 [::1] → ::1，其余条目与顺序逐字节不变。"""
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1,::1,[::1]")
    _sanitize_no_proxy_env()
    assert os.environ["NO_PROXY"] == "localhost,127.0.0.1,::1,::1"


def test_bracket_ipv6_stripped_lowercase(monkeypatch):
    """验收 3：小写 no_proxy 同处理（httpx 小写优先，漏洗即被绕过）。"""
    monkeypatch.setenv("no_proxy", "localhost,[::1],127.0.0.1")
    _sanitize_no_proxy_env()
    assert os.environ["no_proxy"] == "localhost,::1,127.0.0.1"


def test_both_keys_processed_in_one_pass(monkeypatch):
    """验收 3：大小写两键同场各洗各的。"""
    monkeypatch.setenv("NO_PROXY", "[::1],localhost")
    monkeypatch.setenv("no_proxy", "example.com,[::1]")
    _sanitize_no_proxy_env()
    assert os.environ["NO_PROXY"] == "::1,localhost"
    assert os.environ["no_proxy"] == "example.com,::1"


def test_no_brackets_env_byte_identical(monkeypatch):
    """验收 2：无方括号条目 → env 逐字节不变（零 diff 口径）。"""
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1,::1,.internal,10.0.0.0/8")
    monkeypatch.setenv("no_proxy", "example.com, ::1 ,[ok]x")
    before_upper = os.environ["NO_PROXY"]
    before_lower = os.environ["no_proxy"]
    _sanitize_no_proxy_env()
    assert os.environ["NO_PROXY"] == before_upper
    assert os.environ["no_proxy"] == before_lower


def test_missing_keys_noop(monkeypatch):
    """验收 3：键缺失 → no-op，不新增键。"""
    _sanitize_no_proxy_env()
    assert "NO_PROXY" not in os.environ
    assert "no_proxy" not in os.environ


def test_idempotent_second_run_zero_diff(monkeypatch):
    """幂等：二次调用零 diff（--reload 重入安全）。"""
    monkeypatch.setenv("NO_PROXY", "localhost,[::1]")
    _sanitize_no_proxy_env()
    once = os.environ["NO_PROXY"]
    _sanitize_no_proxy_env()
    assert os.environ["NO_PROXY"] == once == "localhost,::1"


def test_dirty_env_raises_invalid_url_repro(monkeypatch):
    """炸点复现钉：未清洗的 [::1] + 代理 env → httpx 构造 client 抛 InvalidURL。

    钉版 httpx 0.28.1 行为；若上游未来修复，本用例转绿则清洗保持无害（幂等）。
    """
    monkeypatch.setenv("http_proxy", PROXY)
    monkeypatch.setenv("https_proxy", PROXY)
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1,::1,[::1]")
    with pytest.raises(httpx.InvalidURL, match="Invalid port"):
        httpx.Client(trust_env=True)


def test_sanitized_env_httpx_client_ok(monkeypatch):
    """验收 1 回归钉：清洗后 env 构造 sync/async client 均不抛 InvalidURL。"""
    monkeypatch.setenv("http_proxy", PROXY)
    monkeypatch.setenv("https_proxy", PROXY)
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1,::1,[::1]")
    monkeypatch.setenv("no_proxy", "[::1]")
    _sanitize_no_proxy_env()
    with httpx.Client(trust_env=True):
        pass

    async def _mk_async_client() -> None:
        async with httpx.AsyncClient(trust_env=True):
            pass

    asyncio.run(_mk_async_client())
