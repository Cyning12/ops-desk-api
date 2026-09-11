# task_specwave_cleanup_2_1_3 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_specwave_cleanup_2_1_3.md`（10-task 起草 · lint PASS）
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30）
> **日期**：2026-09-11 · **分支**：`task/dsh-coding-kit-2-1-0`
> **结论**：**RETURN-TO-10**（内容阻塞 2 项：验收机验不可达成 / 机验覆盖缺口）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ❌ **2 项内容阻塞**（验收标准 B-1 / B-2，见下）→ 退回 10-task 修订后再审 R+1 |
| **流程闸** HG-TASK-DRAFT | `pending`（blocks 22-R1, 30）· 待维护者签 |
| **流程闸** HG-AUDIT-R1 | `pending`（blocks 30）· 本审查不签收；须 R+1 通过 + 维护者签 `approved` |
| verify 现状 | `spec-wave verify --task` → **BLOCKED exit 2**（两闸 pending · 序内预期 ✓） |

---

## 已核对通过项（机验实证）

| 核对项 | 结果 |
|--------|------|
| `spec-wave task lint --file` | 复跑 **LINT: PASS** exit 0（与 task 自检声明一致） |
| `spec-wave check --target .` | exit 0 · WARN **8 条**根级裸 SPEC（与 task 背景陈述一致 · 文件清单与映射表 8 行一一对应 ✓） |
| cursor rules 残留 | `.cursor/rules/05-harness-starter.mdc` 与 `05-kit-starter.mdc` **各恰好 1 处** `npx dsh-coding-kit`，均在 **L19**，无 marker（与 task 范围 A 陈述一致 ✓） |
| 引用面预查 | `grep -rn "docs/spec/SPEC-" docs/ .cursor/ scripts/ experiments/ AGENTS.md` = **70 行 / 47 文件**（task 称「约 60+ 处」，一致 ✓） |
| 元信息口径 | 与 `task_dsh_coding_kit_upgrade_2_1_0.md` 对齐：`graph_change_layer=none` ✓ `review_hat=20` ✓ `required_invoke_hats=30` ✓ `close_pr_policy=required` ✓ `test_strategy=required` ✓ |
| test_strategy 可执行性 | `node_modules/.bin/spec-wave` 存在（2.1.3）✓；`./scripts/graph-compile.sh` 存在且注释确含 SPEC 引用（L9/L15，graph_delta_note 属实 ✓） |
| 人工闸表 | 两闸全 `pending` ✓；HG-AUDIT-R1 blocks=30 ✓（本审查文不产生任何 approved） |
| 非范围 | 排除 `app/` ✓、`uv.lock`/`.agents/` ✓、kit 上游 assets（`.cursor/commands/kit-*`、`.cursor/skills/*`、`docs/harness/prompts/*` 内旧命令属上游回灌面 → FEEDBACK 轨兜底 ✓） |
| failure_paths | 覆盖引用断裂 / 映射歧义 STOP / marker 误伤 / 上游回灌 / 历史档保留异议 / 兄弟 active task 挡 CLOSE ✓ |
| 思考轮 | R0–R3 回填闭合 · early_stop 理由 + residual_risks 齐 ✓（过程轨 R3 停合理） |
| 歧义上升 | gha-deploy-api 新夹、lc-evidence-chain 合并夹命名 → 已入 failure_paths **STOP 问维护者**条款，未由执行者擅自决定 ✓ |

---

## 阻塞项（内容 · 退回 10-task）

### B-1 · 验收 grep「零命中」不可达成（与非范围冲突）

验收标准第 3 条：`grep -rn "docs/spec/SPEC-" docs/ .cursor/ scripts/ experiments/ AGENTS.md` 零命中。

实证该模式当前命中中，有 **3 处非 8 文件引用的「模式巧合命中」**，本波不可消：

1. `.cursor/skills/harness-10-spec/SKILL.md:51` — `docs/spec/SPEC-<slug>_v1.md`（**模板占位符** · kit skills 资产，sync 回灌面）
2. `docs/harness/prompts/10-spec-requirements.md:51` — 同上占位符（kit prompts 同步资产）
3. `docs/spec/doc-health/README.md:48` — `docs/spec/SPEC-*.md`（doc-health 对 WARN 行为的**文档描述**）

即：不改 kit 上游资产（非范围明确禁止）则验收永远 FAIL；改了则违反非范围且下次 sync 回灌。

**修订建议（10-task）**：验收 grep 改为锚定 8 个具体文件名，例如：
`grep -rEn "docs/spec/SPEC-(gha-deploy-api|harness-to-dsh-kit-graph-migrate|inform-graph-backfill|langchain-evidence-chain|langfuse-sdk-v4-migration|lc-evidence-chain-hardening|qdrant-migration|rag-reranker-p0)" docs/ .cursor/ scripts/ experiments/ AGENTS.md` 零命中；
或将占位符/描述行显式列为验收豁免并在 task 内写明。

### B-2 · 验收 grep 覆盖缺口：相对路径变体引用逃逸机验

「全仓引用零断裂」的机验命令只匹配字面 `docs/spec/SPEC-` 前缀。实证至少 **3 处活引用为相对路径变体**，漏改时验收仍 PASS、链接已断：

| 文件 | 行 | 形式 |
|------|----|------|
| `docs/coding_wiki/context.md` | 37 | `../spec/SPEC-gha-deploy-api_v1.md`（task wiki_delta_note 点名要改此文件，却不在验收 grep 覆盖内） |
| `docs/deployment/qdrant-migration-narrative.md` | 7 | `../spec/SPEC-qdrant-migration_v1.md` |
| `docs/spec/inform-graph-backfill/README.md` | 15 | `../SPEC-harness-to-dsh-kit-graph-migrate_v0.md` |

**修订建议（10-task）**：验收补变体形式机验（如 `grep -rEn "(\.\./)+spec/SPEC-|\.\./SPEC-" <同路径集>` 针对 8 文件名零命中），或改为「移动后全仓 markdown 链接检查」类命令；范围第 4 条引用清单应补列上表 3 个文件（context.md 已在清单，另 2 个文件未显式列出——`docs/deployment/` 笼统涵盖但变体形式未点名）。

---

## 非阻塞项（退回 10 时顺带修订 · 不单独构成退回理由）

1. **目标表述口径**：背景/目标 L50「清零 `dsh-coding-kit` 裸命令残留」字面可读为全仓清零；实证仓内活文档仍有多处 `npx dsh-coding-kit`（`docs/coding_wiki/README.md:36`、`topics/wikilinks_export.md:14`、`docs/spec/inform-graph-backfill/README.md:102`、`doc-health/process/agent_close_discipline.md:22-23`、`_tech_graph/shared/99_mermaid_protocol.md:8`、`.cursor/commands/kit-*.md`×3、`.cursor/skills/*` 多处）。其中 `.cursor/commands|skills` 属 kit 上游（FEEDBACK 轨 ✓），其余为历史/过程文档。建议目标限定为「**cursor rules 两处**裸命令残留清零」，或将其余活文档旧命令面显式入非范围/后续波。
2. **依赖节链接断裂**：L114 `[docs/spec/README.md](../docs/spec/README.md)` 自 `docs/tasks/active/` 解析为 `docs/tasks/docs/spec/README.md`（实证不存在）；仓内惯例按仓根相对书写，建议去 `../` 前缀。同行 doc-health 链接同病。
3. **blocks 编号过时**：HG-TASK-DRAFT blocks=`22-R1, 30` 沿用旧帽号；V2 拆分后审查帽为 **20-task-audit**（22 已改名）。与前序 task 口径一致故不阻塞，建议顺手改 `20-R1, 30`。
4. **README 公约行旧名**：`docs/spec/README.md:3`「契约真值在 dsh-coding-kit」——范围 B item 6 正改此文件，建议同行顺手更新为 spec-wave（或在非范围显式排除）。
5. **`docs/spec/doc-health/.DS_Store`**：已 gitignore（实证 IGNORED），无需处理，仅留痕。

---

## 维护者待裁定项（签 HG-AUDIT-R1 前建议一并拍板，避免 30 执行中 STOP）

| # | 裁定项 | README 公约原文 | task 建议映射 | 审查意见 |
|---|--------|----------------|--------------|----------|
| C-1 | `SPEC-gha-deploy-api_v1` 去向 | 「另建专属夹**或**归入既有运维夹」 | 新夹 `docs/spec/gha-deploy-api/` | 仓内无既有运维 spec 夹，新夹合理；请维护者确认夹名 |
| C-2 | `lc-evidence-chain` 合并夹命名 | hardening 行「与 evidence-chain 合并夹」；langchain-evidence-chain 行「专属夹或 agent/rag 族」 | 两文件合并入 `docs/spec/lc-evidence-chain/` | 合并方向有 README 依据；**夹名 `lc-evidence-chain` vs `langchain-evidence-chain`** 请维护者拍板（slug=去版本后缀的字面规则倾向后者，task 取短名） |
| C-3 | `SPEC-inform-graph-backfill_v1` 处置方式 | 「已有 inform-graph-backfill/ · **宜改 POINTER**」 | 整文件迁入既有夹 | README 建议 POINTER 化，task 为整搬（非范围又禁改正文实质）——**整搬 vs 改 POINTER** 是内容抉择，failure_paths 未显式点名此分歧，请维护者裁定后回填映射表 |

---

## 回填清单（给 10-task · R+1）

- [ ] 修订验收标准第 3 条（B-1：锚定 8 文件名或显式豁免占位符命中）
- [ ] 补变体引用机验命令 + 引用清单补列 2 文件（B-2）
- [ ] 目标 L50 口径限定 / 活文档旧命令面处置声明（非阻塞 1）
- [ ] 依赖节两个 `../docs/...` 链接修正（非阻塞 2）
- [ ] blocks `22-R1` → `20-R1`（非阻塞 3）
- [ ] 维护者裁定 C-1/C-2/C-3 后回填映射表与 failure_paths
- [ ] 修订后重跑 `spec-wave task lint` 并回填自检结论，再送 20-task-audit R+1

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本轮回退 · 待 R+1 通过）
- [ ] 裁定 C-1 / C-2 / C-3 并确认回填
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT、HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
