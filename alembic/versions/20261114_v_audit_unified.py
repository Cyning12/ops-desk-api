"""v_audit_unified：审计统一视图（P0' T6 · issue #23 裁定 P3 · 单张 view 合格线）

Revision ID: 20261114_v_audit_unified
Revises: 20261114_ops_goals
Create Date: 2026-11-14

P3：union receipts/llm_usage/hitl_requests，公共列
ts/tenant_id/user_id/run_id/domain/action/outcome（+source_id 回查对账），
view 暴露 tenant_id 供查询侧过滤。不做端点、不做聚合页、不物化。
缺列域补值（30 钉死）：receipts 无 run_id→NULL；llm_usage 无
tenant_id/user_id→''（从严口径承 data 层先例）；hitl user←COALESCE(decision_by,'')。
零源表变更；CREATE OR REPLACE 幂等可重放。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261114_v_audit_unified"
down_revision: str | None = "20261114_ops_goals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VIEW_SQL = """
CREATE OR REPLACE VIEW v_audit_unified AS
SELECT
    created_at                                  AS ts,
    tenant_id                                   AS tenant_id,
    user_id                                     AS user_id,
    NULL::varchar                               AS run_id,
    'capability_receipt'                        AS domain,
    capability_id                               AS action,
    CASE WHEN ok THEN 'ok' ELSE 'error' END     AS outcome,
    id::varchar                                 AS source_id
FROM ops_capability_receipts
UNION ALL
SELECT
    created_at                                  AS ts,
    tenant_id                                   AS tenant_id,
    COALESCE(decision_by, '')                   AS user_id,
    run_id                                      AS run_id,
    'hitl'                                      AS domain,
    blocked_by                                  AS action,
    status                                      AS outcome,
    id                                          AS source_id
FROM ops_hitl_requests
UNION ALL
SELECT
    created_at                                  AS ts,
    ''::varchar                                 AS tenant_id,
    ''::varchar                                 AS user_id,
    run_id                                      AS run_id,
    'llm_usage'                                 AS domain,
    COALESCE(task_type, surface)                AS action,
    'recorded'                                  AS outcome,
    id::varchar                                 AS source_id
FROM ops_llm_usage
"""


def upgrade() -> None:
    op.execute(_VIEW_SQL)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_audit_unified")
