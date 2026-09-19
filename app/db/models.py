"""SQLAlchemy ORM models for Ops Desk."""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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
    __table_args__ = (
        UniqueConstraint("run_id", "seq", name="uq_ops_lg_rag_run_events_run_seq"),
    )

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
        UniqueConstraint(
            "tenant_id", "idempotency_key", name="uq_ops_capability_idem_tenant_key"
        ),
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
