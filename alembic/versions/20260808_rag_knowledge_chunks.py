"""ops_knowledge_chunks: RAG 知识分块表(R-1 · 契约 rag-knowledge-contract-v1 §2a)

Revision ID: 20260808_rag_chunks
Revises: 20260724_pr_first_review_at
Create Date: 2026-08-08

- 组合键 (repo, source_type, source_id, chunk_index) · upsert 定位
- embedding vector(1024) · bge-m3 自部署(契约 Q3)
- HNSW(cosine)+ fts_tokens tsvector(触发器维护 · 含 alias 变体)
- 查询函数:ops_rag_match_chunks(语义)/ ops_rag_keyword_chunks(关键词)
  —— RRF 融合在应用层(R-3),对齐 Ink hybrid_search.sql 双路设计
- 易变字段(state/labels)不入本表,查询时 join ops_issues 活表(契约 Q2)
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260808_rag_chunks"
down_revision: Union[str, None] = "20260724_pr_first_review_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 幂等:init 迁移已建扩展,此处防御旧库
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # 1) 表
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_knowledge_chunks (
            id            BIGSERIAL PRIMARY KEY,
            repo          TEXT NOT NULL,
            source_type   TEXT NOT NULL CHECK (source_type IN ('issue', 'pr', 'doc')),
            source_id     TEXT NOT NULL,
            chunk_index   INTEGER NOT NULL,
            content       TEXT NOT NULL,
            images        JSONB NOT NULL DEFAULT '[]'::jsonb,
            content_hash  TEXT NOT NULL,
            embedding     vector(1024) NOT NULL,
            embedded_at   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ops_knowledge_chunks_key
        ON ops_knowledge_chunks (repo, source_type, source_id, chunk_index)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_source
        ON ops_knowledge_chunks (repo, source_type, source_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_embedding_hnsw
        ON ops_knowledge_chunks USING hnsw (embedding vector_cosine_ops)
        """
    )

    # 2) FTS 列 + GIN
    op.execute("ALTER TABLE ops_knowledge_chunks ADD COLUMN IF NOT EXISTS fts_tokens TSVECTOR")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_fts_gin
        ON ops_knowledge_chunks USING gin (fts_tokens)
        """
    )

    # 3) alias 文本(移植 Ink rag_fts_alias_text:日期/版本号/分隔符/CamelCase 变体)
    op.execute(
        r"""
        CREATE OR REPLACE FUNCTION ops_rag_fts_alias_text(input_text text)
        RETURNS text
        LANGUAGE plpgsql
        IMMUTABLE
        AS $$
        declare
          s text := coalesce(input_text, '');
          token text;
          m text[];
          y int;
          mo int;
          d int;
          mo2 text;
          d2 text;
          mo1 text;
          d1 text;
          out text := '';
          added int := 0;
          max_added int := 60;
        begin
          if length(s) > 200000 then
            s := left(s, 200000);
          end if;

          -- 日期:YYYY[-/.]M[-/.]D 全变体
          for m in
            select regexp_matches(s, '(\d{4})[./-](\d{1,2})[./-](\d{1,2})', 'g')
          loop
            y := m[1]::int;
            mo := greatest(1, least(12, m[2]::int));
            d := greatest(1, least(31, m[3]::int));
            mo2 := lpad(mo::text, 2, '0');
            d2 := lpad(d::text, 2, '0');
            mo1 := mo::text;
            d1 := d::text;
            out := out
              || ' ' || y::text || '-' || mo2 || '-' || d2
              || ' ' || y::text || '-' || mo1 || '-' || d1
              || ' ' || y::text || '/' || mo2 || '/' || d2
              || ' ' || y::text || '/' || mo1 || '/' || d1
              || ' ' || y::text || '.' || mo2 || '.' || d2
              || ' ' || y::text || '.' || mo1 || '.' || d1
              || ' ' || y::text || ' ' || mo2 || ' ' || d2
              || ' ' || y::text || ' ' || mo1 || ' ' || d1;
            added := added + 8;
            if added >= max_added then
              return btrim(out);
            end if;
          end loop;

          -- 版本号:v0.1.0 / 0.1.0 / 0-1-0 / 0_1_0
          for m in
            select regexp_matches(s, '\bv?(\d+)\.(\d+)(?:\.(\d+))?\b', 'g')
          loop
            out := out
              || ' ' || 'v' || m[1] || '.' || m[2] || '.' || coalesce(m[3], '0')
              || ' ' || m[1] || '.' || m[2] || '.' || coalesce(m[3], '0')
              || ' ' || m[1] || '-' || m[2] || '-' || coalesce(m[3], '0')
              || ' ' || m[1] || '_' || m[2] || '_' || coalesce(m[3], '0');
            added := added + 4;
            if added >= max_added then
              return btrim(out);
            end if;
          end loop;

          -- 分隔符归一:标识符/路径 token 拆分
          for token in
            select distinct t from regexp_split_to_table(s, '\s+') as t
            where length(t) between 3 and 64
              and t ~ '[_./\\-]'
              and t ~ '[A-Za-z0-9]'
            limit 40
          loop
            out := out || ' ' || regexp_replace(token, '[_./\\-]+', ' ', 'g');
            added := added + 1;
            if added >= max_added then
              return btrim(out);
            end if;
          end loop;

          -- CamelCase 拆分(轻量)
          for token in
            select distinct t from regexp_split_to_table(s, '\s+') as t
            where length(t) between 6 and 64
              and t ~ '^[A-Za-z][A-Za-z0-9]+$'
              and t ~ '[a-z]'
              and t ~ '[A-Z]'
            limit 40
          loop
            out := out || ' ' || regexp_replace(token, '([a-z0-9])([A-Z])', '\1 \2', 'g');
            added := added + 1;
            if added >= max_added then
              return btrim(out);
            end if;
          end loop;

          return btrim(out);
        end;
        $$;
        """
    )

    # 4) 触发器:content 写入/更新时自动维护 fts_tokens
    op.execute(
        """
        CREATE OR REPLACE FUNCTION ops_knowledge_chunks_fts_tokens_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        begin
          new.fts_tokens := to_tsvector(
            'simple',
            coalesce(new.content, '') || ' ' || coalesce(ops_rag_fts_alias_text(new.content), '')
          );
          return new;
        end;
        $$;
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_ops_knowledge_chunks_fts ON ops_knowledge_chunks")
    op.execute(
        """
        CREATE TRIGGER trg_ops_knowledge_chunks_fts
        BEFORE INSERT OR UPDATE OF content
        ON ops_knowledge_chunks
        FOR EACH ROW
        EXECUTE FUNCTION ops_knowledge_chunks_fts_tokens_update();
        """
    )

    # 5) 语义路:cosine top-k(threshold 为 null 不过滤;评级闸在应用层,契约 Q4)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION ops_rag_match_chunks(
          query_embedding vector(1024),
          match_count integer default 10,
          match_threshold double precision default null
        )
        RETURNS TABLE (
          id bigint,
          repo text,
          source_type text,
          source_id text,
          chunk_index integer,
          content text,
          images jsonb,
          similarity double precision
        )
        LANGUAGE sql
        STABLE
        PARALLEL SAFE
        AS $$
          select
            c.id, c.repo, c.source_type, c.source_id, c.chunk_index,
            c.content, c.images,
            (1 - (c.embedding <=> query_embedding))::double precision as similarity
          from ops_knowledge_chunks c
          where
            match_threshold is null
            or (1 - (c.embedding <=> query_embedding))::double precision > match_threshold
          order by c.embedding <=> query_embedding
          limit greatest(match_count, 1);
        $$;
        """
    )

    # 6) 关键词路:websearch_to_tsquery( Ink 同款,支持引号/减号语法)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION ops_rag_keyword_chunks(
          query_text text,
          match_count integer default 10
        )
        RETURNS TABLE (
          id bigint,
          repo text,
          source_type text,
          source_id text,
          chunk_index integer,
          content text,
          images jsonb,
          score double precision
        )
        LANGUAGE sql
        STABLE
        PARALLEL SAFE
        AS $$
          select
            c.id, c.repo, c.source_type, c.source_id, c.chunk_index,
            c.content, c.images,
            ts_rank_cd(c.fts_tokens, websearch_to_tsquery('simple', query_text))::double precision as score
          from ops_knowledge_chunks c
          where
            query_text is not null
            and btrim(query_text) <> ''
            and c.fts_tokens @@ websearch_to_tsquery('simple', query_text)
          order by score desc, c.id asc
          limit greatest(match_count, 1);
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS ops_rag_keyword_chunks(text, integer)")
    op.execute("DROP FUNCTION IF EXISTS ops_rag_match_chunks(vector, integer, double precision)")
    op.execute("DROP TRIGGER IF EXISTS trg_ops_knowledge_chunks_fts ON ops_knowledge_chunks")
    op.execute("DROP FUNCTION IF EXISTS ops_knowledge_chunks_fts_tokens_update()")
    op.execute("DROP FUNCTION IF EXISTS ops_rag_fts_alias_text(text)")
    op.execute("DROP TABLE IF EXISTS ops_knowledge_chunks")
