# Invoke · 20 帽 · task 审查 R1（cosign-gate-semantics）

| 字段 | 值 |
|------|-----|
| hat_id | `20`（task-audit · 书面审 · 人审转录棒） |
| task_slug | `cosign-gate-semantics` |
| task_paths | `docs/tasks/active/task_cosign_gate_semantics.md` |
| related_review_or_none | `docs/harness/reviews/task_cosign_gate_semantics_audit_R1_20261106.md`（lead 人审原文转录 · source = PR #351 review `5795679444`） |
| git_branch | `fix/cosign-gate-semantics`（30 分支 · 本 invoke 随 30 PR 出货） |
| created_utc_or_local | 2026-11-06 |
| notes | 本棒**非自签**——task 档审查内容与四闸签认均为 lead（Cyning12）GitHub PR #351 review `5795679444` APPROVED 原文；签认依据链 = issue #333 comment `6676316476`（立项令五要求）→ PR #351 review `5795679444`（四闸签认 + 设计闸裁决）→ issue #333 comment `6676780590`（四闸签认留痕 + 30 授权六交付条件）；授权链 = 2026-11-06 08:48 维护者授权 + 12:17『验收333』指示 |

---

## §1 · 审查摘要

- **审查对象**：task_cosign_gate_semantics.md（10 起草 + 四闸签认代录 · PR #351 · `70cb1a0` + `f72ab1d` · 零 `app/` diff）
- **核对结论**：§2 审查文五项全 PASS（lead 原文转录）——题面精确化 / 三案分析各自带滑点 / 0c88ac32 仓外承载面如实登记 / test_strategy 承度 / 四闸签认
- **裁决落档**：审查文 §3 = **案①幂等为主干**（幂等锚五元组 · 同锚重送达同效力不重复记录 · replay 附注）+ 覆盖不设默认（append-only · 同锚+显式替换意图追加新行 · 旧行保留引注）+ 拒重复不设（补发合法通路）+ **落点 = gate 记录层**（消费门内 = 仓外运行时面随 residual_risk 登记）；task 档闸表四行 approved（代录依据 review `5795679444` + #6676780590）

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_cosign_gate_semantics.md` | 0 | LINT: PASS（四闸 approved 代录后） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS（scope all · missing 0 · issues 0） |
| `npx --yes spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_cosign_gate_semantics.md` | 0 | VERIFY: PASS（四闸 approved · R1 审查文 + 20 invoke 随 30 棒补齐后复检） |

## §3 · 下一棒

`30`（#6676780590 六条件 · 分支 `fix/cosign-gate-semantics`）→ 出货 PR 待 lead 终审 → 40 复跑（独立复跑不采信 30 自报）→ CLOSE

---

### 修订

| 日期 | 说明 |
|------|-----|
| 2026-11-06 | 20-R1 审查棒 invoke 落档（lead 人审转录 · 非自签 · 随 30 PR 出货） |
