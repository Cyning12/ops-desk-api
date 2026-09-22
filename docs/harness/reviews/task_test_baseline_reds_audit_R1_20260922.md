# task_test_baseline_reds R1 审查文（20-task-audit）

> **审查帽**：20-task-audit · R1
> **task**：`docs/tasks/active/task_test_baseline_reds.md`（bugfix 轨 · 双轨跳 SPEC · 40 invoke 观察项 ≈ mini-SPEC）
> **task_slug**：`test-baseline-reds` · **分支**：`fix/test-baseline-reds`（base master）
> **审查日期**：2026-09-22 · **审查方式**：读 task/invoke/代码锚点 + 亲跑三缺陷复现 + CI workflow 核验

---

## 一、结论摘要

| 维度 | 结论 |
|------|------|
| 总体 | **通过 · 零内容阻塞** |
| 范围/非范围 | 通过（边界钉死，B1 影响面已实扫） |
| 验收标准 | 通过（全部断言化 · 前红后绿基线已录） |
| failure_paths | 通过（7 条 · 每条可执行可复核） |
| 思考轮 R0–R5 | 通过（early_stop at R3 合规 · 理由具体 · 风险已注） |
| 返工项 | **无** |

**结论**：PASS（零阻塞 · 无返工项）。task 内容可交维护者签 HG-AUDIT-R1；审查文不附 30 Prompt。

### 流程闸（与内容分列）

| human_gate | status | 说明 |
|------------|--------|------|
| HG-TASK-DRAFT | pending | blocks 20-R1/30 · 维护者签后 00 代录 |
| HG-AUDIT-R1 | pending | blocks 30 · 本审查零阻塞后维护者签 |
| HG-GRAPH-MODULES | approved | 2026-09-22 00 代录 · graph_change_layer=none 与实扫一致 |
| HG-PILOT-OPSDESK-GLAYER | n/a | 非物理分层试点 task |

**流程观察（非内容阻塞）**：HG-TASK-DRAFT blocks_hats 含 20-R1 而 status 为 pending；本 R1 审查由父帽委派启动并交付，维护者须在 30 下发前补签 HG-TASK-DRAFT 与 HG-AUDIT-R1 两道闸。

---

## 二、三缺陷根因实证复核（亲跑 · 与 task 基线对照）

### D1 · chat_ws ×2 —— 复现一致

- 本审查亲跑：`pytest tests/test_chat_ws.py -q` → **2 failed / 4 passed**（`test_ws_message_streams_events` + `test_ws_second_message_while_active_rejected`），与 task §背景基线逐字一致。
- 伴随 `RuntimeError: Event loop is closed` teardown 噪音，与 task「噪音 · 非根因」定性一致。
- 测试库实测：`ops_knowledge_chunks` 不存在，public 共 26 表 —— 与 task L3（schema 漂移）及 R3「验证毕已 drop 表恢复红基线」记载一致。

### D1 断言过期论断 · 读码复核 —— 成立

- `tests/test_chat_ws.py:160` 期望 `[run.start, thinking, thinking, answer, answer, done]`（grep 核实行号与序列）。
- 现行图拓扑：`app/ops/chat/graph.py:45-46` general/overview → `retrieve`，`:50` retrieve → grade —— 检索链为现行接线。
- `app/ops/chat/rag_nodes.py:107` retrieve 节点必发 `tool_result` 事件，`:175` grade 节点再发一次。
- 推论：环境层（L2 代理 env / L3 缺表）即使全修，事件流 index 2 起必含 `tool_result`，与断言期望的 `thinking` 不匹配 —— **「断言过期为主根因、不可省略」论断成立**。task 据此钉死「断言对齐现行拓扑 · 不回退图拓扑」，方向正确。

### D2 · capability proxy —— 复现一致

- 本审查亲跑：`pytest tests/test_capability_http_adapter.py -q -k proxy` → **1 failed / 1 passed**，失败为 `tests/test_capability_http_adapter.py:384: Failed: DID NOT RAISE`，与 task 基线逐字一致。
- 读码核实：`http_generic.py:306-313` `_capability_opener` 显式挂 `ProxyHandler({"http": "http://127.0.0.1:1"})`；目标 host 为 127.0.0.1（`_local_json_server` 固定 loopback）。macOS 系统级 loopback 旁路使 `proxy_open` 短路为直连 → 本地 JSON 服务应答 200 → DID NOT RAISE。Linux 无此旁路 → CI 绿。「本地红 CI 绿」OS 差异论断成立。
- 同文件 `test_urllib_transport_bypasses_ambient_http_proxy` 断言语义相反（绕过环境代理→应调通），不受旁路影响 —— task「碰巧不受影响」表述与读码一致。

### D3 · backfill flaky —— 复现一致（40% 翻车率坐实）

- 本审查亲跑单测连跑 15 次：**6 failed / 9 passed = 40% 翻车率**，与 task 记载的 8/20≈40% 同量级同性质。
- 抓取一次失败断言实据：`assert (3 == 2)`，`BackfillReport(status='pass', embedded=3, remaining_null_active=0)` —— 与 task 竞态链（注入行 uuid 落 keyset 水位后 → 被下一页扫到并嵌入 → embedded==3/status=pass 翻车）逐点吻合。
- 读码核实竞态链：`scripts/memory_embedding_backfill.py:215-222` keyset 分页 `id > last_id ORDER BY id ASC`；`tests/test_memory_embedding_backfill.py:559` 并发注入 `uuid.uuid4()`，注入时机在首页 embed 期间（`fake.on_text = concurrent_write`，行 567）。根因定位成立。

---

## 三、「CI 假绿」论断核验 —— 属实

- `.github/workflows/pytest.yml`：ubuntu-latest，env `DATABASE_URL=postgresql+asyncpg://u:p@localhost:5432/test`（行 26），**jobs 内无 postgres service 定义**（全文核实，无 services: 节）。
- `tests/conftest.py:74-93` `_setup_test_database`：asyncpg 连 admin DSN 失败 → `DB_AVAILABLE=False` → 行 115 起所有 DB 用例走 `skipif(not DB_AVAILABLE)`。
- 结论：CI 上 chat_ws 全部 DB 用例为 skip 绿，三缺陷从未在 CI 真跑 —— **「CI 假绿」论断属实**。task 将其处理为 F4 注记（不修 CI · 另 task 议），非范围划定合理；验收 A4 已写明「CI 绿不视为真跑的证据」，未把 skip 绿当真跑证据使用，表述严谨。

---

## 四、范围 · 钉死契约 · failure_paths 核对

| 核对项 | 结果 |
|--------|------|
| 改动边界「只改 tests/（含 conftest）· app//scripts//alembic//.github/ 零 diff」 | 钉死契约 + failure_paths（git diff 检出→40 拒收）+ 验收 A6 三处互锁；当前分支 `git diff master...HEAD --stat` 仅 docs/（task + 10 份 10 帽 invoke），现状一致 |
| 禁止 skip/xfail/「本地跳过」掩盖 | 钉死契约首条 + failure_paths 专列 + fix_verdicts invoke 排除岔路，三处一致 |
| D1 修复语义（对齐现行拓扑 · 打桩确定化 · 不回退图） | 与读码结论匹配；打桩面（provider/embedder/hybrid_recall 最小面）留 30 裁量，R2 residual_risks 已注 |
| D1 环境隔离（代理 env 净化 · 补 ops_knowledge_chunks DDL） | conftest.py:23 已有 `OPS_CHAT_TRACER setdefault` 先例可对齐；`_create_test_schema`（:150-190）已有幂等 ALTER 补丁模式可复用；DDL 对齐源 `alembic/versions/20260808_rag_chunks.py` 列入只读依赖 |
| D2 修复语义（monkeypatch proxy_bypass · 不改生产语义） | 与根因匹配；`_capability_opener` 空 dict 不走代理的刻意设计已注明不动 |
| D3 修复语义（确定性小 id · 不改分页逻辑） | 与失败实据匹配；「keyset 幂等性是生产正确性来源」排除改生产岔路，裁定稳健 |
| failure_paths（7 条） | 每条触发条件→系统行为→可重试→用户可见齐全；含 env 净化误伤 integration 用例的注记路径 |
| B1 旧测影响面 | 五面（WS/TestClient、代理 env、run_backfill、conftest 共有面、SSE 对照）实扫落盘；本 bugfix 属测试行为变更类，「旧测 grep 影响面」项已具备（B1 表），checklist 提醒项满足 |

---

## 五、验收标准核对（断言化 · 前红后绿）

- 全部 9 条 checkbox 均为可机读断言：A1/A2 前红基线已录数字（2f/4p · 1f/1p），后绿目标为确定数（6 passed · 2 passed）；A3 双门槛（单测 20 连跑全绿 + 全量 3 连跑零复发）；A4 双环境（本地真 PG 确定性绿 + CI 零新增红，且明示 CI 绿 ≠ 真跑证据）；A5 全量回归含 B1 五处与 ≥99 条基线；A6 git diff 路径白名单；ruff 与 task lint 命令化。
- 首条人工闸序约束（HG-AUDIT-R1 approved 后方可勾码项）与闸表 blocks 关系一致。
- 本审查亲跑确认三条「修复前红」基线今日仍成立（见 §二），前红后绿链条可执行。
- 非阻塞措辞建议（不退回）：A2 末句「monkeypatch 不打桩时不依赖宿主 OS 旁路列表语义」语义为「打桩后断言与宿主 OS 无关」，30 执行时按此理解即可。

---

## 六、思考轮 R0–R5 审查 —— early_stop at R3 合规

| 检查点 | 结果 |
|--------|------|
| 控制表回填 | R0–R3 结论/early_stop/reason/residual_risks 逐轮回填；R4/R5 标「未开 · early_stop at R3」，actual_last_round=R3 明确 |
| R3 交叉验证实质性 | 反向实证（补表 + 净化 env 后实得 index 2 = `tool_result`）把「环境层全修仍红」坐实，直接排除「30 只修环境层收不了尾」的返工路径 —— 是有信息量的验证轮，非凑轮 |
| early_stop 理由 | 「三层缺陷根因全部实证闭环 · 修复方向唯一且无方案分叉值得展开」—— 与 §二复核结论一致：三条岔路（skip 掩盖 / 回退拓扑 / 改生产码）已在 R2 逐条排除 |
| residual_risks | R2（D1 打桩面裁量）与 R3（CI 假绿只注记不修）均已注明，均有归属（30 裁量 / 另 task 议） |
| 收尾动作可核 | 「验证毕已 drop 表恢复红基线」经本审查实测成立（26 表 · 无 ops_knowledge_chunks） |

---

## 七、退回项

**无。**

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文件 §一）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 附 · 本审查亲跑证据摘要

| 命令 | 结果 | 对照 task 基线 |
|------|------|----------------|
| `pytest tests/test_chat_ws.py -q` | 2 failed / 4 passed（含 Event loop is closed 噪音） | 一致 |
| `pytest tests/test_capability_http_adapter.py -q -k proxy` | 1 failed / 1 passed（DID NOT RAISE） | 一致 |
| `test_reconcile_mismatch_marks_failed` ×15 连跑 | 6 failed / 9 passed（40%） | 与 8/20≈40% 一致 |
| 失败断言取样 | `assert (3 == 2)` · status='pass' embedded=3 remaining=0 | 与竞态链吻合 |
| 测试库 pg_tables | 无 ops_knowledge_chunks · 26 表 | 与 L3/R3 记载一致 |
| `npx spec-wave task lint` | PASS | 验收项预核通过 |
| `git diff master...HEAD --stat` | 仅 docs/（task + 10 份 invoke） | 改动边界现状一致 |

## 附 · 交接物

- 审查文：`docs/harness/reviews/task_test_baseline_reds_audit_R1_20260922.md`（本文件）
- 20 invoke 快照：`docs/harness/invokes/by-task/test-baseline-reds/invoke_20260922_20_audit_r1.md`（required_invoke_hats 含 20 · 必落盘）
