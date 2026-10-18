"""Pytest fixtures.

Database isolation: integration tests run against a dedicated ``opsdesk_test``
database so destructive fixtures (e.g. ``clean_sync_data``) can never wipe the
development database that holds real imported data. The test database is
created on demand and its schema is managed via ``Base.metadata.create_all``.

**这条隔离保证由 ``_assert_test_database`` 强制执行**：目标库名必须以 ``_test`` 结尾，
否则 conftest 在 import 期直接抛错。需要换库（CI / 多实例）请设
``OPS_TEST_DATABASE_URL``——**不要复用业务的 ``DATABASE_URL``**，.env 里那个指向开发库。

⚠️ 已知缺口（test-baseline-reds F4 · 只注记不修，另 task 议）：CI pytest workflow
（.github/workflows/pytest.yml）的 DATABASE_URL 指向 localhost:5432 但 job **无 postgres
service** → 本文件 ``_setup_test_database`` 连不上 → DB_AVAILABLE=False → 全部 DB 用例
skip。即「CI 绿」对 DB 用例是 **skip 绿**（假绿），不构成真跑证据；真跑基线以本地真 PG
（opsdesk_test）为准。修 CI（加 postgres service）不在本 task 范围。
"""

from __future__ import annotations

import asyncio
import os
import random
import re
import sys
from datetime import datetime, timedelta

# 先于 import app.config（其 load_dotenv）关掉 tracing，避免本机 .env 的 keys 在 pytest 里误上报
os.environ.setdefault("OPS_CHAT_TRACER", "")


def _sanitize_no_proxy_env() -> None:
    """剔除 no_proxy/NO_PROXY 中 bracketed IPv6 条目（如 [::1]）。

    test-baseline-reds D1-L2：macOS 宿主常见
    NO_PROXY=localhost,127.0.0.1,::1,[::1]，而 httpx(trust_env=True) 建
    Client 时把 [::1] 当 URL 解析，直接抛 InvalidURL: Invalid port: ':1]'
    ——embedder/reranker 的 httpx 调用在宿主 env 下必炸（CI runner 无此 env）。
    裸 ::1 httpx 可解析，保留；只删 [...] 形式。须在 import app 之前生效。
    注记：本净化只影响 loopback 旁路列表语义，不删代理本体；integration marker
    真连用例若依赖 bracketed IPv6 no_proxy 条目（未见）须显式自理。
    """
    for key in ("no_proxy", "NO_PROXY"):
        raw = os.environ.get(key)
        if not raw:
            continue
        kept = [
            token
            for token in (t.strip() for t in raw.split(","))
            if token and not (token.startswith("[") and token.endswith("]"))
        ]
        if kept:
            os.environ[key] = ",".join(kept)
        else:
            os.environ.pop(key, None)


_sanitize_no_proxy_env()

# 本地/CI 精简 langchain 元包可能缺 langchain.debug，某些三方路径读它会 AttributeError。
# 用官方 set_debug() 预热：它内部会 catch_warnings 抑制掉
# "Importing debug from langchain root module is no longer supported" 这条告警——
# 直接 hasattr(_langchain, "debug") / 赋值会**触发**它（走的是 langchain.__getattr__）。
# ⚠️ 刻意从 ``langchain_core`` 取，不再从 ``langchain`` 伞包取：
#   langchain 0.2.x 写死了 ``langchain-core>=0.2.43,<0.3.0``，与 langgraph 1.x
#   要求的 ``langchain-core>=1.4.7`` **直接冲突**。而这里唯一要的就是
#   langchain_core.globals 里那个 debug 开关，伞包不是必需品
#   （LangGraph 1.0 也明确不再依赖 langchain 包）。
try:
    from langchain_core.globals import set_debug
except ImportError:
    pass
else:
    set_debug(False)

_TEST_DB_URL = "postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test"

# 换测试库**只能**用这个变量（CI / 本机多实例）。
# 刻意不复用业务的 DATABASE_URL：.env 里那个指向**开发库**，而 clean_sync_data 会 delete 全表。
TEST_DATABASE_URL_KEY = "OPS_TEST_DATABASE_URL"

_TEST_DB_SUFFIX = "_test"
_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")

# PG 连不上时的真实原因。以前静默返回 False → 所有 DB 测试悄悄 SKIP，
# 和"测试都过了"长得一模一样；至少要把原因喊出来。
_DB_UNAVAILABLE_REASON: list[str] = []


def _assert_test_database(url: str) -> tuple[str, str]:
    """校验目标库是测试库，返回 ``(url, db_name)``。

    不是测试库就**直接抛**，不静默、不退化。理由：``clean_sync_data`` 会
    ``delete(OpsRepo)``，而 ops_issues / ops_pull_requests / ops_scan_snapshots /
    ops_sync_runs / ops_graph_snapshots 五张表都是 ON DELETE CASCADE——
    指向开发库就是在删真实导入数据。
    """
    name = url.rsplit("/", 1)[-1].split("?")[0]
    if not _DB_NAME_RE.match(name) or not name.endswith(_TEST_DB_SUFFIX):
        raise RuntimeError(
            f"pytest 目标库名必须是合法标识符且以 '{_TEST_DB_SUFFIX}' 结尾，当前是 {name!r}。\n"
            f"  原因：clean_sync_data 等 fixture 会 delete(OpsRepo) 并级联删掉 "
            f"issues / PRs / snapshots——指向开发库就是在删真实导入数据。\n"
            f"  要换库：{TEST_DATABASE_URL_KEY}=postgresql+asyncpg://user:pw@host:5432/<名字>_test"
        )
    return url, name


def _setup_test_database() -> bool:
    """Point DATABASE_URL at the test DB if PostgreSQL is reachable.

    Must run before app modules are imported (the engine is created at import
    time). Returns whether PostgreSQL is available.
    """
    import asyncpg  # noqa: PLC0415

    from app.config import settings  # noqa: PLC0415

    # 先校验再连：目标库不对就该立刻炸，而不是"连上了再说"
    target, db_name = _assert_test_database(os.environ.get(TEST_DATABASE_URL_KEY, _TEST_DB_URL))

    async def _prepare() -> bool:
        admin_dsn = settings.database_url.replace("+asyncpg", "").rsplit("/", 1)[0] + "/postgres"
        try:
            conn = await asyncpg.connect(admin_dsn)
        except (OSError, asyncpg.PostgresError) as exc:
            _DB_UNAVAILABLE_REASON.append(f"{type(exc).__name__}: {exc}")
            return False
        try:
            exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
            if not exists:
                # CREATE DATABASE 不接受绑定参数；db_name 已由 _DB_NAME_RE 校验
                await conn.execute(f'CREATE DATABASE "{db_name}"')
        finally:
            await conn.close()
        return True

    available = asyncio.run(_prepare())
    if available:
        # settings is already instantiated by the import above; mutate it so
        # the engine (created on app.db.session import) targets the test DB.
        # 同时写回 os.environ，保证 conftest 之后才 import 的东西看到同一个库。
        os.environ["DATABASE_URL"] = target
        settings.database_url = target
    return available


DB_AVAILABLE = _setup_test_database()

if not DB_AVAILABLE:
    # 跳过 ≠ 通过：凭据改了而 conftest 没跟上时，这里以前完全无声。
    print(
        "[conftest] PostgreSQL 不可用，DB 相关用例将被**跳过**（不是通过）。原因："
        + ("; ".join(_DB_UNAVAILABLE_REASON) or "（无：可能是超时或没走到连接）"),
        file=sys.stderr,
    )

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.models import OpsInviteToken, OpsRepo, OpsSession, OpsSessionChat, OpsUser  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.ops.deps import get_current_user  # noqa: E402
from app.ops.security import generate_invite_token, hash_token  # noqa: E402


def _random_username() -> str:
    """Return a unique username for this test run."""
    import uuid

    return f"tester-{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP test client."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True, scope="session")
async def _create_test_schema():
    """Create all tables in the test database once per session."""
    if DB_AVAILABLE:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # create_all 不改已有列类型；本地 opsdesk_test 可能仍是 Integer
            await conn.execute(
                text("ALTER TABLE ops_issues ALTER COLUMN github_issue_id TYPE BIGINT")
            )
            await conn.execute(
                text("ALTER TABLE ops_pull_requests ALTER COLUMN github_pr_id TYPE BIGINT")
            )
            await conn.execute(
                text("ALTER TABLE ops_repos ALTER COLUMN github_repo_id TYPE BIGINT")
            )
            # memory-facts-p1：存量 opsdesk_test 的 ops_memory_facts 无 embedding 列，
            # create_all 不管 ALTER；ORM INSERT 会带该列（deferred 只影响 SELECT），
            # 缺列会让 P0 写入路径在测试库炸掉
            await conn.execute(
                text("ALTER TABLE ops_memory_facts ADD COLUMN IF NOT EXISTS embedding vector(1024)")
            )
            # memory-preference-profile：存量测试库 CHECK 仍是 kind='fact'，
            # create_all 不改既有约束；对齐 models.py 放宽（同 D5 迁移语义）
            await conn.execute(
                text(
                    "ALTER TABLE ops_memory_facts "
                    "DROP CONSTRAINT IF EXISTS ck_ops_memory_facts_kind"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE ops_memory_facts "
                    "ADD CONSTRAINT ck_ops_memory_facts_kind "
                    "CHECK (kind IN ('fact', 'preference'))"
                )
            )
            # test-baseline-reds D1-L3（schema 漂移补丁）：ops_knowledge_chunks 由
            # alembic/versions/20260808_rag_chunks.py 裸 SQL 建，无 ORM 模型 →
            # Base.metadata.create_all 不含此表 → retrieve 混合召回 SQL 炸
            # UndefinedTableError。与上面 ALTER 补丁同模式：幂等 IF NOT EXISTS，
            # 列定义逐字对齐该 migration（含 CREATE EXTENSION vector）；后续迁移
            # 未给本表加列（sparse_embedding 仅出现在 RAG_SECOND_PATH=sparse
            # 实验 SQL 路径，非默认召回路径，本补丁不补）。
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS ops_knowledge_chunks (
                        id           bigserial PRIMARY KEY,
                        repo         text        NOT NULL,
                        source_type  text        NOT NULL,
                        source_id    text        NOT NULL,
                        chunk_index  integer     NOT NULL,
                        content      text        NOT NULL,
                        metadata     jsonb       NOT NULL DEFAULT '{}'::jsonb,
                        images       jsonb       NOT NULL DEFAULT '[]'::jsonb,
                        content_hash text        NOT NULL,
                        embedding    vector(1024) NOT NULL,
                        embedded_at  timestamptz NOT NULL DEFAULT now(),
                        fts_tokens   tsvector
                            GENERATED ALWAYS AS (to_tsvector('simple'::regconfig, content)) STORED,
                        CONSTRAINT uq_ops_knowledge_chunks_key
                            UNIQUE (repo, source_type, source_id, chunk_index)
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_source "
                    "ON ops_knowledge_chunks (repo, source_type, source_id)"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_embedding_hnsw "
                    "ON ops_knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_fts_gin "
                    "ON ops_knowledge_chunks USING gin (fts_tokens)"
                )
            )
        await engine.dispose()
    yield


@pytest.fixture(autouse=True)
async def _reset_engine():
    """Dispose the async engine before each test to avoid cross-event-loop connection reuse."""
    await engine.dispose()
    yield


@pytest.fixture(autouse=True)
def _reset_capability_budget():
    """每个用例前清零 capability 的会话配额计数。

    配额是**进程内全局状态**（和注册表、metrics 同源），不清就会跨用例累积；
    而不带 ctx 的调用全部落进匿名桶 ``""``，跑满 64 次之后后面每个用例都被
    ``policy_blocked: budget_exhausted`` 拦下——症状长得像功能坏了，实际是状态泄漏。
    """
    from app.ops.capability import fallback
    from app.ops.capability.budget import reset as budget_reset
    from app.ops.capability.circuit import reset as circuit_reset

    budget_reset()
    circuit_reset()
    # 降级缓存也是进程内全局状态（按 (能力,租户,参数) 分桶、有界），
    # 不清会让上一个用例的成功结果被下一个用例的 cache 降级命中——
    # 症状是"降级莫名其妙成功了"，实际是串了数据。
    fallback.reset()
    yield
    budget_reset()
    circuit_reset()


@pytest.fixture(autouse=True)
def _reset_llm_circuit():
    """每个用例前清空 LLM provider 熔断器（llm-layer-hardening 清单 #10）。

    provider 级 breaker 是**进程内单例**（与 capability 配额/熔断同源），
    上一用例 trip 的 breaker 会污染下一用例——症状是「莫名 circuit_open」，
    实际是状态泄漏。对齐上面 _reset_capability_budget 的先例。
    """
    from app.llm import circuit as llm_circuit
    from app.llm import usage as llm_usage

    llm_circuit.reset()
    llm_usage.reset_persist_failure_count()
    yield
    llm_circuit.reset()


@pytest.fixture
async def clean_sync_data():
    """Remove all synced repos and cascading children before a test.

    Safe to delete broadly **only because** ``_assert_test_database`` 保证目标库名以
    ``_test`` 结尾（连带级联删除 issues / PRs / snapshots 也只发生在测试库）。
    谁要是把这道闸拆了，这个 fixture 就变成"删光开发库导入数据"的按钮。
    """
    from sqlalchemy import delete

    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo))
        await db.commit()
    yield
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo))
        await db.commit()


@pytest.fixture
async def seeded_maintainer():
    """Create a maintainer user with an unused invite token and a plaintext token."""
    plaintext_invite = generate_invite_token()
    username = _random_username()
    async with AsyncSessionLocal() as db:
        user = OpsUser(username=username, role="maintainer")
        db.add(user)
        await db.flush()

        invite = OpsInviteToken(
            token=hash_token(plaintext_invite),
            role="maintainer",
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        db.add(invite)
        await db.commit()

        yield {
            "user": user,
            "plaintext_invite": plaintext_invite,
        }

        # Cleanup
        async with AsyncSessionLocal() as cleanup_db:
            from sqlalchemy import delete

            await cleanup_db.execute(delete(OpsSession).where(OpsSession.user_id == user.id))
            await cleanup_db.execute(
                delete(OpsInviteToken).where(OpsInviteToken.token == hash_token(plaintext_invite))
            )
            await cleanup_db.execute(
                delete(OpsSessionChat).where(OpsSessionChat.user_id == user.id)
            )
            await cleanup_db.execute(delete(OpsUser).where(OpsUser.id == user.id))
            await cleanup_db.commit()


@pytest.fixture
def override_auth_maintainer():
    """Override auth dependency with a test maintainer."""
    from functools import wraps

    from app.db.models import OpsUser

    test_user = OpsUser(
        id="00000000-0000-0000-0000-000000000001",
        username="admin",
        role="maintainer",
    )

    @wraps(get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def override_auth_viewer():
    """Override auth dependency with a test viewer."""
    from functools import wraps

    from app.db.models import OpsUser

    test_user = OpsUser(
        id="00000000-0000-0000-0000-000000000002",
        username="viewer",
        role="viewer",
    )

    @wraps(get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def sample_sync_payload():
    """Return a deterministic sample sync payload dict."""
    import uuid

    suffix = uuid.uuid4().hex[:8]
    github_repo_id = random.randint(1, 2_147_483_647)
    return {
        "repo": {
            "owner": "acme",
            "name": f"ios-smoke-{suffix}",
            "full_name": f"acme/ios-smoke-{suffix}",
            "github_repo_id": github_repo_id,
            "default_branch": "main",
        },
        "issues": [
            {
                "number": 1,
                "title": "登录页面闪退",
                "state": "open",
                "labels": ["bug", "ios"],
                "module_tag": "auth",
                "author": "dev-a",
                "html_url": "https://github.com/acme/ios-smoke/issues/1",
                "created_at": "2026-07-17T09:00:00Z",
                "updated_at": "2026-07-17T09:00:00Z",
            }
        ],
        "pull_requests": [
            {
                "number": 2,
                "title": "Fix login crash",
                "state": "open",
                "draft": False,
                "ci_status": "success",
                "author": "dev-b",
                "html_url": "https://github.com/acme/ios-smoke/pull/2",
                "created_at": "2026-07-17T09:30:00Z",
                "updated_at": "2026-07-17T09:30:00Z",
            }
        ],
        "sync_run": {
            "sync_type": "full",
            "status": "completed",
            "started_at": "2026-07-17T10:00:00Z",
            "finished_at": "2026-07-17T10:01:00Z",
            "summary": {"issues": 1, "pulls": 1},
        },
        "scan_snapshot": {
            "parsed_summary": {"modules": ["auth"]},
            "raw_markdown": "# Scan summary",
        },
        "graph_snapshot": {
            "payload": {"nodes": [], "edges": []},
            "module_matrix": {"auth": [1]},
        },
    }
