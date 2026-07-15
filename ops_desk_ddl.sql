-- Ops Desk Kimi Code v1 PostgreSQL DDL
-- PostgreSQL 15+ with pgvector extension

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================
-- 1. Auth
-- ============================================================

CREATE TABLE ops_users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        TEXT NOT NULL UNIQUE,
    role            TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('viewer', 'maintainer')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ops_invite_tokens (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token           TEXT NOT NULL UNIQUE,
    role            TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('viewer', 'maintainer')),
    used_by_user_id UUID REFERENCES ops_users(id) ON DELETE SET NULL,
    used_at         TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ops_invite_tokens_token ON ops_invite_tokens(token);

CREATE TABLE ops_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES ops_users(id) ON DELETE CASCADE,
    token_hash      TEXT NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ops_sessions_user_id ON ops_sessions(user_id);
CREATE INDEX idx_ops_sessions_token_hash ON ops_sessions(token_hash);

-- ============================================================
-- 2. Repositories
-- ============================================================

CREATE TABLE ops_repos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner           TEXT NOT NULL,
    name            TEXT NOT NULL,
    full_name       TEXT NOT NULL UNIQUE,
    default_branch  TEXT,
    description     TEXT,
    github_repo_id  BIGINT UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 3. Issues
-- ============================================================

CREATE TABLE ops_issues (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id         UUID NOT NULL REFERENCES ops_repos(id) ON DELETE CASCADE,
    github_issue_id BIGINT,
    number          INTEGER NOT NULL,
    title           TEXT NOT NULL,
    body            TEXT,
    state           TEXT NOT NULL DEFAULT 'open',
    labels          TEXT[] DEFAULT '{}',
    scan_status     TEXT,
    module_tag      TEXT,
    author          TEXT,
    assignees       TEXT[] DEFAULT '{}',
    html_url        TEXT,
    created_at      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL,
    closed_at       TIMESTAMPTZ,
    raw_payload     JSONB,
    UNIQUE(repo_id, number)
);

CREATE INDEX idx_ops_issues_repo_state_updated ON ops_issues(repo_id, state, updated_at DESC);
CREATE INDEX idx_ops_issues_labels ON ops_issues USING GIN(labels);
CREATE INDEX idx_ops_issues_module_tag ON ops_issues(module_tag);

-- ============================================================
-- 4. Pull Requests
-- ============================================================

CREATE TABLE ops_pull_requests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id         UUID NOT NULL REFERENCES ops_repos(id) ON DELETE CASCADE,
    github_pr_id    BIGINT,
    number          INTEGER NOT NULL,
    title           TEXT NOT NULL,
    body            TEXT,
    state           TEXT NOT NULL DEFAULT 'open',
    draft           BOOLEAN NOT NULL DEFAULT FALSE,
    ci_status       TEXT,
    author          TEXT,
    reviewers       TEXT[] DEFAULT '{}',
    html_url        TEXT,
    created_at      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL,
    merged_at       TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    raw_payload     JSONB,
    UNIQUE(repo_id, number)
);

CREATE INDEX idx_ops_pull_requests_repo_state_updated ON ops_pull_requests(repo_id, state, updated_at DESC);

-- ============================================================
-- 5. Sync Runs
-- ============================================================

CREATE TABLE ops_sync_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id         UUID NOT NULL REFERENCES ops_repos(id) ON DELETE CASCADE,
    sync_type       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'running',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    summary         JSONB,
    error_message   TEXT
);

CREATE INDEX idx_ops_sync_runs_repo_started ON ops_sync_runs(repo_id, started_at DESC);

-- ============================================================
-- 6. Scan Snapshots
-- ============================================================

CREATE TABLE ops_scan_snapshots (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id         UUID NOT NULL REFERENCES ops_repos(id) ON DELETE CASCADE,
    scan_run_id     UUID REFERENCES ops_sync_runs(id) ON DELETE SET NULL,
    parsed_summary  JSONB NOT NULL,
    raw_markdown    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ops_scan_snapshots_repo_created ON ops_scan_snapshots(repo_id, created_at DESC);

-- ============================================================
-- 7. Graph Snapshots
-- ============================================================

CREATE TABLE ops_graph_snapshots (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id         UUID NOT NULL REFERENCES ops_repos(id) ON DELETE CASCADE,
    graph_run_id    UUID REFERENCES ops_sync_runs(id) ON DELETE SET NULL,
    payload         JSONB NOT NULL,
    module_matrix   JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ops_graph_snapshots_repo_created ON ops_graph_snapshots(repo_id, created_at DESC);

-- ============================================================
-- 8. Chat Sessions
-- ============================================================

CREATE TABLE ops_sessions_chat (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES ops_users(id) ON DELETE CASCADE,
    title           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ops_sessions_chat_user_updated ON ops_sessions_chat(user_id, updated_at DESC);

-- ============================================================
-- 9. Chat Runs
-- ============================================================

CREATE TABLE ops_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES ops_sessions_chat(id) ON DELETE CASCADE,
    query           TEXT NOT NULL,
    intent          TEXT,
    status          TEXT NOT NULL DEFAULT 'running',
    model           TEXT,
    latency_ms      INTEGER,
    answer          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ops_runs_session_created ON ops_runs(session_id, created_at DESC);

-- ============================================================
-- 10. Run Events (SSE archive)
-- ============================================================

CREATE TABLE ops_run_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id          UUID NOT NULL REFERENCES ops_runs(id) ON DELETE CASCADE,
    seq             INTEGER NOT NULL,
    ts_ms           INTEGER NOT NULL,
    agent_role      TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(run_id, seq)
);

CREATE INDEX idx_ops_run_events_run_seq ON ops_run_events(run_id, seq);
CREATE INDEX idx_ops_run_events_run_type ON ops_run_events(run_id, event_type);
