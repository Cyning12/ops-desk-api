# 40 invoke · task_stage_w_write_expand（核验 30 交付 · 独立复跑 · 不采信自报 + live 全链实测）

| 项 | 内容 |
|----|------|
| **帽** | 40-verify · **日期** 2026-11-05 |
| **task** | `docs/tasks/active/task_stage_w_write_expand.md` |
| **分支** | `agent/stage-w-impl-d5d8a1204a9c`（reset 自 origin/master `51030a4` = PR #327 squash 合入点 · 40 全程零仓内码改动） |
| **核验对象** | PR #327 全量 diff（`git diff 6955b4c..51030a4` · 11 文件）+ master 活链实测 |
| **依据** | issue #323 维护者 comment `6654867916`（40 复跑销项令） |
| **结论** | **PASS（带两项偏差登记 + 一项既有缺陷实证）**——30 自报全部独立复跑成立；live 全链八段达成（末段经测试等价 shim 补位）；发现 1 枚 master 既有潜在缺陷（非 #327 回归） |

---

## 逐项核验结论

### 1. 闸态 verify（master 实跑）✅

`npx spec-wave verify --target . --task docs/tasks/active/task_stage_w_write_expand.md` → **VERIFY: PASS** · 四闸 approved（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-STAGE-W-EXPAND-DESIGN）。

### 2. 红线对拍（`git diff 6955b4c..51030a4`）✅

- 全量 delta 恰 11 文件，全部落在 30 交付面（`ops.write.v1.yaml` / `defaults.py` / `note_store.py` / `manifest.py` / `models.py` / alembic / 测试 ×2 / 图谱 / task 档 / 30 invoke）——无面外改动；
- **红线零命中**：`registry.py` / `policy.py` / `lg_rag/**` / `gateway.py` / `hitl/**` / SSE 事件表 **零 diff**（grep 对拍空集）；
- A5 grep 断言（resume 单路径）与 deny 判序由既有测试全组承接，40 亲跑绿（见第 3 项）。

### 3. 测试独立复跑（不采信 30 自报）✅

- **新测 16 枚**：`pytest tests/test_stage_w_write_expand.py` → **16 passed**（A1 机制全链 / V13 四断言 / FP-4 双形态 / A3 租户隔离 / A2 负样本组 / A5 grep）；
- **关联回归 8 文件**：`pytest tests/test_capability_testing_write.py tests/test_write_approval_gate.py tests/test_capability_manifest.py tests/test_capability_reversibility.py tests/test_capability_idempotency.py tests/test_capability_persistence_db.py tests/test_splittability_hardening.py tests/test_strategy_env_extra_candidates.py` → **全绿**（V13 probe 适配面 / irreversible 口径零影响 / import-linter 白名单 / 判序零 diff 全组钉死）；
- **既有本地产能红基线复核**：master `51030a4` 干净树上 5 枚本地红与 30 档登记一致（diff-whitelist 锚点漂移 ×2 · env 依赖 ×2 · 未提交瞬时态 ×1），**零新增红**。

### 4. live 全链实测（八段达成 · 末段 shim 补位 · 全程留痕）

**环境**：本机 uvicorn :8011（worktree @ `51030a4`）+ PG `opsdesk_test`；env 前置：`OPS_CAPABILITY_EXTRA_MANIFESTS=ops.write.v1.yaml` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=run_note` + `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=ops.write.run_note`（**env 追加口 · 无代码 shim**）+ `OPS_HITL_PERSISTENCE=db` + `OPS_CAPABILITY_PERSISTENCE=db`；maintainer cookie 面登录；测试数据统一前缀 `stagew40`（事后已清理）。

| 段 | 结果 | 证据摘录 |
|----|------|----------|
| ① catalog 可见性 | ✅ | `GET /admin/capability/catalog` → `visible_ids` 含 `ops.write.run_note`（6 枚 · 默认加载面不含 · 独立写 tag 放行生效） |
| ② plans 含写 tool → 挂起 | ✅ | SSE `hitl.waiting`：`blocked_by=capability_write_hitl_required` · `write_intent{capability_id/tenant_id/args 摘要/幂等键模板}` 钉死 · `done{status:waiting_approval}` |
| ③ pending 可见 | ✅ | `GET /hitl/pending`（cookie maintainer 面）列出该申请（owner 过滤生效） |
| ④ decide(approved) | ✅ | HTTP 200 · `status=approved` · `persisted=true`；**重复 decide → 409**「申请已是 approved」（既有守卫 live 实证）；decide(rejected) settle 路径另轮实证 |
| ⑤ resume 受理 | ✅ | `POST /resume` → `resume={status:accepted}` 秒回（异步单飞）；写窗 409「Resume is writing new events; retry after it settles」**live 实证**（F1/F2 语义原样） |
| ⑥ replan carry | ✅ | resume 后 supervisor replan **保号** `…:1` + **args 原样保留**（T4 契约 live 实证 · seq 11 载荷） |
| ⑦ 消费命中 → 真落笔 | ✅（shim 补位） | `capability_write_approval_consumed{approval_id=hitl_bf2cc75d652f4a95a283}` → 便签行落库：`tenant_id=ops-desk-pilot / approval_id 同单 / subtask_id / idempotency_key=stagew40-live-req7`；回执行 `ok=t · write_confirmed=t · receipt_id · captured.note_id`；幂等行 `status=done · attempts=1`——**A4 审计串链 live 四照对齐** |
| ⑧ 收尾帧 | ✅ | `answer`（aggregator）→ `critic` → `done{status:resumed}`（resume 收口契约帧 · `resume.py:131` · freeze 语义原样） |

### 5. 偏差登记与缺陷实证

**偏差 #1（测试等价 shim）**：段⑦需 shim 补位——live 实证（无 shim 两轮，run `fab290e9` / `c02daf71`）发现 **master 既有潜在缺陷**：`_worker_state`（`lg_rag/multi/nodes.py:1359`）构造 Send 载荷**不含 `run_id`**（仅 delegation on 时附带）——Send 载荷即工人所见全部 state，tool_exec 的写审批消费门 `_run_id_of(state)` 得空串 → 早退 fail-closed → **resume 后重下发永远再拦**（闸静默失效）。诊断链：DBG 包装器（仅进程内 monkeypatch · 仓内零改动）实证 state 键集仅 5 枚无 `run_id`；同参数离进程复现匹配成功 → 锁定丢键面。影响面 = 全部写能力（含 testing.write.echo）· PR #303 时期潜伏 · 单元测试全部直调 tool_exec（自带全 state）故从未暴露。**非 #327 回归**（#327 前后行为一致）。shim（`_worker_state` 补 `run_id`）后全链八段达成 → 修复形态已验证。处置建议：**另立 fix task**（一行载荷补键 + 回归测试），维护者裁定。

**偏差 #2（live 环境噪点）**：本机 siliconflow 偶发单调用挂起数分钟（llm 层有界重试内），resume 后 replan 墙钟拉长（run `12b8a6dd` 全链 240s）——环境性，非仓码语义；所有帧最终如实落盘，未伪造。

**偏差 #3（全量套件环境纪律）**：worktree 承主 checkout `.env` 会让 CI skip 面外的本地用例红（delegation enforce / db persistence 族）——40 复跑按先例以**显式空值中和**（`VAR=` 前置 · 防 load_dotenv 回填）取数，与 30 档口径一致。

### 6. 终态工程面

| 项 | 结果 |
|----|------|
| 40 全程仓内码改动 | **零**（仅本 invoke + task 档 40 自检回填入 PR） |
| `ruff check app tests` | 零新增（40 无码改动） |
| `./scripts/graph-compile.sh` | EXIT=0（master 态） |
| `npx spec-wave task lint` | LINT: PASS |

## FAIL 判定扫描

30 无造假：红线零 diff 对拍成立 / 16 枚新测独立复跑全绿 / Q3 迁移 head 链正确（`20261105_capability_notes` 自 `20260923_memory_episodes`）/ V13 谓词语义亲跑四断言 / live 八段（shim 补位）与机制段互证。两项偏差均如实登记，不阻塞。

## 给维护者的裁定建议

1. **40 PASS 可 CLOSE**（PR 待 lead 终审）；task 档移 `docs/tasks/close/` 按仓内既定收口；
2. **另立 fix task**：`_worker_state` Send 载荷补 `run_id`（偏差 #1 · 修复形态已被 shim 实证 · 建议一并补「Send 载荷回归测试：工人可见 state 键集」防再发）；
3. supervisor system prompt 未文档化 `args` 字段（写工具结构化入参靠提示词即兴）——可纳入后续 prompt 资产波次视野（非阻塞）。

## 环境注记

- live 证据文件（ephemeral · 摘录已嵌上文）：/tmp/stagew40_sse*.log · /tmp/stagew40_replay*.log · /tmp/stagew40_server.log · /tmp/stagew40_serve2.py（DBG+shim 启动器 · 不入仓）；
- 本机代理 env 已按先例剔除（httpx bracketed IPv6 no_proxy 坑）；`.env` 承主 checkout 仅 live 用，40 档不提交；
- 测试数据前缀 `stagew40` 三表 + 事件/审批行已清理（DELETE 明细：notes 1 / receipts 1 / idempotency 1 / hitl 4 / events 347）。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-11-05 | 40 核验落盘：verify 闸态 / 红线对拍 / 16+8 文件独立复跑 / live 全链八段实录（shim 补位）/ `_worker_state` 丢 run_id 既有缺陷实证与另立 task 建议 / PASS 带偏差登记 |
