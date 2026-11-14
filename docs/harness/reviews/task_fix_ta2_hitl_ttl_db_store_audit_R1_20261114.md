# R1 设计审查 · fix-ta2-hitl-ttl-db-store

- 结论：GO。根因实证闭环（时区口径），修复面=单行 SQL 口径 + 注释，app 零改动。
- 裁定 ①：修测试不修生产——naive-UTC 是全仓列约定（T6 同口径），生产链路（写入 now_utc / 读取 _decided_at_ts UTC 解释）自洽，错的是测试 SQL 用了 server-TZ now()。
- 裁定 ②：不趁机做 tz-aware 列改造（超范围 · 需全仓迁移评审）。
- 风险：CI 无 PG 该用例 skip，本地真 PG 为唯一验证面——验收以本地真 PG 全绿为准。
