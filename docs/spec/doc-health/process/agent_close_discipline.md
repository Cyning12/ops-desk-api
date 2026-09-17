# process · Agent CLOSE 纪律（ops-desk-api · W0 可执行副本）

> **状态**：对齐 kit **1.7.1**（1.7.0 CLOSE 闸 + Hub / PR）  
> **契约真值**：`dsh-coding-kit/docs/spec/doc-health/process/agent_close_discipline.md`  
> **本文件**：供 Open Folder=本仓 时直接执行；若与 kit 冲突，以 kit 为准并开 FEEDBACK。  
> **本仓 Hub**：`docs/tasks/done/README.md`（已启用 → Hub 行必做）

---

## 1. 一句话纪律

验收绿了只叫 **复检通过**；只有做完「合入证据（或豁免）+ `task close --yes` + **Hub 追加行**」才准写 **CLOSE 完成 / CLOSE: PASS**。

无 `--yes` 的预检只能写 **`CLOSE: READY`（dry-run）**，禁止把 READY 写成 PASS。

---

## 2. 00 / CLOSE 棒清单（本仓）

1. task 状态 `done` / `completed`；验收勾选与自检已回填。  
2. 有代码变更：关联 PR **MERGED**（或 `close_pr_policy=exempt` + `close_pr_exempt_note`，或 `--allow-no-pr-merge`）。可用 `gh pr view` 看当前分支。  
3. 预检：`npx spec-wave task close --file <task>`（**不要** `--yes`）→ 摘要写 **`CLOSE: READY` / dry-run**，禁止写完成态 `CLOSE: PASS`。  
4. 执行：`npx spec-wave task close --file <task> --yes` → 成功才写 **`CLOSE: PASS`**。  
5. 确认已离开 `active/`，进入 `done/`（或域子目录）。  
6. **本仓必做**：`docs/tasks/done/README.md` 对应域表追加一行（`close_hub_index` 默认开；缺行则 BLOCK）；invoke `task_paths` 改为归档路径。  
7. 禁止「CLOSE: PASS 但暂留 active」而不留豁免/清理 task。

Hub 闸临时关闭：`.cyning-harness/local.json` 设 `close_hub_gate: false`，或单次 `--allow-no-hub`，并记 FEEDBACK。

---

## 3. 可复制片段

`````text
关账清单（ops-desk-api · W0 · kit 1.7.1）
- [ ] 复检绿 —— alone ≠ CLOSE 完成
- [ ] PR MERGED 或豁免理由已写（close_pr_merged）
- [ ] Hub docs/tasks/done/README.md 已追加行（close_hub_index）
- [ ] task close dry-run → CLOSE: READY（未写 PASS）
- [ ] task close --yes 已执行 → CLOSE: PASS
- [ ] active 已无该文件
- [ ] invoke task_paths 已改归档路径
`````

---

## 4. 验版摩擦 → FEEDBACK

升级/试用新版本 kit 时若 CLOSE/Hub/文案不符预期：写 [`../feedback/_TEMPLATE.md`](../feedback/_TEMPLATE.md) 复制为新文件，勿只留在对话里。

---

## 5. 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-08-26 | 自 kit 镜像落盘 · 绑定本仓 Hub |
| 2026-08-26 | 对齐 1.7.0+：dry-run=`READY`；`--yes`=`PASS`；Hub 必做；PR MERGED / 豁免 |
