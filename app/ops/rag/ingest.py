"""R-2 入库管线核心（契约 Q1a/1b/1c/1d · R-2 D1-D5）。

流程：扫源 → content_hash 水位对比 → 变化集 clean/chunk/前缀/embed/整组替换
（D3）→ 全集对账删墓碑 → 计数报告。

同步实现（D5）：CLI 批处理无并发可榨，encode 是阻塞 CPU 调用，不进异步循环。
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import OpsIssue, OpsPullRequest, OpsRepo
from app.ops.rag.chunker import HARD_TOKEN_LIMIT, chunk_markdown, truncate_middle
from app.ops.rag.clean import clean_markdown
from app.ops.rag.embedder import Embedder
from app.ops.rag.prefix import build_prefix, embed_text
from app.ops.rag.tokenizer import TokenCounter

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1024  # 契约 Q3：bge-m3@1024；维度变更须重建表 + 全量重灌
DOCS_REPO = "ops-desk-workspace"


@dataclass
class SourceUnit:
    repo: str
    source_type: str  # issue | pr | doc
    source_id: str  # issue/pr = number 字符串；doc = 路径（契约 Q2）
    title: str
    body: str
    module_tag: str | None
    html_url: str | None
    updated_at: str
    content_hash: str


def _hash(title: str, body: str) -> str:
    return hashlib.sha1(f"{title}\n{body}".encode()).hexdigest()


def load_issue_units(
    session: Session, limit: int | None = None, source_id: str | None = None
) -> list[SourceUnit]:
    stmt = (
        select(OpsIssue, OpsRepo.full_name)
        .join(OpsRepo, OpsIssue.repo_id == OpsRepo.id)
        .order_by(OpsIssue.number)
    )
    if source_id:
        stmt = stmt.where(OpsIssue.number == int(source_id))
    if limit:
        stmt = stmt.limit(limit)
    return [
        SourceUnit(
            repo=repo_name,
            source_type="issue",
            source_id=str(issue.number),
            title=issue.title,
            body=issue.body or "",
            module_tag=issue.module_tag,
            html_url=issue.html_url,
            updated_at=issue.updated_at.isoformat() if issue.updated_at else "",
            content_hash=_hash(issue.title, issue.body or ""),
        )
        for issue, repo_name in session.execute(stmt)
    ]


def load_pull_units(
    session: Session, limit: int | None = None, source_id: str | None = None
) -> list[SourceUnit]:
    stmt = (
        select(OpsPullRequest, OpsRepo.full_name)
        .join(OpsRepo, OpsPullRequest.repo_id == OpsRepo.id)
        .order_by(OpsPullRequest.number)
    )
    if source_id:
        stmt = stmt.where(OpsPullRequest.number == int(source_id))
    if limit:
        stmt = stmt.limit(limit)
    return [
        SourceUnit(
            repo=repo_name,
            source_type="pr",
            source_id=str(pr.number),
            title=pr.title,
            body=pr.body or "",
            module_tag=getattr(pr, "module_tag", None),
            html_url=pr.html_url,
            updated_at=pr.updated_at.isoformat() if pr.updated_at else "",
            content_hash=_hash(pr.title, pr.body or ""),
        )
        for pr, repo_name in session.execute(stmt)
    ]


def load_doc_units(docs_roots: list[Path]) -> list[SourceUnit]:
    """source_id = 根目录名/相对路径（如 05-plan/04-agent-completion-roadmap_v1_zh.md）。"""
    units: list[SourceUnit] = []
    for root in docs_roots:
        for path in sorted(root.rglob("*.md")):
            body = path.read_text(encoding="utf-8")
            title = next(
                (line[2:].strip() for line in body.splitlines() if line.startswith("# ")),
                path.stem,
            )
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            units.append(
                SourceUnit(
                    repo=DOCS_REPO,
                    source_type="doc",
                    source_id=f"{root.name}/{path.relative_to(root)}",
                    title=title,
                    body=body,
                    module_tag=None,
                    html_url=None,
                    updated_at=mtime.isoformat(),
                    content_hash=_hash(title, body),
                )
            )
    return units


def _ref_of(unit: SourceUnit) -> str:
    if unit.source_type == "doc":
        return unit.source_id
    return f"{unit.repo}#{unit.source_id}"


def _existing_hashes(session: Session) -> dict[tuple[str, str, str], str]:
    rows = session.execute(
        text(
            "SELECT repo, source_type, source_id, content_hash "
            "FROM ops_knowledge_chunks "
            "GROUP BY repo, source_type, source_id, content_hash"
        )
    )
    return {(r.repo, r.source_type, r.source_id): r.content_hash for r in rows}


_DELETE_BY_KEY = text(
    "DELETE FROM ops_knowledge_chunks "
    "WHERE repo = :repo AND source_type = :stype AND source_id = :sid"
)

_INSERT_CHUNK = text(
    "INSERT INTO ops_knowledge_chunks "
    "(repo, source_type, source_id, chunk_index, content, metadata, images, content_hash, embedding) "
    "VALUES (:repo, :stype, :sid, :idx, :content, "
    "CAST(:meta AS jsonb), CAST(:images AS jsonb), :hash, CAST(:vec AS vector))"
)


def ingest(
    session: Session,
    embedder: Embedder,
    counter: TokenCounter,
    units: list[SourceUnit],
    dry_run: bool = False,
) -> dict:
    existing = _existing_hashes(session)
    seen = {(u.repo, u.source_type, u.source_id) for u in units}
    stale = [k for k in existing if k not in seen]
    changed = [u for u in units if existing.get((u.repo, u.source_type, u.source_id)) != u.content_hash]
    report = {
        "scanned": len(units),
        "to_upsert": len(changed),
        "unchanged": len(units) - len(changed),
        "to_delete": len(stale),
        "chunks_written": 0,
    }
    if dry_run:
        return report

    # 1) 变化集：清洗 → 切分 → 前缀注入（content 存注入后文本，展示时剥离，契约 §1b）
    pending: list[tuple[SourceUnit, int, str, list[dict]]] = []
    for u in changed:
        cleaned = clean_markdown(u.body)
        prefix = build_prefix(
            title=u.title, source_type=u.source_type,
            ref=_ref_of(u), module_tag=u.module_tag,
        )
        chunks = chunk_markdown(cleaned.text, counter)
        if not chunks and u.title.strip():
            # E7：空正文单元（全量实测 9/2748）→ 仅标题 chunk，保证可按标题检索到
            chunks = [u.title.strip()]
        for idx, chunk in enumerate(chunks):
            content = embed_text(prefix, chunk)
            if counter.count(content) > HARD_TOKEN_LIMIT:
                logger.warning(
                    "超模型硬顶 %s %s chunk %d，截中段", u.source_type, u.source_id, idx
                )
                content = truncate_middle(content, counter)
            media = [m for m in cleaned.media if m["anchor"] in chunk]
            pending.append((u, idx, content, media))

    # 2) 批量 embed + 维度断言（契约 Q3：不符即停，防混库）
    vectors = embedder.embed([p[2] for p in pending])
    for v in vectors:
        if len(v) != EMBEDDING_DIM:
            raise RuntimeError(
                f"embedding 维度 {len(v)} != {EMBEDDING_DIM}：换模型须重建表 + 全量重灌"
            )

    # 3) 整组替换（D3）：单元级删旧插新，逐单元提交（崩溃可续，水位跳过已写）
    by_key: dict[tuple[str, str, str], list[tuple[SourceUnit, int, str, list[dict], list[float]]]] = {}
    for (u, idx, content, media), vec in zip(pending, vectors, strict=True):
        by_key.setdefault((u.repo, u.source_type, u.source_id), []).append(
            (u, idx, content, media, vec)
        )
    for (repo, stype, sid), rows in by_key.items():
        session.execute(_DELETE_BY_KEY, {"repo": repo, "stype": stype, "sid": sid})
        for u, idx, content, media, vec in rows:
            session.execute(
                _INSERT_CHUNK,
                {
                    "repo": repo,
                    "stype": stype,
                    "sid": sid,
                    "idx": idx,
                    "content": content,
                    "meta": json.dumps(
                        {
                            "module_tag": u.module_tag,
                            "html_url": u.html_url,
                            "updated_at": u.updated_at,
                            "embedding_model": embedder.name,
                        }
                    ),
                    "images": json.dumps(media),
                    "hash": u.content_hash,
                    "vec": json.dumps(vec),
                },
            )
        session.commit()
        report["chunks_written"] += len(rows)
        logger.info("upsert %s %s：%d chunks", stype, sid, len(rows))

    # 4) 全集对账：源里消失的单元，chunk 表删除（墓碑清理）
    for repo, stype, sid in stale:
        session.execute(_DELETE_BY_KEY, {"repo": repo, "stype": stype, "sid": sid})
    if stale:
        session.commit()

    return report
