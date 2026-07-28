# FEEDBACK · RUNBOOK 流程化 · overlay 升级序（from ops-desk-api · 2.22 dogfood）

> **日期**：2026-07-28  
> **对象**：产品仓 `cyning-harness` · 建议回填 `docs/RUNBOOK_upgrade_wiki_delta_v1_zh.md`（及 ide/adapters README 交叉链）  
> **来源**：ops-desk-api 升 2.22.0 验证 U2 部分根治时的**操作序**摩擦（非能力缺口）  
> **证据**：`FEEDBACK_harness_2_22_0_from_ops_desk_api_20260728.md` · PR https://github.com/Cyning12/ops-desk-api/pull/23  
> **severity**：无 block · 最高 **P2**（流程未写清 → Agent/人靠经验才绿）

---

## 1. 问题陈述

2.22 已提供 local 块 + `graph_modules_path` + overlay hint，**能力上**可零手恢复。  
但 RUNBOOK §1.2 目前是「做法表 + diff 命令」，**缺少强制操作序**：

| 缺口 | 后果（本波实踩） |
|------|------------------|
| 未写「先迁契约并 **commit**，再 upgrade」 | 脏树 → **S5 中止 apply**；易误判 upgrade 失败 |
| 未写「从 &lt;2.22 且有仓内定制」的迁移动作清单 | Agent 仍可能把词写在产品 marker 内 → 继续被冲 |
| §0b 快速路径未交叉链 overlay 迁 | 已迁完 wiki_delta 的仓升 2.22 时跳过 §1.2 → 漏迁 |
| 未写二次 upgrade / 负面边界抽检 | 「是否真零手恢复」靠经验口头验 |

目标：把本波成功路径写成 **可复制、可 CI 对照的 RUNBOOK 步骤**，不依赖 dogfood 记忆。

---

## 2. 建议 RUNBOOK 增补（草案 · 供产品采纳）

### 2.1 新增 §1.2.1 · 首次接入 overlay 契约（强制序）

适用于：manifest &lt; 2.22，或 ≥2.22 但仍把定制写在产品 `cyning-harness:begin/end` 内。

建议正文（产品可改写，语义勿丢）：

1. **迁 profile**（若需 G-L / 非默认模块页）  
   在 `.cyning-harness/profile.json` 与 `tracks` **同级**增加：  
   `"graph_modules_path": "l1/01_modules"`（路径按仓裁剪；默认可不写 = `01_struct`）。
2. **迁 AGENTS（及如有定制的 CLAUDE）**  
   - 产品块内：只保留产品 fragment 语义，**删除**仓特异词。  
   - 紧接产品 `end` **之后**增加：  
     `<!-- cyning-harness-local:begin -->` … 仓特异句 … `<!-- cyning-harness-local:end -->`  
   - **禁止**：local 嵌在产品 begin/end 内；禁止改 `.cursor/rules/05-harness-starter.mdc` 塞仓特异词（会被 cp）。
3. **提交契约（关键）**  
   `git add` profile + AGENTS（+ local 相关）→ `git commit`  
   工作区须对 sync 足够干净；否则下一步 upgrade 可能 **S5 拒 apply**。  
   紧急可用 `--force` / `HARNESS_SYNC_FORCE=1`，但默认路径应是先 commit，勿把 force 当常态。
4. **再钉版 upgrade**  
   `npx --yes @cyning/harness@<目标版> upgrade --yes`  
   `npx --yes @cyning/harness@<目标版> check`  
   注视 stdout：`overlay · FRAGMENT graph_modules_path → …` 与 `hint · overlay`。
5. **有 pin 则 bump**（upgrade 不代写）。
6. **验收（合规零手恢复）**  
   - `git diff HEAD -- AGENTS.md CLAUDE.md .cursor/rules/05-harness-starter.mdc docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`  
   - 期望：local 关键词仍在；FRAGMENT 含 profile 路径（非误回默认且丢定制）；**无需**从 backup 手贴。  
   - 建议再跑一次 `upgrade --yes`：第二次 overlay diff 宜空或仅产品合法更新。

### 2.2 修订 §0b 快速路径

在「已迁完 wiki_delta」快速路径中增加一行：

- 若目标 ≥ **2.22** 且仓内曾有 overlay 定制 → **先做 §1.2.1**（或确认已有 local 块 + 所需 `graph_modules_path`），再 upgrade。

### 2.3 修订 §1.2 表（补一行）

| 做法 | 说明 |
|------|------|
| **操作序** | **先迁并 commit 契约 → 再 upgrade**；脏树可能 S5；勿依赖「upgrade 后代手恢复」 |

### 2.4（可选）§1.2.2 负面边界

一句话即可：定制只写在产品 marker 内且无 local → upgrade **仍冲**（证明边界；勿当 bug）。

### 2.5 版本钉

RUNBOOK 内示例命令建议统一钉当前文档版（如 `@2.22.0`），避免与 §0b/`check` 漂移（延续 F-220-04）。

---

## 3. 建议交叉链

| 文档 | 动作 |
|------|------|
| `ide/adapters/README.md` | 在 local 块节 POINTER「首次迁入见 RUNBOOK §1.2.1」 |
| `ONBOARDING.md` | 升级 checklist 增加「overlay 契约已 commit」 |
| `CHANGELOG` 后续 patch | 若只改文档：注明「RUNBOOK 操作序 · ops dogfood」 |

---

## 4. 非目标

- 不要求改 sync 取消 S5（脏树拒 apply 合理）。  
- 不要求 prompts 停止全量 cp。  
- 不要求 CI 默认 `--strict`。  
- 不在本 FEEDBACK 要求立刻改码；产品用下方 Prompt 确认并回填即可。

---

## 5. severity

| ID | 主题 | severity |
|----|------|----------|
| RB-ORD-01 | 缺「先 commit 契约再 upgrade」 | **P2** |
| RB-ORD-02 | §0b 未交叉链 overlay 迁 | **P2** |
| RB-ORD-03 | 缺二次 upgrade / 负面边界句 | **P3** |
| RB-ORD-04 | 示例命令版本钉漂移 | **P3** |

---

## 复制区（整段粘贴 → Open Folder = cyning-harness）

`````text
你负责产品仓 cyning-harness。请把「upgrade overlay 合规迁入」从经验流程写成 RUNBOOK 强制操作序（文档回填；默认本会话不改 sync 行为，除非维护者明示实现）。

【Open Folder】
对准 cyning-harness git root（用 git rev-parse --show-toplevel；勿写死假路径）。

【背景】
- 能力已在 2.22.0：local 块 + graph_modules_path + overlay hint（ops U2 部分根治）。
- 消费者 ops-desk-api dogfood：合规下 upgrade 可零手恢复；但若「先改 AGENTS/profile 未 commit 就 upgrade」会撞 S5；若跳过迁契约仍靠手恢复。
- 真值：docs/RUNBOOK_upgrade_wiki_delta_v1_zh.md §0b / §1.2 · ide/adapters/README.md · CHANGELOG 2.22.0
- 消费者 FEEDBACK（只读）：
  - ops-desk-api/docs/harness/evidence/FEEDBACK_harness_2_22_0_from_ops_desk_api_20260728.md
  - ops-desk-api/docs/harness/evidence/FEEDBACK_RUNBOOK_overlay_procedure_from_ops_desk_api_20260728.md（本诉求全文）

【任务】
1. 评估并回填 RUNBOOK（建议新增 §1.2.1「首次接入 overlay 契约」），强制序须含：
   A. profile 可选 graph_modules_path（与 tracks 同级）
   B. AGENTS：仓特异词移到产品 begin/end **外**的 cyning-harness-local 块；禁止写进 cursor mdc / 产品块内
   C. **先 git commit 契约，再 upgrade**（说明脏树 → S5；--force 非默认）
   D. 钉版 upgrade + check；注视 hint / graph_modules_path 行
   E. 有 pin 则额外 bump
   F. 验收：git diff 四文件；local 仍在；FRAGMENT 含 profile 路径；建议第二次 upgrade diff 空
2. §0b 快速路径交叉链：目标 ≥2.22 且曾有 overlay 定制 → 先 §1.2.1。
3. §1.2 表补「操作序」行；可选一句负面边界（产品块内裸定制仍冲）。
4. 示例命令钉到文档当前大版本（避免与 check 漂移）。
5. adapters README / ONBOARDING 加 POINTER（若合适）。

【约束】
- 不削弱 S2/S5/close/wiki_delta/pre-30/HG-*。
- 禁擅自 npm publish；改动走产品 task + PR。
- 默认以文档回填为主；若要改 upgrade stdout 文案（例如 S5 时提示「先提交 local/profile」）可列为可选小改并单独说明。

【验收】
- RUNBOOK 出现可复制逐步序（非仅概念表）。
- §0b ↔ §1.2.1 互链。
- 输出：改动文件清单 · 建议版本（文档 patch 或 2.22.x/2.23）· 是否需消费者再 dogfood 一句。
`````

---

## 维护者备注（勿粘贴）

- 本文件可与 2.22 FEEDBACK 一并交产品 00。  
- ops 仓 PR #23 已验证能力；本反馈只追 **文档流程化**。  
- 若产品采纳后发版，ops 仅需抽检 RUNBOOK 可读性，不必再迁契约。
