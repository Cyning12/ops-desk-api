"""Pytest fixtures.

Database isolation: integration tests run against a dedicated ``opsdesk_test``
database so destructive fixtures (e.g. ``clean_sync_data``) can never wipe the
development database that holds real imported data. The test database is
created on demand and its schema is managed via ``Base.metadata.create_all``.

**这条隔离保证由 ``_assert_test_database`` 强制执行**：目标库名必须以 ``_test`` 结尾，
否则 conftest 在 import 期直接抛错。需要换库（CI / 多实例）请设
``OPS_TEST_DATABASE_URL``——**不要复用业务的 ``DATABASE_URL``**，.env 里那个指向开发库。
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

# 本地/CI 精简 langchain 元包可能缺 .debug；langchain_core.globals.get_debug 会 AttributeError
try:
    import langchain as _langchain

    if not hasattr(_langchain, "debug"):
        _langchain.debug = False
except ImportError:
    pass

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
        await engine.dispose()
    yield


@pytest.fixture(autouse=True)
async def _reset_engine():
    """Dispose the async engine before each test to avoid cross-event-loop connection reuse."""
    await engine.dispose()
    yield


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
