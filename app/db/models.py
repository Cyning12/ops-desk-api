"""SQLAlchemy ORM models for Ops Desk."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

#: 记忆事实 embedding 维度（bge-m3@1024，与 app/ops/rag/ingest.py EMBEDDING_DIM 同源）
MEMORY_FACT_EMBEDDING_DIM = 1024


def now_utc() -> datetime:
    """Return current UTC time."""
    return datetime.utcnow()


class OpsUser(Base):
    """Pre-provisioned user. Registration is not open in v1."""

    __tablename__ = "ops_users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="viewer")
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)

    sessions: Mapped[list["OpsSession"]] = relationship(back_populates="user")
    chat_sessions: Mapped[list["OpsSessionChat"]] = relationship(back_populates="user")


class OpsInviteToken(Base):
    """Invite token for user creation."""

    __tablename__ = "ops_invite_tokens"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="viewer")
    used_by_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_users.id", ondelete="SET NULL"), nullable=True
    )
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)


class OpsSession(Base):
    """DB-backed authentication session."""

    __tablename__ = "ops_sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    # 阶段 T：session 为租户真源（F1=C）；缺省试点 A
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, default="ops-desk-pilot")
    created_at: Mapped[datetime] = mapped_column(default=now_utc)

    user: Mapped["OpsUser"] = relationship(back_populates="sessions")


class OpsRepo(Base):
    """GitHub repository metadata."""

    __tablename__ = "ops_repos"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    owner: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # GitHub node id 超过 int32；ORM Integer 会让 asyncpg 按 int32 绑定
    github_repo_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)


class OpsIssue(Base):
    """GitHub issue data."""

    __tablename__ = "ops_issues"
    __table_args__ = (UniqueConstraint("repo_id", "number", name="uq_ops_issues_repo_number"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False
    )
    github_issue_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=False, default="open")
    labels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    scan_status: Mapped[str | None] = mapped_column(String, nullable=True)
    module_tag: Mapped[str | None] = mapped_column(String, nullable=True)
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    assignees: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    html_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, default="ops-desk-pilot")


class OpsPullRequest(Base):
    """GitHub pull request data."""

    __tablename__ = "ops_pull_requests"
    __table_args__ = (
        UniqueConstraint("repo_id", "number", name="uq_ops_pull_requests_repo_number"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False
    )
    github_pr_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=False, default="open")
    draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ci_status: Mapped[str | None] = mapped_column(String, nullable=True)
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewers: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    html_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    merged_at: Mapped[datetime | None] = mapped_column(nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    first_review_at: Mapped[datetime | None] = mapped_column(nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, default="ops-desk-pilot")


class OpsSyncRun(Base):
    """GitHub sync execution record."""

    __tablename__ = "ops_sync_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False
    )
    sync_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(default=now_utc)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class OpsScanSnapshot(Base):
    """Scan summary snapshot."""

    __tablename__ = "ops_scan_snapshots"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False
    )
    scan_run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_sync_runs.id", ondelete="SET NULL"), nullable=True
    )
    parsed_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    raw_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)


class OpsGraphSnapshot(Base):
    """Graph snapshot: nodes, edges, modules."""

    __tablename__ = "ops_graph_snapshots"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False
    )
    graph_run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_sync_runs.id", ondelete="SET NULL"), nullable=True
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    module_matrix: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)


class OpsSessionChat(Base):
    """Chat session (distinct from auth session)."""

    __tablename__ = "ops_sessions_chat"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)

    user: Mapped["OpsUser"] = relationship(back_populates="chat_sessions")
    runs: Mapped[list["OpsRun"]] = relationship(back_populates="chat_session")


class OpsRun(Base):
    """Single chat run."""

    __tablename__ = "ops_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_sessions_chat.id", ondelete="CASCADE"), nullable=False
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="running")
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)

    chat_session: Mapped["OpsSessionChat"] = relationship(back_populates="runs")
    events: Mapped[list["OpsRunEvent"]] = relationship(back_populates="run")


class OpsRunEvent(Base):
    """Archived SSE event stream."""

    __tablename__ = "ops_run_events"
    __table_args__ = (UniqueConstraint("run_id", "seq", name="uq_ops_run_events_run_seq"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_runs.id", ondelete="CASCADE"), nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    ts_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_role: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)

    run: Mapped["OpsRun"] = relationship(back_populates="events")


class OpsLgRagThread(Base):
    """lg-rag 会话 SoT（thread_id）；独立于 ops_sessions_chat。"""

    __tablename__ = "ops_lg_rag_threads"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)

    turns: Mapped[list["OpsLgRagTurn"]] = relationship(back_populates="thread")


class OpsLgRagTurn(Base):
    """lg-rag 一轮消息（user / assistant / system 摘要）。"""

    __tablename__ = "ops_lg_rag_turns"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    thread_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("ops_lg_rag_threads.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)

    thread: Mapped["OpsLgRagThread"] = relationship(back_populates="turns")


class OpsLgRagRunEvent(Base):
    """lg-rag SSE 事件落盘（T4 replay）；独立于 ops_run_events。"""

    __tablename__ = "ops_lg_rag_run_events"
    __table_args__ = (UniqueConstraint("run_id", "seq", name="uq_ops_lg_rag_run_events_run_seq"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_users.id", ondelete="CASCADE"), nullable=False
    )
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ts_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_role: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)


class OpsLgRagRun(Base):
    """lg-rag run 一等实体（P0' T4 · issue #23 裁定 A1）。

    run_id 与事件表同型（uuid4().hex · String(64)）零迁移；`run_events.run_id`
    **刻意不加 FK**——orphan 补偿「先扫事件后补 run 行」的顺序容错要求事件可先于
    run 行存在。status 词表镜像 done payload 逐字落列（running / waiting_approval /
    done / resumed / disconnected / error）；tenant_id 必填（tenant freeze F1-F6），
    补行等不可知场景落 `''`（承 ops_capability_notes 先例）。
    """

    __tablename__ = "ops_lg_rag_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops_users.id", ondelete="CASCADE"), nullable=False
    )
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)


class OpsGoal(Base):
    """Goal 落表（P0' T5 · issue #23 裁定 A2：图零改动，落图为外状态）。

    **仅 DDL 零功能**——注入 query 前缀 / status 规则流转（不让 LLM 自判）属 P1
    另卡。status 词表（本卡仅 docstring 登记，P1 可迁移修订）：
    active（默认）/ paused / done / abandoned。tenant_id 必填（freeze F1-F6），
    承 notes/runs 先例默认 `''`；thread_id 不加 FK（承 run_events 顺序容错先例，
    P1 接线时可再迁移）。
    """

    __tablename__ = "ops_goals"

    goal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)


class OpsSessionSummary(Base):
    """会话历史真摘要缓存（session-summary-fallback D2 · C1 独立表）。

    与原文 SoT（ops_lg_rag_turns / ops_runs）**物理分表**——摘要绝不写回
    turns 表（防摘要的摘要失真复利 + 原文可查对账）。
    key 铁律：（thread_id, chunk_hash）唯一；chunk_hash 必含
    内容哈希 + prompt_version + model——窗口滑动内容变 → hash 变 →
    自然 miss，**无主动失效逻辑**。
    """

    __tablename__ = "ops_session_summaries"
    __table_args__ = (
        UniqueConstraint("thread_id", "chunk_hash", name="uq_ops_session_summaries_thread_chunk"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    thread_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("ops_lg_rag_threads.id", ondelete="CASCADE"), nullable=False
    )
    #: sha256(prompt_version + model + chunk turns canonical JSON)
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False)
    #: 恒 "llm"（预留未来 heuristic 来源）
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="llm")
    created_at: Mapped[datetime] = mapped_column(default=now_utc)


class OpsCapabilityReceipt(Base):
    """副作用回执（W5）：**副作用以收据为真**。

    写能力（``side_effect ∈ {write, irreversible}``）无论成败都落一行——
    一次"失败"的写可能已经在下游生效（超时 / 半成功），不留就无从对账。

    命中幂等键、**没有真正执行**的那次调用**不落**（没执行就没有副作用）。
    """

    __tablename__ = "ops_capability_receipts"
    __table_args__ = (
        # 同一租户内按幂等键对账（可为空：无幂等键的写能力）
        UniqueConstraint("receipt_id", name="uq_ops_capability_receipts_receipt_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    #: 外部可见的回执号（由 capability.receipts.new_receipt_id() 生成）
    receipt_id: Mapped[str] = mapped_column(String(32), nullable=False)
    capability_id: Mapped[str] = mapped_column(String(128), nullable=False)
    side_effect: Mapped[str] = mapped_column(String(16), nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
    #: 这次写是否在放行下执行（Host 单次放行 / env）——审计要能区分
    write_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    subtask_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    idempotency_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    #: 按 manifest 的 receipt.capture 抓到的关键字段（如 ticketId / url）
    captured: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)


class OpsCapabilityIdempotency(Base):
    """幂等防重表（W5）：**目标不是强幂等，而是同一个键不在本层发出两次请求**。

    ``status='in_flight'`` 时由 ``lease_expires_at`` 兜底：
    **没有租约，进程崩一次就会把该键永久卡死，而且是静默的。**
    """

    __tablename__ = "ops_capability_idempotency"
    __table_args__ = (
        # 幂等键的唯一性作用域：**租户内唯一**（跨租户不该互相影响）
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_ops_capability_idem_tenant_key"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(512), nullable=False)
    capability_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    #: in_flight | done
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    #: 租约到期时间；status=done 时无意义
    lease_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    #: 累计尝试次数（含接管）；>1 说明发生过重试或租约接管
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    #: 完成时关联的回执号（供 duplicate 时返回给调用方对账）
    receipt_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)


class OpsCapabilityNote(Base):
    """受控写便签（stage-w-write-expand · Q1=S1 仓内落笔型写）。

    第二条真实窄写能力 ``ops.write.run_note`` 的落笔目标面：run 备注/审计便签。
    全部经既有受控写闸链落笔（HITL 审批 → resume 单路径 → 执行），行上带
    ``tenant_id`` / ``approval_id`` / ``idempotency_key``——审计串链可查询，
    且 ``(tenant_id, idempotency_key)`` 唯一约束是「重放不双写」的 DB 级兜底
    （幂等 store 进程丢失/跨实例漂移时仍然成立）。
    """

    __tablename__ = "ops_capability_notes"
    __table_args__ = (
        # 幂等键作用域 = 租户内唯一：同键重放 DB 级不双写（FP-4 兜底防线）
        UniqueConstraint(
            "tenant_id", "idempotency_key", name="uq_ops_capability_notes_tenant_key"
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    capability_id: Mapped[str] = mapped_column(String(128), nullable=False)
    #: 与 Principal 同源；代码从 ctx 构造，禁止取模型产出（F1=C 纪律）
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    #: 便签归因 run
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    subtask_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    #: 审计串链：消费的那张 HITL 审批单 id（span approval_id 同源）
    approval_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    idempotency_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)


class OpsHitlRequest(Base):
    """人工审批申请（HITL）——**授权记录**，不是日志。

    触发点只有一个：``prefix_touch_required``。它的含义是"要满足这一步，
    得重跑一个**已执行**的步骤"，而按 Q8 §2.2，改已执行步骤的 ``args``
    就是换一个幂等键 = 一次**新的写**。所以必须有人批。

    为什么必须落库（不能只打在 LangGraph 状态里）：进程内状态重启即丢，
    "申请丢了"和"从来没申请过"在观测上长得一模一样 —— 人会一直等一个
    根本不存在的审批。

    ``unlock_subtask_id``：审批通过要解锁的那一步。解锁 = 把它从不可变前缀里
    摘出来 ⇒ 可恢复点回退到它 ⇒ 从那里重跑（这就是"改历史"的授权边界）。
    """

    __tablename__ = "ops_hitl_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    #: LangGraph checkpoint 标识（PG saver 才有；InMemorySaver 时为 None）
    checkpoint_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    #: 被拦下的步骤
    subtask_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    #: 拦截原因（当前只会是 prefix_touch_required）
    blocked_by: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    #: 审批通过后允许重跑的**已执行**步骤
    unlock_subtask_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    #: pending | approved | rejected | expired
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    decision_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)


class OpsMemoryFact(Base):
    """事实型记忆（L4 · memory-facts-p0）：**只记事实，不记对话**。

    失效一律走状态机（superseded / revoked / expired），**不物理删**——
    旧值留表供审计对账；召回只认 ``status='active'`` 且未过期。
    写入须经 ``app.ops.memory.gate.should_write`` 过闸，闸拒 = 不落库。
    """

    __tablename__ = "ops_memory_facts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'superseded', 'revoked', 'expired')",
            name="ck_ops_memory_facts_status",
        ),
        # memory-preference-profile：放开 preference（首期显式-only · 迁移
        # 20260922_memory_kind_preference 同步放宽落库 CHECK）
        CheckConstraint("kind IN ('fact', 'preference')", name="ck_ops_memory_facts_kind"),
        # 召回主谓词：(tenant, user, key, status)
        Index(
            "idx_ops_memory_facts_recall",
            "tenant_id",
            "user_id",
            "key",
            "status",
        ),
        # revoke_by_source 按源头批量纠错
        Index("idx_ops_memory_facts_source_run", "source_run_id"),
        # 过期扫描只看活跃行：部分索引 WHERE status='active'
        Index(
            "idx_ops_memory_facts_expires_active",
            "expires_at",
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    #: 与 Principal 同源；代码从请求 ctx 构造，禁止取模型产出
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    #: 主体隔离最小粒度
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    #: 规范化事实键（小写点分层，约定见 app/ops/memory/README.md）
    key: Mapped[str] = mapped_column(String, nullable=False)
    #: 事实值（jsonb；闸限制为标量，见 gate.should_write）
    value: Mapped[object] = mapped_column(JSONB, nullable=False)
    #: 'fact' 客观事实 | 'preference' 用户显式偏好（首期显式-only，见
    #: app/ops/memory/gate.py 双向 key 域绑定 pref.*）
    kind: Mapped[str] = mapped_column(String, nullable=False, default="fact")
    #: 溯源：产生该事实的 run（可空 = 人工/系统导入）
    source_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_turn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    #: 显式声明取代哪条旧事实（自引用）
    supersedes: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ops_memory_facts.id", ondelete="SET NULL"),
        nullable=True,
    )
    #: active | superseded | revoked | expired
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    #: TTL；null = 不过期。查询路径自带过滤，不依赖 sweep 存活（双保险）
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    #: P1 向量召回（nullable；既有行不回填 = 只走确定性通路即正确）。
    #: deferred=True：普通 SELECT 不带本列——migration 未跑时 P0 确定性
    #: 通路 SQL 不含它（对齐 failure path「向量列不存在 → 回退确定性」）；
    #: 相似度由向量 SQL 计算，不在 Python 侧触发 deferred 懒加载。
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(MEMORY_FACT_EMBEDDING_DIM), nullable=True, deferred=True
    )
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(default=now_utc, onupdate=now_utc)


class OpsMemoryEpisode(Base):
    """情景记忆（host-v1-episodic-memory-feedback D1 · Q1 run 级）：**经验≠事实**。

    U4 铁律：与事实记忆（ops_memory_facts）**物理分表 · 闸分立 · 召回路径
    分立 · 零互写**——事实是主体绑定的可验证标量，经验是 run 级模式归纳
    （plan 摘要 + 工具序列 + 成败标签）。写入须经
    app.ops.memory.episode_gate.should_write_episode 过闸，闸拒 = 不落库。
    失效走逻辑 revoked（revoke_by_run 一键纠错），**不物理删**；
    召回只认 status='active' 且 outcome='success'（污染放大防线第一层）。
    """

    __tablename__ = "ops_memory_episodes"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('success', 'failure', 'partial')",
            name="ck_ops_memory_episodes_outcome",
        ),
        CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_ops_memory_episodes_status",
        ),
        # 召回主谓词：(tenant, outcome, status)
        Index(
            "idx_ops_memory_episodes_recall",
            "tenant_id",
            "outcome",
            "status",
        ),
        # 聚类键 + 召回指纹匹配
        Index("idx_ops_memory_episodes_fingerprint", "context_fingerprint"),
        # revoke_by_run 纠错溯源
        Index("idx_ops_memory_episodes_run", "run_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    #: 与 Principal 同源；代码从请求 ctx 构造，禁止取模型产出
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    #: run 归因（V1-A 主体绑定同源；Q1 裁定 run 级，一 run 至多一条）
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    #: 任务域（承 IntentV1 domain 词表；unknown 允许）
    task_domain: Mapped[str] = mapped_column(String, nullable=False)
    #: 上下文指纹（确定性哈希：domain+意图特征+工具序列骨架；聚类键）
    context_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    #: plan 摘要（结构元数据非用户内容；≤200 字符，闸拒超长）
    plan_summary: Mapped[str] = mapped_column(Text, nullable=False)
    #: 工具序列骨架（capability id 数组；≤16，闸拒超长）
    tool_sequence: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    #: success | failure | partial 成败标签
    outcome: Mapped[str] = mapped_column(String, nullable=False)
    #: 失败分类词表（failure 必填合法 · Q2 聚类键；success/partial 可空）
    failure_class: Mapped[str | None] = mapped_column(String, nullable=True)
    #: active | revoked（逻辑失效不物理删，承事实记忆先例）
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(default=now_utc)


class OpsLlmUsage(Base):
    """LLM usage 账本（llm-layer-hardening D4）：**这个 run 花了多少 token 可查**。

    纪律：
    - 只存 token 计数与模型名，**不存** prompt/answer 正文（正文 I/O 仍在
      Langfuse 侧、可关、截断）；
    - run_id 双口径并存（chat=ops_runs.id UUID / lg_rag=uuid4().hex）→
      text + surface 区分，**不设 FK**；无上下文调用点 run_id=NULL ·
      surface=background；
    - 无 usage 末帧不落行（**不写 0 假账**）；cost_est 由查询/导出侧
      × price_table_v1.yaml（占位价 · E5 公式），表内不存金额。
    """

    __tablename__ = "ops_llm_usage"
    __table_args__ = (
        # 按 run 聚合查询（这个 run 的 answer+grader+extract 合计）
        Index("idx_ops_llm_usage_run_id", "run_id"),
        # 按入口面 + 时间扫描（成本盘点）
        Index("idx_ops_llm_usage_surface_created", "surface", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4())
    )
    #: chat=ops_runs.id（UUID 字符串）/ lg_rag=uuid4().hex；无上下文 → NULL
    run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    #: 入口面：chat / lg_rag / background
    surface: Mapped[str] = mapped_column(String, nullable=False, default="background")
    #: 任务类型档：answer / grader / extract / structured；未分档 → NULL
    task_type: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False, default="")
    model: Mapped[str] = mapped_column(String, nullable=False, default="")
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cached_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: 传输重试后的实际尝试次数（含首次）；>1 说明发生过退避重试
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(default=now_utc)
