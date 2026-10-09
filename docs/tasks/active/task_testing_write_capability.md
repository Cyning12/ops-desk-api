# Task：testing-write-capability（D2 · 注册非只读测试 capability · 补齐 HITL 全链可审对象）

> **状态**：`draft`（2026-10-09 · 10-task 落稿 · 人工闸全 pending → 30 拒开工）  
> **类型**：**behavior**（小 task · 免 SPEC · 依据=验收登记偏差项）  
> **依据**：`docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 偏差登记 #1/#2 区：「阶段 3 真实图挂起 → decide → resume 解锁全链未验（全只读能力面无可审对象）→ 注册非只读测试 capability → 另立 task」——本 task 即该 task  
> **分支**：`task/testing-write-capability`（base：`master` 57fbf84）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `testing-write-capability` |
| **git_branch** | `task/testing-write-capability` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 新增 pytest：filter 豁免字段单测（命中/未命中/deny_high_risk 不可豁免）+ manifest 加载隔离 + 罐头 adapter 零 IO 断言 + enforce 下 delegation_issue_hitl_required 集成断言；全量 `pytest tests` 回归零新增红；off 三 env 皆不设时与 master 基线逐字节零 diff（注册表 snapshot / 可见集 / catalog count 对照） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `l1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` capability 模块条目：新增 testing.v1.yaml manifest + CapabilityFilter.allow_write_tags_any 字段 + defaults.py 罐头函数 |
| **graph_delta_note** | 模块边界不变（仍进程内注册表）；仅模块内字段/文件增量 → G-L1 层同步 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | behavior 小 task · 免 SPEC · 无 wiki 条目变更（验收登记偏差项即依据） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 00 代录人签 → 30 → 40 → CLOSE |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | pending | 20-R1, 30 | 10-task 落稿待 00/维护者签 |
| HG-AUDIT-R1 | pending | 30 | 20-task-audit R1 审查文落盘 + 人签后方可 30 |
| HG-GRAPH-MODULES | pending | 30 | `graph_change_layer=l1`（capability 模块内增量）· 人签图谱同步口径 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点 task |

---

## 背景与目标

2026-10-09 本地验收（`docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 阶段 3）实证：当前 capability 注册表**全只读**（`side_effect: read` · 可见集基线 `deny_write: true` · 可见集 8 个 tool），`LG_RAG_DELEGATION_TOKEN_MODE=enforce` 下按 Q2 裁定「只读自动放行」（`app/ops/capability/delegation.py:488-514` `auto_approve_ok` 三条件），**永远无真实 HITL 挂起可触发**——「真实图挂起 → decide → resume 解锁」全链无验收对象（设计真态，非缺陷，但验收链不可达）。

**一句话目标**：注册一枚 `side_effect: write` 的**测试专用罐头 capability**（语义 mock · 零真实写），并配一条**受控可见性放行口径**（env 门控 tag 白名单，**不全局松 deny_write**），使 enforce 模式下「plans 含该 tool → hitl.waiting 挂起 → pending 可见 → decide(approved) → resume → done{completed}」全链可真实验收；off（默认）模式逐字节零 diff。

---

## 现状锚点（只读 · 30 必读 · 10 已逐行实读）

| 锚点 | 实证 |
|------|------|
| `app/ops/capability/manifests/builtin.v1.yaml:7-29` | 字段族范式：id/kind/description/when_to_use/when_not_to_use/tags/risk_level/side_effect/enabled/tenant_scoped/args_schema/reversible/execution_type/max_reversal_latency/requires_stop_support/adapter（首枚条目逐字段齐） |
| `app/ops/capability/delegation.py:488-514` | `auto_approve_ok` 三条件（纯代码判定）：① capability_set ⊆ 有效 scope；② 全部 `side_effect ∈ READONLY_SIDE_EFFECTS={none,read}`（:80）；③ 无 `kind ∈ NON_AUTO_KINDS={sandbox,cli}`（:82）。任一不满足 → 不放行 + 原因串 |
| `app/ops/lg_rag/multi/nodes.py:277-295` | `_delegation_issue_block_reason` 触发链：tool ∉ effective_scope → **不走 HITL**（:287-288 直接 None）；未注册 → 安全默认交人；`auto_approve_ok` False → `委派签发需人工审批（{why}）` |
| `app/ops/lg_rag/multi/nodes.py:701-726` | hitl_required 落点：contract gate（693-707）之后，`_delegation_active()` 且 type==tool 时签发审批拦截（710-726），`blocked["hitl_required"]=True` 在 :713-715，审计 `AUDIT_TOKEN_ISSUE_HITL_REQUIRED` :721-725 |
| `app/ops/lg_rag/multi/nodes.py:252-254` | `_delegation_active()`：mode != off 即启用；**off = 现状逐字节零 diff（默认 off）** |
| `app/ops/capability/baseline.py:33-44` | 可见集基线：`kinds={local_fn}` + `allow_tags_any={oa}` + `deny_high_risk=True` + **`deny_write=True`**（:43 · 「第一期只读：写能力在裁剪阶段就不进模型视野」） |
| `app/ops/capability/registry.py:112-133` | `_match_filter` 判序：enabled → kinds（allow_tags_any 只豁免本层）→ deny_high_risk → **deny_write（:128，`WRITE_SIDE_EFFECTS={write,irreversible}` · types.py:26）** → tags_any 收窄 |
| `app/ops/capability/manifest.py:54,60,155-165` | `MANIFEST_DIR` 内 builtin 默认加载；额外清单须 `OPS_CAPABILITY_EXTRA_MANIFESTS` 显式列出（默认空 · 两层「显式打开」纪律见 baseline.py:17-18） |
| `app/ops/capability/baseline.py + builder.py:28 + nodes.py:92 + admin/capability.py:179` | `baseline_filter` 三使用点；**BUILDER_CAP_FILTER / _SUPERVISOR_CAP_FILTER 为模块级常量（import 时固化）**——env 门控必须在 import app 之前生效（对齐 tests/conftest.py 既有 setdefault 先例） |
| `app/ops/hitl/router.py:5-10` | 验收链路由真值：`GET /api/ops/hitl/pending`（cookie maintainer）· `POST /api/ops/hitl/requests/{id}/decide` · `POST /api/ops/hitl/requests/{id}/resume` |
| `app/ops/capability/defaults.py:42-74` | 罐头 adapter 范式：纯函数返回罐头 dict，零 IO 零 DB 零外网（`utc_now_iso` 注「无副作用 · 不连外网」） |

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **manifest 选型** | **独立文件 `app/ops/capability/manifests/testing.v1.yaml`**（R2 裁定）；**禁止并入 builtin.v1.yaml**——并入会破 `tests/test_capability_manifest.py:83` `capability_manifest_count == 5` 断言，且使注册表恒多一枚（off 非零 diff） |
| **加载纪律** | testing.v1.yaml **不得进默认加载面**；仅经 `OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载（既有两层显式打开纪律的第三层） |
| **可见性放行口径** | env 门控 **tag 白名单豁免**（新增 `OPS_CAPABILITY_ALLOW_WRITE_TAGS`，默认空；R2 裁定）；**禁止全局松 `deny_write`**（含 env 版全局开关）；**禁止把 `testing` 加进 `DOMAIN_ALLOW_TAGS`**（那是豁免 kinds 裁剪的域放开，语义不符且非 env 门控）；**`deny_high_risk` 永不设豁免口** |
| **deny_write 基线不动** | `baseline.py:43` `deny_write=True` 保持；豁免只在 `allow_write_tags_any` 命中时跳过 deny_write 一层，判序其余不变（`registry._match_filter` 既有「一个 tag 不能换全部豁免」纪律延续到写维度） |
| **adapter 语义 mock** | 罐头函数落 `app/ops/capability/defaults.py`（建议名 `testing_write_echo`）：返回罐头 dict，**零 IO · 零 DB · 零外网 · 零文件写 · 零 subprocess**；函数体不得 import 任何 IO 库（requests/httpx/Path.write/subprocess 等）；docstring 明写「语义 mock · 无真实写操作」 |
| **capability 字段钉死** | `side_effect: write`（触发 auto_approve_ok 条件②不放行）；`kind: local_fn`；**`risk_level` 不得为 `high`**（deny_high_risk 无豁免口，标 high 则可见性永不达——建议 `medium`）；tags 必含 `testing`（建议 `[testing, mock, write]`）；`enabled: true`；`tenant_scoped: false`；`reversible: true` · `execution_type: instant` · `max_reversal_latency: 0` · `requires_stop_support: false` |
| **判定逻辑零改动** | `auto_approve_ok` / `_delegation_issue_block_reason` / HITL pending-decide-resume 链本身**一行不改**（本 task 只提供可审对象与可见性口径，不改审批语义） |
| **off 零 diff** | 三个 env（`OPS_CAPABILITY_EXTRA_MANIFESTS` / `OPS_CAPABILITY_ALLOW_WRITE_TAGS` / `LG_RAG_DELEGATION_TOKEN_MODE`）皆不设时：注册表 snapshot / 可见集 8 枚 / catalog count 5 / 全量 pytest 与 master 基线一致 |
| **env 生效时机** | env 门控在 `baseline_filter()` 调用点读取；BUILDER/SUPERVISOR filter 为模块级常量 → 验收环境与测试内 monkeypatch 均须在 **import app 之前**或重建 filter 后生效（30 在测试内显式处理，禁止依赖 import 顺序巧合） |

---

## 范围

- [ ] **F1 · manifest**：新增 `app/ops/capability/manifests/testing.v1.yaml`（version: 1 · 单枚条目 · 字段族逐字段对齐 builtin 范式 · 头注释明写「测试专用 · 仅 OPS_CAPABILITY_EXTRA_MANIFESTS 显式加载 · 语义 mock 无真实写」）
- [ ] **F2 · adapter**：`app/ops/capability/defaults.py` 增罐头函数（纯函数罐头 dict）；**不进 `_DEFAULT_SPECS`**（注册只经 manifest 加载路径）
- [ ] **F3 · 可见性放行口径**：`types.py` `CapabilityFilter` 增 `allow_write_tags_any: frozenset[str] | None = None`（与 `allow_tags_any` 对称 · docstring 写明方向=豁免 deny_write 一层且不豁免 deny_high_risk）；`registry._match_filter` 在 deny_write 判定处加豁免分支（命中 `allow_write_tags_any ∩ spec.tags` 则跳过本层）；`baseline.py` `baseline_filter()` 读 `OPS_CAPABILITY_ALLOW_WRITE_TAGS`（逗号分隔 · 默认空 → 字段为 None）透传
- [ ] **F4 · 测试**：新增/扩展 pytest（见验收 A4）；旧测影响面按 B1 清单亲跑
- [ ] **F5 · 图谱同步**：`docs/_tech_graph/l1/01_modules.md` capability 模块条目增量（graph_change_layer=l1）
- [ ] **F6 · 验收链证据**：enforce 全链本地实跑记录落 invoke（40 或验收人执行 · 命令与断言见 A1）

### 非范围

- 改 `auto_approve_ok` / `_delegation_issue_block_reason` / HITL 链（pending/decide/resume）任何判定语义
- 全局松 `deny_write`（含 env 版总开关）；给 `deny_high_risk` 开豁免口；改 `DOMAIN_ALLOW_TAGS` 既有成员
- 真实写操作接入（任何 DB/文件/外网写）；新增非罐头 capability
- 验收登记偏差 #2 的 compose 形态（`OPS_HITL_PERSISTENCE=db` 透传）——另立 task
- builtin.v1.yaml 五枚既有条目的任何字段改动
- 前端审批 UI 改动；docker-compose.yml 改动

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| HG-AUDIT-R1 / HG-GRAPH-MODULES pending 即 30 | **拒开工**（GATE_VERIFY 拦） | 是 | 是 |
| testing capability 被 deny_write 基线裁掉 → 模型不可见 → plans 不含该 tool → tool ∉ effective_scope（nodes.py:287-288）→ **不走 HITL，全链验收不可达** | 预案=F3 放行口径（env 门控 tag 白名单）；30 自检：放行 env 设置后 `list_capabilities(filter=baseline_filter(...))` 必含该条目，否则不得进入验收链 | 是 | 否 |
| adapter 误触真实写（IO/DB/外网/文件） | 防线三层：① 钉死契约禁 import IO 库（review 机械可查）；② 新增单测断言罐头返回且无 IO 副作用（socket/DB fixture 不触）；③ 20/40 审查逐行核函数体 | 是 | 否 |
| `risk_level: high` 误标 | deny_high_risk 恒裁且无豁免口 → 可见性永不达；F1 模板钉死 medium + A6 断言兜底 | 是 | 否 |
| enforce 未开（off 默认）时行为漂移 | off 三 env 皆不设 → manifest 不加载 → 注册表/可见集/catalog 零 diff；A5 对照 master 基线机断 | 是 | 否 |
| 放行 env 设了但 EXTRA_MANIFESTS 未设（或反之） | 只加载不可见（deny_write 仍生效）或只放行无条目——两层显式打开语义本身；验收命令清单把三 env 写成一组，缺一即 A1 不可达 | 是 | 是（验收人） |
| 既有 catalog/visibility 测试断言被新条目/新字段打破 | B1 清单 10 已实扫；30 亲跑全清单 + 全量 pytest 零新增红；`test_allow_tags_does_not_waive_deny_write`（domain_allowlist:102-112）语义必须保持（新字段不影响旧断言） | 是 | 否 |
| 测试内 monkeypatch env 但因模块级常量已固化而不生效 | 30 在测试内显式重建 filter（重新调用 baseline_filter 或 reload 模块），禁止依赖 import 顺序；钉死契约已写明 | 是 | 否 |
| `npx spec-wave task lint` 红 | 30 返工修结构 | 是 | 否 |

---

## B1 · 旧测影响面（10 已实扫落盘 · 20-audit 核查清单 · 30 亲跑义务）

| 文件 | 断言面 | 预期 |
|------|--------|------|
| `tests/test_capability_manifest.py` | :58-83 builtin 五枚与 `_DEFAULT_SPECS` 对齐 + `capability_manifest_count == 5`（:83）；:300 nonexistent 路径 | **零 diff 期望**（独立文件方案不进 builtin 统计）；若红说明选型被擅改 → 退回 |
| `tests/test_capability_domain_allowlist.py` | :90-99 一个 tag 不换全部豁免；**:102-112 allow_tags 不豁免 deny_write（钉死语义）**；:129-166 基线零影响/形状稳定（:160-166 四字段断言）；:169+ 端到端裁剪 | 既有断言全绿；`test_baseline_filter_shape_is_stable` 如断言字段全集须 30 扩展（允许新增字段断言，禁删旧断言） |
| `tests/test_lg_rag_supervisor_capability_catalog.py` | :50-57 supervisor 可见集含 mock_get_issue_status/utc_now_iso（成员断言 · 非总数） | 零 diff（off 时新条目不可见） |
| `tests/test_admin_capability_observability.py` | :174-200 deny_write 展示面 | 零 diff |
| `tests/test_capability_visibility_and_receipts.py` | _match_filter 语义族（:82-171） | 零 diff（新字段默认 None 不改判序） |
| `tests/test_capability_gateway.py` | write 拦截面（policy/circuit/budget 经 WRITE_SIDE_EFFECTS） | 零 diff |
| `tests/test_strategy_builder.py` / `tests/test_strategy_scenario.py` | BUILDER_CAP_FILTER 使用面 | 零 diff |
| `tests/test_prompt_assets.py` / `tests/test_prompt_assembly.py` | 目录渲染进 prompt 断言 | 零 diff（off 时目录不变） |
| `tests/test_hitl_pending_decide.py` / `tests/test_hitl_resume.py` | HITL 链既有 20 用例（409/404/422/归属过滤/decide→resume 图替身/真 PG 重启链） | 全绿（本 task 不改链）；A4 集成断言可复用其 fixture |
| `tests/eval/test_capability_redlines.py` | :1745-1884 eval 红线面（非默认跑） | 30 注记是否受影响；默认不跑不阻塞 |

---

## 验收标准

- [ ] 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved 后方可勾选下列码项
- [ ] **A1（enforce 全链 · 补齐 2026-10-09 验收唯一未验项）**：env 组 `OPS_CAPABILITY_EXTRA_MANIFESTS=<repo-relative manifest path>` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing` + `LG_RAG_DELEGATION_TOKEN_MODE=enforce` 下起服务（env 须在 import app 前生效）：plans 含该 tool 的 run → SSE/状态断言 `hitl.waiting` 挂起（blocked_by=`delegation_issue_hitl_required`）→ `GET /api/ops/hitl/pending`（cookie maintainer）可见该 request → `POST /api/ops/hitl/requests/{id}/decide` approved → resume → 终态 `done{completed}`。证据（命令 + 响应摘录）落 40 invoke
- [ ] **A2（off 零 diff · 默认 off 纪律）**：三 env 皆不设：① registry snapshot 不含 testing 条目（count 不变）② `list_capabilities(filter=baseline_filter(...))` 可见集仍 8 枚且不含该条目 ③ `capability_manifest_count == 5` 断言原样绿 ④ 全量 `pytest tests` 与 master 基线零新增红
- [ ] **A3（加载≠可见 · deny_write 不全局松）**：只设 EXTRA_MANIFESTS 不设 ALLOW_WRITE_TAGS：注册表含该条目（snapshot 可见）但 baseline 可见集**不含**（deny_write 仍生效）；`test_allow_tags_does_not_waive_deny_write` 原样绿
- [ ] **A4（新增测试）**：① `allow_write_tags_any` 命中→豁免 deny_write / 未命中→仍裁 / high risk 即使命中仍裁（deny_high_risk 无豁免口）三例单测 ② manifest 显式加载后 registry 含该条目且 adapter 可调 ③ 罐头 adapter 返回罐头 dict 且零 IO 断言 ④ enforce + 放行 env 下 delegation 签发审批集成断言（可复用 hitl fixture 图替身段，真实挂起段由 A1 本地链兜底）
- [ ] **A5（adapter 罐头防线）**：`grep` 函数体无 `requests`/`httpx`/`subprocess`/`open(`/`.write`/`Path` IO 调用；docstring 含「语义 mock」；40 逐行核
- [ ] **A6（字段钉死）**：manifest 条目 `side_effect: write` · `kind: local_fn` · `risk_level != high` · tags 含 `testing` · `enabled: true`（加载后经 registry 断言）
- [ ] **A7（B1 旧测清单）**：B1 表 10 个文件全绿亲跑记录（命令 + 结果）落 40 invoke
- [ ] `ruff check app tests` 触及路径绿；`./scripts/graph-compile.sh` 绿（F5 图谱同步后）
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_testing_write_capability.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 依据 | `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md`（偏差登记 · 阶段 3 未验项） |
| 触发链真值（只读） | `app/ops/capability/delegation.py:488-514` · `app/ops/lg_rag/multi/nodes.py:252-254,277-295,701-726` |
| 可见性机制（改动面） | `app/ops/capability/types.py:136-164` · `registry.py:112-133` · `baseline.py:33-44` |
| manifest/adapter（改动面） | `app/ops/capability/manifests/` · `manifest.py:54,155-165` · `defaults.py` |
| HITL 链（复用 · 不改） | `app/ops/hitl/router.py:5-10` · `tests/test_hitl_pending_decide.py` · `tests/test_hitl_resume.py` |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-16 capability 契约纪律：注册表 ≠ 注册中心 · args_schema 仅形态） |
| 上游任务范式 | `docs/tasks/done/task_host_v1_visibility_scenario_policy.md`（可见性/域放开裁定先例）· `docs/tasks/done/task_catalog_manifest_yaml.md`（manifest 字段族先例） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 + GATE_VERIFY）· 2. 本 task（钉死契约 + B1 + 验收标准）· 3. `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md`（偏差登记原文）· 4. `docs/standards/CODING_BACKEND_L2_v1_zh.md` · 5. `app/ops/capability/delegation.py:488-514` + `app/ops/lg_rag/multi/nodes.py:252-295,701-726`（触发链 · 只读）· 6. `app/ops/capability/baseline.py` + `registry.py:112-133` + `types.py:136-164`（可见性机制 · 改动面）· 7. `app/ops/capability/manifests/builtin.v1.yaml` + `defaults.py`（字段族/罐头范式）· 8. `FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题=验收偏差登记的既定「另立 task」项；需求边界无歧义 | no | — | none |
| R1 | 范围=manifest+adapter+可见性放行口径+测试+图谱；HITL 链/判定逻辑/真实写全部非范围 | no | — | 无 |
| R2 | 三裁定落定：① 独立 testing.v1.yaml（并入 builtin 破 count==5 + off 非零 diff）② env 门控 allow_write_tags_any（否掉全局松 deny_write / 加 DOMAIN_ALLOW_TAGS / enabled=false 三岔路）③ 罐头 adapter 零 IO | no | — | 放行口径新字段的判序护栏须 20 复核 |
| R3 | 交叉验证：触发链复核（tool∉scope 不走 HITL → 可见性必须解）+ risk_level≠high 约束发现 + B1 旧测面实扫 + off 零diff 论证（不加载=零 diff） | no | — | BUILDER/SUPERVISOR filter 模块级常量的 env 生效时机已钉死契约 |
| R4 | failure_paths 推演：八条覆盖（可见性裁掉预案/真实写防线/off 漂移/旧测破/env 半设/import 时机/lint 红/闸拒开工） | no | — | 无 |
| R5 | 验收口径机断化收敛（A1–A7 均可对命令输出断言）；无方案分叉残留 | yes | 三裁定各有实证排除岔路 · 触发链与旧测面均实读闭环 · 验收链路由真值已核 | 见 R2/R3 |

**actual_last_round**：R5 · **early_stop**：yes · **residual_risks**：见 R2/R3

### R0 · 问题框定

验收登记偏差项已写明处置路径（「注册非只读测试 capability（manifest 增条目 · side_effect≠read）→ 另立 task」），本 task 直接承接，无需重开需求分析。Q2 裁定（只读自动 · 其余 HITL）为既有设计真态，本 task 不动裁定，只补可审对象。

### R1 · 范围钉死

改动面五件：testing.v1.yaml（新）· defaults.py 罐头函数（增）· CapabilityFilter 字段（增）· _match_filter 豁免分支（增）· baseline_filter env 读取（增）。判定逻辑（auto_approve_ok / nodes 触发链 / HITL 路由）一行不改——验收对象是「既有审批链遇上真实非只读条目」，不是「新审批链」。

### R2 · 方案裁定（三裁定 · 各排除岔路）

**裁定一 · manifest 选型=独立 testing.v1.yaml**。岔路排除：并入 builtin.v1.yaml 会破 `test_capability_manifest.py:83` `count==5` 硬断言，且 builtin 默认加载 → 注册表恒多一枚 → off 模式非零 diff（违反验收 A2）；独立文件 + EXTRA_MANIFESTS 显式加载使「off 零 diff」由**不加载**天然保证，并复用仓内既有「两层显式打开」纪律（baseline.py:17-18）。

**裁定二 · 可见性放行口径=env 门控 tag 白名单豁免字段**。实证矛盾：`baseline.py:43` `deny_write=True` 恒裁写能力（registry.py:128），而 `nodes.py:287-288` tool∉scope 不走 HITL——不放行则全链验收永不可达。四岔路：① 全局松 deny_write（含 env 总开关）→ 任务明文禁止，且一开则所有写能力全可见，口径过粗，**否**；② `testing` 加入 `DOMAIN_ALLOW_TAGS` → 该集合豁免的是 kinds 裁剪（baseline.py:11-15 语义不符），且非 env 门控、全局生效，off 零 diff 失守，**否**；③ `enabled: false` 默认 → manifest 为静态 yaml 无 env 门控，验收须手改文件，不可机断，**否**；④ **新增 `CapabilityFilter.allow_write_tags_any` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS`（默认空）** → 与 `allow_tags_any` 对称的最小机制增量，默认空=判序零 diff，命中只豁免 deny_write 一层（deny_high_risk 无豁免口延续「一个 tag 不换全部豁免」纪律），**选定**。三层显式打开成形：EXTRA_MANIFESTS（加载）→ ALLOW_WRITE_TAGS（可见）→ DELEGATION_TOKEN_MODE=enforce（触发）。

**裁定三 · adapter=defaults.py 罐头函数**。岔路排除：接真实写（DB/文件/外网）→ 引入副作用与回滚议题，远超「可审对象」所需，**否**；罐头纯函数复用 `utc_now_iso` 范式（「无副作用 · 不连外网」），HITL 触发只依赖 manifest 声明的 `side_effect: write`（auto_approve_ok 读 spec 字段，不执行 adapter），语义 mock 足够且安全。

### R3 · 交叉验证

- **触发链复核**：`nodes.py:283-295` 逐行实读——tool 空/∉scope 直接 None（不走 HITL），故「模型可见 → 进 plan → ∈ allowed_capability_ids/delegation_scope」是挂起前提，可见性放行不可省；`nodes.py:710-726` 落点确认 hitl_required=True + 审计留痕为既有行为，本 task 零改动即可复用。
- **risk_level 约束发现**（实读 registry.py:126-128 得出）：deny_high_risk 无豁免口且判序在 deny_write 之前——条目若标 high 则任何放行口径都救不回，故钉死 `risk_level != high`（建议 medium）。
- **B1 旧测面实扫**：grep + 实读 10 文件断言面（见 B1 表），最关键两处：`test_capability_manifest.py:83` count==5（决定裁定一）、`test_capability_domain_allowlist.py:102-112` deny_write 不豁免钉死（决定裁定二的护栏形状）。
- **off 零 diff 论证**：EXTRA_MANIFESTS 默认空（manifest.py:155-160）→ 不加载 → 注册表/可见集/catalog/prompt 渲染全不变；ALLOW_WRITE_TAGS 默认空 → filter 新字段为 None → `_match_filter` 判序逐字节不变；DELEGATION_TOKEN_MODE 默认 off（nodes.py:252-254）→ 拦截段整段短路。三层各自独立零 diff，合取成立。
- **env 生效时机**：BUILDER_CAP_FILTER（builder.py:28）/ _SUPERVISOR_CAP_FILTER（nodes.py:92）为模块级常量 import 时固化——验收起服务前 set env 天然满足；测试内须显式重建 filter，已写入钉死契约。

### R4 · failure_paths 推演

按任务书四类必覆盖逐项落到机制：可见性被裁（→ F3 预案 + 30 自检断言）、adapter 真实写（→ 三层防线：契约禁 import + 零 IO 单测 + 审查逐行核）、off 漂移（→ 三层独立零 diff 论证 + A2 对照基线）、旧测破（→ B1 十文件清单 + A7 亲跑义务）；另补 import 时机与 env 半设两条实操坑。

### R5 · 验收口径机断化收敛

A1 全链逐段对应既有路由真值（pending/decide/resume · router.py:5-10）与 SSE 挂起语义（hitl.waiting / blocked_by=delegation_issue_hitl_required）；A2–A6 均可对命令输出或 registry 断言机断；A7 落到 B1 文件清单。无残留方案分叉 → early_stop。

---

### 自检结论（执行者）

> **待 40 回填**（draft 占位 · A1–A7 核验结论 + 证据 invoke 链接）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-09 | 10-task 落稿（behavior 小 task · 免 SPEC · R0–R5 全轮 · early_stop at R5）· HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending → 30 拒开工 |
