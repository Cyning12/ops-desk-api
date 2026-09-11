# task_specwave_cleanup_2_1_3 审查（R3 · 20-task-audit · R+2 复审）

> **审查对象**：`docs/tasks/active/task_specwave_cleanup_2_1_3.md`（10-task 承接 R2 B-3 修订 · lint PASS）
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30）
> **日期**：2026-09-11 · **分支**：`task/dsh-coding-kit-2-1-0`
> **前序**：`task_specwave_cleanup_2_1_3_audit_R1_20260911.md`（RETURN-TO-10 · B-1/B-2）· `task_specwave_cleanup_2_1_3_audit_R2_20260911.md`（RETURN-TO-10 · B-3）
> **结论**：**PASS**（R2 阻塞 B-3 修复有效 · 内容零阻塞 · 本轮为终轮，审查签收/关闭）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **零内容阻塞**——B-3 修复经独立实证有效（见下），验收全部条目可机验 |
| **流程闸** HG-TASK-DRAFT | `pending`（blocks 20-R1, 30）· 待维护者签 |
| **流程闸** HG-AUDIT-R1 | `pending`（blocks 30）· 本审查书面通过；须维护者签 `approved` 后 30 方可开工 |
| lint 复跑 | `spec-wave task lint --file` → **LINT: PASS** exit 0（2026-09-11 本帽复跑 ✓，与 task 自检第三行一致） |

---

## B-3 修复有效性 · 独立实证（本轮核心）

### 1. 合成串测试：锚定 grep 不误命中新位置、必命中旧位置

在 `/tmp/r3_synth/` 构造 10 个合成文件，对验收 (a)/(b) 模式逐一验证：

| 合成形式 | 样例 | (a) 绝对锚定 | (b) 相对锚定 | 期望 |
|----------|------|:---:|:---:|:---:|
| 旧绝对 | `docs/spec/SPEC-gha-deploy-api_v1.md` | **命中** ✓ | — | 必命中 ✓ |
| 旧相对 `../spec/` | `../spec/SPEC-qdrant-migration_v1.md` | — | **命中** ✓ | 必命中 ✓ |
| 旧相对 `../../spec/` | `../../spec/SPEC-qdrant-migration_v1.md` | — | **命中** ✓ | 必命中 ✓ |
| 旧相对 `../`（无 spec/） | `../SPEC-harness-to-dsh-kit-graph-migrate_v0.md` | — | **命中** ✓ | 必命中 ✓ |
| 旧相对 `../../`（无 spec/） | `../../SPEC-inform-graph-backfill_v1.md` | — | **命中** ✓ | 必命中 ✓ |
| 新绝对 | `docs/spec/gha-deploy-api/SPEC-gha-deploy-api_v1.md` | 不命中 ✓ | 不命中 ✓ | 不误命中 ✓ |
| 新相对 | `../gha-deploy-api/SPEC-…`、`../../lc-evidence-chain/SPEC-…` | 不命中 ✓ | 不命中 ✓ | 不误命中 ✓ |
| 裸文件名 | `SPEC-rag-reranker-p0_v1.md` | 不命中 ✓ | 不命中 ✓ | 不误命中 ✓ |
| kit 占位符 | `docs/spec/SPEC-<slug>_v1.md` | 不命中 ✓ | 不命中 ✓ | 不误命中 ✓ |

10/10 符合期望。B-3 三条 FAIL 路径全部消除：夹内合法新引用不命中、历史档机械替换残留裸文件名不命中、占位符不命中。

### 2. 豁免参数正确性与账目闭合

| 项 | 实证 |
|----|------|
| `--exclude=task_specwave_cleanup_2_1_3.md` | task 自身命中 (a) 8 + (b) 1 = **9 处**，与 L98 豁免说明「9 处文件名属元信息引用」一致 ✓（R2 回填选项「显式豁免」被采纳，合法） |
| `--exclude-dir=reviews` | `docs/harness/reviews/` 命中 (a) 9 + (b) 3，全部豁免 ✓（R1/R2 历史审查文不改写） |
| 账目闭合 | (a)：59（无豁免）− 8（task）− 9（reviews）= **42**（豁免后），与自检第三行声明一致 ✓；(b)：8 − 1 − 3 = **4** ✓ |
| 豁免后基线无新位置巧合命中 | 豁免后 (a) 42 命中中 `docs/spec/<夹>/SPEC-` 形式 **0 处** ✓——基线干净，迁移后归零可达成 |

### 3. R2 回填清单逐项核对

| R2 要求 | 落实 |
|---------|------|
| 验收拆 (a)(b) 旧位置锚定 + (c) 新位置可达，test_strategy_note 同步 | ✓ L96(a)/L97(b)/L99(c)，test_strategy_note L19 同步改写（b 处以「同范围同豁免」引用，全式在验收条内） |
| 映射表写死夹内文件名（保留 `SPEC-<name>_vN.md` · 循 agent-infra 先例） | ✓ L62 写死；先例实证：`docs/spec/agent-infra/SPEC-capability-gateway_v0.md`、`SPEC-structured-output-gateway_v0.md` 现存 ✓ |
| task 自身 9 处命中处置 | ✓ 显式豁免（L98 豁免说明含理由与范围） |
| 思考轮增 R5 + early_stop residual_risks 更新 | ✓ R5（L141）回填 B-3 全貌；residual_risks ②（L143）覆盖「裸文件名永不零命中 → 旧位置锚定 + 豁免 + test -f 兜底」 |
| 重跑 task lint 回填自检第三行 | ✓ 自检第三行（L152）+ 本帽复跑 PASS 一致 |

### 4. 映射表 ↔ `test -f` 一致性（程序比对）

映射表 8 行目标与验收 (c) 8 个 `test -f` 路径**逐一相等**，且每个目标文件名 = 源文件名（保留原文件名约定无漂移）。8 个源文件实证仍在根级（`ls docs/spec/SPEC-*.md` = 8）；8 个目标当前均不存在（迁移前 `test -f` 全 FAIL，迁移后全 PASS——检查有鉴别力 ✓）。C-3 目标夹 `docs/spec/inform-graph-backfill/` 实证存在 ✓。

---

## 终查项（验收可机验性 / 闭合 / 闸）

| 核对项 | 结果 |
|--------|------|
| 验收全部 10 条可机验 | ✓ L93 grep、L94 ls、L96-99 (a)(b)(c) 全式命令、L100 三处点名行核对、L101 README 三项内容核对、L102 check 零 WARN、L103 verify、L104 graph-compile、L105 FEEDBACK 落盘，均有明确判据 |
| 范围/非范围闭合 | ✓ 范围 A(2 处裸命令)/B(8 文件+引用同步+README) 与非范围 9 条（app/、上游回灌、占位符 3 处豁免、旧命令面、.DS_Store、不代签）互补无冲突 |
| C-1/C-2/C-3 写死 | ✓ 映射表标裁定（L62/L66/L68/L69-70），failure_paths 歧义行「执行时不再 STOP」（L112），无残留待定项 |
| 思考轮 R0–R5 闭合 | ✓ 六轮全有焦点+结论；R4 承接 R1、R5 承接 R2，链路完整 |
| early_stop 与 residual_risks 一致 | ✓ R5 停，理由（过程轨面小可验证）+ 三条 residual_risks 与豁免/锚定设计一一对应 |
| 两闸 pending 未代签 | ✓ HG-TASK-DRAFT、HG-AUDIT-R1 均 `pending`（L38-39）；本审查文不产生任何 approved |
| 前置状态实证 | spec-wave 2.1.3 binary 存在且 lint 可跑 ✓；分支 `task/dsh-coding-kit-2-1-0` ✓ |

---

## 非阻塞备注（不构成退回理由 · 30 执行时注意即可）

1. test_strategy_note 中 (b) 命令以「<同范围同豁免>」缩写，全式在验收 L97——执行时以验收条为准。
2. 豁免后基线 (a) 42 / (b) 4 为**迁移前**快照；30 执行后此数应归零，若残留即引用断裂，按 failure_paths 第一行回滚重来。

---

## 签收 / 关闭

- 本审查（R3）为终轮：**书面审查通过并签收**，审查轨关闭。
- task 内容层面已具备 30 可执行性；**30 开工的唯一前置是流程闸**：维护者在 task 人工闸表签 HG-TASK-DRAFT 与 HG-AUDIT-R1 = `approved`。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 / R2 / R3 审查结论（R3 = PASS · 终轮签收）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
