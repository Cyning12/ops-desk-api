"""记忆状态机 service：write / revoke / sweep / recall（P0 候选来源仅显式调用）。

纪律：
- 写入先过闸（`should_write`）；**闸拒 = 不落库**，抛 `GateRejectedError`。
- 同 `(tenant_id, user_id, key)` 已有 active → **同一事务**内置旧行
  `superseded`、新行 `supersedes` 指旧 id；后写赢，旧值留表可审计。
- 失效走状态机（superseded / revoked / expired），运行期**不物理删**；
  合规物理删除只走管理面 `purge_by_user`（双闸门 · 记动作不记内容）。
- 召回只认 `status='active'` 且未过期——**查询路径自带 `expires_at` 过滤**，
  不依赖 sweep 存活（双保险）。
- session 纪律：传入 `session` 时调用方持有事务（本模块只 flush）；
  不传则模块自开 `AsyncSessionLocal` 并自行 commit（对齐 thread_store 先例）。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsMemoryFact, now_utc
from app.db.session import AsyncSessionLocal
from app.ops.memory.gate import FactCandidate, should_write
from app.ops.tracing import update_current_span_metadata

if TYPE_CHECKING:
    from app.ops.rag.embedder import Embedder

logger = logging.getLogger(__name__)

STATUS_ACTIVE = "active"
STATUS_SUPERSEDED = "superseded"
STATUS_REVOKED = "revoked"
STATUS_EXPIRED = "expired"


class GateRejectedError(ValueError):
    """写入闸拒绝：携带稳定原因码；**调用方不得静默吞掉**。"""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


async def _write_in_session(session: AsyncSession, candidate: FactCandidate) -> OpsMemoryFact:
    """同一事务内：旧 active 置 superseded → 插入新行（supersedes=旧 id）。

    查重谓词含 `kind`（memory-preference-profile 双保险第二道）：跨 kind
    同 key 不互相 supersede——第一道防线是闸的双向 key 域绑定，本谓词防
    未来 key 域约定松动时的静默互冲。
    """
    result = await session.execute(
        select(OpsMemoryFact)
        .where(
            OpsMemoryFact.tenant_id == candidate.tenant_id,
            OpsMemoryFact.user_id == candidate.user_id,
            OpsMemoryFact.key == candidate.key,
            OpsMemoryFact.kind == candidate.kind,
            OpsMemoryFact.status == STATUS_ACTIVE,
        )
        .order_by(OpsMemoryFact.updated_at.desc(), OpsMemoryFact.created_at.desc())
    )
    existing = list(result.scalars().all())
    fact = OpsMemoryFact(
        tenant_id=candidate.tenant_id,
        user_id=candidate.user_id,
        key=candidate.key,
        value=candidate.value,
        kind=candidate.kind,
        supersedes=str(existing[0].id) if existing else None,
    )
    session.add(fact)
    await session.flush()  # 先拿到新行 id，同事务内改旧行
    for old in existing:
        old.status = STATUS_SUPERSEDED
        old.updated_at = now_utc()
    await session.flush()
    return fact


async def write_fact(
    candidate: FactCandidate,
    *,
    source_run_id: str | None = None,
    source_turn: int | None = None,
    expires_at: datetime | None = None,
    session: AsyncSession | None = None,
    embedder: Embedder | None = None,
) -> OpsMemoryFact:
    """过闸 → 落库；闸拒抛 `GateRejectedError`（不落库）；写故障向上抛（不静默）。

    P1：`MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` 时写入后计算 embedding
    （同步 Embedder 线程卸载）；嵌入/列写失败**不阻断写入**，该行 embedding
    留 NULL 走确定性通路（log 标记）。开关关闭时与 P0 逐字节一致。
    """
    decision = should_write(candidate)
    if not decision.allowed:
        logger.info(
            "memory fact rejected reason=%s key=%s tenant=%s",
            decision.reason_code,
            candidate.key,
            candidate.tenant_id,
        )
        raise GateRejectedError(decision.reason_code)
    candidate = FactCandidate(
        tenant_id=candidate.tenant_id.strip(),
        user_id=candidate.user_id.strip(),
        key=candidate.key.strip(),
        value=candidate.value,
        kind=candidate.kind,
    )
    if session is not None:
        fact = await _write_in_session(session, candidate)
        fact.source_run_id = source_run_id
        fact.source_turn = source_turn
        fact.expires_at = expires_at
        await session.flush()
        await _maybe_embed_fact(fact, candidate, embedder=embedder, session=session)
        return fact
    async with AsyncSessionLocal() as own, own.begin():
        fact = await _write_in_session(own, candidate)
        fact.source_run_id = source_run_id
        fact.source_turn = source_turn
        fact.expires_at = expires_at
    # commit 由 begin() 退出时完成；expire_on_commit=False 保证属性可读
    await _maybe_embed_fact(fact, candidate, embedder=embedder, session=None)
    return fact


async def revoke_by_source(
    source_run_id: str,
    *,
    session: AsyncSession | None = None,
) -> int:
    """按源头批量置 `revoked`（纠错唯一入口）；幂等；审计日志记影响行数。

    只动 `active` 行：superseded 行本就不可见，保留其状态可还原
    "它当时被谁取代"的审计链。已 revoked 的行不动 ⇒ 重复调用影响 0 行。
    """
    stmt = (
        update(OpsMemoryFact)
        .where(
            OpsMemoryFact.source_run_id == source_run_id,
            OpsMemoryFact.status == STATUS_ACTIVE,
        )
        .values(status=STATUS_REVOKED, updated_at=now_utc())
    )
    if session is not None:
        result = await session.execute(stmt)
        count = int(result.rowcount or 0)
    else:
        async with AsyncSessionLocal() as own, own.begin():
            result = await own.execute(stmt)
            count = int(result.rowcount or 0)
    # 审计日志：纠错动作本身必须可追查（含幂等 0 行）
    logger.info("memory revoke_by_source source_run_id=%s affected=%d", source_run_id, count)
    return count


async def revoke_by_key(
    tenant_id: str,
    user_id: str,
    key: str,
    *,
    session: AsyncSession | None = None,
) -> int:
    """按 key 一键置 `revoked`（显式偏好/事实的纠错入口）；幂等；审计记行数。

    存在理由：显式写入 `source_run_id` 为空，`revoke_by_source` 定位不到；
    合规删除权要求用户可清除自己的偏好。**必带 tenant+user 谓词**
    （跨 tenant = 0 行）。只动 `active` 行 ⇒ 重复调用影响 0 行（幂等）。
    清除后召回零命中（召回只认 active），不物理删。
    """
    stmt = (
        update(OpsMemoryFact)
        .where(
            OpsMemoryFact.tenant_id == tenant_id,
            OpsMemoryFact.user_id == user_id,
            OpsMemoryFact.key == key,
            OpsMemoryFact.status == STATUS_ACTIVE,
        )
        .values(status=STATUS_REVOKED, updated_at=now_utc())
    )
    if session is not None:
        result = await session.execute(stmt)
        count = int(result.rowcount or 0)
    else:
        async with AsyncSessionLocal() as own, own.begin():
            result = await own.execute(stmt)
            count = int(result.rowcount or 0)
    # 审计日志：纠错动作本身必须可追查（含幂等 0 行）
    logger.info("memory revoke_by_key key=%s tenant=%s affected=%d", key, tenant_id, count)
    return count


async def sweep_expired(
    now: datetime | None = None,
    *,
    session: AsyncSession | None = None,
) -> int:
    """定期任务：`expires_at < now` 的活跃行置 `expired`。

    召回正确性**不依赖**本函数（查询路径自带过期过滤）；sweep 只做显式盘点。
    """
    now = now or now_utc()
    stmt = (
        update(OpsMemoryFact)
        .where(
            OpsMemoryFact.status == STATUS_ACTIVE,
            OpsMemoryFact.expires_at.is_not(None),
            OpsMemoryFact.expires_at < now,
        )
        .values(status=STATUS_EXPIRED, updated_at=now_utc())
    )
    if session is not None:
        result = await session.execute(stmt)
        return int(result.rowcount or 0)
    async with AsyncSessionLocal() as own, own.begin():
        result = await own.execute(stmt)
        return int(result.rowcount or 0)


@dataclass(frozen=True)
class PurgeReport:
    """purge_by_user 报告（backfill 报告字段族 · 计数守恒纪律钉死）。

    守恒：实删 ``deleted == scanned``（同谓词同事务无并发写入时）；
    干跑 ``deleted == 0``；``sum(by_status.values()) == scanned``。
    干跑/实删同谓词同计数口径（口径漂移 = 管理面 409 误拒）。
    """

    dry_run: bool
    #: 谓词匹配行数（全 status）
    scanned: int
    #: 实际删除行数（干跑恒 0）
    deleted: int
    #: 按 status 分桶计数（干跑/实删同口径）
    by_status: dict[str, int]
    elapsed_s: float
    recorded_at: datetime


def _purge_predicate(tenant_id: str, user_id: str):
    """purge 谓词锚点：含且仅含 tenant_id + user_id（越域防线 · 变异检验①兜底）。"""
    return (
        OpsMemoryFact.tenant_id == tenant_id,
        OpsMemoryFact.user_id == user_id,
    )


async def _purge_in_session(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    dry_run: bool,
) -> PurgeReport:
    """同事务内：同谓词计数（总数 + by_status 分桶）→ 干跑零写 / 实删整行 DELETE。"""
    started = time.monotonic()
    predicate = _purge_predicate(tenant_id, user_id)
    count_result = await session.execute(
        select(OpsMemoryFact.status, func.count()).where(*predicate).group_by(OpsMemoryFact.status)
    )
    by_status = {str(row_status): int(n) for row_status, n in count_result.all()}
    scanned = sum(by_status.values())
    deleted = 0
    if not dry_run:
        result = await session.execute(delete(OpsMemoryFact).where(*predicate))
        deleted = int(result.rowcount or 0)
    # 审计日志：记动作不记内容（无 key/value · revoke 先例同形 · 含幂等 0 行）
    logger.info(
        "memory purge_by_user tenant=%s user=%s dry_run=%s affected=%d",
        tenant_id,
        user_id,
        dry_run,
        deleted,
    )
    return PurgeReport(
        dry_run=dry_run,
        scanned=scanned,
        deleted=deleted,
        by_status=by_status,
        elapsed_s=time.monotonic() - started,
        recorded_at=now_utc(),
    )


async def purge_by_user(
    tenant_id: str,
    user_id: str,
    *,
    dry_run: bool = True,
    session: AsyncSession | None = None,
) -> PurgeReport:
    """按 ``(tenant_id, user_id)`` **全 status 整行物理删除**（合规删除权 · 管理面唯一入口）。

    - 谓词含且仅含 tenant+user（revoke_by_key 谓词纪律钉死 · 跨 tenant = 0 行）。
    - **全 status 无差别整行 DELETE**（active/superseded/revoked/expired ·
      embedding 列随行消失；向量 SQL 查表本身，行零残留 = 两通路零残留）。
    - ``dry_run=True``（**默认**）：同谓词只读计数（总数 + by_status 分桶），**零写**；
      实删与干跑同谓词保证计数口径一致。
    - 幂等：DELETE 天然幂等，重复实删第二次 ``deleted == 0``（revoke 幂等语义同形）。
    - 单条 DELETE 语句单事务原子执行（无半删中间态）；session 纪律同模块先例
      （传入 session 调用方持事务只 flush；不传自开 ``AsyncSessionLocal`` 并 commit）。
    - 审计 ``logger.info`` 记动作不记内容（无 key/value · revoke 先例同形 ·
      含幂等 0 行）；管理面入口与 expected_count 双闸门见 ``app/ops/admin/memory.py``。
    """
    if session is not None:
        return await _purge_in_session(session, tenant_id, user_id, dry_run=dry_run)
    async with AsyncSessionLocal() as own, own.begin():
        return await _purge_in_session(own, tenant_id, user_id, dry_run=dry_run)


async def recall_active(
    tenant_id: str,
    user_id: str,
    *,
    limit: int = 8,
    now: datetime | None = None,
    session: AsyncSession | None = None,
) -> list[OpsMemoryFact]:
    """确定性召回（无向量）：`(tenant_id, user_id)` + active + 未过期，
    `updated_at desc` top-N。必带 tenant 谓词（跨 tenant = 空结果）。
    """
    now = now or now_utc()
    stmt = (
        select(OpsMemoryFact)
        .where(
            OpsMemoryFact.tenant_id == tenant_id,
            OpsMemoryFact.user_id == user_id,
            OpsMemoryFact.status == STATUS_ACTIVE,
            (OpsMemoryFact.expires_at.is_(None)) | (OpsMemoryFact.expires_at > now),
        )
        # 确定性排序：updated_at 并列时按 created_at / id 兜底，截断不随机
        .order_by(
            OpsMemoryFact.updated_at.desc(),
            OpsMemoryFact.created_at.desc(),
            OpsMemoryFact.id.desc(),
        )
        .limit(max(0, limit))
    )
    if session is not None:
        result = await session.execute(stmt)
        return list(result.scalars().all())
    async with AsyncSessionLocal() as own:
        result = await own.execute(stmt)
        return list(result.scalars().all())


# ---------------- P1 · 向量语义召回（默认关 · MEMORY_FACTS_VECTOR_RECALL_ENABLED） ----------------

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")

# 融合权重初值（SPEC R5 residual ①：初值需实测调参；改动须同步 README）
#: 无向量相似度时的相似分地板（embedding 为 NULL 的存量行 / 未进向量 top-M）
SIM_FLOOR = 0.3
#: 时间衰减半衰期（天）：decay = 0.5 ** (age_days / HALF_LIFE_DAYS)
HALF_LIFE_DAYS = 90.0
#: 来源权重：source_run_id 为空（显式/人工）高于抽取写入
SOURCE_WEIGHT_EXPLICIT = 1.0
SOURCE_WEIGHT_EXTRACTED = 0.8

# 向量 top-M 召回（裸 SQL 风格同 rag retrieve.py；必带 tenant/user 谓词）
_VECTOR_RECALL_SQL = text(
    "SELECT id, embedding <=> CAST(:qvec AS vector) AS dist "
    "FROM ops_memory_facts "
    "WHERE tenant_id = :tenant AND user_id = :user AND status = 'active' "
    "AND (expires_at IS NULL OR expires_at > :now) "
    "AND embedding IS NOT NULL "
    "ORDER BY dist "
    "LIMIT :m"
)


def memory_facts_vector_recall_enabled() -> bool:
    """`MEMORY_FACTS_VECTOR_RECALL_ENABLED`：默认 false；非法值回退 false + warning。"""
    raw = (os.getenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED") or "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid MEMORY_FACTS_VECTOR_RECALL_ENABLED=%r; fallback to false", raw)
    return False


def _fact_embed_text(key: str, value: object) -> str:
    """嵌入文本 = 注入行同形 `key=value`（语义信号对齐召回展示面）。"""
    text_value = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return f"{key}={text_value}"


def _resolve_embedder(embedder: Embedder | None):
    """未显式注入时复用 rag 查询侧工厂（默认 SiliconFlow ApiEmbedder）。"""
    if embedder is not None:
        return embedder
    from app.ops.rag.embedder import get_query_embedder

    return get_query_embedder()


async def _embed_one(embedder: Embedder, text_value: str) -> list[float] | None:
    """同步 Embedder 协议线程卸载（对齐 rag_nodes/lc_evidence_chain 先例）。

    失败返回 None（调用方走确定性通路），不在此抛。
    """
    try:
        vectors = await asyncio.to_thread(embedder.embed, [text_value])
    except Exception:
        logger.warning("memory fact embed failed; row stays deterministic", exc_info=True)
        return None
    if not vectors or not vectors[0]:
        logger.warning("memory fact embed returned empty; row stays deterministic")
        return None
    return vectors[0]


async def _set_embedding(
    fact_id: str, vector: list[float], *, session: AsyncSession | None
) -> None:
    """单列 UPDATE 回填 embedding；caller session 用 SAVEPOINT 隔离，
    失败只回滚本语句，不污染调用方事务。"""
    stmt = update(OpsMemoryFact).where(OpsMemoryFact.id == fact_id).values(embedding=vector)
    if session is not None:
        async with session.begin_nested():
            await session.execute(stmt)
        return
    async with AsyncSessionLocal() as own, own.begin():
        await own.execute(stmt)


async def _maybe_embed_fact(
    fact: OpsMemoryFact,
    candidate: FactCandidate,
    *,
    embedder: Embedder | None,
    session: AsyncSession | None,
) -> None:
    """写入时嵌入（V1）：开关关 → 零行为；嵌入/列写失败不阻断写入，
    该行 embedding 留 NULL 走确定性通路（log 标记，对齐 failure_paths）。"""
    if not memory_facts_vector_recall_enabled():
        return
    vector = await _embed_one(
        _resolve_embedder(embedder), _fact_embed_text(candidate.key, candidate.value)
    )
    if vector is None:
        return
    try:
        await _set_embedding(str(fact.id), vector, session=session)
    except Exception:
        logger.warning(
            "memory fact embedding persist failed id=%s; row stays deterministic",
            fact.id,
            exc_info=True,
        )


def _source_weight(fact: OpsMemoryFact) -> float:
    """显式/人工来源（source_run_id 为空）权高于抽取。"""
    return SOURCE_WEIGHT_EXTRACTED if fact.source_run_id else SOURCE_WEIGHT_EXPLICIT


def _as_utc(value: datetime) -> datetime:
    """tz 归一：**naive 一律视为 UTC**（不转本地时区、不把 aware 转 naive）。

    真库列由 migration 建 timestamptz → 读回 aware；`now_utc()` 与测试库
    （create_all plain DateTime）为 naive。两侧混算前统一归一到 aware-UTC，
    语义无损（PG 对 naive→timestamptz 的解释同为 UTC）。
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _time_decay(fact: OpsMemoryFact, now: datetime) -> float:
    """指数半衰：decay = 0.5 ** (age_days / HALF_LIFE_DAYS)；未来时间戳按 0 天。"""
    age_seconds = max(0.0, (_as_utc(now) - _as_utc(fact.updated_at)).total_seconds())
    return 0.5 ** ((age_seconds / 86400.0) / HALF_LIFE_DAYS)


def _fuse_recall(
    deterministic: list[OpsMemoryFact],
    vector_sims: dict[str, float],
    vector_rows: dict[str, OpsMemoryFact],
    *,
    limit: int,
    now: datetime,
) -> list[OpsMemoryFact]:
    """确定性 top-N ∪ 向量 top-M → 去重 → 相似×衰减×来源权重 → 截断。

    截低分不随机：并列按 `updated_at desc, created_at desc, id desc` 兜底
    （与 recall_active 同一确定性排序纪律）。
    """
    by_id: dict[str, OpsMemoryFact] = {}
    for fact in deterministic:
        by_id[str(fact.id)] = fact
    for fact_id, fact in vector_rows.items():
        by_id.setdefault(fact_id, fact)

    def _sort_key(fact: OpsMemoryFact) -> tuple:
        sim = vector_sims.get(str(fact.id), SIM_FLOOR)
        score = sim * _time_decay(fact, now) * _source_weight(fact)
        return (score, fact.updated_at, fact.created_at, str(fact.id))

    fused = sorted(by_id.values(), key=_sort_key, reverse=True)
    return fused[: max(0, limit)]


async def _vector_top_m(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    query_vector: list[float],
    *,
    m: int,
    now: datetime,
) -> tuple[dict[str, float], dict[str, OpsMemoryFact]]:
    """向量 top-M：cosine 距离升序；返回 (id→相似度, id→ORM 行)。

    相似度 = 1 - cosine_distance，截到 [0,1]。ORM 行补取时**再次**带
    tenant/user/active/未过期谓词（双保险，不信任第一跳的 id 集）。
    """
    rows = await session.execute(
        _VECTOR_RECALL_SQL,
        {
            "tenant": tenant_id,
            "user": user_id,
            "qvec": json.dumps(query_vector),
            "m": max(0, m),
            "now": now,
        },
    )
    sims: dict[str, float] = {}
    ids: list[str] = []
    for row in rows:
        fact_id = str(row.id)
        sims[fact_id] = min(1.0, max(0.0, 1.0 - float(row.dist)))
        ids.append(fact_id)
    if not ids:
        return sims, {}
    result = await session.execute(
        select(OpsMemoryFact).where(
            OpsMemoryFact.id.in_(ids),
            OpsMemoryFact.tenant_id == tenant_id,
            OpsMemoryFact.user_id == user_id,
            OpsMemoryFact.status == STATUS_ACTIVE,
            (OpsMemoryFact.expires_at.is_(None)) | (OpsMemoryFact.expires_at > now),
        )
    )
    return sims, {str(f.id): f for f in result.scalars().all()}


async def _recall_with_vector_in_session(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    query: str,
    *,
    limit: int,
    now: datetime,
    embedder: Embedder | None,
) -> list[OpsMemoryFact]:
    deterministic = await recall_active(tenant_id, user_id, limit=limit, now=now, session=session)
    try:
        query_vector = await _embed_one(_resolve_embedder(embedder), query)
        if query_vector is None:
            raise RuntimeError("embedder unavailable")
        # 向量 top-M 初值 = 召回预算 N（改动须同步 README）
        sims, vector_rows = await _vector_top_m(
            session, tenant_id, user_id, query_vector, m=limit, now=now
        )
    except Exception:
        # 向量通路任何失败（embedder/列不存在/查询错误）→ 回退 P0 确定性召回
        logger.warning(
            "memory_vector_degraded: vector recall failed; fallback to deterministic",
            exc_info=True,
        )
        update_current_span_metadata({"memory_vector_degraded": True})
        return deterministic
    return _fuse_recall(deterministic, sims, vector_rows, limit=limit, now=now)


async def recall_with_vector(
    tenant_id: str,
    user_id: str,
    query: str,
    *,
    limit: int = 8,
    now: datetime | None = None,
    session: AsyncSession | None = None,
    embedder: Embedder | None = None,
) -> list[OpsMemoryFact]:
    """混合召回（V1）：确定性 top-N ∪ 向量 top-M → 融合排序 → 预算截断。

    向量通路失败 → 回退 `recall_active` 确定性结果 + span/log
    `memory_vector_degraded`，不拖垮请求；tenant 谓词同 P0 纪律。
    """
    now = now or now_utc()
    if session is not None:
        return await _recall_with_vector_in_session(
            session, tenant_id, user_id, query, limit=limit, now=now, embedder=embedder
        )
    async with AsyncSessionLocal() as own:
        return await _recall_with_vector_in_session(
            own, tenant_id, user_id, query, limit=limit, now=now, embedder=embedder
        )
