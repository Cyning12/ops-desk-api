# Task：delegation-naming-boundary（委派令牌正名 + write 护栏解耦 · FP-2 唯一有意行为变化）

- **状态**：draft v0.2（2026-10-20 10-task 修订 · 20-task-audit R1=conditional_pass M1–M3 签前闭合（审查文 \`docs/harness/reviews/task_delegation_naming_boundary_audit_R1_20261020.md\`）· 待 R2/HG-AUDIT-R1 → 30）
- **类型**：refactor（纯符号正名 · 无 deprecation 过渡）+ **intentional behavior change（FP-2 护栏默认开 · 唯一）**
- **依据**：`docs/spec/delegation-naming-boundary/SPEC-delegation-naming-boundary_v0.md`（v0.1 · **signed · HG-SPEC-SIGNOFF=approved 2026-10-19 维护者**）+ `docs/harness/reviews/spec_delegation-naming-boundary_audit_R1_20261019.md`（R1 conditional_pass 阻塞 0 · 锚点 8/9 → v0.1 闭合 → R2 pass）
- **建议序**：4/5（query-coref-rewrite 已合 PR #284 · memory-injection-consumer 已合 PR #285 · scenario-stage-rewire 已合 PR #286 → **本 task** → tech-graph-flow-resync）
- **分支**：本文件落盘于文档线 `docs/task-delegation-naming-boundary`（自 master `31924af` 切出）；30 开工分支 `task/delegation-naming-boundary`（30 开工前自 master 另行切出 · 勿与文档线混用）

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `delegation-naming-boundary` |
| **git_branch** | `task/delegation-naming-boundary`（30 开工自 master 切出 · 最新 base 30 按实钉锚） |
| **implement_repo** | ops-desk-api（本仓） |
| **spec** | `docs/spec/delegation-naming-boundary/SPEC-delegation-naming-boundary_v0.md`（v0.1 signed） |
| **test_strategy** | required |
| **test_strategy_note** | 既有测试逐字不改全绿（仅符号名同步例外）+ 新增护栏开关矩阵/默认开拦截/env 非法回退断言 + diff 白名单 _resolve_base 式四态基线锚点测试；不打真模型；全量 pytest 绿 |
| **code_quality_bar** | L2_backend |
| **graph_change_layer** | none（预期 · 图谱 G-L1 行内备注回写不构成层级变更） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` capability 行（:34）delegation 备注段写实 10 项职责 + lg_rag 行（:35）T1 备注正名同步 + 护栏解耦/新开关/FP-2 声明 + 闸登记表新行；不新增一级模块 · 零新跨模块边 · 不增 implementedBy · 零新路由/表/SSE 事件类型 |
| **graph_delta_note** | 口径承上游 `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` §4 Q3（S1 不新增一级模块 · 图谱义务=行内备注）+ T1 闸登记先例（01_modules.md:116）；30 实判越出 → 回炉补签 HG-GRAPH-MODULES |
| **wiki_delta** | `docs/guides/GUIDE_env_inventory_v1.md`（lg_rag 段补登记 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 新键） |
| **wiki_delta_note** | env 台账登记属 D2 范围；无 WikiTrack 读序/规范层变更 |
| **review_hat** | 20 |
| **required_invoke_hats** | 10,20,30,40 |
| **invoke_retention_profile** | default（`docs/harness/invokes/by-task/delegation-naming-boundary/` · 本文件起草即建目录占位） |
| **experience_capture** | required |
| **kpi_aggregator** | n/a |
| **orchestration** | 10 落稿（本文件）→ 20-task-audit R1 → HG-AUDIT-R1（维护者已授权 00 代签后续文档闸 · 落闸动作在 20-task-audit 之后由 00 执行，起草时 pending）→ 30（红测先行 · 正名+解耦实施）→ 40 → PR+CI 绿 → CLOSE → 下游棒：tech-graph-flow-resync（建议序 5/5 · 另 SPEC/task） |
| **freeze_id** | 承 SPEC：审计五动作词表 / 拒绝码 R-a~R-f / TTL 600s / HITL TTL 3600s / 三档默认值 / SSE 事件类型（`lg-rag-sse-v1`）/ HTTP 面（`lg-rag-http-v1`）**全零变更**；30 实判需动 → 回 SPEC 升 freeze，禁 silent 扩 |

### 人工闸

| 闸 | 状态 | 阻塞 | 备注 |
|---|---|---|---|
| HG-SPEC-SIGNOFF | **approved**（2026-10-19 维护者） | 20 书面审 | SPEC v0.1 文末 |
| HG-AUDIT-R1 | **approved**（2026-10-20 维护者授权 00 代签 · R2=pass · R1 M1–M3 闭合） | 30 改码 | 审查文 docs/harness/reviews/task_delegation_naming_boundary_audit_R1_20261020.md + _R2_20261020.md（锚点 24 命中/2 漂移 · 门控修正核验成立）；授权链 invoke_20261020_gate_sign_hg_audit_r1.md |
| HG-GRAPH-MODULES | **approved**（graph_change_layer 评估：正名+独立开关**不触发图谱行变更**——capability/lg_rag 行内备注回写即可，不增行/边/implementedBy/路由/表/SSE 事件类型，承 §4 Q3 与 :116 先例） | 30 改码 | `graph_change_layer=none` 预期不再签；30 实判越出（新行/新边）→ 回炉补签 |

---

## 背景与目标

### 问题（承 SPEC §1）

委派令牌（host-v1-delegation-token · Agent Host V1-A）落地后两个名实问题：① `auto_approve_ok` 名不符实——它不做「自动批准」，而是「签发策略是否放行」的三条件纯函数判定；② write 孪生护栏耦合在 `_delegation_active()` 上，delegation off（默认态）时护栏**从不生效**——名（护栏在码）实（护栏默认死）分离。

### 目标（承 SPEC §1）

D1 正名 `auto_approve_ok` → `issuance_policy_allows`（直接改名 · 不留别名 · 无 deprecation 过渡）；D2 护栏解耦为独立开关 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` **默认开**（FP-2 = 唯一有意行为变化 · invoke+图谱显式声明）；D3 图谱 capability 行 delegation 备注段写实 10 项职责（承 §4 Q3 不增行）。

## 范围

### D1 正名 `auto_approve_ok` → `issuance_policy_allows`（行号 10-task 于 master `31924af` 亲读复核，30 按实校正）

- **新名定为 `issuance_policy_allows`**（承 SPEC D1 首选 · 30 不另择；如确须偏离 → 回炉 10/20，禁静默改）
- 定义：`app/ops/capability/delegation.py:479` `def auto_approve_ok(specs, *, effective_scope)` 三条件纯函数（:479-505）
- 调用：`app/ops/lg_rag/multi/nodes.py:420` `dl.auto_approve_ok([entry[0]], effective_scope=scope)`；docstring 提及 `nodes.py:408`
- 测试：`tests/test_capability_delegation.py:338-360` 区域——`test_auto_approve_*` 三例（:338/:352/:359）+ 调用 :340/:354/:360，测试函数名与符号同步
- 测试（注释级 · 20-task-audit R1 M1 全仓实证补登）：`tests/test_capability_testing_write.py:185/:412/:468` 三处注释含旧名（`# 触发 auto_approve_ok 条件②不放行` 等）——**注释级改名同步 · 逻辑零改**（落入 TC1 tests/ 断言面 · TC8 白名单已补登）
- 图谱：`docs/_tech_graph/l1/01_modules.md:35` lg_rag 行 T1 备注「`auto_approve_ok` 纯函数零 IO」字样同步
- 判定逻辑（三条件）**逐字节保持**，diff 仅符号名 + docstring（TC2 机断）
- 历史 docs（reviews / tasks/done / invokes / specs）旧名引用属**不可变历史记录 · 不动**；TC1 grep 断言面 = `app/` `tests/` `docs/_tech_graph/`，豁免清单落 invoke

### D2 write 护栏解耦为独立开关（默认开 · FP-2 唯一有意行为变化）

- **门控真锚点**（10-task 于 master `31924af` 亲读复核 · 30 按实校正）：
  - `app/ops/lg_rag/multi/nodes.py:903` `write_done_keys = _write_success_call_keys(done, by_id) if _delegation_active() else {}`（条件建索引）
  - `app/ops/lg_rag/multi/nodes.py:931` `if _delegation_active() and str(row.get("type") or "") == "tool":` guard-skip 块头——块内含 :932 write_key 计算、:933-963 异 sid 命中 guard-skip（**:941-942 台账键 `write_replay_guard_skip`/`replay_of` = 金样钩子**）、:964-967 同批双胞胎次发挂起
  - 关联行：:930 `write_key = None` 初始化、:987-988 `if write_key is not None: batch_write_keys[write_key] = sid`（首发登记在门控块外 · 由 write_key 惰性控 · 解耦后随 write_key 自然跟随——30 须核对此跟随关系不破）
- **N3 校正**：R1 审查文列第三处 `:970` 系同形 `if` 行误并——`:970` 实为签发审批门 `issue_reason = await _delegation_issue_block_reason(state, row)` 块头，属 delegation 本体功能，**不在解耦面**，保持 `_delegation_active()` 耦合不动；`:1271` `if _delegation_active() and not fallback and subtasks:` 同理不动
- **新开关定为 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED`**（布尔 · **默认 true=开** · 非法值回退开 · 解析承 `SESSION_SUMMARY_ENABLED` 先例——**仅承解析模式**：该先例默认关、本键默认开，方向相反，防误抄（R1 N-d）；键名对齐台账 `write_replay_guard_*`）。SPEC 允许三档或布尔，本 task 定布尔
- 语义：护栏激活条件 = 新开关 on，**不再依赖** `_delegation_active()`；delegation on 时行为与 master 逐字节一致（TC5 牙）
- **FP-2 声明**：delegation off（默认态）下护栏由「从不生效」变「默认生效」——既有 supervisor 委派链路如依赖「护栏不生效」旧行为将首次被拦；此为 intentional behavior change，落 invoke + 图谱 lg_rag 行备注显式声明（TC10 牙）
- env 台账 `docs/guides/GUIDE_env_inventory_v1.md`：delegation 三键（`LG_RAG_DELEGATION_TOKEN_MODE`/`SECRET`/`TTL_SECONDS`）已登记 :12-14 capability 段（20-task-audit R1 M3 事实校正）；新键 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 补登记 lg_rag 段（先例 :35 `LG_RAG_VISIBILITY_SCENARIO_MODE` 行）

### D3 图谱 `01_modules.md` 回写

- capability 行 :34：delegation 备注段写实 10 项职责（承 SPEC D3 · 不新增一级模块）
- lg_rag 行 :35：T1 备注正名同步 + 护栏解耦/新开关/FP-2 intentional behavior change 声明
- 闸登记表新增 HG-GRAPH-MODULES approved 回写行（格式承 :110-128 先例：闸|状态|签署说明|日期|回写摘要）
- 不新增一级模块 · 零新跨模块边 · 不增 implementedBy · 零新路由/表/SSE 事件类型

### D4 测试同步与基线锚点测试

- `tests/test_capability_delegation.py:338-360` 符号名同步（除此之外既有测试逐字不改）
- 新增护栏开关矩阵测试（30 定文件名，建议 `tests/test_lg_rag_write_replay_guard.py`）：默认开拦截（TC3）/ 关恢复旧行为（TC4）/ delegation on 矩阵（TC5）/ env 非法回退（TC7）
- 基线锚点测试 **_resolve_base 式四态**（TC8）：钉锚 → merge-base 退化 → 后续波次可审计 skip → 锚缺失 skip；实现照抄蓝本 `tests/test_memory_injection_consumer.py:608-632`（_resolve_base 三级探测）+ :635-660（三路 diff + untracked 枚举 + 第四态）与 `tests/test_strategy_scenario.py:451-536`（_WAVE_TIP 第四态波次判定）

## 非范围（承 SPEC 原样 + task 级补充）

承 SPEC 非范围：不增一级模块（承 §4 Q3）；不改审计五动作词表 / 拒绝码 R-a~R-f / TTL 600s / HITL TTL 3600s / 三档默认值；SSE/HTTP 面零变更；worktree 脏改动另修。

task 级补充：

- **本起草阶段零 `app/` `tests/` 改码**（仅 task 文档 + invoke 占位）
- 不改 `nodes.py:970` 签发审批门与 `:1271` 的 delegation 耦合（非解耦面）
- 不改 SPEC——**N7** 核对结论：SPEC v0.1 :159 §8 R0 小节第 4 处「SPEC §4 Q3」dangling 引用（未指向 host-v1 文档路径）v0.1 后仍在、非阻塞；task 不代改，移交维护者择机闭合（40 复核）
- **N5 裁定**：上游「子代理 B 名实审查报告」不补落盘——SPEC §1 转述为 10 项超名清单唯一真值载体（承 R1 N5 备选口径）
- **N6**：worktree 脏改动声明（tests/test_lg_rag_supervisor_capability_catalog.py 重复 import）本仓 master 不可证（实证 :15 单次 import）——task 不依赖、不处置
- 历史 docs 旧名引用不动（不可变历史记录）

## failure_paths

| ID | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|---|
| FP-1 | 改名遗漏残留（`app/` `tests/` `docs/_tech_graph/` 任一 `auto_approve_ok` 残留） | TC1 grep 断言 fail | 是（补齐改名） | 否 |
| FP-2 | 护栏默认开误伤既有 supervisor 委派链路（delegation off 下既有 write 链路首被拦） | TC3/TC4/TC5 金样+矩阵断言 fail；应急口 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED=false` 恢复旧行为 | 是 | **是（intentional behavior change · invoke/图谱显式声明）** |
| FP-3 | enforce 档回归 | 既有 enforce 用例 fail（TC6） | 是 | 否 |
| FP-4 | 开关关闭护栏不生效面反向漏拦（关态残留拦截） | TC4 与 master 基线逐字节对拍 fail | 是 | 否 |
| FP-5 | 改名不等价（三条件判定逻辑漂移） | TC2 判定逻辑 diff 断言 fail | 是 | 否 |
| FP-6 | 词表/拒绝码/SSE/HTTP 面变更（freeze 破坏） | TC6 freeze grep+diff 断言 fail | 是 | 否 |
| FP-7 | `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 非法值行为漂移 | TC7 回退默认开断言 fail | 是 | 否 |
| FP-8 | 基线锚点不可解析时静默 pass/fail | TC8 _resolve_base 退化 → 仍不可得 `pytest.skip` 带实测 ref 状态（绝不静默） | 是 | 否 |

## 验收标准

- [ ] **TC1 改名零残留（承 SPEC FP-1）**：`grep -rn "auto_approve_ok" app/ tests/ docs/_tech_graph/` 零命中。豁免清单（落 invoke）：① 历史 docs reviews/tasks/done/invokes/specs（不可变历史记录）；② `01_modules.md` **闸登记表既有历史回写行**（:116 等 · 同不可变历史记录 · 20-task-audit R1 M2 补登）。口径注明（R1 N-e）：SPEC FP-1 表述「全仓」vs 本 TC 三面窄化——三面断言 + 两类豁免后等价全仓口径，非缩水。
- [ ] **TC2 正名落位与等价（承 SPEC FP-5）**：`delegation.py` `def issuance_policy_allows(specs, *, effective_scope)` 落位 + 三条件判定逐字节保持（diff 仅符号名/docstring）+ `nodes.py:420` 调用与 :408 docstring 同步 + `pytest tests/test_capability_delegation.py` 全绿（`test_issuance_policy_allows_*` 同步）。
- [ ] **TC3 默认开拦截（FP-2 正牙）**：env 全不设（delegation 默认 off）→ supervisor write 双胞胎重放金样被拦 · 台账含 `write_replay_guard_skip` + `replay_of`（钩子 nodes.py:941-942）。
- [ ] **TC4 关恢复旧行为（FP-2 逆牙 · 承 SPEC FP-4）**：`LG_RAG_WRITE_REPLAY_GUARD_ENABLED=false` + delegation off → 行为与 master 基线逐字节一致。
- [ ] **TC5 delegation on 矩阵回归（承 SPEC FP-3 邻面）**：delegation on × guard on → 与 master 逐字节零 diff；× guard off → 护栏不生效但签发审批门（:970）照常（delegation 耦合不动）。
- [ ] **TC6 freeze 零变化（承 SPEC FP-3/FP-6）**：审计五动作词表 / 拒绝码 R-a~R-f / SSE 事件类型 / HTTP 面 grep+diff 断言空；freeze `lg-rag-sse-v1`/`lg-rag-http-v1` 不升；既有 enforce 档用例全绿。
- [ ] **TC7 env 非法回退（承 SPEC FP-7）**：`LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 非法值（如 `"2"`/`""`）→ 回退默认开 + 护栏生效断言。
- [ ] **TC8 diff 白名单 + _resolve_base 式四态**：改动面 ⊆ {`app/ops/capability/delegation.py`、`app/ops/lg_rag/multi/nodes.py`、`tests/test_capability_delegation.py`、`tests/test_capability_testing_write.py`（仅注释级改名 · R1 M1 补登）、新增护栏矩阵测试文件、`docs/_tech_graph/l1/01_modules.md`、`docs/guides/GUIDE_env_inventory_v1.md`、`docs/harness/invokes/by-task/delegation-naming-boundary/**`、`docs/tasks/active/task_delegation_naming_boundary.md`}；基线锚点解析四态——① `git rev-parse --verify {钉锚}^{commit}` → ② 退化 `merge-base HEAD origin/{GITHUB_BASE_REF 或 master}`（双 ref 试）→ ③ 钉锚命中 ∧ 越白名单 ∧ 越出面全非本波次（_WAVE_TIP 判定）→ 可审计 skip（越出面含本波次仍 fail）→ ④ 仍不可得 `pytest.skip` 带实测 ref 状态（绝不静默 pass/fail）；**banned 禁区断言（`scripts/` `alembic/` 白名单外 `app/`）前置于全部 skip 出口**（task 级强化 · 蓝本 :659-660 置尾承改为前置——skip 不得掩盖禁区触碰）；实现注（R1 N-a）：态④锚不可解析时 banned 检测以「vs HEAD + untracked」兜底，不可因基线缺失整体豁免禁区；实现照抄 `tests/test_memory_injection_consumer.py:608-660` + `tests/test_strategy_scenario.py:451-536` 口径。
- [ ] **TC9 静态与全量**：`ruff check app tests` 绿 + `pytest tests` 全量绿（既有测试除符号名同步逐字不改）。
- [ ] **TC10 文档三落位**：`01_modules.md` capability :34 + lg_rag :35 回写（正名同步 + 护栏解耦/新开关 + FP-2 声明 + 闸登记表新行）断言；`GUIDE_env_inventory_v1.md` lg_rag 段 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 在册断言；invoke 目录 10/20/30/40 齐；`./scripts/graph-compile.sh` EXIT=0。

## 依赖

- base：master `31924af`（PR #287 已合）；文档线 `docs/task-delegation-naming-boundary`；30 分支 `task/delegation-naming-boundary`
- SPEC：`docs/spec/delegation-naming-boundary/SPEC-delegation-naming-boundary_v0.md`（v0.1 signed）；审查文：`docs/harness/reviews/spec_delegation-naming-boundary_audit_R1_20261019.md`（R1/R2）
- 上游裁定：`docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` §4 Q3（不增一级模块 · v0.1 已修）
- 代码锚点（10-task 已于 master `31924af` 亲读复核 · 行号 30 按实校正）：`delegation.py:479-505`；`nodes.py:408/:420/:903/:930-988/:970/:1271`；`tests/test_capability_delegation.py:338-360`；`01_modules.md:34/:35`
- `_resolve_base` 先例：`tests/test_memory_injection_consumer.py:608-632`（三级探测）+ :635-660（diff 白名单 + 第四态）+ `tests/test_strategy_scenario.py:451-536`（_WAVE_TIP 波次判定）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 结构先例：`docs/tasks/done/task_scenario_stage_rewire.md`、`docs/tasks/done/task_memory_injection_consumer.md`

## 给执行帽的必读列表

1. 本 task 全文（含人工闸表 · **HG-AUDIT-R1=pending 未签不得 30**）
2. `docs/spec/delegation-naming-boundary/SPEC-delegation-naming-boundary_v0.md`（v0.1 · D1/D2/D3 + FP-1~FP-7 + freeze 面）
3. `docs/harness/reviews/spec_delegation-naming-boundary_audit_R1_20261019.md`（N3/N5/N6/N7 移交项本 task 已吸收落位）
4. `app/ops/capability/delegation.py:479-505`、`app/ops/lg_rag/multi/nodes.py:900-990` 全文亲读（实施前再复核行号与 :987-988 跟随关系）
5. `tests/test_memory_injection_consumer.py:608-660` `_resolve_base` + `tests/test_strategy_scenario.py:451-536` `_WAVE_TIP`（TC8 实现蓝本 · 禁临场发明基线解析）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 开工 GATE_VERIFY）

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 问题框定 | SPEC v0.1 已签 · D1 正名/D2 解耦默认开/D3 图谱写实 · R1 阻塞 0 锚点 8/9 | 否 | — | N3 第三处坐标存疑 |
| R1 锚点亲读 | master `31924af` 全锚复核：护栏两处真门控 :903/:931（+ :930/:987-988 关联）· :970 签发审批门误并澄清 | 否 | — | :987-988 跟随关系 30 核对 |
| R2 格局沿用 | 闸表三行/TC 全机断/FP 表/R 轮控制表沿用 #3 定稿格局（scenario-stage-rewire · memory-injection-consumer） | 否 | — | 无 |
| R3 反例与边界 | FP-1~FP-8 完备（残留/FP-2 误伤/enforce 回归/关态漏拦/等价/freeze/env 非法/基线静默）· banned 禁区断言前置（00 指令 · 蓝本置尾承改） | 否 | — | banned 前置与蓝本置尾差异 → 20 审查确认 |
| R4 开放点收口 | 新名定 `issuance_policy_allows` · 开关定 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 布尔默认开非法回退开 · N5 不补落盘 · N7 移交不代改 | 是 | 开放点全收口 · TC1–TC10 全可机断 | 无 |
| R5 定稿自检 | 闸表齐 · N3/N5/N6/N7 落位 · FP-2 验收三牙（TC3/TC4/TC5）· 零 `app/` 改码零代签 | 是 | lint PASS 后提交 | 无 |

### R0 轮：依据读取

SPEC v0.1（D1 正名 / D2 解耦默认开 / D3 图谱写实 · FP-1~FP-7 · freeze 面）+ R1 conditional_pass（阻塞 0 · 锚点 8/9 · N3/N5/N6/N7 移交）+ R2 pass + 上游 §4 Q3 不增行裁定。结论：可起草。

### R1 轮：锚点亲读复核（master `31924af`）

护栏耦合**两处真门控** :903/:931（+ :930/:987-988 关联行）；R1 N3 第三处 :970 系签发审批门误并，不在解耦面（D2 显式校正）。改名面 8 处代码/测试（含 v0.2 M1 补登 test_capability_testing_write.py 注释级三处）+ 1 处图谱字样（闸登记历史行 :116 等不动 · TC1 豁免②）。capability 行 :34、lg_rag 行 :35 无 delegation 独立行（承 Q3）。env 台账：delegation 三键已登记 GUIDE :12-14 capability 段（v0.2 M3 校正 v0.1「未登记在先」误述）· 新键补登记 lg_rag 段。

### R2 轮：格局沿用

闸表三行 / TC1-TC10 全可机断 / FP 表 / R 轮控制表 / 必读列表，全沿用 #3 定稿格局（task_scenario_stage_rewire.md · task_memory_injection_consumer.md）。

### R3 轮：反例与边界

FP-1~FP-8 对齐 SPEC FP-1~FP-7 + task 级 FP-8（基线锚点静默）；banned 禁区断言**前置**于全部 skip 出口（00 指令 · 对蓝本置尾顺序的 task 级强化：skip 不得掩盖禁区触碰）。

### R4 轮：开放点收口

新名定 `issuance_policy_allows`（SPEC D1 首选）；开关定 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 布尔默认开、非法回退开（承 `SESSION_SUMMARY_ENABLED` 解析先例 · 键名对齐台账 `write_replay_guard_*`）；N5 定不补落盘；N7 定移交不代改。early_stop：开放点全收口、TC 全可机断。

### 自检结论（R5 轮 · 定稿自检）

- 闸表三行齐（SPEC-SIGNOFF approved / AUDIT-R1 pending blocks 30 / GRAPH-MODULES approved 口径写明）✔
- N3 落 D2 门控真锚点（含 :970 误并校正）✔ N5/N6/N7 落非范围 ✔
- FP-2 行为变化验收：TC3 默认开拦截 + TC4 关恢复 + TC5 矩阵 + FP-2 行「用户可见=是」✔
- 改名兼容处置：承 SPEC 直接改名不留别名/无 deprecation（D1 写明 · TC1 零残留牙）✔
- 本起草阶段零 `app/` 改码、未改 SPEC、未代签任何闸 ✔
- v0.2（20-task-audit R1 conditional_pass 签前闭合）：M1 D1+TC8 补登 test_capability_testing_write.py ✔ M2 TC1 豁免②闸登记历史行 ✔ M3 env 台账措辞校正 ✔ nits N-a（banned 兜底）/N-d（先例方向）/N-e（口径注明）吸收 ✔ N-b 维持「30 按实校正」· N-c 仅知会 ✔

## 修订记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-10-20 | 10-task 起草（master `31924af` 亲读复核锚点 · N3 坐标校正 :903/:931 两处真门控 + :970 误并澄清 · 开放点收口新名/开关键名） |
| v0.2 | 2026-10-20 | 20-task-audit R1=conditional_pass 签前闭合：M1 D1 改名面+TC8 白名单补登 `tests/test_capability_testing_write.py:185/:412/:468`（注释级）· M2 TC1 豁免②闸登记表既有历史回写行 · M3 env 台账措辞校正（delegation 三键已登记 GUIDE :12-14 capability 段）· nits N-a banned 态④「vs HEAD+untracked」兜底 / N-d 解析先例方向注明 / N-e TC1 口径注明（N-b 维持 30 按实校正 · N-c 仅知会） |
