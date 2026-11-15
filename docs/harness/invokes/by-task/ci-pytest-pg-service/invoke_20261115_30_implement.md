# invoke_20261115_30_implement

## 内容

实施两件：① pytest.yml 挂 pgvector/pgvector:pg16 service（健康检查 pg_isready · 端口 5432）+ env DATABASE_URL/OPS_TEST_DATABASE_URL 指向 opsdesk_test；② conftest.py:12-16 注释同步（skip 假绿口径已消）。

## 结果

- python yaml 解析通过，services.postgres 就位。
- 零 app/alembic/tests 逻辑改动（conftest 仅注释块替换）。

## 偏差记录

无。
