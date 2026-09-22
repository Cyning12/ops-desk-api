"""ops_memory_facts CHECK 放宽：kind IN ('fact','preference')（memory-preference-profile）

Revision ID: 20260922_memory_kind_preference
Revises: 20260921_llm_usage
Create Date: 2026-09-22

画像层解锁首期：放开 `kind='preference'`（**只收显式声明**——闸双向
key 域绑定 `pref.*` + 抽取管道物理不产 preference，见
app/ops/memory/gate.py / extract.py）。

**零数据迁移**：存量行全 `kind='fact'`，只 drop/add 约束；不新增列、
不新增索引（kind 列与召回索引在 20260921_memory_facts 已存在）。

**回滚须知**：downgrade 重建旧 CHECK `kind = 'fact'`，若库内仍有
preference 行会违反约束**显式炸**——回滚前必须先清 preference 行：

    DELETE FROM ops_memory_facts WHERE kind = 'preference';

（物理删仅限迁移回滚这一运维动作；在线纠错走状态机 revoke，不物理删。）
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260922_memory_kind_preference"
down_revision: str | None = "20260921_llm_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CONSTRAINT = "ck_ops_memory_facts_kind"


def upgrade() -> None:
    op.execute(
        f"ALTER TABLE ops_memory_facts DROP CONSTRAINT IF EXISTS {_CONSTRAINT}"
    )
    op.execute(
        f"ALTER TABLE ops_memory_facts ADD CONSTRAINT {_CONSTRAINT} "
        "CHECK (kind IN ('fact', 'preference'))"
    )


def downgrade() -> None:
    # 回滚须先清 preference 行（见模块 docstring），否则 ADD CONSTRAINT 显式炸
    op.execute(
        f"ALTER TABLE ops_memory_facts DROP CONSTRAINT IF EXISTS {_CONSTRAINT}"
    )
    op.execute(
        f"ALTER TABLE ops_memory_facts ADD CONSTRAINT {_CONSTRAINT} "
        "CHECK (kind = 'fact')"
    )
