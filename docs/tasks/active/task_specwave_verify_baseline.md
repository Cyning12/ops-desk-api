# Task：specwave-verify-baseline（仓级 verify 缺口基线收口 · chore）

> **状态**：draft（10 落稿 · 20 审与三闸 pending）
> **类型**：仓级 chore（文档合规 · SPEC §9 序3 · 维护者令 2026-10-11 立项）
> **依据**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序3（仓级 verify EXIT=2 BLOCKED 92 缺口 · 实跑复核 93）· T1 40 钉案③
> **分支**：`task/specwave-verify-baseline`（base = master `cae745e`）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `specwave-verify-baseline` |
| **帽链** | 10-task → 20-task-audit → 三闸 → 30 → 40 → PR → CLOSE |
| **人工闸** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = **pending**（00 代录）· HG-PILOT-OPSDESK-GLAYER n/a |
| **图谱预判** | n/a（纯文档面 · 不动模块图谱） |

## 1. 背景与实证（2026-10-11 实跑真值 · base cae745e）

- `npx spec-wave verify` **真 EXIT=2**（注意：`verify | tail` 管道会吞码报 0 · 先前 30 棒「EXIT=0 自报不准」即此坑 · 测码须 pipefail 或重定向后取 $?）· 尾行 `VERIFY: BLOCKED · 仓级 reviews 缺口 93`。
- **缺口构成（93 = done/ 155 档中的不合规集）**：
  | 类型 | 数 | 含义 |
  |---|---|---|
  | 审查文无结论/签收节 | 52 | reviews 档在但无「结论/签收」起首的 ##/### 节或节内无通过词 |
  | missing R<n> review | 36 | done 档**零审查档**（如 task_strategy_builder_spec · task_tenant_readonly_predicate 在 docs/harness/reviews/ 无对应档） |
  | 结论节缺审查行为陈述（SUBJ） | 5 | 档 M 语义判须陈述审查行为（审查/评审/核对…3.0-W4 NEW-5） |
- 审查档现址 `docs/harness/reviews/`（133 档 · 命名 `task_*_audit_R<n>_YYYYMMDD.md`）；新规约档落 `docs/audits/task-review/`（`YYYYMMDD_slug_rN.md` · 双址并存）。
- **影响**：仓级 verify 红灯常驻 → 新增档合规信号被 92/93 存量噪音淹没，门禁失去预警价值。

## 2. 目标

仓级 `npx spec-wave verify` EXIT=0 PASS（或经明示豁免清单后 PASS），增量门禁恢复预警力；存量处理口径诚实（**禁伪造审查**）。

## 3. 范围（D 块 · 候选开放不锁死 · 留 20 审）

### D1 · 存量 93 处置口径（核心裁定 · 三选一/可混合）
- **A 全量补审**：93 档逐一出补录审查文——诚实但工作量巨大，且历史档语义难以真审（作者/上下文多已散失），有「为绿而写」风险。
- **B 基线豁免清单 + 增量门禁**：verify 支持/加豁免清单（存量 93 按文件名钉死列入 · 新增档必须合规），红灯转绿且增量预警力恢复——成本最低，但存量永不合规。
- **C 混合（倾向）**：近期/高价值档（如 202609 后 done）真补审 · 古早档入豁免清单并注记「存量基线豁免 · 未审」——诚实且可行。
- 须先探 `npx spec-wave verify` 是否原生支持豁免机制（supports/CLI 面实证），不支持则豁免清单由仓内脚本/配置承载并回写 verify 用法文档。

### D2 · 双址归一（可选 · 留裁定）
- `docs/harness/reviews/` vs `docs/audits/task-review/` 双址并存是否本 task 收（挪档/软链/规约文档钉一址），或留后续。倾向本 task 只钉规约文档，不挪存量（最小面）。

### D3 · EXIT 码自证口径
- 验收/文档中凡引 verify EXIT 一律 pipefail 或重定向取真值，堵管道吞码坑（T1 30 棒前科）。

## 4. 钉死契约（红线）

1. **零业务码改动**——纯文档面（+ 可选 verify 豁免配置）。
2. **禁伪造审查**：补录审查文必须如实标注「存量补录 · 非同期审查」性质；豁免清单档如实注「未审」。
3. **增量门禁不破**：本 task 落地后新增 task/spec 档不合规时 verify 必须红（反向实证）。
4. **既有 133+ 合规档零 diff**。
5. **done/ 档本体零改**（不篡改历史档内容）。

## 5. 验收标准（TC 组 · 可机验）

- **TC1 基线全表**：缺口 93 逐档分类落账（表格：档名/类型/处置=补审或豁免），与实跑输出 1:1 对账。
- **TC2 绿证**：`set -o pipefail; npx spec-wave verify` EXIT=0 · 尾行 PASS（处置全部落地后）。
- **TC3 反向实证**：临时加一不合规档 → verify 红且指向该档 → 撤档复绿（增量门禁力证）。
- **TC4 诚实性抽查**：豁免/补录档注记措辞如实（维护者抽 5 档可读）。
- **TC5 反回归**：全量 pytest 零新增红（master 基线对拍）· 既有档 git diff 零。

## 6. 非范围

- verify 工具本体（spec-wave 上游）规则改动——如须豁免机制而上游无口，仓内承载并文档化，不改上游。
- 古早档内容质量重审（超出 chore 面）。
- reviews 双址物理归一（D2 除非裁定收）。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 落稿（**00 代笔** · 首棒卡滞 interrupt 留痕 · 授权 m01606 过程文档代签）：实跑真值 EXIT=2/93 缺口三类分账（52+36+5）· D1 倾向 C 混合 · 管道吞码坑钉 D3 · 三闸 pending |
