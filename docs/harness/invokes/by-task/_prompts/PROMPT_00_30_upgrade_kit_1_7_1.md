# 可复制 Prompt · ops-desk-api · 升级 dsh-coding-kit 1.7.1

> **给谁**：Open Folder = **ops-desk-api** 的 Agent（00 可兼 30；或 00 签闸后交 30）。  
> **task**：`docs/tasks/active/task_dsh_coding_kit_upgrade_1_7_1.md`  
> **本文件**：整段复制「复制区」作为该 Agent 第一条用户消息。  
> **取代**：`PROMPT_00_30_upgrade_kit_1_7_0.md`

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 仓 Agent（优先 00 统筹；闸通过后可同会话 30 执行）。目标：把本仓 dsh-coding-kit 从 1.6.1 升级到 1.7.1，并完成 doc-health 试点文档迁移与 CLOSE dogfood，以及确认 Starter 00-orchestrator.md 落地；不改 app/ 业务代码。

════════════════════════════════════
A. Open Folder / 必读
════════════════════════════════════

1) Open Folder = ops-desk-api 仓根。
2) 必读 task：docs/tasks/active/task_dsh_coding_kit_upgrade_1_7_1.md（范围 A 升级 + B 文档迁移；验收可勾选）。
3) 必读试点：docs/spec/doc-health/README.md · process/agent_close_discipline.md · feedback/。
4) 先例：docs/tasks/done/task_dsh_coding_kit_upgrade_1_6_1.md（升级序列 / local 块 / FEEDBACK 体例）。
5) 消费者提示（kit 1.7.0 + 1.7.1）：
   - task close 无 --yes → CLOSE: READY（不再 PASS）
   - --yes 成功 → CLOSE: PASS
   - 新闸 close_pr_merged（PR MERGED 或 exempt / --allow-no-pr-merge）
   - 新闸 close_hub_index（本仓已有 docs/tasks/done/README.md → 默认开；可 close_hub_gate:false / --allow-no-hub）
   - check 对 docs/spec 根级裸 SPEC-*.md 打 WARN（不挡；不要求本波搬迁）
   - 1.7.1：docs/harness/prompts/00-orchestrator.md 入 Starter（00 默认行为；不进默认 Skills）

════════════════════════════════════
B. 闸纪律
════════════════════════════════════

- 读 task 人工闸表。HG-TASK-DRAFT / HG-AUDIT-R1 若仍为 pending：
  - 若维护者本窗已授权「可签过程文档」→ 你可代签为 approved，并落盘轻量 R1 审查文到 docs/harness/reviews/；
  - 否则 STOP，只输出 gate_id + 路径，不改码。
- 30 前：npx dsh-coding-kit verify --task docs/tasks/active/task_dsh_coding_kit_upgrade_1_7_1.md（缺件按先例留痕豁免并写明）。

════════════════════════════════════
C. 执行步骤（按序）
════════════════════════════════════

1) 探查：npx --yes dsh-coding-kit@1.7.1 --help / check（可用 npm_config_cache=/tmp/npm-cache-lg）。
2) refresh-ide-blocks：先 --dry-run；需要时 --yes；确认 local 块保留。
3) upgrade --yes；确认 .cyning-harness/manifest.json version=1.7.1。
4) 确认 docs/harness/prompts/00-orchestrator.md 存在且含「默认行为」表。
5) 验证：verify（本 task）、./scripts/graph-compile.sh、pytest（无新增失败）。
6) 文档迁移：
   - 更新 docs/spec/doc-health/README.md（1.7.1 已发版 · SPEC 已签）。
   - 对齐 process/agent_close_discipline.md 与 READY/PASS / Hub / PR 口径。
   - 确认 docs/spec/README.md 历史债表仍在；记录 check 的裸 SPEC WARN 条数。
7) CLOSE dogfood：对本 task 跑 task close（不要 --yes）→ 截取 stdout 证明 CLOSE: READY；若 close_hub_index BLOCK → 先补 Hub 行或记 FEEDBACK。
8) 清理可安全修改的过程文档里「dry-run=CLOSE: PASS」或过时 @cyning/harness task close 完成态表述（勿批量改 done/ 历史）。
9) 有摩擦：docs/spec/doc-health/feedback/ 按 _TEMPLATE 落盘并更新 feedback/README 表。
10) 回填 task 自检 / 验收勾选；落盘 invoke（10 与 30/40）；开 PR；PR MERGED 后再 task close --yes + Hub 行（遵守 CLOSE DoD）。未授权则不要 push/publish。

════════════════════════════════════
D. 禁止
════════════════════════════════════

- 不改 app/
- 不搬迁 docs/spec 根级历史裸 SPEC（仅 WARN）
- 不 npm publish；不强制 gh pr merge（检查 MERGED 即可）
- 不把 dry-run READY 写成 CLOSE: PASS
- 不强制装 harness-00 Skill（仅 prompts）

════════════════════════════════════
E. 回报（≤15 行）
════════════════════════════════════

manifest 版本 · 00-orchestrator 有无 · local 块 · READY 实证一行 · WARN 条数 · FEEDBACK 路径或「无出入」· PR 链接 · 阻塞项。
`````

---

## 维护者备注（勿粘贴）

- task 闸默认 pending；本窗若授权代签，Agent 按复制区 B 节处理。  
- 关账须满足 1.7.0+：`CLOSE: PASS` 仅在 `--yes` 且 Hub/PR 条件满足后。  
- 试点 FEEDBACK 优先 `docs/spec/doc-health/feedback/`（与旧 `docs/harness/evidence/FEEDBACK_*` 并存；本波用新轨）。
