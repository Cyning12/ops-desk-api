-- 影子库初始化：zhparser + chinese 文本检索配置（A 臂）
-- 用法：psql "$SHADOW_DSN" -f init_chinese_fts.sql

CREATE EXTENSION IF NOT EXISTS zhparser;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);
ALTER TEXT SEARCH CONFIGURATION chinese
  ADD MAPPING FOR n, v, a, i, e, l, j WITH simple;

-- 分词探针（验收）：
-- SELECT to_tsvector('chinese', 'Kimi Code 自动压缩被取消');
-- 期望：中文已拆开（如 '自动' '压缩' '取消'）+ 英文按词
