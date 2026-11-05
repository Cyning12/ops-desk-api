# Invoke · 20 帽 · task 审查 R1（fix-seen-surface-idempotency）

| 字段 | 值 |
|------|-----|
| hat_id | `20`（task-audit · 书面审 · 人审转录棒） |
| task_slug | `fix-seen-surface-idempotency` |
| task_paths | `docs/tasks/active/task_fix_seen_surface_idempotency.md` |
| related_review_or_none | `docs/harness/reviews/task_fix_seen_surface_idempotency_audit_R1_20261106.md`（lead 人审原文转录 · source = PR #345 review `5792245814`） |
| git_branch | `fix/seen-surface-idempotency`（30 分支承袭 · 本 invoke 随 30 分支出货） |
| created_utc_or_local | 2026-11-06 |
| notes | 本棒**非自签**——task 档审查内容与四闸签认均为 lead（Cyning12）GitHub PR #345 review `5792245814` APPROVED 原文；签认依据链 = issue #335 comment `6668554143`（立项令）→ PR #345 review `5792245814`（四闸签认 + 决策点②签认）→ issue #335 comment `6669768156`（四闸签认 + 30 授权六交付条件 + 决策点①委派工人探针裁决）；授权边界：审查棒零码改动 · 窗口授权（2026-11-05 22:26 → 2026-11-06 07:00） |

---

## §1 · 审查摘要

- **审查对象**：task_fix_seen_surface_idempotency.md（10 起草壳 · PR #345 · 零 `app/` diff · squash `ec87535`）
- **核对结论**：§2 四项全 PASS（lead 原文转录）——实扫声明诚实（grep 零命中机制命名 · 承载面留 30 探针 · 承锚点留痕纪律）、红线逐字入 FP（含 FP-6 防幂等键削单条件）、红测负样本形态（真派发路径 + 常规对拍零漂移）、四闸签认（HG-TASK-DRAFT / HG-WRITE-TICKET-IDEMPOTENCY-DESIGN 双决策点照留 / HG-AUDIT-R1 / HG-GRAPH-MODULES）
- **裁决落档**：审查文 `docs/harness/reviews/task_fix_seen_surface_idempotency_audit_R1_20261106.md` §3；task 档闸表四行 approved（代录依据 review `5792245814` + #6669768156）；决策点①（修复落点）经 #6669768156 明示**委派 30 工人红测探针实证后裁决**——30 裁决 = 案 A ∪ 案 B 同链双点半卫（task 档 30 注留痕）

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_seen_surface_idempotency.md` | 0 | LINT: PASS（四闸 approved 代录后复检） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_seen_surface_idempotency.md` | 0 | VERIFY: PASS（四闸 approved · 20 invoke 随 30 棒补齐后复检） |

## §3 · 下一棒

`30` 已交付（issue #335 #6669768156 · 分支 `fix/seen-surface-idempotency` · 六条件对照见 30 invoke）→ 出货 PR 待 lead 终审 → 40 复跑照旧 → CLOSE

---

### 修订

| 日期 | 说明 |
|------|-----|
| 2026-11-06 | 20-R1 审查棒 invoke 落档（lead 人审转录 · 非自签 · 随 30 分支出货） |
