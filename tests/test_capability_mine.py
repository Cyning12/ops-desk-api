"""用户态可见能力目录端点 GET /api/ops/capability/mine · 契约测试（B1）。

钉死契约（task_capability_mine_endpoint）：
- TC1 未登录 401（承 get_current_user 既有语义 · dependency_overrides 不挂即真路径）
- TC2 maintainer 字段族九键齐 + 与 evaluate_visibility 直出对拍一致
- TC3 viewer ⊆ maintainer（roles=frozenset({user.role}) 映射机断 · N3/FP-4）
- TC4 空集 200 {"items": [], "count": 0}（FP-2 · 不 500）
- TC5 出站白名单：响应体不含 adapter / local_fn: · 九键之外零键（FP-5）
- TC6 单源对拍：路由返回 == capability_catalog_snapshot 直出投影（FP-6 零过滤）

fixture manifest 控在册集：autouse 清注册表 → 用例按需注册 fixture 条目 →
收尾恢复默认（clear + ensure_default_capabilities · 承 test_capability_gateway 先例）。
"""

from __future__ import annotations

import pytest

from app.main import app as fastapi_app
from app.ops.capability import (
    CapabilitySpec,
    LocalFnAdapter,
    capability_catalog_snapshot,
    get_registry,
    register,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.types import Principal
from app.ops.deps import get_current_user

MINE_URL = "/api/ops/capability/mine"

MAINTAINER_ID = "00000000-0000-0000-0000-000000000001"
VIEWER_ID = "00000000-0000-0000-0000-000000000002"

# 出站白名单九键（钉死契约 4 · status 常量 available 承可见性求值结果）
WHITELIST_KEYS = frozenset(
    {
        "id",
        "kind",
        "description",
        "when_to_use",
        "tags",
        "risk_level",
        "side_effect",
        "enabled",
        "status",
    }
)

# B2 admin 面字段 / 内部装配 · 用户面不出站
FORBIDDEN_KEYS = frozenset(
    {
        "adapter",
        "args_schema",
        "when_not_to_use",
        "tenant_scoped",
        "reversible",
        "execution_type",
    }
)


def _make_user(user_id: str, username: str, role: str):
    from app.db.models import OpsUser

    return OpsUser(id=user_id, username=username, role=role)


def _override_user(user) -> None:
    # 注意：override 按自身签名解析——禁 *args/**kwargs（会被当 query 参数 422）
    async def fake_get_current_user():
        return user

    fastapi_app.dependency_overrides[get_current_user] = fake_get_current_user


def _register_fixture_specs() -> None:
    """fixture manifest 在册集：一条全可见（未声明 visibility）+ 一条 maintainer 限定。

    故意带上 args_schema / when_not_to_use / tenant_scoped / reversible /
    execution_type——这些是「绝不该出站」的字段，TC5 靠它们证投影泄露。
    """
    register(
        CapabilitySpec(
            capability_id="fixture_visible_all",
            kind="local_fn",
            description="fixture：全员可见只读条目",
            when_to_use="fixture 对拍用 · 任何登录用户可见",
            when_not_to_use="不该出站字段 · fixture",
            tags=("fixture", "readonly"),
            risk_level="low",
            side_effect="read",
            enabled=True,
            tenant_scoped=True,
            reversible=True,
            execution_type="instant",
            args_schema={"type": "object", "properties": {}},
        ),
        LocalFnAdapter(lambda payload: {"echo": payload}),
    )
    register(
        CapabilitySpec(
            capability_id="fixture_maintainer_only",
            kind="local_fn",
            description="fixture：仅 maintainer 角色可见",
            when_to_use="fixture 对拍用 · 角色限定",
            when_not_to_use="不该出站字段 · fixture",
            tags=("fixture",),
            risk_level="medium",
            side_effect="read",
            enabled=True,
            visibility={"roles": ["maintainer"]},
            args_schema={"type": "object", "properties": {}},
        ),
        LocalFnAdapter(lambda payload: {"echo": payload}),
    )


@pytest.fixture(autouse=True)
def _fixture_registry():
    """注册表隔离：清空 → 用例自控在册集 → 恢复默认（承 test_capability_gateway 先例）。"""
    get_registry().clear()
    yield
    get_registry().clear()
    ensure_default_capabilities()
    fastapi_app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# TC1 · 鉴权（FP-1）
# ---------------------------------------------------------------------------


async def test_mine_requires_auth_401(client):
    """无 cookie → 401（get_current_user 既有三分支语义 · 不挂 override 即真路径）。"""
    _register_fixture_specs()
    resp = await client.get(MINE_URL)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# TC2 · maintainer 字段族 + 单源对拍（钉死契约 3/6）
# ---------------------------------------------------------------------------


async def test_mine_maintainer_fields_and_visibility_parity(client):
    _register_fixture_specs()
    _override_user(_make_user(MAINTAINER_ID, "admin", "maintainer"))

    resp = await client.get(MINE_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "count"}
    assert body["count"] == len(body["items"])
    assert body["count"] >= 1

    for item in body["items"]:
        assert set(item.keys()) == WHITELIST_KEYS
        assert item["status"] == "available"

    # 条目 id 集与 evaluate_visibility 对同一在册集直出对拍完全一致（禁双真源）
    principal = Principal(
        user_id=MAINTAINER_ID,
        tenant_id="ops-desk-pilot",
        roles=frozenset({"maintainer"}),
    )
    visible, _summary = capability_catalog_snapshot(principal=principal)
    expected_ids = {s.capability_id for s in visible}
    actual_ids = {item["id"] for item in body["items"]}
    assert actual_ids == expected_ids
    assert "fixture_maintainer_only" in actual_ids  # maintainer 看得到角色限定条目


# ---------------------------------------------------------------------------
# TC3 · viewer ⊆ maintainer（N3 钉死 · FP-4）
# ---------------------------------------------------------------------------


async def test_mine_viewer_subset_of_maintainer(client):
    _register_fixture_specs()

    _override_user(_make_user(VIEWER_ID, "viewer", "viewer"))
    resp_viewer = await client.get(MINE_URL)
    assert resp_viewer.status_code == 200
    viewer_ids = {item["id"] for item in resp_viewer.json()["items"]}

    _override_user(_make_user(MAINTAINER_ID, "admin", "maintainer"))
    resp_maintainer = await client.get(MINE_URL)
    assert resp_maintainer.status_code == 200
    maintainer_ids = {item["id"] for item in resp_maintainer.json()["items"]}

    # roles=frozenset({user.role}) 映射机断：viewer 看不到 maintainer 限定条目
    assert "fixture_maintainer_only" not in viewer_ids
    assert "fixture_visible_all" in viewer_ids
    assert viewer_ids <= maintainer_ids
    assert viewer_ids != maintainer_ids  # 真子集：证明角色裁剪真的生效


# ---------------------------------------------------------------------------
# TC4 · 空集如实（FP-2 · 不 500）
# ---------------------------------------------------------------------------


async def test_mine_empty_visible_set_200(client):
    """可见集被全裁（viewer 对 maintainer 限定条目）→ 200 空集如实，不 500 不伪造。"""
    register(
        CapabilitySpec(
            capability_id="fixture_maintainer_only",
            kind="local_fn",
            description="fixture：仅 maintainer 角色可见",
            when_to_use="fixture 对拍用 · 角色限定",
            tags=("fixture",),
            risk_level="medium",
            side_effect="read",
            enabled=True,
            visibility={"roles": ["maintainer"]},
        ),
        LocalFnAdapter(lambda payload: {"echo": payload}),
    )
    _override_user(_make_user(VIEWER_ID, "viewer", "viewer"))

    resp = await client.get(MINE_URL)
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "count": 0}


# ---------------------------------------------------------------------------
# TC5 · 出站白名单（FP-5 · grep 机断）
# ---------------------------------------------------------------------------


async def test_mine_response_whitelist_no_internal_assembly(client):
    _register_fixture_specs()
    _override_user(_make_user(MAINTAINER_ID, "admin", "maintainer"))

    resp = await client.get(MINE_URL)
    assert resp.status_code == 200

    # 序列化响应体 grep：内部装配痕迹零命中
    assert "adapter" not in resp.text
    assert "local_fn:" not in resp.text

    for item in resp.json()["items"]:
        assert set(item.keys()) == WHITELIST_KEYS
        assert not (set(item.keys()) & FORBIDDEN_KEYS)


# ---------------------------------------------------------------------------
# TC6 · 单源对拍（FP-6 · 路由层零过滤）
# ---------------------------------------------------------------------------


async def test_mine_route_matches_snapshot_projection(client):
    """路由返回值 == capability_catalog_snapshot 直出经同一白名单投影（含顺序）。

    路由层若有任何自有过滤/排序/裁剪，本条立刻红。
    """
    from app.ops import capability_mine

    _register_fixture_specs()
    _override_user(_make_user(MAINTAINER_ID, "admin", "maintainer"))

    principal = Principal(
        user_id=MAINTAINER_ID,
        tenant_id="ops-desk-pilot",
        roles=frozenset({"maintainer"}),
    )
    visible, _summary = capability_catalog_snapshot(principal=principal)
    expected_items = [capability_mine.project_capability(spec) for spec in visible]

    resp = await client.get(MINE_URL)
    assert resp.status_code == 200
    assert resp.json()["items"] == expected_items
