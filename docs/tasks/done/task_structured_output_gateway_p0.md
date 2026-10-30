# Task：Structured Output Gateway · P0（parse_only + 公共 JSON 提取）

> **状态**：completed（P0 50 PASS · ~~同分支待合入~~ **已随 PR #58 MERGED 2026-08-26** · merge commit `15064ed`；修订注记 2026-10-30：原「待合入」为陈旧表述，按磁盘实态更正）  
> **类型**：feature / agent-infra（Structured Output Gateway 首波）  
> **上游 SPEC**：`docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md`（active · `HG-SPEC-SIGNOFF=approved` · 2026-08-26）  
> **总轨**：`structured-output-gateway`（00 切分：P0 / P1 / P2 / P3 四子 task）  
> **实现仓**：本仓 · Open Folder = `ops-desk-api/`  
> **分支**：`task/structured-output-gateway`  
> **无关**：勿与 `task_ops_sync_sender_migration` / `task_rag_answer_mixed_evidence` / `task_retrieval_longquery_analysis` 混改；**禁止**本波实现 Capability Gateway。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `structured-output-gateway-p0` |
| **git_branch** | `task/structured-output-gateway` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单元 mock：合法 JSON / fence / 前后杂讯 / 结构坏引号 deterministic repair / schema 缺字段·类型错 → 失败不得当成功；不连真 LLM/真库 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 行备注增量：结构化解析抽至 `app/ops/structured_output/`（parse_only）；**不**新增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无业务 HTTP / 无用户可见 Wiki 面变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无（无业务 HTTP freeze） |
| **orchestration** | 总轨四子 task：本 task = P0；后续 `structured-output-gateway-p1` / `-p2` / `-p3` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签（20 R1 内容 pass · 维护者授权过程闸） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；审查文 `docs/harness/reviews/task_structured_output_gateway_p0_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅 G-L1 `lg_rag` 备注增量、不新增一级模块；沿用仓内惯例（维护者授权：非新增一级可按惯例） |

---

## 背景与目标

`lg_rag` 多处 `_extract_json_object` / 弱校验解析，缺少统一 host 权威管道。SPEC 对照 Agently output-control，本仓自建 Gateway（**不是** Skill；**禁止**引入 Agently 运行时依赖）。

**P0 完成态**：可复用的 `parse_only`（无 LLM）+ Pydantic 校验 + 公共 JSON 提取（封装/替换现有 `_extract_json_object`）；单测绿。

---

## 范围 / 非范围

**范围**：

- 新建包草案：`app/ops/structured_output/`（最终文件布局由 30 定，须可 import）
- `parse_only(text, *, schema) -> ParseOutcome`（概念名；实现可同名或等价公开 API）
- 管道子集：extract/parse →（可选）deterministic repair → Pydantic schema validate
- 公共 JSON 提取：封装或替换 `app/ops/lg_rag/multi/nodes.py` 的 `_extract_json_object`（调用方改为走公共模块；**本 task 不要求**改 router/supervisor 业务语义）
- 单测：`tests/` 下覆盖 SPEC §8 parse/validate 子集
- G-L1：`lg_rag` 备注一句 + `./scripts/graph-compile.sh` exit 0（若改图谱）

**非范围**：

- `complete_structured` / `max_retries` / `OUTPUT CORRECTION`（→ P1）
- 接入 `supervisor_node` / `router` / `info_extract` 业务路径与 fallback span（→ P2）
- `ensure_keys` / custom validate / 与 `with_structured_output` 并存策略文档（→ P3）
- Capability Gateway 任意实现
- 改 `app/ops/chat/graph.py` 拓扑或 SSE 契约
- 引入 Agently / instructor 等重框架
- 改无关 active task 文件或业务

---

## 验收标准

- [x] 存在可 import 的 Structured Output P0 API：`parse_only`（或 task 注明的公开等价名）支持 Pydantic model schema
- [x] Host 权威：schema 失败 **不得**返回成功业务数据（断言失败 outcome / raise，由实现选型但须单测钉死）
- [x] 公共 JSON 提取：合法对象 / ```json fence / 前后废话 → 抽出 dict；纯非法 → 失败
- [x] deterministic repair：仅结构符号（如中英括号/坏引号类）；**不**改字符串语义内容；有至少 1 个正例 + 1 个「不得改语义」边界
- [x] `lg_rag` 侧 `_extract_json_object` 已委托公共实现，或删除并改为 import 公共函数（行为不劣于现宽容解析；既有 multi 单测不回归）
- [x] 单测 mock、不连真 LLM/真库；`pytest` 触及本 task 测试文件全绿
- [x] `ruff check` 触及路径绿
- [x] `git diff` 相对本分支基线：`app/ops/chat/graph.py` **零改动**
- [x] G-L1 `lg_rag` 备注已更新且 **未**新增一级模块；`./scripts/graph-compile.sh` exit 0
- [x] 无 Agently 运行时依赖写入 `requirements.txt` / pyproject

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 无法抽出 JSON | repair 后仍失败 → ParseOutcome 失败（或等价）；**不**伪造成功 dict | N（P0 无 LLM） | 调用方处理 |
| Schema 不匹配 | 失败 outcome / raise；不得当成功业务数据 | N（P0） | 调用方处理 |
| repair 后仍非法 | 同失败路径 | N | 调用方处理 |
| 误改 `chat/graph.py` / 实现 Capability Gateway / 引入 Agently | 验收打回 | N | 开发可见 |
| 既有 `tests/test_lg_rag_multi.py`（等）回归失败 | 验收打回，修委托兼容性 | Y | 开发可见 |

---

## 依赖

- SPEC：`docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md`
- 讨论：`docs/discussions/2026-08-26_lg-rag-agent-capability-architecture.md`
- 规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 现码：`app/ops/lg_rag/multi/nodes.py`（`_extract_json_object`）· `app/ops/lg_rag/nodes.py`（`_parse_route` 仅对照，P0 可不改）
- 闸片段：`docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 给执行帽（30）必读

1. 本 task 全文（验收 / 非范围 / failure_paths / 人工闸表）
2. SPEC §3 管道 · §3.2 Host 权威 · §3.3 Repair 边界 · §4 P0
3. `FRAGMENT_30_gate_verify_v1_zh.md`（首输出 GATE_VERIFY）
4. `CODING_BACKEND_L2_v1_zh.md`
5. `app/ops/lg_rag/multi/nodes.py` 现有 `_extract_json_object`
6. 硬约束：不改 `chat/graph.py`；不实现 Capability Gateway；不引 Agently；单测 mock

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | 委托 `_extract_json_object` 时行为微差导致 multi 单测碎（用既有用例钉兼容）；P0 未接业务节点，真实解析收益延后到 P2；图谱仅备注增量若漏改则 compile 仍绿但 inform 不完整 |

### R0
P0 只交付无 LLM 的 parse+validate；禁止把 P1 correction 混进本 task。

### R1
包路径用 `app/ops/structured_output/`；G-L1 **不**新增一级模块，只改 `lg_rag` 备注。

### R2
Host 权威优先于「宽容成功」：Pydantic 失败必须失败 outcome。

### R3
deterministic repair 只修结构符号；语义字符串不动。

### R4
P0 可让 multi 委托公共 extract，但 **不**改 supervisor fallback / router / info_extract 业务语义（留给 P2）。

### R5
单测与既有 `test_lg_rag_multi` 合跑不回归；无真 LLM；禁止 Agently 依赖进 requirements。

---

### 自检结论

> 2026-08-26 · 00 机械复检 · **PASS**（30 子 agent [Review](f43bff5d-7783-415d-b35a-ed545919c32b) 实现 + 40 自检）

- [x] 验收标准全部勾选（见 30 invoke）
- [x] ruff / pytest（21 passed：parse_only + multi）绿
- [x] `chat/graph.py` 零 diff
- [x] G-L1 备注 + graph-compile exit 0
- [x] verify PASS

**50 结论**：PASS · P0 可关账；下一棒开 P1

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | Structured Output Gateway P0：`parse_only` + 公共 extract + multi 委托 |
| 归档 | `docs/tasks/done/task_structured_output_gateway_p0.md` |
| PR | [#58](https://github.com/Cyning12/ops-desk-api/pull/58) MERGED |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 00 起草 P0（总轨四切分之首）；闸 pending |
| 2026-08-26 | 20 R1 pass；00 代签 HG-TASK-DRAFT + HG-AUDIT-R1 |
| 2026-08-26 | 30/40 PASS；00 50 机械复检 PASS；CLOSE（暂留 active） |

| 2026-08-26 | 归档：PR #58 MERGED · git mv → docs/tasks/done/ |
