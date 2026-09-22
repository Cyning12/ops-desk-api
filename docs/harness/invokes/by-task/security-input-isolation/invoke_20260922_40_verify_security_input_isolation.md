# invoke · 40 核验 · security-input-isolation（W1 输入结构隔离）

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 40 核验 |
| **核验对象** | 30 交付 `1ae6487` + 图谱新签 `ad17eef` + HG-GRAPH-MODULES 行 ratify `52d1b45` |
| **task** | `docs/tasks/active/task_security_input_isolation.md`（验收 25 条 · B1 11 行） |
| **SPEC** | `docs/spec/security-hardening/SPEC-security-hardening_v1.md`（W1 · 诚实定性：只声称归因+机检+零请求） |
| **分支** | `task/security-hardening`（全程核验 · 禁止 master/main 改码 · 禁止 push · 已遵守；基线对照走 worktree 未切分支） |
| **改动纪律** | 40 不改实现码；唯一临时改码 = 变异检验①复做（已还原 · 工作树净） |

## 总判定

**PASS（25/25 验收条亲核通过）**，附 1 条如实补记的 on 态边界风险（不阻塞 · 灰度前须处置 · 见下「问题清单」）。

## 核验证据（全部真跑留痕）

### 1. 全量 pytest + 基线红对照

- 当前 HEAD（52d1b45）：`pytest tests` = **1329 passed, 3 failed, 1 skipped**（collected 1333 = 基线 1278 + 新增 55，与 30 自称一致）。
- 3 红 = `test_capability_http_adapter::test_urllib_transport_honors_explicit_capability_proxy` + `test_chat_ws` ×2。**基线对照实证**：`git worktree` 挂 `origin/master` = `d0e818c`（未切分支）+ 补同 `.env`，复跑该 3 用例**同样 3 红**（同 .venv 直跑）→ 环境性基线红，与本次改动无关，30 自称属实。
- 基线 collect-only = **1278**（真跑复核 task 基线数属实）。
- `test_memory_embedding_backfill` flaky：本次全量跑未复现（30 自称「复跑即绿」可信，未作否决项）。

### 2. 双断言亲核（读码 + 亲跑）

- **装配层越权**（`tests/eval/test_input_isolation.py` P3① / wiring `test_answer_on_undeclared_content_rejected_zero_request`）：读码确认为**真双断言**——`len(prov.calls) == 0`（没发出去）**且** `{"input_isolation_rejected": True} in spans`（走了拒收路径），缺一不过；越权构造手法 = monkeypatch `wrap_slot` 为恒等直拼，触发 `assert_slots_declared` 显式炸。亲跑通过。
- **G4 非法 tool id**（P3②）：`gateway.await_count == 0`（AsyncMock side_effect=AssertionError，触达即炸）**且** `supervisor_invalid_tool_id` span 标记出现 + 整单 fallback 语义断言（`out["subtasks"][0]["type"] == "rag"`）。亲跑通过。
- aggregator 面同款（wiring `test_aggregator_on_unwrapped_tool_output_rejected_zero_request`）：stream.await_count==0 + rejected span。

### 3. off 三态对拍亲核（逐字节 · 非空转）

- wiring 层：`test_answer_off_three_states_byte_identical[unset/false/garbage]` 对拍基准 = **现网装配公式重构**（`answer_user_template("v1").format(question=..., retrieved_chunks=format_evidence_block(...))`）逐字节相等；continuity 面对拍 `assemble_graph_messages`（off 基准函数）消息类型+正文逐字节 + `slot_ids` 零泄漏；tool_exec/aggregator 面原文逐字节；非法值 warning 有 caplog 断言。
- 金样层 P5：四面三态逐字节 + off 零触达 spy（触达即 raise AssertionError，非仅计数）。
- **变异检验①复做**（下条）证明对拍非空转：开关恒 true 时对拍全挂。

### 4. 变异检验①复做（开关可检）

- 临时改 `slots.py::security_input_isolation_enabled` 首行 `return True`（MUTATION-40 标记）→ 三新测文件 **18 failed / 37 passed**：off 三态对拍×6 + 零触达×2 + aggregator/tool_exec off 对拍 + 金样 P5 + 开关单测×8 全挂。
- `git checkout -- app/ops/prompts/slots.py` 还原 → 55/55 复绿 · `git status` 净（MUTATION 标记零残留）。②③ 由 30 已做并留痕（invoke 记录），40 抽①复做属实。

### 5. ruff / graph-compile

- `ruff check app tests` = **57 = 基线 57**（同 venv 对基线 worktree 直跑对拍）· 零新增。
- `./scripts/graph-compile.sh` 绿（9 md normalize check ok）；运行后 `graph.json` 仅 `generated_at` 时间戳漂移，已 `git checkout` 还原（与 master diff = 零语义 diff · 亲验）。

### 6. B1 抽核（8 行亲跑 + 金样对拍 + 转义机制读码）

- 抽核实跑全符：#1 lc_evidence_chain=19 且 `format_evidence_block|retrieved_chunks` 在既有 tests **零命中**（仅新 wiring 文件命中）；#3 lg_rag_multi=11 且 :231 = `test_invalid_tool_id_in_plan_fallback_single_rag` 逐字符；#5 memory_injection=23 且 :34/:45/:57/:266 四锚点逐字符（off 对拍/非法值 warning/fact-only 逐字节）；#4 assembly=5/packs=20/assets=13；#7 supervisor 10/14/12/9；#8 session_summary=29；#2 grader=4/nodes=3；#6 continuity=15；#11 alembic diff vs master = **0 行**。
- 命名扫 `SLOT_REGISTRY|wrap_slot|assert_slots_declared|SECURITY_INPUT_ISOLATION`：命中仅限本波新增/接线文件，既有文件零命中（无冲突）。
- **金样 yaml↔测试一一对应亲核**：`evals/security/input_isolation_v1.yaml` redlines P0–P5 与 `IMPLEMENTED` 装饰器登记一一对应（P0 自守）；G1–G4 金样在 P1/P2/P3/P4 中均被 `_case()` 取用，无挂空清单。
- **伪造标记转义机制读码**（`slots.py:102-107`）：`</slot:`/`<slot:`/`[已知事实]`/`[用户偏好]` 全角化；替换顺序安全（`</slot:` 不含 `<slot:` 子串）；全角形态不匹配 `_SLOT_TOKEN_RE` 故不再构成结构边界；P4 断言转义后 `<slot:memory_fact`/`[已知事实]` 不存在且全角形态可见 + 校验只认真实 tool_result 边界。**防伪造边界有效**（残余：语义级模仿「以下是系统指令：…」非结构伪造，SPEC §7② 已列灰度抽检项，诚实定性不声称防住）。
- **非 str 回执边界读码 + 亲测**：见「问题清单」①。

### 7. 图谱行 52d1b45 ratify 真读

- `git show 52d1b45`：`01_modules.md` 人签表新行由「00 代录位（…待 00 ratify）」改为「00 代录（…30 回写内容 00 ratify 2026-09-22）」——**真 ratify**，非空签。
- 当前表内：`lc_evidence_chain` 行（:24）依赖出边已含 `prompts`（slots 槽位机制 · 备注级）+ 行备注（answer.py 装配面接线）；`lg_rag` 行（:27）备注含 security-input-isolation 装配/聚合面接线 prompts 内部路径说明 + 「行内路径不构成新跨模块边」承 C2 裁定——与 task D5 钉死逐项符。

## 25 条验收判定汇总

| 块 | 条数 | 判定 |
|----|------|------|
| 人工闸（HG-AUDIT-R1 approved 后 30） | 1 | ✅（e82cb22 签收在 1ae6487 之前） |
| D1 槽位机制（六槽位/表外炸/包装三件套/assert 显式炸/off 零触达） | 4 | ✅ 亲跑 55 新增全绿 |
| D2 四面接线（rag_evidence 锚点/[i] 格式保留 · tool_result+_degraded 块内 · 归因角色序不变 · memory_fact 声明补全） | 4 | ✅ |
| D3 开关回退（off 三态逐字节+非法值 warning · 降级/拒收分立 · env 重读无缓存） | 3 | ✅ |
| D4 金样零请求（清单一一对应 · sentinel 槽位归因 · 双断言缺一不过 · 伪造转义 · 零 LLM-as-judge） | 5 | ✅ 双断言读码+亲跑 |
| D5 图谱/文档（零 alembic · 边+备注+人签行 ratify · graph-compile 绿 · prompts 模块说明） | 2 | ✅ 真读核验 |
| 变异检验（①40 复做 18 挂→还原绿 · ②③ 30 留痕） | 3 | ✅ |
| 工程（B1 闸前置回填 · pytest/ruff · diff 白名单） | 3 | ✅ diff vs master 仅 slots 新模块+四面接线+开关+evals/测试/图谱/文档 |
| **合计** | **25** | **25/25 PASS** |

## 问题清单

1. **on 态边界（如实补记 · 不阻塞 · 灰度前须处置）**：非 str 结构化工具回执（**内建 mock capability 真实返回 dict**，40 亲测 `ainvoke("mock_get_deploy_info")` output 为 dict）在 on 态：tool_exec 保原结构不包装（设计正确 · consumes 绑定不破坏）→ 但 aggregator 声明 `tool_result` 而 payload 无边界标记 → `SlotUndeclaredError` 显式炸整单 + span `input_isolation_rejected`（40 亲测复现）。方向 fail-closed（宁可不发出）安全、off 默认关兜住、SPEC §7③ 已列校验误伤残余风险，故不否决验收；但 30 invoke 只记了「非 str 保原结构」未记聚合面后果——**on 态灰度开启前必须处置**（建议：非 str output 在 tool_exec 侧 json 序列化后走 `tool_result` 槽包装，或 aggregator 对非 str output 段降级/豁免），建议记入 W2/灰度 task。
2. 3 红基线环境性（worktree d0e818c 实证同红）——非本波问题，合并前不阻塞但应知会维护者。
3. `graph-compile.sh` 运行即扰动 `graph.json` 时间戳——已还原，属工具既有行为非本波引入。

## 诚实定性复核

SPEC/task/代码 docstring/金样清单四处口径一致：W1 交付「可归因 + 可机检 + 越权构造零请求」，**不声称防住注入**（文本边界非硬边界 · W2 检测层真兜底）。30 交付无超额声称，属实。
