# task_stage_w_write_expand 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_stage_w_write_expand.md`（master `910ae2b` · 220 行逐行 · 10 落稿 `agent/stage-w-task-split-dde653139625` + 签认 `461e525` + 列修复 `95026b2` 三段构成）
> **审查帽**：20-task-audit（R1 · 书面审 · 不改 task 实质内容 · **不代签**任何 human_gate · 未执行 30）
> **审查日期**：2026-11-05 · **审查时仓态**：master @ `910ae2b`（= PR #325 merge commit · CI 4/4 绿）
> **开窗授权**：issue #323 维护者 2026-11-05 令（comment `6651138647`）：「下一棒：20-task-audit R1 书面审（HG-AUDIT-R1 随档签），审毕停下来等 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸人签」
> **输入真值（全部实读）**：SPEC v0.1 正本（HG-SPEC-SIGNOFF approved · B1 已修订）· issue #323 签收链 · PR #325 全线程（lead 预审 `6650428109` · 10 起草方随签 `6650458696` · lead 代录核验 `6651135210`）· 上游 done task 链（`task_api_controlled_write_hitl` PR #303 + fix #307/#313-314/#319）
> **结论**：**PASS（内容零阻塞）**——承袭保真、闸表签认链合规、锚点全实证、验收可机断、思考轮闭合；非阻塞观察 4 条；**HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 维持 pending，待维护者人签（本帽不代签）**

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS · 零内容阻塞**——范围 D1–D4 / 非范围八条 / FP-1~FP-7 / A1–A8 逐块与 SPEC v0.1 对照保真；钉死契约 8 条覆盖 SPEC 设计纪律 6 条 + Q4 加载期断言（v0.1 B1 修订口径逐字在册）+ 独立写 tag；A2+ 增量显式化验收项（lead 预审要点③）防 30 漏项 |
| **签认链** HG-STAGE-W-EXPAND-DESIGN | **approved · 合规**——签认三元组在册（issue #323 维护者令 + PR #325 lead 预审 `6650428109` + 代录 commit `461e525`）；签认内容与 SPEC §4 Q1 建议序一致（S1 中签 · Q2 env 显式 opt-in 随签 · Q3 新表→修订表回填随签 · S2 另立独立 SPEC · S3 本波不碰）；维护者 issue #323 亲签确认（`6651138647`），非无授权自签；`95026b2` 仅补 blocks_hats 空单元格，签认内容逐字未动 |
| **流程闸** HG-TASK-DRAFT | `pending`（blocks 20-R1/30 · 待人签 · 本审查为其书面审交付） |
| **流程闸** HG-AUDIT-R1 | `pending`（本审查文落盘即其前置交付 · **随档人签**后方 approved） |
| **流程闸** HG-GRAPH-MODULES | `pending`（`graph_change_layer=G-L1` 行备注预估 · 30 回写回签 · 口径与 D4 一致） |
| SPEC 正本保真 | ✓ master 正本 vs 已签 `fa83be6` **零 diff**（`git diff 910ae2b fa83be6` 空） |
| lint 复跑 | `npx spec-wave@3.5.0 task lint --file docs/tasks/active/task_stage_w_write_expand.md` → **LINT: PASS** exit 0（2026-11-05 本帽复跑 ✓） |
| draft 洁净度 | ✓ PR #325 三文件全 docs（task 档 + SPEC 正本 + 10 invoke）；`app/` / `alembic/` / `tests/` 零触碰（PR files API 实证）；manifests/ 仍仅 builtin.v1.yaml + oa.readonly.v1.yaml + testing.v1.yaml（无提前实施） |
| 30 闸态实跑 | `npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_stage_w_write_expand.md` → **VERIFY: BLOCKED**（HG-AUDIT-R1/HG-TASK-DRAFT/HG-GRAPH-MODULES pending · HG-STAGE-W-EXPAND-DESIGN approved ✅）——与本审查结论一致，审毕停等三闸人签 |

本审查文按结论机读口径书写：「结论」起首节 · 通过词落节内 · 实质内容充足 · 无否定共现。

---

## 审查要点逐项核对

### 1. 承袭保真度（task 档 vs SPEC v0.1 · 逐块对照）✅

| SPEC v0.1 块 | task 档对应 | 核验 |
|--------------|-------------|------|
| §1 设计纪律 6 条 | 钉死契约 8 条 | ✅ ① 闸链零新建（复用 `tool_exec_node` · 不改 `blocked_by` 语义）② 判序零 diff（`_match_filter`/`policy.py` 闸序段逐字节零 diff · `deny_high_risk` 永不豁免）③ resume 单路径 ④ 租户封闭（`tenant_scoped: true` · F1–F6）⑤ 显式打开纪律（三层显式打开 · 默认零 diff）⑥ 幂等（顶层 `idempotency_key` 强制）——六条逐字承袭；⑦ 加载期断言（Q4 v0.1 B1 修订口径：**「除 mock 特例清单（`testing.write.echo`，以 `testing`/`mock` tag 为谓词）外，写能力 `tenant_scoped` 必须为 true；特例清单不扩容」**——与 SPEC §4 Q4 v0.1 句逐字一致，B1 阻塞已消）⑧ 首条写 tag 独立（SPEC D1「tags 含独立写 tag」提为独立钉死行）——拆行不提义，无新增约束 |
| §2 范围 D1–D4 | 范围 D1–D4 | ✅ D1 全要素在册（端到端链 write 级可逆→Policy→HITL→decide→resume→执行→审计 · manifest 字段族对齐范式 · `hitl.required: true` · 独立写 tag · ∩visible/allowlist「可达≠默认可达」）；D2 租户下推+负样本三枚；D3 只验不建+缺口走修订表；D4 G-L1 行备注+不新增一级模块——无漏项无越界 |
| §3 非范围 8 条 | 非范围 8 条 | ✅ 逐条一致（不多扩/不碰 irreversible/无自动改码合 PR/无 web UI/SSE 零改/闸链一行不动·jsonb 增键走修订表/无 OA·iOS·P/无生产数据）；task 第 6 条「→ 本档修订表回填」指代 task 档，指代清晰 |
| §5 FP-1~FP-7 | failure_paths FP-1~FP-7 + 闸行 | ✅ 七条逐条锚既有语义一致；FP-6 同标「仅 Q1=S2 时启用」（Q1=S1 已签 → 休眠条款，见 N3）；task 增「可重试/用户可见」两列与末行闸行（任一 pending 即 30 拒开工）——**列扩充与增行均为 task 层执行信息增量，不改 SPEC 裁定语义** |
| §6 A1–A8 | 验收 A1–A8 + **A2+** | ✅ A1–A8 逐条承袭（端到端竖切含 auto 模式 / 负样本组 / 租户三处一致 / 审计串链 / 反回归零 diff+grep / freeze 零破 / pytest+ruff+graph-compile / task lint）；**A2+ 为 task 层显式化增量**（SPEC §4 Q4 加载期断言列为独立验收项）——lead 预审要点③「防 30 漏项」，与 v0.1 B1 修订口径逐字一致，属签收链既定动作非越权 |
| §7 R0–R5 | 思考轮控制（承 · 不重开） | ✅ R0–R5 全轮承 SPEC 不重裁；控制表槽位/`actual_last_round`/`early_stop=no`/`residual_risks` 齐；task 层残余未定项唯一 Q1 已随 HG-STAGE-W-EXPAND-DESIGN 签署消解（residual_risks 行仍记「Q1 选型未签」系落稿时态，签认行已回填，见 N4） |
| §4 Q1 建议序 | HG-STAGE-W-EXPAND-DESIGN 签认内容 | ✅ 签 S1 = SPEC 建议序「S1 先行」一致；Q2 随签 env 显式 opt-in = Q2 建议裁定一致；Q3 随签新表→修订表回填 = Q3 口径一致；S2 另立独立 SPEC / S3 本波不碰 = SPEC 建议序一致 |

### 2. 闸表与签认链合规 ✅

| 核对点 | 裁定 |
|--------|------|
| 四闸齐 · 结构合规 | ✅ HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-STAGE-W-EXPAND-DESIGN 四行全在；blocks_hats 列经 `95026b2` 修复后 4 列对齐（代录行签认内容逐字未动，lead 线程 `6651135210` 已声明并复 lint） |
| HG-STAGE-W-EXPAND-DESIGN 签认依据 | ✅ 三元组在册：① issue #323 维护者 2026-11-05 令「Q1 留 task 闸随档裁决 · 类比 HG-STAGE-W-DESIGN 先例」② PR #325 lead 选型分析 `6650428109`（维护者代理人预审 · S1/S2/S3 收益代价成对 + 随签意见）③ 代录 commit `461e525` + 维护者 issue #323 亲签确认 `6651138647`——**授权链完整**（维护者令 → lead 代录 → 维护者确认），符合闸表签认「依据可溯」纪律；10 起草方随签回复 `6650458696` 明确「本草稿方回复不构成 human_gate 人签」，无角色混同 |
| 签认内容 vs SPEC 一致性 | ✅ S1 仓内落笔中签 / Q2 env 显式 opt-in / Q3 若需新表→修订表回填 alembic 义务 / S2 留作下一波独立 SPEC / S3 本波不碰——五项与 SPEC §4 Q1 表 + Q2/Q3 建议逐项一致，无越权扩签 |
| 余三闸 pending 三方一致 | ✅ task 状态行 / 人工闸表 / orchestration 行 / `spec-wave verify` 实跑输出 四方一致（VERIFY: BLOCKED · 仅 HG-STAGE-W-EXPAND-DESIGN approved） |
| HG-GRAPH-MODULES 口径 | ✅ 「预估 G-L1 行备注薄增量、不新增一级模块；30 交付时按实增量回写回签」——与 `graph_change_layer=G-L1` / `graph_delta`（`01_modules.md` capability 行一句备注）/ D4 三方互洽 |

### 3. 锚点实证（task 现状锚点表 10 行 + 钉死契约锚 · 本帽亲读 @910ae2b）✅

| 锚点 | 实证结果 |
|------|----------|
| 全仓唯一 write = `testing.write.echo` | ✅ `grep side_effect app/ops/capability/manifests/`：仅 testing.v1.yaml:28 = write；builtin.v1.yaml 五枚 :20-103 全 read；oa.readonly.v1.yaml 三枚 :31/:98/:159 全 read |
| testing.v1.yaml 字段族 | ✅ tags `[testing, mock, write]` :26 · `side_effect: write` :28 · `tenant_scoped: false` :30 · `hitl:` :31 · 顶层 `idempotency_key` :33——「mock 特例清单 + testing/mock tag 谓词」豁免口径的豁免对象实证成立（Q4/A2+ 断言按字面实现不会误杀） |
| `registry.py::_match_filter` deny 判序 | ✅ `deny_high_risk` :118 在 `deny_write` :120 前；docstring :110「只豁免 deny_write 一层 · deny_high_risk 永不豁免」；**行窗 :112-140 实读 :112-133**——语义全中，行号漂移承仓例（见 N1） |
| `types.py::WRITE_SIDE_EFFECTS` | ✅ :24 `frozenset({"write", "irreversible"})`——写判定词表挂点实证 |
| `policy.py` 闸序段 | ✅ :95 注释「危险程度 → 副作用 → 危险形态 → 输入完整性」在册——判序零 diff 的另一承载面 |
| `nodes.py` 审批闸 | ✅ `:314 _BLOCKED_BY_CAPABILITY_WRITE = "capability_write_hitl_required"` · 消费落点 :1900/:1912；write 孪生护栏 `:1217-1278`（`write_done_keys`/`write_replay_guard_skip`）在册（FP-4 运行期承载） |
| `gateway.py:1318` span `approval_id` | ✅ 逐行在册（D3 只验不建的审计串链落值面） |
| `router.py::_execute_decided_resume` | ✅ :493 唯一定义；`auto_resume` 同源惰性 import 复用（:554/:571 守卫链注释在册）——resume 单路径实证 |
| `admin/service.py::process_sync_payload` | ✅ :50 在册（S3 候选面；Q1=S1 后本波不消费，见 N2） |
| `01_modules.md` capability 行 | ✅ :34 行在册（G-L1 回写面；行内 2026-10-30 阶段 W 备注与 task 背景叙述一致） |
| SPEC 正本保真 | ✅ master `docs/spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md` vs 已签 `fa83be6` **零 diff**——lead 预审要点①复核成立 |

### 4. 元信息 / 四字段纪律 ✅

| 字段 | 核验 |
|------|------|
| `task_slug` / `git_branch` / `implement_repo` | ✅ `stage-w-write-expand` / `task/stage-w-write-expand`（base master）/ `ops-desk-api`——与 SPEC `invoke_slug`、invoke 目录、10 invoke 记录四方一致 |
| `test_strategy` + note | ✅ `required`；note 承 SPEC（pytest 为主 · 不连真外网 · S2 canned 条件句随 Q1=S1 休眠） |
| `code_quality_bar` | ✅ `L2_backend`（对齐 `docs/standards/CODING_BACKEND_L2_v1_zh.md`） |
| `graph_change_layer` / `graph_delta` / `graph_delta_note` | ✅ `G-L1` 行备注预估 + capability 行一句 + 30 实扫升 G-L2 口径 + HG-GRAPH-MODULES 随 30 回写回签——三处互洽 |
| `wiki_delta` | ✅ `n/a` + note（契约真值在 workspace · 本波不改 capability SPEC 备注面） |
| `review_hat` | ✅ `20`（符合 AGENTS.md「task 生产字段须含 graph_change_layer 与 review_hat（默认 20）」） |
| `required_invoke_hats` / `invoke_retention_profile` | ✅ `10,20,30,40` / `default` |
| `orchestration` | ✅ 链路「10 落稿 → 20-task-audit R1 → 维护者签四闸 → 30 → 40 → PR+CI 绿+merge → 图谱回写 → CLOSE」与本审查所在位置一致 |
| `freeze_id` | ✅ SSE `lg-rag-sse-v1` 零改 / web `hitl-browser-decide-v1` 稳定 / F1–F6 不破 / 倾向零 alembic + 新表走 Q1/Q3 修订表回填——与 SPEC 元信息一致 |
| 自检结论段 | ✅ 10 自检两命令（task lint / lint-wiki-delta PASS）在册；本帽复跑 task lint **PASS** 实证 |
| 修订表 | ✅ 两行（10 落稿 · HG-STAGE-W-EXPAND-DESIGN 签认 + 列修复声明），签认行含依据引用，符合四字段纪律 |

### 5. 验收可机断性 ✅

A1–A8 逐条可机断（承 20-spec-audit R1 对同套 A1–A8 的核验结论，本次复核无漂移）：A1 fixture 轨全链 / A2 负样本组五枚 / **A2+ 加载期断言为 loader 测试可机断言（豁免谓词写死：id ∈ {testing.write.echo} ∪ tags ∩ {testing, mock} → 跳过；断言其对 builtin/oa.readonly 全 read 面天然空转）** / A3 三处 tenant_id 一致 / A4 台账+span 落值 / A5 git diff 空 + grep 单路径 / A6 freeze 零破 / A7 pytest+ruff+graph-compile / A8 task lint——A2+ 为本审查重点复核项：断言谓词与 testing.v1.yaml 实字段（:26/:28/:30）精确互洽，**不存在 SPEC R1 B1 类自相矛盾残留**。

### 6. 思考轮闭合 ✅

控制表槽位 R0–R5 齐 · `actual_last_round: R5` · `early_stop: no` · `residual_risks` 回填；R0 实证锚（active 实扫 / 唯一 write = mock）与本审查 §3 独立复核一致；R5 残余「Q1 选型未签」已随 HG-STAGE-W-EXPAND-DESIGN 签署消解（签认行回填）——控制表正文仍记落稿时态，属档案性质非失洽（见 N4）。

---

## 非阻塞观察项（不阻塞签闸 · 不阻 30 · 供维护者/30 参考）

| # | 项 | 性质 |
|---|----|------|
| N1 | 现状锚点表 `registry.py::_match_filter（:112-140）` 行窗实读 :112-133 | 行号漂移 · 语义全中 · 承仓例「行号录自审查实证 · 30 按实校正」（同 SPEC R1 审查 N3 口径） |
| N2 | 给执行帽必读列表 item 7 仍含 `app/ops/admin/service.py`（S3 候选面） | Q1=S1 已签后本波不消费该锚点；系 SPEC §8 代码锚承袭（不重裁纪律），30 按 S1 范围执行即可，无需修订 |
| N3 | FP-6 与 test_strategy_note 中 S2 条件句（外部失败面 / canned adapter）随 Q1=S1 签署转为休眠条款 | 条件句保留 = 承袭不另裁，Q1 若复盘改裁 S2 时条款自动复用；30 零动作 |
| N4 | 思考轮控制表 residual_risks 仍记「Q1 选型未签」 | 系 10 落稿时态档案；签认行（修订表第二行）已回填 S1 签署事实，二者并存为时间序档案非矛盾 |

## 阻塞项

**无内容阻塞。**

## 回填清单

无（零内容阻塞 · 无退回 10-task 项 · 本审查不改 task 档实质）。

---

## 三闸签认建议（本帽不代签）

| 闸 | 建议 | 依据 |
|---|------|------|
| HG-TASK-DRAFT | 建议维护者人签 approved | 本审查 PASS（零内容阻塞）· task lint PASS · draft 洁净度实证 |
| HG-AUDIT-R1 | 建议维护者人签 approved（随档签） | 本审查文落盘即其前置交付；issue #323 令「HG-AUDIT-R1 随档签」 |
| HG-GRAPH-MODULES | 建议维护者人签 approved（口径签） | 预估 G-L1 行备注薄增量、不新增一级模块；30 交付时按实增量回写回签确认（D4 承载，闸表口径已在册） |

**审毕停等三闸人签**（issue #323 维护者令）：三闸签齐前 30 拒开工（`spec-wave verify` BLOCKED 实证）；签齐后下一棒 = 30 实扫（落笔目标表选型若须新表 → 修订表回填 alembic 义务，Q3 随签口径）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-11-05 | R1：task 档（master `910ae2b`）书面审——六项核对全绿（承袭保真 / 签认链合规 / 锚点 12 项实证 / 四字段纪律 / 验收可机断含 A2+ / 思考轮闭合）· **PASS 零内容阻塞**；非阻塞 N1–N4（行窗漂移 / S3 锚点休眠 / S2 条款休眠 / residual_risks 时态档案）；**HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 维持 pending 不代签**，审毕停等三闸人签（issue #323 维护者令） |
