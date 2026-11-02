"""只读资源面租户谓词（W-fix-2 · task_api_w_join_gap_fix · 红测先行）。

F13 实证（联调 A4 补测②）：session 切 B（ops-desk-pilot-b）后
GET /api/ops/issues · /pulls · /overview 仍返回 A 租户数据 —— 三处零 tenant 引用。

F4 口径（workspace 租户契约 freeze）：跨租户列表 → **空集**（详情路由不存在 ·
三端点均仅 list/聚合）；同租户读零变化。租户真源 = request.state.ops_tenant_id
（deps.py:43-45 注入）；测试 override 绕过鉴权时须显式设 state，
state 缺失回落默认租户 A（与 deps 回落同值 · 既有测试依赖此路径）。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import wraps

import pytest
from httpx import AsyncClient

from app.db.models import OpsIssue, OpsPullRequest, OpsRepo
from app.db.session import AsyncSessionLocal
from app.ops.deps import get_current_user
from app.ops.tenant_context import TENANT_A, TENANT_B
from tests.conftest import DB_AVAILABLE, fastapi_app

pytestmark = pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")


def _make_override(tenant_id: str):
    """cookie 鉴权 override：显式注入 request.state.ops_tenant_id（模拟 session 真源）。"""
    from app.db.models import OpsUser

    test_user = OpsUser(
        id="00000000-0000-0000-0000-000000000001",
        username="admin",
        role="maintainer",
    )

    @wraps(get_current_user)
    async def fake(request, *args, **kwargs):
        request.state.ops_tenant_id = tenant_id
        return test_user

    return fake


@pytest.fixture
def override_auth_tenant_a():
    fastapi_app.dependency_overrides[get_current_user] = _make_override(TENANT_A)
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def override_auth_tenant_b():
    fastapi_app.dependency_overrides[get_current_user] = _make_override(TENANT_B)
    yield
    fastapi_app.dependency_overrides.clear()


async def _seed_tenant_a_data() -> None:
    """种一仓一 issue（closed）一 PR（merged），全部 tenant_id=A（模型默认值即 A）。"""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name="tenant-fixture", full_name="acme/tenant-fixture")
        db.add(repo)
        await db.flush()
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=1,
                title="A 租户 issue",
                state="closed",
                created_at=now - timedelta(days=3),
                updated_at=now,
                closed_at=now,
                tenant_id=TENANT_A,
            )
        )
        db.add(
            OpsPullRequest(
                repo_id=repo.id,
                number=2,
                title="A 租户 PR",
                state="closed",
                created_at=now - timedelta(days=2),
                updated_at=now,
                merged_at=now,
                first_review_at=now - timedelta(days=1),
                tenant_id=TENANT_A,
            )
        )
        await db.commit()


# ---------------------------------------------------------------------------
# 负样本：B session 下三端点空集（F13 修复前红：泄漏 A 行）
# ---------------------------------------------------------------------------


async def test_issues_cross_tenant_returns_empty(
    client: AsyncClient, override_auth_tenant_b, clean_sync_data
) -> None:
    await _seed_tenant_a_data()
    response = await client.get("/api/ops/issues")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0, f"跨租户泄漏：B 看到 A 的 issue {data['total']} 条"
    assert data["items"] == []


async def test_pulls_cross_tenant_returns_empty(
    client: AsyncClient, override_auth_tenant_b, clean_sync_data
) -> None:
    await _seed_tenant_a_data()
    response = await client.get("/api/ops/pulls")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0, f"跨租户泄漏：B 看到 A 的 PR {data['total']} 条"
    assert data["items"] == []


async def test_overview_cross_tenant_zeroed(
    client: AsyncClient, override_auth_tenant_b, clean_sync_data
) -> None:
    """B session 下聚合指标全部归零（sync_run/scan_snapshot 无 tenant_id · 全局面不断言）。"""
    await _seed_tenant_a_data()
    response = await client.get("/api/ops/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["cycle_time"]["sample_size"] == 0, "跨租户泄漏：B 看到 A 的 cycle_time 样本"
    assert data["review_time"]["sample_size"] == 0, "跨租户泄漏：B 看到 A 的 review_time 样本"
    assert data["issue_throughput"]["count"] == 0, "跨租户泄漏：B 看到 A 的 issue 吞吐"
    assert all(t["closed_issues"] == 0 and t["merged_prs"] == 0 for t in data["trend"]), (
        "跨租户泄漏：B 看到 A 的 trend 数据点"
    )


# ---------------------------------------------------------------------------
# 正样本：同租户（显式 state=A）读零变化
# ---------------------------------------------------------------------------


async def test_issues_same_tenant_unaffected(
    client: AsyncClient, override_auth_tenant_a, clean_sync_data
) -> None:
    await _seed_tenant_a_data()
    response = await client.get("/api/ops/issues")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "A 租户 issue"


async def test_pulls_same_tenant_unaffected(
    client: AsyncClient, override_auth_tenant_a, clean_sync_data
) -> None:
    await _seed_tenant_a_data()
    response = await client.get("/api/ops/pulls")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "A 租户 PR"


async def test_overview_same_tenant_unaffected(
    client: AsyncClient, override_auth_tenant_a, clean_sync_data
) -> None:
    await _seed_tenant_a_data()
    response = await client.get("/api/ops/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["cycle_time"]["sample_size"] == 1
    assert data["issue_throughput"]["count"] == 1
    today = data["trend"][-1]
    assert today["closed_issues"] == 1 and today["merged_prs"] == 1
