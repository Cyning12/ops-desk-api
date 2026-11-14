"""P0' T6 · v_audit_unified 统一审计视图（issue #23 裁定 P3 · 单张 view 合格线）。

验收原文：按 run_id+时间窗一条 SQL 拉出跨三域执行链；view 暴露 tenant_id 供过滤。
本地真 PG 实证（承 T4/T5 体例）。
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 v_audit_unified")


async def _ensure_view() -> None:
    """测试库走 create_all（不含 view）——用迁移同款 SQL 保证存在（幂等）。"""
    from pathlib import Path

    from app.db.session import AsyncSessionLocal

    sql = Path("alembic/versions/20261114_v_audit_unified.py").read_text()
    body = sql.split('_VIEW_SQL = """', 1)[1].split('"""', 1)[0]
    async with AsyncSessionLocal() as db:
        await db.execute(text(body))
        await db.commit()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_v_audit_unified_cross_domain_chain_by_run_and_window(seeded_maintainer) -> None:
    """P3 验收：按 run_id+时间窗一条 SQL 拉出跨三域执行链。"""
    from app.db.models import OpsCapabilityReceipt, OpsHitlRequest, OpsLlmUsage
    from app.db.session import AsyncSessionLocal

    await _ensure_view()
    run_id = uuid.uuid4().hex
    rid = f"rc-{uuid.uuid4().hex[:8]}"
    receipt_pk = str(uuid.uuid4())
    hid = f"hitl-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        db.add(
            OpsCapabilityReceipt(
                id=receipt_pk,
                receipt_id=rid,
                capability_id="ops.write.run_note",
                side_effect="write",
                ok=True,
                write_confirmed=True,
                tenant_id="t-audit",
                user_id="u-1",
            )
        )
        db.add(
            OpsHitlRequest(
                id=hid,
                run_id=run_id,
                thread_id=f"th-{run_id[:8]}",
                tenant_id="t-audit",
                blocked_by="prefix_touch_required",
                status="approved",
                decision_by="ops-admin",
            )
        )
        db.add(
            OpsLlmUsage(
                run_id=run_id,
                surface="lg_rag",
                task_type="answer",
                provider="siliconflow",
                model="deepseek-v3",
                prompt_tokens=10,
                completion_tokens=5,
            )
        )
        await db.commit()
        rows = (
            await db.execute(
                text(
                    "SELECT domain, action, outcome, tenant_id, user_id, run_id"
                    " FROM v_audit_unified"
                    " WHERE (run_id = :rid OR source_id = :src)"
                    # 三源 created_at 均 now_utc 存 UTC naive——时间窗须同口径锚定
                    # （now() 是 timestamptz 本地时区，直比有 +08 偏移 footgun）
                    "   AND ts >= (now() AT TIME ZONE 'UTC') - interval '1 hour'"
                    " ORDER BY ts"
                ),
                {"rid": run_id, "src": receipt_pk},
            )
        ).all()
        domains = {r.domain for r in rows}
        # receipts 无 run_id 列（30 裁定补 NULL）——经 source_id（=源表 PK id，
        # 非 receipt_id）回查对账入链
        assert "capability_receipt" in domains
        hitl = [r for r in rows if r.domain == "hitl"]
        llm = [r for r in rows if r.domain == "llm_usage"]
        assert hitl and hitl[0].run_id == run_id and hitl[0].outcome == "approved"
        assert hitl[0].user_id == "ops-admin"  # decision_by 补值
        assert llm and llm[0].action == "answer" and llm[0].outcome == "recorded"
        # 清理
        for table, key, val in (
            ("ops_capability_receipts", "receipt_id", rid),
            ("ops_hitl_requests", "id", hid),
            ("ops_llm_usage", "run_id", run_id),
        ):
            await db.execute(text(f"DELETE FROM {table} WHERE {key} = :v"), {"v": val})
        await db.commit()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_v_audit_unified_tenant_filter_and_llm_tenant_empty(seeded_maintainer) -> None:
    """tenant_id 过滤可用 + llm_usage 行 tenant_id=''（从严口径）。"""
    from app.db.models import OpsLlmUsage
    from app.db.session import AsyncSessionLocal

    await _ensure_view()
    run_id = uuid.uuid4().hex
    async with AsyncSessionLocal() as db:
        db.add(
            OpsLlmUsage(
                run_id=run_id,
                surface="lg_rag",
                task_type=None,  # 未分档 → action 落 surface（30 裁定 COALESCE）
                provider="p",
                model="m",
                prompt_tokens=1,
                completion_tokens=1,
            )
        )
        await db.commit()
        row = (
            await db.execute(
                text(
                    "SELECT tenant_id, user_id, action FROM v_audit_unified"
                    " WHERE domain = 'llm_usage' AND run_id = :rid"
                ),
                {"rid": run_id},
            )
        ).one()
        assert row.tenant_id == ""  # 从严：llm 无 tenant 列补 ''
        assert row.user_id == ""
        assert row.action == "lg_rag"  # task_type NULL → surface
        # tenant 过滤：'' 行可被 tenant_id='' 谓词命中，t-audit 谓词不命中
        n = (
            await db.execute(
                text(
                    "SELECT count(*) FROM v_audit_unified"
                    " WHERE domain = 'llm_usage' AND run_id = :rid AND tenant_id = 't-audit'"
                ),
                {"rid": run_id},
            )
        ).scalar_one()
        assert n == 0
        await db.execute(text("DELETE FROM ops_llm_usage WHERE run_id = :v"), {"v": run_id})
        await db.commit()
