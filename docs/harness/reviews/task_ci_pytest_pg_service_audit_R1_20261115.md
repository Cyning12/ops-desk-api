# R1 审查 · ci-pytest-pg-service（2026-11-15）

## 结论

GO（轻量 CI 基础设施卡 · 风险面收敛）。

## 核查项

1. **机制链闭合**：conftest.py:120 读 OPS_TEST_DATABASE_URL（默认 :76 localhost）→ :123 admin_dsn=settings.database_url 去尾段+/postgres → :133 CREATE DATABASE（镜像 superuser ops 有 CREATEDB 权限）→ 迁移 20260715_init_ops_desk.py:23-24 CREATE EXTENSION IF NOT EXISTS（superuser 可执行）。CI 提供 service 后全链无需代码改动。
2. **镜像选型**：pgvector/pgvector:pg16 自带 vector 扩展；uuid-ossp 属 postgresql-contrib 已内置。与本地 brew postgresql@18 大版本差（16 vs 18）：迁移与用例均未用 17/18 特性（既有 SQL 均为标准语法），风险可接受；如 CI 暴露版本差异再对齐。
3. **断言安全**：_assert_test_database（conftest.py:90-106）要求库名 _test 结尾——本卡 env 库名 opsdesk_test 合规；不放宽该断言（红线）。
4. **时长预算**：service 拉起+健康检查约 30-60s，验收上限 +2min 可达。
5. **不外指**：service 为 job 级临时容器，runner  localhost 网络，无外部依赖。

## 风险登记

- R-1：pg16 与本地 pg18 行为差（低概率）→ 暴露后钉版本对齐卡。
- R-2：既有「2 skipped」非 DB 类用例应保持原样跳过，验收需逐个核名。
