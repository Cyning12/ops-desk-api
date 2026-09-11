# task_specwave_cleanup_2_1_3 审查（R2 · 20-task-audit · R+1 复审）

> **审查对象**：`docs/tasks/active/task_specwave_cleanup_2_1_3.md`（10-task 承接 R1 修订 · lint PASS）
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30）
> **日期**：2026-09-11 · **分支**：`task/dsh-coding-kit-2-1-0`
> **前序**：`task_specwave_cleanup_2_1_3_audit_R1_20260911.md`（结论 RETURN-TO-10 · 阻塞 B-1/B-2 · 非阻塞 5 项 · 裁定项 C-1/C-2/C-3）
> **结论**：**RETURN-TO-10**（R1 意见 9 项中 8 项已落实 ✓；B-1/B-2 的修订引入新致命缺陷 1 项，见 B-3）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ❌ **1 项内容阻塞**（B-3：修订后的验收 grep 丢失目录锚定，迁移正确完成后机验仍永不零命中）→ 退回 10-task 修订后再审 R3 |
| **流程闸** HG-TASK-DRAFT | `pending`（blocks 20-R1, 30）· 待维护者签 |
| **流程闸** HG-AUDIT-R1 | `pending`（blocks 30）· 本审查不签收；须 R3 通过 + 维护者签 `approved` |
| lint 复跑 | `spec-wave task lint --file` → **LINT: PASS** exit 0（2026-09-11 本帽复跑 ✓，与 task 自检第二行一致） |

---

## R1 意见落实核对（逐项 · 机验实证）

### B-1（验收 grep 锚定 + 豁免）→ 部分落实 · 修复方式引入 B-3（见下）

| 核对点 | 结果 |
|--------|------|
| 验收 grep 锚定 8 个具体文件名（含 `_vN` 版本后缀 + `\.md`） | ✓ 已改（task L95 / test_strategy_note L19） |
| kit 占位符 2 处显式豁免 | ✓ 非范围 L87 点名 `.cursor/skills/harness-10-spec/SKILL.md:51`、`docs/harness/prompts/10-spec-requirements.md:51`；验收第 4 条（L96）列为豁免核对项 |
| doc-health 描述行 1 处豁免 | ✓ 同上 L87/L96 点名 `docs/spec/doc-health/README.md:48` |
| 豁免不被误命中 | ✓ 实证：对 3 个豁免文件跑锚定模式（甚至去掉 `_vN`/.md 的宽松模式）**exit 1 零命中**——占位符 `SPEC-<slug>_v1.md` 与通配 `SPEC-*.md` 均不含 8 个具体名，永不被误命中 |

### B-2（相对路径变体覆盖）→ 已落实 ✓

| 核对点 | 结果 |
|--------|------|
| 3 处变体入引用清单 | ✓ 范围 B item 4（L75）逐一点名 `context.md:37`、`qdrant-migration-narrative.md:7`、`inform-graph-backfill/README.md:15`（含行号与字面形式） |
| 验收 grep 覆盖变体 | ✓ 实证：当前锚定 grep 共 **74 命中 / 47 文件**，其中确含上述 3 个变体文件（`context.md:37`、`qdrant-migration-narrative.md:7+245`、`inform-graph-backfill/README.md:15`）——裸文件名模式天然同时覆盖 `docs/spec/` 前缀与 `../` 变体 |
| 但覆盖方式与 B-3 冲突 | ⚠️ 见阻塞项 B-3 |

### C-1/C-2/C-3（维护者裁定写死）→ 已落实 ✓

- 映射表（L66-L70）：C-1 新夹 `docs/spec/gha-deploy-api/`、C-2 合并夹名定 `lc-evidence-chain`、C-3 整文件迁入既有夹不留根级 POINTER，均标「**裁定**」并注明「维护者 2026-09-11 已裁定并写死」（L62）✓
- failure_paths 歧义行同步改写（L108）：「目标夹约定歧义」行已改为「已裁定写死 · 执行时**不再 STOP**；新发现的歧义仍 STOP 问维护者」✓ 不再是待定项
- 思考轮 R4（L136）与 early_stop residual_risks（L139）同步回填 ✓

### 非阻塞 5 项 → 全部落实 ✓

| # | R1 意见 | 落实 |
|---|---------|------|
| 1 | 目标口径限定 | ✓ L50 限定为「cursor rules 两处 L19」；非范围 L86 逐一点名 5 处活文档旧命令面留待后续波 + kit 上游走 FEEDBACK 轨 |
| 2 | 依赖链接修复 | ✓ L118 两个链接去 `../` 前缀（仓根相对惯例）；`docs/spec/README.md`、`docs/spec/doc-health/README.md`、`./task_dsh_coding_kit_upgrade_2_1_0.md` 均实证存在 |
| 3 | blocks 帽号 | ✓ L38 HG-TASK-DRAFT blocks=`20-R1, 30` |
| 4 | README L3 旧名 | ✓ 范围 B item 6（L77）纳入「顺手更新 L3 公约行 `dsh-coding-kit` → `spec-wave`」，验收第 5 条（L97）对应 |
| 5 | .DS_Store 留痕 | ✓ 非范围 L88「已 gitignore · 仅留痕不处理」 |

---

## 阻塞项（内容 · 退回 10-task）

### B-3 · 修订后验收 grep 丢失目录锚定：迁移**正确完成**后零命中仍永不可达成（B-1/B-2 修复引入的新缺陷）

R1 建议原方案为 **`docs/spec/SPEC-` 前缀锚定**（目录锚定 · 迁移后旧路径不存在则天然零命中）+ 单独的相对变体 grep。10-task 修订时将二者合并为**裸文件名**模式（`SPEC-(8 名)\.md` · 不带任何目录前缀），该模式把「旧位置引用」与「文件名的任何合法提及」混为一谈。实证三条独立路径均致验收 FAIL：

1. **仓内自身先例反证**：迁入专属夹的 SPEC **保留原文件名**——`docs/spec/agent-infra/SPEC-capability-gateway_v0.md`、`SPEC-structured-output-gateway_v0.md` 现存；且全仓 **20 处**对夹内 SPEC 的活引用（done tasks / invokes / prompts）**均含裸文件名**（如 `docs/spec/agent-infra/SPEC-capability-gateway_v0.md`）。本 task 映射表目标夹 + C-3「整文件迁入」+ 非范围「不改 SPEC 正文实质内容」均指向同一形态 → 迁移后合法新引用 `docs/spec/gha-deploy-api/SPEC-gha-deploy-api_v1.md` 等**必然命中**裸文件名 grep → 验收第 3 条永远 FAIL。
2. **历史档「仅机械路径替换」策略**（范围 B item 5）：`docs/spec/SPEC-gha-deploy-api_v1.md` → `docs/spec/gha-deploy-api/SPEC-gha-deploy-api_v1.md` 机械替换后仍含裸文件名 → 当前 74 命中中 done/reviews/invokes/experiments 的大头替换后**依然命中**。
3. **task 文件自身 9 处命中**：映射表源列（8 行）+ test_strategy_note + failure_paths 均含旧路径/裸文件名；验收 grep 覆盖 `docs/` 含 `docs/tasks/active/` 自身。R1 审查文亦有 3 处。task 未规定执行后改写自身映射表源列，亦未将 task/reviews 列入豁免。

即：B-1 的「不可达成」以另一种形式回归——**30 按 task 正确执行完毕，验收仍 FAIL**。

**修订建议（10-task）**：验收第 3 条拆为「旧位置形式」锚定的两条机验 + 一条新位置可达性机验，并写死夹内文件名约定：

```bash
# (a) 绝对旧位置零命中
grep -rEn "docs/spec/SPEC-(gha-deploy-api_v1|harness-to-dsh-kit-graph-migrate_v0|inform-graph-backfill_v1|langchain-evidence-chain_v1|lc-evidence-chain-hardening_v1|langfuse-sdk-v4-migration_v1|qdrant-migration_v1|rag-reranker-p0_v1)\.md" docs/ .cursor/ scripts/ experiments/ AGENTS.md
# (b) 相对旧位置变体零命中（覆盖 ../spec/SPEC-… 与 ../SPEC-…）
grep -rEn "(\.\./)+(spec/)?SPEC-(同上 8 名)\.md" docs/ .cursor/ scripts/ experiments/ AGENTS.md
# (c) 新位置可达：8 个目标文件存在
test -f docs/spec/gha-deploy-api/SPEC-gha-deploy-api_v1.md && …（8 个）
```

- 写死夹内文件名约定：保留 `SPEC-<name>_vN.md`（循 `agent-infra/` 先例），消除「目标夹内文件名」歧义；
- task 自身命中处置：迁移后映射表源列回填为新路径（历史原文可入 R 轮/修订记录表述，或把 task 自身列入显式豁免）；
- test_strategy_note 同步改写。

---

## 独立复核（R2 新增核对 · 全通过项）

| 核对项 | 结果 |
|--------|------|
| `spec-wave task lint --file` 复跑 | **LINT: PASS** exit 0 ✓（与 task 自检第二行 2026-09-11 复跑声明一致） |
| `spec-wave check --target .` | exit 0 · WARN 仍 **8 条**根级裸 SPEC（8 源文件实证仍在根级 · 与 task 背景/映射表一一对应 ✓） |
| 范围/非范围闭合 | ✓ 非范围 9 条覆盖 app/、上游回灌、占位符豁免、旧命令面、.DS_Store、不代签闸；范围 A/B 边界清晰 |
| 人工闸 | 两闸全 `pending` ✓ 无代签 ✓ blocks 帽号已更新为 20-R1 ✓ |
| 验收可机验性 | 除 B-3 所涉第 3 条外，其余 8 条均可机验且有对应命令 ✓ |
| 思考轮 | R4 回填承接 R1 全项 ✓ early_stop 理由 + residual_risks 更新 ✓（B-3 未入 residual_risks——退回后须补） |
| 引用面基线 | 锚定 grep 当前 74 命中 / 47 文件，全部命中均为旧位置形式（实证无新位置形式的巧合命中），基线干净 ✓ |

---

## 回填清单（给 10-task · R3）

- [ ] 验收第 3 条按 B-3 建议拆为旧位置锚定 (a)(b) + 新位置可达 (c)，test_strategy_note 同步
- [ ] 映射表写死夹内文件名（保留 `SPEC-<name>_vN.md` · 循 agent-infra 先例）
- [ ] task 自身 9 处命中的处置（迁移后源列回填新路径 / 显式豁免）写入范围或验收
- [ ] 思考轮增 R5 回填本轮 B-3；early_stop residual_risks 更新
- [ ] 重跑 `task lint` 回填自检第三行，再送 20-task-audit R3

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 / R2 审查结论（本轮仍回退 · 待 R3 通过）
- [ ] （C-1/C-2/C-3 已裁定 ✓ 无新增裁定项）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT、HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
