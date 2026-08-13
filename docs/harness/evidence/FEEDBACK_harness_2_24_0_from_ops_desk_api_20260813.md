# FEEDBACK · harness 2.24.0 · from ops-desk-api（upgrade 复检 · overlay / skills）

> **日期**：2026-08-13  
> **业务仓**：`ops-desk-api`（FastAPI · WikiTrack 已启用 · G-L 试点）  
> **git root**：`/Users/cyning/Desktop/Ops-desk/ops-desk-api`  
> **起点**：manifest `2.22.0` → 目标钉 `@cyning/harness@2.24.0`  
> **对照**：产品 RUNBOOK · CHANGELOG 2.22.1–2.24.0 · 前波 FEEDBACK 2.22 U2  
> **上波**：FEEDBACK `docs/harness/evidence/FEEDBACK_harness_2_22_0_from_ops_desk_api_20260728.md` · PR #23  
> **分支**：`task/upgrade-harness-2-20-runbook-feedback`（自 `origin/master`）

---

## 1. 结论（验收）

| 项 | 结果 |
|----|------|
| manifest | **2.24.0**（from 2.22.0） |
| pin | 无 · N/A |
| `graph_modules_path` | **`l1/01_modules`** |
| AGENTS local 块 | 关键词在（pre-30 / HG-PILOT / G-L0） |
| **合规路径：upgrade 后零手恢复** | **PASS**（第一次 / 第二次均未从 backup 手贴） |
| `task lint`（本 task） | PASS（W4 warn：无思考轮节 · 合法豁免） |
| `lint-wiki-delta` | scanned=30 · missing=0 · PASS |
| `lint-wiki-delta --strict` | **FAIL** · 仅 `task_ops_sync_sender_migration.md`（`wiki_delta_none_no_note`）· **本波禁止改该 task** |
| `skills check` | **PASS**（v2.23+ · 无 drift） |
| severity=block | **无**（对本仓 overlay 契约） |

**判定**：2.22 overlay 契约在 2.24 钉升下仍成立；合规路径无需人手恢复 AGENTS / FRAGMENT / CLAUDE / cursor mdc。

---

## 2. overlay 迁法（本仓 · 沿用 2.22）

1. `.cyning-harness/profile.json` 顶层 `"graph_modules_path": "l1/01_modules"`。  
2. `AGENTS.md`：产品 `cyning-harness:begin/end` 外紧随 `cyning-harness-local:begin/end`。  
3. 先 commit 契约/产物，再 `upgrade`（脏树撞 S5）。

---

## 3. upgrade 实录

### 3.1 before check

```text
npx @cyning/harness check --target .
→ 包版本 2.24.0 · manifest 2.22.0 · 状态: 可升级 · exit 0
```

### 3.2 第一次（干净树 · 钉 2.24.0）

```text
npx --yes @cyning/harness@2.24.0 upgrade --target . --yes
→ prompts 全量 cp（README 等有 diff）
→ overlay · FRAGMENT graph_modules_path → l1/01_modules
→ hint · overlay … 本波 diff --stat:（AGENTS/CLAUDE/mdc/FRAGMENT 空）
→ manifest 2.24.0 · exit 0
```

| 文件 | 手恢复？ | 说明 |
|------|----------|------|
| AGENTS.md | **否** | local 块保留；相对 HEAD 无 diff |
| FRAGMENT_30 | **否** | `{l1/01_modules或—}` 仍在 |
| CLAUDE.md / cursor mdc | **否** | 无 diff |
| prompts/*.md | N/A | 产品全量 cp · 预期 |

### 3.3 第二次（同版本幂等）

- 第一次后未提交 → `upgrade` **S5 中止**（exit 1）· 与 2.22 FEEDBACK「先 commit 再 upgrade」一致。  
- 提交 sync 产物后重跑：

```text
npx --yes @cyning/harness@2.24.0 upgrade --target . --yes
→ hint · overlay … 本波 diff --stat:（空）
→ local.json 未变（跳过写入）
→ 仅 manifest.upgraded_at 时间戳更新 · exit 0
```

| 检查 | 结果 |
|------|------|
| local 关键词 | 仍在 |
| FRAGMENT `l1/01_modules` | 仍在 |
| 相对 HEAD overlay（AGENTS/CLAUDE/mdc/FRAGMENT） | **空**（零手恢复） |

### 3.4 skills（v2.23+ 引入 · 本波复检）

```text
npx @cyning/harness skills check  → PASS · frontmatter 合法 · skills/ 无 drift · exit 0
npx @cyning/harness skills build  → PASS · 6 文件 → 产品包 skills/（不改业务仓 docs/skills）· exit 0
```

说明：`skills build` 写产品包内 `skills/`，本仓 `docs/skills/` 真值未被动；check 无 drift。

---

## 4. lint / strict / verify

```text
task lint --file …task_upgrade…          → PASS · exit 0（W4）
task lint-wiki-delta                     → PASS · scanned=30 · missing=0 · exit 0
task lint-wiki-delta --strict --json     → FAIL · exit 2 · issues=[task_ops_sync_sender_migration wiki_delta_none_no_note]
verify --task …task_upgrade…             → PASS · exit 0
check                                    → 已是最新 · exit 0
```

未改 close / pre-30 / HG-* 闸语义。`--strict` 失败项 **不在本 task 范围**（派工禁止动 `task_ops_sync_sender_migration`）。

---

## 5. 剩余缺口与 severity

| ID | 现象 | severity | 说明 |
|----|------|----------|------|
| U2-ok | 合规路径零手恢复 ×2 | info | 2.24 复检通过 |
| S5-order | 第一次 upgrade 未提交再跑撞 S5 | **P3** | 同 2.22；先 commit sync 再二次 upgrade |
| strict-other-task | 全局 `--strict` 被无关 active task 挡住 | **P3** | 需另开 task 补 `wiki_delta_note`；非本波 |
| prompts-cp | prompts 仍全量 cp | info | 预期 |
| skills-v223 | skills build/check 可用 | info | build 落产品包；业务仓 docs/skills 另轨 |

---

## 6. 对本仓 / 产品建议

| 侧 | 建议 |
|----|------|
| 本仓 | 合入本分支 PR；00 验收关账；另开小 task 修 `task_ops_sync_sender_migration` 的 `wiki_delta_note` 以使全局 `--strict` 绿 |
| 产品 | S5 操作序已在 2.22 FEEDBACK 提过；本波无新 overlay 缺口 |

---

## 7. 验收清单

- [x] manifest = 2.24.0  
- [x] profile `graph_modules_path=l1/01_modules`  
- [x] AGENTS 产品块外有 local 块且关键词在  
- [x] upgrade 后无需 backup 手恢复（合规路径 · ×2）  
- [x] FEEDBACK 已落盘  
- [x] skills check PASS（本波新增复检）  
- [ ] 全局 `lint-wiki-delta --strict`（阻塞在无关 task · 留给 00/另 task）  
