# SPEC：委派令牌正名与边界清理（v0.1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-10-19 维护者会话签收 · 20-spec-audit R2 pass）
> **track**：`refactor`（命名与边界归位，**零行为变更**铁律；不新增路由 / 表 / event_type / 一级模块）
> **上游**：2026-10-19 委派令牌模块名实审查（子代理 B 报告）：模块实际职责远超「令牌」二字，含 10 项超名功能；其中最名实不符的是 write 孪生护栏挂在 delegation 开关下
> **建议序**：**4/5**
> **现状锚点**：
> - `app/ops/capability/delegation.py`（600 行，纯函数零 LLM 零 IO）：令牌模型/签名验签/nonce registry/签发器 supersede/`auto_approve_ok` 签发审批/审计五动作词表；
> - 图内接线 `app/ops/lg_rag/multi/nodes.py`：`_approval_consumed` HITL 消费门（:325-377）、签发审批（:400-426）、scope 声明∩裁剪（:1264-1286）、分发签发（:1328-1337）、tool_exec 注入（:1564-1572）、**write 孪生护栏（:825-865）**；
> - 验签门 `app/ops/capability/gateway.py:277-334`（在 lookup 之前）；
> - 三档 `off/observe/enforce` **默认 off**（`nodes.py:261-263`）。
> **下游**：20-spec-audit / HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `delegation-naming-boundary` |
| **invoke_slug** | `delegation-naming-boundary` |
| **test_strategy** | `required` |
| **test_strategy_note** | 重构铁律：既有测试**逐字不改**全绿（除 import 路径/符号名同步）· write 护栏解耦后独立开关三档行为断言（delegation off 时护栏仍生效）· 行为等价金样（同输入同审计词表同拒绝码 R-a~R-f） |
| **默认分支** | `task/delegation-naming-boundary` |
| **graph_change_layer** | `none` 预期（符号重命名 + 内部归属移动；`01_modules.md` capability 行 delegation 备注段（+ lg_rag 行接线备注如需）更新职责边界描述） |
| **freeze_id** | 委派审计五动作词表 / 拒绝码 R-a~R-f / SSE / HTTP **全部零变更**；若 30 发现必须改任一对外词表 → 回本 SPEC 升 freeze |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved（2026-10-19 维护者） | 维护者会话签收；审查文 `spec_delegation-naming-boundary_audit_R1_20261019`（R2 pass · N3/N5/N6/N7 移交 task 吸收 · FP-2 唯一行为变化签署知情） |

---

## 1. 背景与目标

名实审查结论（2026-10-19）：

- **纠偏**：委派令牌不是 delegation-echo worktree 新增——由 commit `da3ffc8`（Host V1-A）已在 master；worktree 仅文档面改动（外加一处脏改动：`tests/test_lg_rag_supervisor_capability_catalog.py:14` 重复 import `SupervisorPlanError`，在 worktree 分支上顺手修，不在本 SPEC 范围）。
- **坐实**：模块功能超名 10 项——审计台账、签发审批策略、HITL 消费门、scope 收窄、supersede 生命周期、nonce 防重放、write 孪生护栏、参数约束引擎、三档灰度、主体身份绑定。

审查裁定的最小成本路径（本 SPEC 落地）：

1. `auto_approve_ok` 正名——它实际是「签发审批策略」判定，名字读起来像布尔开关；
2. **write 孪生护栏从 delegation 开关解耦**——它是反回环/反自引用护栏（防 write 类子任务孪生重复），本质独立于委派令牌，挂在 `delegation_mode()!=off` 下导致「关委派就关掉了一个安全护栏」，是最名实不符的一处；
3. 其余 8 项超名功能**不动结构**（承 host-v1-delegation-token SPEC §4 Q3 已裁定不新增一级模块，出处：`docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` §4 Q3），只在图谱备注把职责边界写实。

### 一句话目标

正名 + 护栏解耦 + 图谱备注写实，**零行为变更**（除护栏获得独立开关这一语义修复）；类型名 `DelegationToken` 不改，不新增一级模块。

---

## 2. 范围

单 task。

### D1 · `auto_approve_ok` 正名

| 项 | 约定 |
|---|---|
| 改名 | `auto_approve_ok` → `issuance_policy_allows`（或 task 阶段选定的等价名，语义=签发策略判定）；全部调用点同步 |
| 兼容 | 内部符号无对外冻结面，直接改名不留别名（grep 全仓零残留断言） |
| 文档 | delegation 模块 docstring 更新职责清单 |

### D2 · write 孪生护栏解耦

| 项 | 约定 |
|---|---|
| 现状 | 护栏（`nodes.py:825-865`）仅在 `_delegation_active()` 为真时生效 |
| 目标 | 护栏有**自己的开关**（env 三档或布尔，task 阶段定键名，**默认开**——它是安全护栏），不再依赖 delegation 开关 |
| 语义变化 | delegation off（默认）时护栏从「不生效」变为「生效」——这是本 SPEC **唯一的有意行为变化**，属安全修复；必须在 invoke 与图谱备注显式声明 |
| 回归 | 护栏触发/不触发金样在三档 delegation × 开关矩阵下断言 |

### D3 · 职责边界写实（图谱备注）

| 项 | 约定 |
|---|---|
| 图谱 | `01_modules.md` capability 行 delegation 备注段（+ lg_rag 行接线备注如需）补齐 10 项实际职责（审计台账/签发审批/HITL 消费门/scope 收窄/supersede/nonce/write 护栏解耦后位置/参数约束/三档/主体绑定） |
| 不改 | `DelegationToken` 类型名、模块文件名、目录层级 |

---

## 3. 非范围

- ❌ 新增一级模块（承 host-v1-delegation-token SPEC §4 Q3 已裁定）
- ❌ 委派预算、跨进程 nonce/单飞、回执联动、撤销列表（审查点名的「未做」项，均为后续波次另案）
- ❌ worktree 脏改动（重复 import）——在 worktree 分支自行修复
- ❌ 改审计五动作词表 / 拒绝码 R-a~R-f / TTL 默认值（600s）/ HITL 消费 TTL（3600s）
- ❌ 三档默认值变化（delegation 维持默认 off）
- ❌ 其他 strategy/nodes 目录的顺手清理

---

## 4. 方案对比（R2 落盘）

| 方案 | 内容 | 裁定 |
|---|---|---|
| A 全面拆模块 | 按 10 项职责拆多个一级模块 | **弃**。承 host-v1-delegation-token SPEC §4 Q3 已裁定；动静大收益小 |
| B 只改文档 | 图谱备注写实，代码不动 | **弃（单独做不够）**。write 护栏挂错开关是实际安全语义问题，不只是文档问题 |
| C 本 SPEC：正名+解耦+写实 | 最小成本路径 | **采纳** |
| D 改 `DelegationToken` 类型名 | 连类型一起正名 | **弃**。类型名本身准确（它确实是令牌模型），超名的是模块职责不是类型 |

---

## 5. failure_paths

| ID | 路径 | 期望 |
|---|---|---|
| FP-1 | 改名后全仓 grep | `auto_approve_ok` 零残留；既有测试除符号名同步外逐字不改全绿 |
| FP-2 | delegation off（默认）+ 护栏开关开（默认） | write 孪生护栏**生效**（相对现网的行为变化点，金样断言） |
| FP-3 | delegation enforce + 护栏开关开 | 行为与现网一致（回归） |
| FP-4 | 护栏开关关 | 护栏不生效，无论 delegation 档位 |
| FP-5 | 签发审批判定 | 同输入同结果（改名等价断言） |
| FP-6 | 审计词表 / 拒绝码 | 零变更（diff 断言词表字符串） |
| FP-7 | env 非法值（新护栏开关） | 回退默认开（安全方向 fail-closed） |

---

## 6. 验收

- [ ] `auto_approve_ok` 全仓零残留，调用点同步，测试绿
- [ ] write 孪生护栏独立开关默认开；FP-2/3/4 矩阵断言绿
- [ ] 审计词表/拒绝码/TTL 默认值零变更断言
- [ ] `01_modules.md` capability 行 delegation 备注段（+ lg_rag 行接线备注如需）写实（10 项职责 + 护栏解耦声明）
- [ ] invoke 显式声明唯一行为变化点（FP-2）
- [ ] 不增一级模块/路由/表/event_type

---

## 7. 风险

| 风险 | 缓解 |
|---|---|
| FP-2 行为变化在生产意外触发护栏 | delegation 默认 off 意味着 write 类子任务本就稀少；护栏是安全方向；invoke 声明 + 图谱备注 |
| 改名漏调用点 | FP-1 grep 零残留断言 + 编译/测试全绿 |
| 「正名」扩大成「重构」 | SPEC 非范围钉死；20-task-audit 核对 diff 面 |

回滚：git revert（除 FP-2 语义修复外全部等价）。

---

## 8. 思考轮控制

| 轮 | 结论 | early_stop | reason | residual_risks |
|---|---|---|---|---|
| R0 | 名实审查裁定最小成本路径 | no | | |
| R1 | 范围=正名+护栏解耦+图谱写实；拆模块/未做项/worktree 脏改动非范围 | no | | |
| R2 | 采纳 C；弃全面拆模块/只改文档/改类型名 | no | | |
| R3 | 唯一行为变化=护栏独立生效（安全方向，fail-closed 默认开） | no | | FP-2 生产影响需维护者知情 |
| R4 | 等价断言 + 矩阵金样可全测 | no | | |
| R5 | draft 可交 20-spec-audit | no | 人签未发生 | HG-SPEC-SIGNOFF=pending |

`actual_last_round`：R5

### R0
子代理 B 报告：10 项超名功能清单；write 护栏最名实不符；SPEC §4 Q3 不新增一级模块的既有裁定。

### R1
成功=名实一致且护栏不再被无关开关连坐；失败=重构扩大化或行为漂移。

### R2
见 §4。

### R3
安全：护栏默认开是 fail-closed 方向；其余全部等价。

### R4
`test_strategy=required`；测试逐字不改是重构铁律的机器化表达。

### R5
本文件不授权改 `app/`。下一棒：20-spec-audit 或维护者人签 → 00 起草 task。

---

## 9. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-19 | v0 draft：委派令牌名实审查落盘（正名 + write 护栏解耦 + 图谱写实 · 零行为变更铁律除 FP-2） |
| 2026-10-19 | v0.1：20-spec-audit R1 建议修订（M1 路径正名 `app/ops/capability/delegation.py` · M2 图谱行措辞 capability+lg_rag 行 · N4 Q3 出处补引 · 审查文 `spec_delegation-naming-boundary_audit_R1_20261019`） |
| 2026-10-19 | HG-SPEC-SIGNOFF=approved（维护者会话签收 · R2 pass · N3/N5/N6/N7 移交 task）；交 00 起草 task |
