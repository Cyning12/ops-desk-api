# Task：fix-delegation-pattern-fullmatch（委派令牌 pattern 约束 re.search → re.fullmatch · fail-closed 收紧）

- **状态**：active（已签收 · 2026-10-26 10-task 落稿 · 20-task-audit R1=fail 三项已 fixback · R2 复审 pass · 维护者人签 HG-TASK-DRAFT+HG-AUDIT-R1 → 可派 30）
- **类型**：bugfix（intentional behavior change：未锚定 pattern 语义由「包含一段」收紧为「整串匹配」· fail-closed 方向）
- **依据**：外部评审第三轮实弹复现 3/3 成立（00 已于 master 核实 · 见背景节）；bugfix 免 SPEC（承 harness-10-spec「bugfix 可跳过」先例）
- **分支**：本文件落盘时工作区在 `task/specwave-3-5-0`（别的任务分支 · 勿混入）；**30 开工须自 master 新建 `task/fix-delegation-pattern-fullmatch`**，禁直推 master，PR 前 `pytest tests` 绿 + `./scripts/graph-compile.sh` 过

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `fix-delegation-pattern-fullmatch` |
| **git_branch** | `task/fix-delegation-pattern-fullmatch`（30 开工自 master 切出 · 最新 base 30 按实钉锚） |
| **implement_repo** | ops-desk-api（本仓） |
| **spec** | n/a（bugfix · 问题/修法/验收由本文件承载；上游语义真值见 `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` :67 pattern 约束条目） |
| **test_strategy** | required |
| **test_strategy_note** | 红测先行：三条对抗用例先在 master 上复现红（search 放行）→ 改 fullmatch 转绿（TC3 取两态判别值 `"../../etc/passwd\n"`：search 放行 / fullmatch 拒 · python3 实证；原实弹值 `"../../etc/passwd"` 整串本即匹配宽字符集 pattern=字符集过宽独立问题 · out_of_scope 另 task）；正向防误伤 + 非 str 拒 + 既有委派验签测试零 diff（除语义本意改变者）；全量 `pytest tests` 绿；不打真模型（纯函数零 IO 可机断） |
| **code_quality_bar** | L2_backend（`docs/standards/CODING_BACKEND_L2_v1_zh.md`） |
| **graph_change_layer** | `none`（预期 · 单行语义收紧不增路由/表/一级模块/SSE 事件类型；G-L1 行内备注回写不构成层级变更） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` capability 行（:34）delegation 段备注补「参数约束 pattern=re.fullmatch 整串匹配（fail-closed 收紧 · 2026-10-26 fix-delegation-pattern-fullmatch）」+ 文末闸登记表新行；不新增一级模块 · 零新跨模块边 · 不增 implementedBy · 零新路由/表/SSE 事件类型 |
| **graph_delta_note** | 图谱义务=行内备注（承 SPEC Q3「不新增一级模块」与 delegation-naming-boundary 01_modules.md:130 先例）；30 实判越出（新行/新边/新事件类型）→ 回炉补签 HG-GRAPH-MODULES，禁 silent 扩 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 无 env/词表/规范层变更；pattern 语义收紧真值回写 01_modules.md 行内备注即可，不进 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default`（`docs/harness/invokes/by-task/fix-delegation-pattern-fullmatch/` · 本文件起草即建 10 invoke 骨架） |
| **experience_capture** | recommended |
| **kpi_aggregator** | n/a |
| **orchestration** | 10 落稿（本文件）→ 20-task-audit R1 → HG-AUDIT-R1 维护者人签 → 30（红测先行 · 自 master 切分支）→ 40 → PR+CI 绿（`pytest tests` + `./scripts/graph-compile.sh`）→ CLOSE |
| **freeze_id** | 拒绝码 R-a~R-f / 审计词表 / TTL 600s / 三档模式默认值 / SSE（`lg-rag-sse-v1`）/ HTTP（`lg-rag-http-v1`）**全零变更**；30 实判需动 → 回 00 升 freeze，禁 silent 扩 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 初稿人扫通过（维护者会话签收 2026-10-26 · 00 代录入表） |
| **HG-AUDIT-R1** | **approved** | **30** | 20-task-audit R1=fail（B1/B2/B3）已 fixback；R2 复审 pass（`docs/harness/reviews/task_fix_delegation_pattern_fullmatch_audit_R2_20261026.md`）；**维护者人签 2026-10-26**（会话明示「签收」· 00 代录入表） |
| HG-GRAPH-MODULES | approved | 30 | `graph_change_layer=none` 预期不再签（承 01_modules.md:130 delegation-naming-boundary「在册」签法先例 · 与 graph_delta 同源；「图谱在册/在册」签法首见 :112/:113 · 2026-09-30）；30 实判越出 → 回炉补签 |

---

## 背景与目标

### 问题

委派令牌 `param_constraints`（enum / max_len / pattern）是「本次派发的参数授权范围」，随令牌走、逐子任务签发；`pattern` 是其用正则锁参数值的手段。当前验签侧 `app/ops/capability/delegation.py` `check_param_constraints`（:289-307）的 pattern 分支（:303-306）：

```python
if _CONSTRAINT_PATTERN in rule and (
    not isinstance(value, str) or re.search(rule[_CONSTRAINT_PATTERN], value) is None
):
    return str(arg_name)
```

`re.search` 只要求串中「存在一段」匹配。约束作者未写锚点时闸门**静默放宽且无报错**——「看起来有闸的假门」，与本仓 `app/ops/capability/budget.py:103-105` 注释批判的 subtask 分桶假门同类。

外部评审第三轮实弹复现（00 已于 master 核实，全部成立）：

1. `pattern=\d+` + `value="123abc"` → 期望拒，实际放行（search 找到 `123`）
2. `pattern=^[a-z]+$` + `value="abc\n"` → 期望拒，实际放行（Python `$` 匹配换行前）
3. `pattern=^[\w./-]+$` + `value="../../etc/passwd"` → 期望拒，实际放行（**纯字符集过宽** · 与匹配函数无关：该值整串本即匹配此 pattern，python3 实证 fullmatch 下仍放行）——**本修法不治**，登记 `out_of_scope` 另 task（见文末）；对抗测试 TC3 改用两态判别值 `"../../etc/passwd\n"`（search 放行 / fullmatch 拒 · python3 实证）

**定性**：约束由 Host 签发侧声明（模型写不了 pattern），攻击面小，**非 P0 安全洞**；但假门比没门更危险，本次修复把锁从「虚掩」变为「整串匹配」，属 fail-closed 方向的收紧。

### 目标（修法）

1. `delegation.py:304` `re.search` → `re.fullmatch`（**一行**）。fullmatch 要求整串匹配，天然消解「缺锚点」与 `$` 匹配换行前两个坑，无需依赖作者写 `^...$`。
2. 同步检查模块 docstring / 注释中对 search 语义的描述，改为 fullmatch 语义（10 预扫：模块内无显式「search」字样——:248 节注释与 :290 docstring 未写匹配语义；30 按实复核，若补描述须写「整串匹配（fullmatch）」）。
3. **兼容性检查（R 轮必做项）**：`grep -rn "pattern" app/ops/capability/manifests/*.yaml` 与全仓 `param_constraints` 出现点。00 已预扫：manifests 无 pattern 键；`param_constraints` 仅出现于 `app/ops/capability/delegation.py`（:178,195,225,239,252,262,265,268,289,291,405,425,426,454,555）与 `tests/test_capability_delegation.py`、SPEC/task 文档。fullmatch 化把未锚定 pattern 语义从「包含」变为「整串」，**这正是修复意图**；若存量约束依赖 search 语义须显式改写并说明。委派令牌 TTL 600s 无持久化，无线上兼容负担。
4. **不受影响分支（不要动）**：enum 分支（:297）、max_len 分支（:299-302）。

---

## 范围

- [ ] `app/ops/capability/delegation.py:304` `re.search` → `re.fullmatch`（一行）
- [ ] 同步模块 docstring / 注释的匹配语义描述（若有；30 按实复核 :248 / :290）
- [ ] `tests/test_capability_delegation.py`（文件已确认存在）新增对抗测试，见验收 TC1–TC5
- [ ] R 轮兼容性 grep 复扫并对拍 00 预扫结果（漂移 → 回填本 task 再走 20 复审）
- [ ] 图谱行内备注回写（graph_delta 行）

## 非范围

- ❌ 改 enum 分支（`delegation.py:297`）/ max_len 分支（:299-302）
- ❌ 改签发侧 `validate_param_constraints`（`delegation.py:252`）
- ❌ 动委派三档模式开关与 `_delegation_gate`（`app/ops/capability/gateway.py:277-334`）
- ❌ 顺手「加固」任何其他闸层——发现新问题记入本节 out_of_scope 清单（另立 task）
- ❌ 改 TTL / 签名 / nonce / 审计词表 / 拒绝码（freeze 全零变更）
- ❌ **本起草阶段零 `app/` / `tests/` 改码**（仅 docs）
- ❌ 触碰工作区既有改动 `docs/arch-browser/dist/site-data.json`（别人分支的 M）

---

## 失败路径（failure_paths）

| ID | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----|----------|----------|--------|----------|
| FP-1 | 存量约束依赖 search「包含」语义（未锚定 pattern 预期子串通过） | fullmatch 化后由放行变拒（**修复意图**）；R 轮兼容性 grep 实证兜底：manifests 无 pattern 键 · `param_constraints` 仅 delegation.py + 测试/文档；30 复扫发现新出现点依赖 search 语义 → 显式改写并回填本 task 说明，**禁静默** | 是 | 调用方收 `REJECT_PARAM_VIOLATION`（字段名） |
| FP-2 | HG-AUDIT-R1 未签即 30 改码 | GATE_VERIFY **拒开工**（FRAGMENT_30_gate_verify） | 是 | — |
| FP-3 | 非 str 值（int / list / None）配 pattern 约束 | :304 前半分支 `not isinstance(value, str)` 语义不变 → 拒（TC5 钉死） | — | `REJECT_PARAM_VIOLATION` |
| FP-4 | 兼容性 grep 漏检 / 与 00 预扫漂移 | R 轮必做项：30 红测前重跑两条 grep 对拍；漂移 → 回填 task → 20 复审后再签 | 是 | — |
| FP-5 | 误改 enum / max_len 分支（非范围越界） | diff 评审拦；验收对照既有 enum/max_len 用例零 diff | 否 | — |
| FP-6 | 正向误伤（合法整串值被拒） | TC4 防误伤用例钉死：`d+`+"123"、`^[a-z]+$`+"abc" 必须通过 | 是 | — |

---

## 验收标准

新增对抗测试落在既有 `tests/test_capability_delegation.py`（已确认存在；既有 `test_constraint_pattern_pass_and_fail` :233-237 用 `^[0-9]+$` + "123"/"12a"，fullmatch 下**保持绿**，作零 diff 对照）：

- [ ] **TC1**：`pattern=\d+` + `value="123abc"` → **拒**（`verdict.ok is False` 且 `reject_class == REJECT_PARAM_VIOLATION` 且 `violated_field` 为该字段名）
- [ ] **TC2**：`pattern=^[a-z]+$` + `value="abc\n"` → **拒**
- [ ] **TC3**：`pattern=^[\w./-]+$` + `value="../../etc/passwd\n"` → **拒**（两态判别成立：search 放行 / fullmatch 拒 · python3 实证；原实弹值 `"../../etc/passwd"` 整串本即匹配此 pattern，fullmatch 下仍放行=字符集过宽独立问题 · 登记 out_of_scope 另 task）
- [ ] **TC4 正向防误伤**：`pattern=\d+` + `value="123"` → 通过；`pattern=^[a-z]+$` + `value="abc"` → 通过
- [ ] **TC5 非 str**：int / list / None 值配 pattern 约束 → 拒（:304 前半分支语义不变）
- [ ] **TC6 反回归全量**：`pytest tests` 全绿；既有委派验签测试零 diff（除语义本意改变者）；`ruff check` 触及路径绿
- [ ] **TC7 图谱回写**：01_modules.md capability 行备注 + 闸登记表新行落盘；`./scripts/graph-compile.sh` EXIT=0
- [ ] **TC8 lint 预检**：`npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` 通过（与 CI 真值 `.github/workflows/lint-wiki-delta.yml:39` `run:` 行逐字一致 · 钉版 @3.5.0）

## 依赖

- 分支：30 自 master 新建 `task/fix-delegation-pattern-fullmatch`（当前工作区 `task/specwave-3-5-0` 为别的任务分支，**勿在其上实施**；`docs/arch-browser/dist/site-data.json` 的 M 勿动）。
- 锚点（10 已亲读核实 · 行号 30 按实校正）：
  - `app/ops/capability/delegation.py:289-307` `check_param_constraints`（:303-306 pattern 分支 = 唯一改点；模块内 `re.search` 唯一出现于 :304，`re.compile` 于 :283 签发侧不受影响）
  - `app/ops/capability/delegation.py:248` 节注释 / :290 docstring（语义描述复核点）
  - `tests/test_capability_delegation.py:233-237`（既有 pattern 用例 · 零 diff 对照）
  - `app/ops/capability/gateway.py:277-334` `_delegation_gate`（**非范围** · 仅定位用）
  - `app/ops/capability/budget.py:103-105`（「假门」同类定性参照 · 只读）
  - `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md:67`（pattern 约束语义真值）
  - `docs/_tech_graph/l1/01_modules.md:34` capability 行（delegation 段备注回写点 · :130 delegation-naming-boundary 先例）

## 给执行帽的必读列表

1. 本 task 全文（含人工闸表 · **HG-AUDIT-R1=pending，维护者人签前 30 拒改码**）。
2. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（首输出闸扫描表）。
3. `app/ops/capability/delegation.py` 全文相关段（禁信转述 · 行号按实校正）。
4. `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` §约束子集（:67）。
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
6. 同类先例：`docs/tasks/done/task_supervisor_first_fail_closed.md`（fail-closed 收紧 + K7 旧测影响面清单纪律）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|-----------|----------------------|----------------|
| R0 | 目标=pattern 约束 fail-closed 收紧：`re.search`→`re.fullmatch` 一行 + 对抗测试；定性=非 P0 但「假门」必修 | false | — | — |
| R1 | 证据=外部评审第三轮实弹三条 search 下全放行（00 master 核实）：#1/#2 放宽机理=search 语义（本修法闭合），#3=**纯字符集过宽**（python3 实证 fullmatch 下仍放行 · 与匹配函数无关 · 登记 out_of_scope 另 task）；锚点亲读（:303-306 唯一改点 · 模块内 `re.search` 唯一）；兼容性预扫：manifests 无 pattern 键 · `param_constraints` 出现点已枚举 | false | — | 存量未锚定约束若依赖 search 语义将由放行变拒（=修复意图 · FP-1 兜底）；宽字符集路径穿越本修法不治（另 task） |
| R2 | 方案=fullmatch（一行）优于「强制作者写锚点」/「自动包 `^(?:...)$`」：fullmatch 天然消解缺锚点与 `$` 换行前两坑，不依赖作者纪律、不改 pattern 字符串（签名载荷零 diff） | false | — | `fullmatch` 与「作者已写 `^...$`」兼容（既有 :234 用例保绿） |
| R3 | 反例闭合：对抗用例覆盖本修法可治的两类放宽机理（TC1 子串命中 / TC2+TC3 `$` 换行前 · TC3 取两态判别值 `"../../etc/passwd\n"`）+ 正向防误伤 + 非 str 拒；宽字符集路径穿越（原实弹 #3）与匹配函数无关 → out_of_scope 另 task；enum/max_len 分支显式不动；**R 轮必做项=兼容性 grep 复扫对拍**（FP-4） | false | — | grep 漂移风险 → FP-4 回填+复审流程兜底 |
| R4 | 验收 TC1–TC8 全部可机断（纯函数零 IO · 不打真模型）；红测先行：三条对抗用例在 master 上先复现红再转绿 | false | — | — |
| R5 | 草稿可交 20-task-audit；**不可**当已签收 | false | — | **HG-AUDIT-R1=pending**（待 20 审 + 维护者人签 · 签前 30 拒改码） |

**actual_last_round**：R5

### R0 · 问题框定

pattern 是委派令牌锁参数值的正则手段；`re.search` 让未锚定 pattern 静默放宽为「包含」，闸门形同虚掩。修复方向唯一：fail-closed 收紧为整串匹配。

### R1 · 证据与审查

实弹三条在 search 下全部放行（00 于 master 核实）：#1（`\d+`+`"123abc"`）与 #2（`^[a-z]+$`+`"abc\n"`）放宽机理=search 语义，本修法闭合；**#3（`^[\w./-]+$`+`"../../etc/passwd"`）python3 实证 fullmatch 下仍放行——该值整串本即匹配宽字符集 pattern，放宽机理=纯字符集过宽，与匹配函数无关，本修法不治**（登记 out_of_scope 另 task；20-task-audit R1-B1 实证纠正）。改点定位唯一（:304 · 全模块唯一 `re.search`）；兼容性预扫完成（manifests 无 pattern · `param_constraints` 仅 delegation.py 十五处 + 测试/文档），无存量依赖 search 语义的声明面。

### R2 · 方案与定夺

fullmatch 一行修法 vs 备选：① 签发侧强制 `^...$` 锚点——把纪律推给作者，仍留人为缺口；② 验签侧自动包 `\A(?:...)\Z`——改写 pattern 字符串进签名载荷，canonical 面变大。fullmatch 不改 pattern 字面值、不依赖作者纪律、签名载荷零 diff，最优。

### R3 · 反例与边界

对抗用例覆盖本修法可治的两类放宽机理：TC1 子串命中（`\d+` 未锚定）、TC2/TC3 `$` 换行前（TC3 取两态判别值 `"../../etc/passwd\n"`：search 放行 / fullmatch 拒 · python3 实证）；**宽字符集路径穿越（原实弹 #3）与匹配函数无关，非本修法反例面**，登记 out_of_scope 另 task（签发侧校验面 · `delegation.py:252` 恰属本 task 非范围，印证应另立）。正向两例防误伤；非 str 前半分支语义不变（TC5）；enum/max_len 显式非范围；TTL 600s 无持久化 → 无线上兼容负担；存量声明面零 pattern → 语义收紧无真实破坏面。

### R4 · 验收/可测性

`test_strategy=required`；`check_param_constraints` 为纯函数零 IO，全部用例经 `_issue`/`_verify` 夹具机断（承 `tests/test_capability_delegation.py` 既有形态），红测先行（master 上先红），不打真模型。

### R5 · 收口

草稿交 20-task-audit；**HG-AUDIT-R1=pending**，维护者人签前 30 拒改码。本文件不授权改 `app/` / `tests/`。

### 自检结论（10-task · 2026-10-26）

- **范围/非范围互斥**：唯一改点 :304 与非范围（enum :297 / max_len :299-302 / 签发侧 :252 / `_delegation_gate` gateway.py:277-334）无重叠；「不顺手加固其他闸层」与非范围末条互锁。
- **每条验收可机断**：TC1–TC6 经既有 `_issue`/`_verify` 夹具断言；TC7 图谱回写 + graph-compile EXIT=0；TC8 lint-wiki-delta 预检；无人工判断项。
- **事实核验**：改点行 :303-306 亲读与背景转述逐字一致；模块内 `re.search` grep 唯一命中 :304；manifests pattern grep 零命中；`param_constraints` 十五处行号与预扫一致；budget.py:103-105 假门注释、gateway.py:277-334 `_delegation_gate`、tests 文件 :233-237 既有 pattern 用例均亲读成立。
- **既有用例影响面（K7 纪律）**：`tests/test_capability_delegation.py` 内 pattern 相关仅 :233-237（`^[0-9]+$` 已锚定 · fullmatch 下保绿 · 零 diff 对照）；其余 `param_constraints` 用例走 enum/max_len 分支不受影响；枚举外既有用例默认保绿。
- **闸纪律**：HG-AUDIT-R1=pending 在表 · R5 residual 同；本帽未改 `app/` / `tests/`、未动 `docs/arch-browser/dist/site-data.json`、未 git 任何操作。

### out_of_scope（发现的新问题登记 · 另立 task）

- **宽字符集 pattern 挡不住路径穿越**（原实弹 #3 · 20-task-audit R1-B1 实证登记）：`^[\w./-]+$` + `"../../etc/passwd"` 整串本即匹配，python3 实证 fullmatch 下仍放行——放宽机理=**纯字符集过宽**，与 search/fullmatch 无关，本 task 一行修法不治。后续方向（另立 task）：签发侧校验面加固（如 `validate_param_constraints` `delegation.py:252` 拒高风险字符集 pattern / 约束作者纪律 lint）——注意 :252 恰属本 task 非范围，印证应另立。
- （30/40 实施中发现的其他闸层问题登记于此，**本 task 不顺手修**）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-26 | 10-task 初稿：背景实弹三条 + fullmatch 一行修法 + 兼容性预扫结论落 R 轮必做项；验收 TC1–TC8；failure_paths FP-1~FP-6；HG-AUDIT-R1=pending 待人签 |
| 2026-10-26 | 维护者人签 HG-TASK-DRAFT + HG-AUDIT-R1（会话签收 · 00 代录入表）→ 可派 30 |
| 2026-10-26 | 10-task fixback（20-task-audit R1=fail 三项）：**B1** TC3 换两态判别值 `"../../etc/passwd\n"`（原值整串本即匹配宽字符集 pattern · python3 实证 fullmatch 下仍放行）+ 实弹 #3 归因去「+ search」改纯字符集过宽 + R1/R3 行与节改写 + test_strategy_note 对齐 + 宽字符集路径穿越登记 out_of_scope 另 task；**B2** TC8 钉版 `spec-wave@3.5.0`（与 lint-wiki-delta.yml:39 逐字一致）；**B3** HG-GRAPH-MODULES 承册锚点 :79 → :130（delegation-naming-boundary「在册」先例 · 首见 :112/:113）；纯文档增量 · 待 20-task-audit R2 复审 |
