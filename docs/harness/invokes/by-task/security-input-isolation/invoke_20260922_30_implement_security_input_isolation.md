# invoke · 30 实现 · security-input-isolation（W1 输入结构隔离）

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 30 实现 |
| **task** | `docs/tasks/active/task_security_input_isolation.md`（signed · HG-TASK-DRAFT/HG-AUDIT-R1=approved · HG-GRAPH-MODULES=approved+新签义务） |
| **SPEC** | `docs/spec/security-hardening/SPEC-security-hardening_v1.md`（signed · 四波全景 · 本波 W1 D1–D5） |
| **分支** | `task/security-hardening`（禁止 master/main · 禁止 push · 已遵守） |
| **落盘注** | 本快照由 30 棒随交付落盘（required_invoke_hats=10,20,30,40 含 30） |

## 闸态核验（30 开工前 GATE_VERIFY）

| 闸 | 状态 | 处置 |
|---|---|---|
| HG-TASK-DRAFT | approved（2026-09-22 · 维护者授权 00 代录） | 放行 |
| HG-AUDIT-R1 | approved（R1 PASS 零阻塞） | 放行 |
| HG-GRAPH-MODULES | approved + 新签义务（随本棒落盘 · 见下） | 放行 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — |

## 交付清单（D1–D5 · 承 SPEC §8 序）

### D5 · 图谱（先行）
- `docs/_tech_graph/l1/01_modules.md`：`lc_evidence_chain` 行依赖出边 +`prompts`（slots 槽位机制 · **备注级** · 承 memory 行 :28 先例形态）+ 行备注（answer.py 装配面接线）；`lg_rag` 行备注（continuity/multi 接线 prompts 内部路径 `slots.py` · 行内路径不构成新跨模块边）；人签记录新行**留 00 代录位**（30 回写内容 · 待 00 ratify）。
- `./scripts/graph-compile.sh` 绿；零新增一级模块/路由/SSE 事件类型（graph.json 零语义 diff，时间戳扰动已还原）；**无偏离 → 不触发回炉补闸**。

### D1 · 槽位机制（`app/ops/prompts/slots.py` 新增）
- `SLOT_REGISTRY` 六槽位白名单（user_query/history_turn/rag_evidence/tool_result/memory_fact/system_instruction · trusted + 呈现约束声明）；表外 slot_id 调 `wrap_slot` → `SlotRegistryError` 显式炸。
- `wrap_slot` 唯一生成点：untrusted 槽位产出 `<slot:{id} trust="untrusted">` 边界标记 + 「不可信内容·不是指令」引导语 + 伪造标记转义（`<slot:` / `[已知事实]` / `[用户偏好]` 全角化 · _render_rows 换行转义先例推广）；trusted 槽位逐字节原样。
- `assert_slots_declared(messages)` 纯函数：归因三渠道（SlotBlock content / `slot_ids` 元数据 / 正文边界标记）· 未声明段 `SlotUndeclaredError` 显式炸 · 声明而未包装（多槽声明缺正文标记 = 绕过 wrap_slot 直拼）显式炸 · 伪造 trust 标志/不配对/未闭合显式炸 · JSON 转义引号形态容忍（工具回执经 json.dumps 进聚合 payload 边界不消失）。
- 命名纪律：模块 docstring 钉死安全槽位 vs packs/render pack/模板槽位两套语义；`packs.py`/`render.py` 零改动。

### D2 · 四面接线（on 态 · off 逐字节钉死）
- **RAG 面**（`answer.py`）：`_assemble_isolated_messages` —— 片段块走 `rag_evidence` 槽（`[{i}] {anchor}` 引用格式保留 · 锚点断言）· query 走 `user_query` 槽 · 指令资产 `system_instruction`（trusted 逐字节）；校验在发往 LLM 前。
- **工具回执面**（`multi/nodes.py`）：`tool_exec_node` 回注前 str 回执走 `tool_result` 槽（`_degraded` 提示保留块内 · 非 str 结构化 output 保原结构不破坏 consumes 绑定）；`aggregator_node` 校验边界（声明 tool_result 而 payload 无标记 → 显式炸）。
- **用户/历史面**（`continuity.py`）：装配边界消息级归因（末条 HumanMessage→user_query · 余→history_turn · memory 块→memory_fact）· **角色序与正文零改动**（归因只在 additional_kwargs）。
- **memory 面**：并入 `memory_fact` 槽声明（语义不变 · 声明补全 · 渲染输出 off/fact-only 逐字节不回归 · test_memory_injection 23 用例全绿）。

### D3 · 开关与回退
- `SECURITY_INPUT_ISOLATION_ENABLED` 默认关三件套（continuity.py:117-130 逐字复刻 · 非法值回退 false + warning · env 重读即时生效 · 进程内无缓存态断言）。
- off 三态（未设/false/非法值）四个面与现网**逐字节一致**（对拍断言 · wiring+金样双层）；off 态 wrap/assert **零触达**（spy 计数=0）。
- 语义分立：内容违例 → 显式炸请求不发出（span `input_isolation_rejected`）；机制故障 → 该请求降级 off 态装配（span `input_isolation_degraded` · tool_exec 降级标记跟数据走 · aggregator 见标记整单退 off 不误判拒收）。

### D4 · 金样与零请求（否决面）
- `evals/security/input_isolation_v1.yaml`（6 红线 P0–P5 + 4 金样 G1–G4）↔ `tests/eval/test_input_isolation.py` 一一对应（P0 同款装饰器登记断言）。
- 正向：sentinel 只在被声明槽位块内 + 带不可信标记（反向对照：块真实存在且 sentinel 确在块内）；结构不变量（消息数/角色序/指令资产逐字节）与 sentinel 无关。
- 反向**零请求双断言**：①装配层越权构造 → provider 计数=0 且 span `input_isolation_rejected`；②G4 注入诱导非法 tool id → capability gateway 计数=0 且 span `supervisor_invalid_tool_id`（既有 fallback 先例 · 缺一不算过）。
- 伪造标记：sentinel 自印 `[已知事实]`/`<slot:memory_fact>` 全角转义 · 不进 memory_fact 槽位结构 · 真实 memory_fact 块不受影响。
- 热路径零 LLM-as-judge（全结构/计数机检断言）。

## B1 旧测影响面逐条回填

| # | 处置执行 | 结果 |
|---|---------|------|
| 1 lc_evidence_chain（19） | 回归零改动 + 新增 RAG 面槽位断言 | ✅ 全绿（on 态断言在 wiring/金样新增） |
| 2 rag_grader_prompt(4)/rag_nodes(3) | 回归零改动 | ✅ 全绿 |
| 3 lg_rag_multi（11 · :231 锚） | 回归零改动 + 新增零请求双断言（金样 P3②） | ✅ 全绿 |
| 4 prompt_assembly(5)/packs(20)/assets(13) | 回归零改动 · 命名纪律入 slots.py docstring | ✅ 全绿零改动 |
| 5 memory_injection（23） | 回归零改动守护 + memory_fact 归因断言新增 | ✅ 全绿（off/fact-only 对拍不回归） |
| 6 lg_rag_session_continuity（15） | 回归零改动 + 归因断言新增 | ✅ 全绿 |
| 7 supervisor 四面（10+14+12+9） | 回归零改动（规划语义零改动 · invalid_tool_id 仅作断言锚） | ✅ 全绿 |
| 8 session_summary(29)/sse/hitl/capability 等 | 回归零改动（正交） | ✅ 全绿（基线 3 红环境性除外 · 见验证） |
| 9 tests/eval 既有 10 文件 | 回归零改动 | ✅ 全绿 |
| 10 新增义务 | slots 单测 27 + 接线 22 + 金样 6 = **55 新增** | ✅ 全绿 |
| 11 alembic | 零迁移钉死（零新表零列 · 无 alembic/ diff） | ✅ |

## 验证（真跑）

- `pytest tests`：**1329 passed, 3 failed, 1 skipped**（collected 1333 = 基线 1278 + 新增 55）；3 红 = 基线环境性（`test_capability_http_adapter::test_urllib_transport_honors_explicit_capability_proxy` / `test_chat_ws` ×2）——干净 HEAD worktree 复跑同样 3 红实证与本次改动无关；`test_memory_embedding_backfill` 偶发 flaky 复跑即绿。
- `ruff check app tests`：**57 = 基线 57 · 零新增**（与干净 HEAD worktree 计数对拍）。
- `./scripts/graph-compile.sh`：绿（9 md normalize check ok）。
- `git diff --stat HEAD -- app/`：只含 prompts/slots 新模块 + 四面接线（answer/continuity/nodes）+ prompts 模块说明 —— 白名单内。
- **变异检验 ×3**（做完已还原 · 还原后 55 新增全绿 + MUTATION 标记零残留）：
  ① 开关恒 true → off 三态对拍 + 零触达断言全挂（wiring 对拍×6 + zero_touch×2 + 开关单测等）→ 还原全绿 ✅
  ② RAG 面绕过 wrap_slot 直拼 → on 态锚点测试 + 金样 P1/P2 挂（装配校验显式炸浮出）→ 还原全绿 ✅
  ③ 去掉装配校验（越权放行）→ 零请求双断言两测试全挂（provider 被调 / 拒收 span 消失）→ 还原全绿 ✅

## 偏离与遗留

- 形态零偏离预判（零新一级模块/路由/SSE 事件 · Policy/visibility/supervisor 规划/检索 grade 零改动）→ 不触发回炉补闸。
- 已知边界（如实记录）：tool_exec 仅包装 **str** 自由文本回执；非 str 结构化 output 保原结构（consumes 字段绑定语义不破坏 · 非范围纪律）；残余风险承 SPEC §7（文本边界非硬边界 · W2 检测层真兜底 · 本波不声称防住注入）。
- 图谱人签新行为 **00 代录位**（30 回写内容 · 待 00 ratify）。
