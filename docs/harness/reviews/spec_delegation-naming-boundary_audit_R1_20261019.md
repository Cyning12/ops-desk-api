# 20-spec-audit R1 书面审：SPEC-delegation-naming-boundary v0

> **hat_id**：20-spec-audit（R1 · 轻量路径：10-spec 思考轮 R0–R5 已内联 SPEC §8，单轮 R1）
> **审查对象**：`docs/spec/delegation-naming-boundary/SPEC-delegation-naming-boundary_v0.md`（draft · 182 行 · HG-SPEC-SIGNOFF=pending）
> **审查日期**：2026-10-19 · **审查人**：Harness 20-spec-audit（书面审 · 不改 SPEC 实质 · **不代签** HG-SPEC-SIGNOFF）
> **结论**：**conditional_pass（PASS-WITH-NITS）** · 三大委托重点全部实证通过 · 阻塞项 0 · **M1/M2 两处锚点措辞事实错误建议 10-spec 签前修订**（不改实质）· M3/N4/N5/N6 移交 00 起草 task 吸收 · **建议维护者在 M1/M2 修订（或明示移交 task 吸收）后可签 HG-SPEC-SIGNOFF**
> **实证复核范围**：SPEC 全文 182 行逐行 · 源码实读 `app/ops/capability/delegation.py` 全文（600 行）· `app/ops/lg_rag/multi/nodes.py:255-384 / :395-434 / :820-869 / :895-984 / :1258-1292 / :1322-1343 / :1558-1579` · `app/ops/capability/gateway.py:270-339`（含 `_prepare_call` 闸序 :337-348）· 全仓 grep `auto_approve_ok` / `_delegation_active` / `_guard_write_key` / `_write_success_call_keys` / 审计词表 / 拒绝码 / 「名实」「子代理 B」· 图谱 `docs/_tech_graph/l1/01_modules.md` capability/lg_rag 行 · 上游 SPEC `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` §4 Q3 · `tests/test_lg_rag_supervisor_capability_catalog.py:1-25`

## 一、三大委托重点核对

### 1. 委派令牌正名（D1）· **PASS**

| 核对点 | 实证 |
|---|---|
| `auto_approve_ok` 真实存在且语义=签发审批策略判定 | `app/ops/capability/delegation.py:479-505` 逐行实读：三条件（scope ⊆ 有效集 :496-497 / 全只读 :498-502 / 无 sandbox·cli :503-504）纯函数零 IO；docstring 自述「自动放行边界三条件」。「读起来像布尔开关、实为策略判定」的名实不符诊断成立 |
| 调用面有界（改名可收口） | 全仓 grep `auto_approve_ok`：代码侧仅 **2 处**——定义 `delegation.py:479` + 调用 `nodes.py:420`（`dl.auto_approve_ok([entry[0]], effective_scope=scope)`）；测试侧 3 处（`tests/test_capability_delegation.py:340/:354/:360`）+ 若干注释/文档引用。FP-1「全仓 grep 零残留」可机断，冲击面小 |
| 改名不留别名合理性 | 符号无对外冻结面（不进出 SSE/HTTP/审计词表），内部符号直改不留别名与 freeze_id 行自洽 |

### 2. write 孪生护栏解耦（D2）· **PASS（附 M3 锚点补挂建议）**

| 核对点 | 实证 |
|---|---|
| 护栏定义面 :825-865 | `_guard_write_key`（nodes.py:825-847 · write 类 canonical 键 · 非 write/序列化失败 → None 不护栏）+ `_write_success_call_keys`（:850-865 · 仅成功终态入索引）。区间逐行吻合 |
| 「仅在 `_delegation_active()` 为真时生效」语义 | **属实**，但耦合门控不在 :825-865 内：:903 `write_done_keys = _write_success_call_keys(done, by_id) if _delegation_active() else {}`、:931 / :970 `if _delegation_active() and str(row.get("type") or "") == "tool":` 三处。「关委派就关掉安全护栏」诊断实证成立（delegation 默认 off ⇒ 现网护栏默认不生效）→ 见 M3 |
| FP-2 唯一有意行为变化显式声明 | **四层显式**：D2 语义变化行「delegation off（默认）时护栏从『不生效』变为『生效』——本 SPEC **唯一的有意行为变化**」· §6 验收「invoke 显式声明唯一行为变化点（FP-2）」· R3 residual「FP-2 生产影响需维护者知情」· §7 风险表首行。声明义务闭合 |
| 新开关默认开 = fail-closed 方向 | D2「默认开——它是安全护栏」+ FP-7「env 非法值回退默认开」互锁；与非范围「三档默认值变化（delegation 维持默认 off）」不冲突（护栏开关 ≠ delegation 开关，边界划清） |
| FP-2/3/4 矩阵可测 | delegation 三档 × 护栏开关矩阵 + `write_replay_guard_skip`/`replay_of` 台账键（:941-942 实证在册）可作金样断言钩子，不依赖人工判断 |

### 3. 审计词表 / 拒绝码零变更可断言 · **PASS**

| 冻结面 | 实证 |
|---|---|
| 审计五动作词表 | `delegation.py:65-69`：`token_issued` / `token_issue_hitl_required` / `token_superseded` / `token_verified` / `token_rejected`（形如 `token_rejected:<class>`）——五个常量字符串，FP-6「diff 断言词表字符串」可机断 |
| 拒绝码 R-a~R-f | `delegation.py:55-62` 六类拒绝常量（R-a 伞含 no_token/signature_invalid/secret_missing · R-b out_of_set · R-c expired · R-d nonce_reused · R-e param_violation · R-f subject_mismatch）逐行在册 |
| TTL 默认值 | 令牌 `DEFAULT_TTL_SECONDS = 600`（:46）· HITL 消费 `DEFAULT_APPROVAL_CONSUMPTION_TTL_SECONDS = 3600`（nodes.py:271 · 域 [1,86400] :276-285）——非范围「不改 TTL 默认值（600s）/ HITL 消费 TTL（3600s）」锚定真值正确 |
| D1/D2 触碰面与冻结面无交集 | 改名面（符号名）与解耦面（nodes 门控行 + 新 env 键）均不触词表/拒绝码/TTL 常量；freeze_id 行「若 30 发现必须改任一对外词表 → 回本 SPEC 升 freeze」留了升级回路 |

## 二、锚点抽查（file:line 实测 vs SPEC 自述）

**一致 8/9 条**（逐行实读）：

| SPEC 锚点 | 实测 | 裁定 |
|---|---|---|
| `nodes.py:261-263` `_delegation_active` 三档默认 off | :261-263 逐字一致（`delegation_mode() != MODE_OFF` · docstring「默认 off」） | ✅ |
| `nodes.py:325-377` `_approval_consumed` HITL 消费门 | def :325 · 止 :377（`return False`）· fail-closed 注释在 :329-332 | ✅ |
| `nodes.py:400-426` 签发审批 `_delegation_issue_block_reason` | def :400 · `return f"委派签发需人工审批（{why}）"` :426 | ✅ |
| `nodes.py:825-865` write 孪生护栏 | :825-847 + :850-865 两函数填满区间 | ✅（门控行另见 M3） |
| `nodes.py:1264-1286` scope 声明∩裁剪 | 注释 :1264-1269 · 块 :1270-1286 | ✅ |
| `nodes.py:1328-1337` 分发签发 | 注释 :1328-1329 · 块 :1330-1337 | ✅ |
| `nodes.py:1564-1572` tool_exec 注入 | 注释 :1564-1565 · 块 :1566-1572 | ✅ |
| `gateway.py:277-334` 验签门在 lookup 之前 | `_delegation_gate` :277-334 逐行一致；闸序实证 `_prepare_call` :347-348「委派令牌验签门（lookup 之前）」先于注册表查询 | ✅ |
| `app/ops/delegation.py`（600 行纯函数零 LLM 零 IO） | **路径漂移**：全仓唯一命中 `app/ops/capability/delegation.py`；600 行 ✅ · 纯函数零 LLM 零 IO ✅（:1-24 docstring 自钉 · imports :28-37 仅 hashlib/hmac/json/logging/re/threading/time/uuid） | ❌ → M1 |

**附带发现**：历史审查文/task 引 `delegation.py:488-514` 为 `auto_approve_ok` 行段，现已漂移为 :479-505（文件演进所致）；本 SPEC 未引该符号行号，不受影响——仅提示后续文档引用需按现状校准。

## 三、结构核对表（范围 / 非范围 / 验收 / failure_paths / 思考轮）

| 项 | 裁定 | 摘要 |
|---|---|---|
| 现状锚点真实性 | ⚠️ 8/9 | 见上表；M1 一处路径漂移，其余全部实证无虚构 |
| 范围 D1/D2/D3 内聚 | ✅ | 三块同属「名实一致」最小成本路径：D1 正名（符号）· D2 解耦（安全语义修复）· D3 写实（图谱备注）；任一单做均不闭合（B 案「只改文档」弃选理由机制性成立——护栏挂错开关是实际安全语义问题） |
| 非范围与范围互斥 | ✅ | §3 六条与 D1–D3 无重叠；「不改类型名/文件名/目录层级」与 D3 互锁；「不改词表/拒绝码/TTL/三档默认值」与 freeze_id、FP-6 三方互锁；worktree 脏改动显式排除 |
| 验收可机断 | ✅ | 六条全部机器可判：grep 零残留 / 三档×开关矩阵金样 / diff 词表断言 / 图谱备注文本 / invoke 声明存在性 / 无新模块·路由·表·event_type |
| failure_paths 充分 | ✅ | FP-1~FP-7 覆盖：改名残留 / 行为变化点（FP-2 金样）/ enforce 回归 / 护栏关断 / 改名等价 / 词表零变更 / env 非法 fail-closed。矩阵维度（delegation 三档 × 护栏开关）与 D2 目标一一对应 |
| R0–R5 思考轮闭合 | ✅ | §8 表 + 各轮小节齐全；`actual_last_round=R5`；early_stop 全 no；R5 reason=「人签未发生」、residual=`HG-SPEC-SIGNOFF=pending` 诚实标记；R2 四案三弃一采各有机制性理由 |
| 人工闸纪律 | ✅ | HG-SPEC-SIGNOFF=pending 在表；SPEC R5 自声明「本文件不授权改 app/」；本帽不代签 |
| 零行为变更铁律（除 FP-2） | ✅ | D1 纯改名（FP-1/FP-5 等价断言）· D3 纯文档 · D2 是唯一语义变化且四层显式声明；既有测试「逐字不改（除符号名同步）全绿」是重构铁律的机器化表达，可机断 |

## 四、问题清单

### 中等（建议 10-spec 签前修订锚点措辞 · 不改实质）

| ID | 位置 | 内容 |
|---|---|---|
| **M1** | SPEC :8（现状锚点首条） | `app/ops/delegation.py` → 实际路径 `app/ops/capability/delegation.py`（glob 全仓唯一命中）。SPEC :10 同块 gateway 路径写对了，更衬出 :8 为漂移；且本 SPEC 主题恰是该模块的「名实」——锚块首条路径失真应签前修正 |
| **M2** | 元信息表 :26 · D3 :81 · 验收 :127（共 3 处） | 「`01_modules.md` **delegation 行**备注」——图谱实证**无 delegation 独立行**：host-v1 SPEC §4 Q3 裁定图谱义务落 `capability` 行 + `lg_rag` 行备注（`01_modules.md:34` capability 行在册实证，delegation 令牌备注挂 capability 行内）。措辞应改「capability 行 delegation 备注段（+ lg_rag 行接线备注如需）」，否则 30 按字面找「delegation 行」会扑空或违规新增行 |

### 非阻塞 nits（移交 00 起草 task 吸收）

| ID | 位置 | 内容 |
|---|---|---|
| N3 | D2 现状行 :72 | 护栏「仅在 `_delegation_active()` 为真时生效」语义实证为真，但耦合门控在 **nodes.py:903 / :931 / :970** 三处（:903 条件建索引 · :931/:970 `if _delegation_active() and ...`），不在所引 :825-865 内。解耦真正要改的正是这三行——建议 task 现状锚点表显式点名，30 免重新定位 |
| N4 | :48 / :88 / :101（共 3 处） | 「SPEC §4 Q3 已裁定不新增一级模块」为 dangling 引用：本 SPEC §4 是方案对比表无 Q3；真值在 `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` §4 Q3（:155-162 裁定 S1 不入新一级模块 · 已实证）。建议补出处「（承 host-v1-delegation-token SPEC §4 Q3）」 |
| N5 | :5 上游行 · R0 :159 | 「2026-10-19 委派令牌模块名实审查（子代理 B 报告）」**未落盘**（全仓 grep「名实/子代理 B/超名」仅命中本 SPEC 自身）；10 项超名清单唯一载体是本 SPEC §1 转述。可追溯性弱——建议补落盘审查报告，或在 SPEC 注明「上游报告未落盘，以本 SPEC §1 为唯一转述真值」 |
| N6 | :41 | worktree 脏改动声明「`tests/test_lg_rag_supervisor_capability_catalog.py:14` 重复 import `SupervisorPlanError`」——本仓 master 实证：`SupervisorPlanError` 单次 import 在 **:15**（:14 是 `_SUPERVISOR_CAP_FILTER`），无重复。该声明指向 delegation-echo worktree 分支状态，本 checkout 不可证；非范围项，仅精度提示（若维护者知情可不改） |

## 五、HG-SPEC-SIGNOFF 建议

**conditional_pass**：范围/非范围/验收/failure_paths/思考轮五面全部闭合且实证；三大委托重点（正名可收口 · 护栏解耦语义属实且 FP-2 四层显式声明 · 词表/拒绝码零变更可机断）全部通过。M1/M2 为锚块事实性措辞错误，**建议 10-spec 做一轮锚点修订（v0 修订记录追加，不动实质）后维护者签署**；若维护者认为可移交 task 阶段吸收（00 起草 task 时在现状锚点表内改正），亦可直签。N3–N6 不阻塞人签。本帽**不代签**；人签前维持：不出 task / 不改码 / 30 拒开工。

## 六、下一棒

人签（或维护者授权）→ **00 起草 task**（slug=`delegation-naming-boundary`，分支 `task/delegation-naming-boundary`）：
1. 吸收 M1/M2/N3–N6 进 task 现状锚点表与验收（尤其 N3：护栏门控三行 nodes.py:903/:931/:970 显式点名）；
2. D2 新护栏开关 env 键名 task 阶段裁定（SPEC 已留口「task 阶段定键名」），默认开 + FP-7 非法值回退默认开；
3. 补 `docs/harness/invokes/by-task/delegation-naming-boundary/` invoke（含 FP-2 唯一行为变化点显式声明——SPEC §6 验收条已挂此义务）；
4. task 草稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30。

---

## 修订记录

| 日期 | 摘要 |
|---|---|
| 2026-10-19 | R1：conditional_pass · 锚点实测 8/9 一致（M1 路径漂移）· M1/M2 签前修订建议 · N3–N6 移交 task · 建议维护者可签 HG-SPEC-SIGNOFF |

---

## R2 复核（2026-10-19）

> **触发**：10-spec 完成 v0.1（M1/M2/N4 修订），00 代转复核请求。
> **范围**：窄幅复核——实测 M1/M2/N4 闭合 + 修订面无夹带 + 裁定修订方范围外发现的第 4 处 Q3 引用（:159）。
> **复核人**：Harness 20-spec-audit（仍不改 SPEC · 不代签）。

### 修订闭合实测（v0 → v0.1，全文 182→183 行）

| 项 | 实测 | 裁定 |
|---|---|---|
| M1 路径正名 | :8 已改 `app/ops/capability/delegation.py`；全 SPEC grep `app/ops/delegation.py` **零残留** | ✅ 闭合 |
| M2 图谱行措辞 | :26 / :81 / :127 三处均改「`01_modules.md` capability 行 delegation 备注段（+ lg_rag 行接线备注如需）」；grep 裸「delegation 行」**零残留** | ✅ 闭合 |
| N4 Q3 出处 | :48 / :88 / :101 三处均补「承 host-v1-delegation-token SPEC §4 Q3」（:48 含完整路径 `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`） | ✅ 闭合 |
| 修订面无夹带 | 标题升 v0.1 · 状态行 `draft`（HG-SPEC-SIGNOFF=pending）未动 · 人工闸表 pending 未动 · §9 仅追加一行 v0.1 修订记录 · 其余各行与 R1 实读版本逐行一致 | ✅ 无夹带 |

### 第 4 处 Q3 引用（:159 · §8 R0 小节）裁定

:159「SPEC §4 Q3 不新增一级模块的既有裁定」与 N4 同类 dangling 引用，但位于 **R0 思考轮叙述小节**（历史记录性质，非规范面：范围/非范围/验收/failure_paths 均不引它）。裁定：**立 N7，非阻塞**——建议 10-spec 顺手补「承 host-v1-delegation-token」前缀保持全文一致（一行修订），或移交 task 阶段吸收；**不阻塞 HG-SPEC-SIGNOFF**。

### R2 最终结论

**pass**。R1 签署条件（M1/M2）全部闭合，N4 闭合，修订面无夹带；残留 N3/N5/N6/N7 均为非阻塞，移交 00 起草 task 吸收。**建议维护者可签 HG-SPEC-SIGNOFF**。本帽不代签。

| 日期 | 摘要 |
|---|---|
| 2026-10-19 | R2：v0.1 窄幅复核 M1/M2/N4 全闭合 · 无夹带 · :159 立 N7（非阻塞）· 结论升 **pass** |
