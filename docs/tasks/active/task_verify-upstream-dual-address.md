# Task：verify-upstream-dual-address（spec-wave findLatestReview 支持址B `docs/audits/task-review/` · 上游根治 + 本仓双址纪律收口）

> **状态**：`draft`  
> **类型**：**upstream-chore**（上游 issue/PR 根治 + 本仓规约收口条件 · 本仓零 `app/` 改动 · `graph_change_layer=none`）  
> **依据**：`docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 3 项 + §4-3（机读纪律坑）· `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`（双址规约 v1 · 过渡方案已钉）  
> **分支**：`task/verify-upstream-dual-address`（base = master `286d825` · worktree `../ops-desk-api-worktrees/t-verify-upstream-dual-address`）  
> **上游仓**：`Cyning12/SpecWave`（github.com/Cyning12/SpecWave）· 本机 checkout `~/Desktop/Projects/dsh-coding-kit` · HEAD `fad4694`（2026-10-11 实证在案）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `verify_upstream_dual_address` |
| **git_branch** | `task/verify-upstream-dual-address` |
| **implement_repo** | 上游 `Cyning12/SpecWave`（本仓仅收口动作：钉版 bump + 规约修订 + verify 实证） |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 上游 PR 在上游仓自带单测（上游仓 `test/` 套件 · 址B 扫描+命名口径用例）；本仓侧零业务码，验收=收口实证（verify 重定向取真码）+ `pytest tests -q` 零新增红对拍 |
| **code_quality_bar** | `not_applicable`（本仓纯文档/配置面 · 上游实现遵循上游仓自身规范与 CI） |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 零图谱变更按实判：不新增路由/表/事件类型/一级模块；本仓改动面=钉版三处 + CONVENTION 规约档修订，均不触 `docs/_tech_graph/` 模块语义 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站（`docs/coding_wiki/`）条目变更；CONVENTION 档属仓级规约非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 上游 issue/PR（SpecWave 仓作业）→ 本仓收口（钉版 bump + 规约修订 + 实证）→ 40 → PR → CLOSE |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | pending | 20-R1, 30 | 初稿人扫（含思考轮 R0/R1 预置内容核真） |
| HG-AUDIT-R1 | pending | 30 | 20 R1 审查文落址A后人签（双址规约过渡期口径：审查文必须落 `docs/harness/reviews/`） |
| HG-GRAPH-MODULES | pending | 30 | `graph_change_layer=none` 按实判复核（零图谱面 · 人签「在册·无图谱变更」） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点 task |

---

## 背景与目标

spec-wave 仓级 verify 的审查门禁消费面 `findLatestReview` 只扫描 `docs/harness/reviews/` 与 `reviews/` 两址（址A），新审查存档址 `docs/audits/task-review/`（址B）**完全不入扫描面**——审查文只落址B时 verify 误报 `missing R<n> review` BLOCKED（误报两起在案：`task_hitl_auto_resume_claim_race`、B1/B2 两 task，见 CONVENTION §一）。过渡方案已钉：审查文必须落址A、可同时落址B（双址复制纪律），存量零挪零改。

**完成态行为**：上游 SpecWave 的 `findLatestReview`（及其同源消费面）支持址B 扫描与址B 命名口径，发版后本仓 bump 钉版、实证「址B 单落即绿」，并修订 CONVENTION 档解除双址复制强制纪律（收口条件逐条满足后生效）。

## 真实代码锚点（2026-10-11 实证 · 禁止漂移）

- 上游源码 `src/checks/review-gates.ts:92-114`（Cyning12/SpecWave @ `fad4694`）：`findLatestReview(target, taskFile)`；**:96** 行 `const dirs = [path.join(target, 'docs/harness/reviews'), path.join(target, 'reviews')]` ——扫描面写死两址，址B 不在内；**:99** 行命名 RE `/^(task_.+?)_audit_R(\d+)_.*\.md$/i`；**:116-119** `findReview` 为同一实现源的布尔投影（status / dry-run / verify 消费）。
- 同文件 **:46** 行：spec 审查扫描（`spec_reviews_retention`）同构双址写死——上游根治须一并评估。
- 本仓安装镜像（编译产物 · 行号与源码对齐）：`node_modules/spec-wave@3.0.1/lib/checks/review-gates.js:89-114`。
- 址B 命名口径 `YYYYMMDD_<slug>_r<n>.md`（CONVENTION §二表）与址A `task_<slug>_audit_R<n>_*.md` **不同构**：无 `task_` 前缀、日期前缀、小写 `_r<n>`——上游支持须同时扩扫描目录 + 识别第二命名口径（方案留 R2 裁定）。
- 本仓钉版三处（收口 bump 点）：`scripts/graph-compile.sh:28`（`GRAPH_CLI=spec-wave@3.0.1`）· `package.json:6`（`"spec-wave": "3.0.1"`）· `.github/workflows/lint-wiki-delta.yml:35`（CI npx 钉版）。钉版背景：3.2.0 `implementedBy` object schema 收紧曾断 CI（交接档 §4-4），bump 须带实证。

## 范围

- [ ] 上游 issue 立项（Cyning12/SpecWave issues）：问题描述 + 上述真实锚点 + 误报实证两起（CONVENTION §一）+ 期望行为（址B 入扫描面且命名口径可机读）
- [ ] 上游 PR：`findLatestReview`（及 `findReview` 同源面、spec 扫描面按 R3 裁定）支持 `docs/audits/task-review/` 扫描与址B 命名口径；上游自带单测覆盖新址+新命名；随上游发版
- [ ] 本仓收口条件（根治后执行 · 定义即本 task 交付物之一）：
  1. 钉版三处 bump 至含址B 支持的上游版本（版本号留档）
  2. 实证：址B 单落审查文（不落址A）时 `npx spec-wave verify --target .`（重定向取 `$?`）EXIT=0 PASS
  3. 修订 `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`：过渡期「必须落址A + 可双落」口径转为收口后口径，解除双址复制强制（修订记录落行）
  4. `AGENTS.md` / `CLAUDE.md` 若含双址相关表述同步修订

## 非范围

- 本仓零业务码改动（`app/` 零触碰 · 纯文档/配置面）
- 存量档零挪零改（CONVENTION 钉死契约：址A 133+ 档与址B 既有档原址原内容）
- `docs/harness/legacy-gate-exempt.yaml` 存量 93 档豁免口径不动（序3 已钉）
- 上游实现方案不在本 task 锁死（R2 思考轮裁定后落 issue/PR）
- harness / task / invoke 档不进上游 PR（upstream_pr 模板规约）
- 上游仓发版流程决策（属上游维护者）

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 上游 issue 被拒 / wontfix | 本仓双址复制纪律长期维持（CONVENTION 过渡期口径继续生效 · 无回归） | 是（换方案再提） | issue 讨论留痕 · 本 task 标 blocked 待维护者裁定 |
| 上游收址B 但不收 `YYYYMMDD_<slug>_r<n>` 命名口径 | 址B 既有档仍不命中 · 收口条件 2 不成立 · 规约维持双落强制 | 是（PR 评审协商或 R2 改裁定） | 上游 PR 评审 + 本 task 修订记录可见 |
| 收口 bump 后 verify / graph-compile 红（3.2.0 implementedBy 类回归） | 钉版回退 · 收口暂停 · 回上游报 regression | 是 | CI 红 + 钉版回退 commit |
| 未 bump 上游版本即提前解除双落纪律 | verify `missing R<n> review` 红（误报面复现 · 预期行为） | 是 | 补落址A 即复绿（CONVENTION §二-2） |
| 20 未签 `HG-AUDIT-R1` 即动收口 | 执行 Agent 拒开工 | 是 | 须先 20 审查 + 人签 |

---

## 验收标准

- [ ] `pytest tests -q` 零新增红（master 基线对拍 · 本仓零业务码构造性成立 + 亲跑留痕）
- [ ] `npx --yes spec-wave task lint-wiki-delta --target .` 通过（wiki_delta 预检 · n/a 恒绿口径）
- [ ] 上游 issue 开立（URL 落本 task 实现备忘 + invoke）
- [ ] 上游 PR 合入并发版（含址B 扫描 + 址B 命名口径单测 · 版本号落本 task）
- [ ] 收口实证：钉版三处 bump 后，址B 单落审查文（不落址A）`npx spec-wave verify --target . > /tmp/verify_closeout.log 2>&1; echo $?` → EXIT=0 PASS（反向实证：bump 前同档单落址B 必红 · 红绿对照留痕）
- [ ] CONVENTION 档修订落盘：过渡口径转收口口径 · 双址复制强制解除条件逐条勾选
- [ ] 既有档零挪零改：址A reviews 档与址B 既有档 git diff 零

---

## 思考轮

> 10 帽义务：预置 R0 + R1–R5 五槽 + 思考轮控制表；R0/R1 已由 10 帽真读实证预填，R2–R5 由执行链回填（禁止仅聊天输出）。

### 思考轮控制（Agent 填 · 20 审）

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 已填（10 帽 · 交接档/规约档/锚点真读） | no |
| R1 | 已填（10 帽 · 上游源码实证） | no |
| R2 | 待填（方案对比 · 见槽内种子） | no |
| R3 | 待填（边界/测试） | no |
| R4 | 待填（测试与 PR 策略） | no |
| R5 | 待填（图谱增量 + 关账判断） | no |

### R0 · 读 task / 交接档 / 规约档

**回填区：**

```text
（10 帽已填 · 2026-10-11）交接档 §2.2-3 立项 + §4-3 口径墙实证；CONVENTION v1 全文已读：
过渡期「审查文必须落址A、可同时落址B」为当前生效纪律；「上游若日后支持，本规约届时修订」为
本 task 收口依据；两起误报（hitl_auto_resume_claim_race · B1/B2）为 issue 实证素材。
```

### R1 · 代码事实

**回填区：**

```text
（10 帽已填 · 2026-10-11）上游 Cyning12/SpecWave @ fad4694 真读：
src/checks/review-gates.ts:96 扫描面写死 docs/harness/reviews + reviews 两址（址B 不在内）；
:99 命名 RE ^(task_.+?)_audit_R(d+)_.*.md$ 不收址B 命名 YYYYMMDD_<slug>_r<n>.md；
:116-119 findReview 布尔投影同一实现源；:46 spec 扫描面同构限制。
本仓钉版三处：scripts/graph-compile.sh:28 · package.json:6 · .github/workflows/lint-wiki-delta.yml:35
（钉 3.0.1 · 3.2.0 implementedBy schema 前科在案）。
```

### R2 · 方案对比

**回填区：**

```text
（待填 · 种子）甲：上游加第三址 + 第二命名 RE（最小面 · 与址B 现档直接兼容）；
乙：上游开可配置扫描目录/命名（通解 · 面大）；
丙：上游钉统一命名口径、址B 改命名迁档（违存量零挪零改契约 · 倾向否）。
须含：址A/址B 同名冲突取舍（按最高 R 轮取最新的既有语义跨址合并是否成立）。
```

### R3 · 边界 / 测试

**回填区：**

```text
（待填 · 种子）址B 目录不存在时零噪音（existsSync continue 同址A 口径）；slug 去 _v<n> 后缀
对址B 命名同样生效；spec 扫描面（review-gates.ts:46）是否一并扩址留裁定；
上游单测：址B 命中/址A+址B 双命中取最高 R/命名口径回归。
```

### R4 · 测试与 PR 策略

**回填区：**

```text
（待填 · 种子）上游 PR 带上游 test/ 用例；本仓收口红绿对照（bump 前址B 单落必红 →
bump 后必绿）；钉版 bump 单独 commit 便于回退。
```

### R5 · 图谱增量 + 关账判断

**回填区：**

```text
（待填 · 种子）graph_change_layer=none 预判：收口仅钉版 bump + 规约档修订，不触
docs/_tech_graph/ 模块语义；若收口形态偏离（如需脚本面改动）回 10 修订。
```

---

## 给执行帽的必读列表

1. `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`（双址规约全文 · 收口修订对象）
2. `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2-3 / §4-3 / §4-4
3. 上游源码 `src/checks/review-gates.ts`（Cyning12/SpecWave · 锚点见本 task「真实代码锚点」节）
4. `docs/harness/legacy-gate-exempt.yaml`（豁免机制 · 不动但须知其存在）
5. 本 task 关联先例：`docs/tasks/done/task_specwave_verify_baseline.md`（序3 · 双址规约立项 task）

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| 上游 issue | ⏳ | URL 回填 |
| 上游 PR / 版本 | ⏳ | PR 号 + 发版版本号回填 |
| 本仓钉版 bump | ⏳ | 三处 · 单独 commit |
| CONVENTION 修订 | ⏳ | 收口口径 |
| 收口红绿实证 | ⏳ | /tmp 日志留痕 |

---

## 测试策略（Harness）

**test_strategy**: `recommended`

- 上游实现面：上游仓自带单测（址B 扫描 + 命名口径用例）随 PR 交付
- 本仓面：零业务码；收口实证 = verify 红绿对照（重定向取真码）+ `pytest tests -q` 零新增红对拍

---

### 自检结论（执行者）

（30/40 回填）

---

### KPI（00）

（`kpi_aggregator: CLOSE` · 关账回溯填写）

---

### 经验总结

（关账填写）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 落稿（task/verify-upstream-dual-address worktree）：交接档 §2.2-3 立项 + CONVENTION v1 全文真读；上游源码锚点实证（Cyning12/SpecWave @ fad4694 · review-gates.ts:92-119/:46）；址B 命名不同构钉为 R2 种子；钉版三处收口点落锚；三闸 pending + HG-GRAPH-MODULES（none 按实判） |
