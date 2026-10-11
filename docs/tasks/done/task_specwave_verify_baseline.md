# Task：specwave-verify-baseline（仓级 verify 缺口基线收口 · chore）

> **状态**：done（2026-10-11 · 验收 TC1-TC5 全过 · 40 复核 PASS（V1-V5 · TC3 反向实证亲跑红绿）· 三闸 approved（维护者授权 m01606/m00255 · 00 代录）· PR [#228](https://github.com/Cyning12/ops-desk-api/pull/228) MERGED（squash `5204330` · 2026-10-11）· CLOSE 归档 done/ · 钉案与学习要点见 CLOSE 文档 [`../close/close_specwave_verify_baseline_20261011.md`](../close/close_specwave_verify_baseline_20261011.md)）
> **类型**：仓级 chore（文档合规 · SPEC §9 序3 · 维护者令 2026-10-11 立项）
> **依据**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序3（仓级 verify EXIT=2 BLOCKED 92 缺口 · 实跑复核 93）· T1 40 钉案③
> **分支**：`task/specwave-verify-baseline`（base = master `cae745e` · 已经 PR #228 squash 合入 master `5204330` · CLOSE 后 worktree `t-specwave-verify-baseline` 与 task/close 分支待清理——本 CLOSE 在该 worktree 内作业无法自清 · 留 00/维护者）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `specwave-verify-baseline` |
| **test_strategy** | `required` |
| **test_strategy_note** | 反向实证（TC3 增量门禁红→绿）+ 全量 pytest 零新增红 |
| **code_quality_bar** | `not_applicable`（纯文档面） |
| **帽链** | 10-task → 20-task-audit → 三闸 → 30 → 40 → PR → CLOSE |
| **graph_delta** | `none` |
| **graph_delta_note** | 纯文档面 · 不动模块图谱 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站变更（仓内规约档非 wiki） |
| **experience_capture** | `required` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **git_branch** | `task/specwave-verify-baseline` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved**（2026-10-11 · 00 代录 · 授权 m01606/m00255） | 20, 30 | R2 PASS-WITH-NITS（docs/audits/task-review/20261011_specwave-verify-baseline_r2.md · 559d24a） |
| HG-AUDIT-R1 | **approved**（同上代录） | 30 | R1 BLOCKER B-1→fe51492 修订→R2 PASS 闭合 · N-4 照登已吸收 |
| HG-GRAPH-MODULES | **approved**（同上代录 · 按实判） | PR | 图谱 n/a 照实（纯文档面 · 模块清单零增删） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 无外部试点面 |

## 1. 背景与实证（2026-10-11 实跑真值 · base cae745e）

- `npx spec-wave verify` **真 EXIT=2**（注意：`verify | tail` 管道会吞码报 0 · 先前 30 棒「EXIT=0 自报不准」即此坑 · 测码须 pipefail 或重定向后取 $?）· 尾行 `VERIFY: BLOCKED · 仓级 reviews 缺口 93`。
- **缺口构成（93 = done/ 154 档中的不合规集 · R1 N-1 修正 155→154）**：
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

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 豁免清单档字段缺/格式错 | verify failClosed 红（原生行为 · R1 探查在案） | 是 | 修清单档复跑 |
| 补录审查文注记缺「存量补录」 | TC4 抽查拦 + 契约 2 grep 机查 | 是 | 补注记 |
| 增量新档不合规 | verify 红指向该档（TC3 反向实证 · 预期行为） | 是 | 新档补合规 |
| 豁免清单被滥用扩列 | 每行须 reason/date/authorized_by 四字段 + PR 审 | 否 | 人审拦截 |

## 验收标准（TC 组 · 可机验）

- [x] 全量测试命令通过：`pytest tests -q` 零新增红（master 基线对拍 · TC5a 由零代码 diff 构造性成立 —— 分支与 master 代码面逐字节同一）
- [x] `npx --yes spec-wave task lint-wiki-delta --target .` 通过（wiki_delta 预检 · n/a 恒绿口径 · 30/40 双跑 EXIT=0 PASS）
- [x] TC1 基线全表：缺口 93 逐档分类落账（36 零审查档 + 39 无结论节 + 13 否定结论词 + 5 缺 SUBJ · 处置全=豁免 · 规约档 §五）· 与实跑输出 1:1 对账。
- [x] TC2 绿证：`npx spec-wave verify --target .`（重定向取 $?）→ EXIT=0 · VERIFY: PASS · 豁免命中 93 · invalid 0（30/40 双跑）。
- [x] TC3 反向实证：30 棒临时不合规档单点红→撤档复绿；40 棒藏豁免档→BLOCKED 93→恢复 PASS · 增量门禁预警力完整。
- [x] TC4 诚实性抽查：93 条目 reason 统一「存量基线豁免 · 未审」· authorized_by 93/93 A1 合规 · 豁免≠审查通过（40 机查 + 抽验 3 档缺口实证）。
- [x] TC5 反回归：全量 pytest 零新增红（TC5a 构造性恒等 · 30 棒亲跑对拍）· 既有档 git diff 零（done/ 与 reviews/ 133+ 档零触碰）。

## 非范围

- verify 工具本体（spec-wave 上游）规则改动——如须豁免机制而上游无口，仓内承载并文档化，不改上游。
- 古早档内容质量重审（超出 chore 面）。
- reviews 双址物理归一（D2 除非裁定收）。

### 自检结论（执行者）

**30 自检（2026-10-11 · 30-implement 棒）**：

- [x] `pytest tests -q` 零新增红（master cae745e 基线对拍）：见 invoke 思考轮 8（分支与 master 同环境同命令对跑 · 失败集逐名比对零新增）。
- [x] `npx --yes spec-wave task lint-wiki-delta --target .` → **EXIT=0 · PASS**（scanned 155 · issues 0）。
- [x] TC1 基线全表：93 档逐档分类落账（36 零审查档 + 39 无结论节 + 13 否定结论词 + 5 缺 SUBJ）· 处置全=豁免 · 落 `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md` §五 · 与实跑输出 1:1 对账。
- [x] TC2 绿证：豁免清单落地后 `npx spec-wave verify --target .`（重定向取 $?）→ **EXIT=0 · VERIFY: PASS** · 豁免命中留痕 93 · invalid 0。
- [x] TC3 反向实证：临时不合规档 `task_tc3_tmp_noncompliant_probe.md` → verify EXIT=2 BLOCKED 缺口 1 逐字指向该档 → 撤档 EXIT=0 复绿 · 零残留（证据 /tmp/tc3_red.txt / /tmp/tc3_green.txt）。
- [x] TC4 诚实性：豁免档 reason 统一「存量基线豁免 · 未审」· 「未审」语义钉于规约档 §三.2（未在址A落可机读通过审查档）· 豁免≠审查通过。
- [x] TC5 反回归：全量 pytest 零新增红 + 既有档 git diff 零（diff 窗仅新增 3 档：豁免 yaml / 规约档 / 本 task 自检回填 · done/ 与 reviews/ 133 档零触碰）。

**40 复核（2026-10-11 · 40-verify 棒 · 独立复核不轻信自述）**：**PASS · 可进 PR 队列**

- [x] V1 commit 链/diff 面：d704c35→72ab71f→db6aa53 三 commit diff=4 档（豁免 yaml/规约档/30 invoke/task 自检）· 全分支对 master cae745e 仅 9 档全 docs/ · done/ 与 reviews/ 零触碰 —— 最小面成立。
- [x] V2 verify 重跑：`npx --yes spec-wave@3.2.0 verify --target .` 重定向取 $? → EXIT=0 · VERIFY: PASS · 豁免命中 93 · invalid 0；抽验 3 档（inform-graph-backfill-w6-modules-trim 零审查档 · capability-gateway-p3/so-schema-hygiene 无结论节）缺口皆实证。
- [x] V3 TC3 反向实证 40 亲跑：藏豁免档 → EXIT=2 BLOCKED 缺口 93 → 恢复 → EXIT=0 PASS · 工作区零残留 —— 增量门禁预警力完整。
- [x] V4 TC4 诚实性：93 条目 reason 统一「存量基线豁免 · 未审」· authorized_by 93/93 A1 合规 · 规约档 §五 93 明细行对账。
- [x] V5 TC2/TC5：lint-wiki-delta EXIT=0 PASS 复跑 · TC5b 既有档零 diff · TC5a 由零代码 diff 构造性成立（分支与 master 代码面逐字节同一）。
- Nit 照登：30 invoke 思考轮 8 残留「（回填中）」占位语 · 不阻 PASS。

复核 commit 列：d704c35（豁免 yaml）· 72ab71f（双址规约+task 自检）· db6aa53（30 invoke）· 40 留痕 6092bcf（骨架）+ 本回填 commit（见 git log）。明细：docs/harness/invokes/by-task/specwave-verify-baseline/invoke_20261011_40_verify.md

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 落稿（**00 代笔** · 首棒卡滞 interrupt 留痕 · 授权 m01606 过程文档代签）：实跑真值 EXIT=2/93 缺口三类分账（52+36+5）· D1 倾向 C 混合 · 管道吞码坑钉 D3 · 三闸 pending |
| 2026-10-11 | B-1 修订（00 · commit fe51492）：E3 节名去编号+TC 勾选化 · E4 失败路径节 · E5 自检结论占位 · E8 wiki_delta 行 · 闸表 4 列化 · N-1 155→154 → R2 PASS-WITH-NITS（559d24a）· N-4 顺手吸收（节去编号+本行补录）· 三闸 00 代录 approved |
| 2026-10-11 | CLOSE（close/specwave-verify-baseline）：PR #228 MERGED（squash `5204330` · CI 绿）· 归档 done/ · 头部状态/验收勾选/本行回填 · CLOSE 文档 `docs/tasks/close/close_specwave_verify_baseline_20261011.md` + 50 invoke 落盘 · 审查文 R1/R2 按双址规约 §二 过渡期口径复制落址A（`docs/harness/reviews/task_specwave_verify_baseline_audit_R{1,2}_20261011.md` · 址B 原件不动）· README 双侧补登 · 质量钉：verify EXIT=0 PASS + task lint PASS（CLOSE 复跑） |
