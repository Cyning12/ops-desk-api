# invoke_20261116_10_draft · p3-t6-idempotency-db-default

## 内容
- task 档：docs/tasks/active/task_p3_t6_idempotency_db_default.md（人工闸三行
  approved · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03498/m03551
  · 范围 6 条 · 验收 11 条带锚 · 思考轮 R0-R5 · 偏差 D1 · 风险登记 R-P3-10 ·
  限制 L1/L2）
- R1 审查文：docs/harness/reviews/task_p3_t6_idempotency_db_default_audit_R1_20261116.md
  （六审查项全 GO · 结论 GO 准入 30）
- registry entry：p3-t6-idempotency-db-default（status: active · base 87fd1ddf ·
  allowed_app_files 三件 · allowed_tree_files 十件 · banned_prefixes=[alembic/, scripts/]）

## 验证台账
- task lint：PASS（frontmatter / 人工闸表 / 验收锚点齐全）
- spec-wave verify：PASS（npx spec-wave verify --target . --task docs/tasks/active/task_p3_t6_idempotency_db_default.md）
- registry yaml safe_load：PASS（entry 结构对齐既有波次字段）

## 偏差
- D1：契约 15 §7.3/§7.5 与 14 终稿 §0/§6.4/§10 口径矛盾——照 14 终稿 + 委派书
  翻转，契约 15 不改（跨仓非本波 allowed_tree），矛盾登记待 lead/00 跨仓和解。

## 结果
进 30。
