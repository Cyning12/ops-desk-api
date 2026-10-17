# task_hitl_resume_replay_contract 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_hitl_resume_replay_contract.md`（HITL resume 终帧字段补齐 + 在飞 replay 语义化状态码 · web 联调 FP-1 报回两观察项 · PR #246 已合入）
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30）
> **日期**：2026-10-12 · **审查时仓态**：master `cff3660`（pull 后 · 工作树净 · task 锚点 base `92a8526`，两 commit 间 app/ 零 diff —— 行号复核在 `cff3660` 实测有效）
> **开窗授权**：用户令「pull 之后来进行审核」（承接 #246 阅读会话）
> **需求真值**：ops-desk-web 联调链 T-W2 FP-1 报回（web PR #61 · 2026-10-11 invoke 留痕）——本 task 即该报回的收口载体，背景节两实证锚（S3 replay seq18 / S2 run `640d68970a564fbb8459d8d40cb1c5f6`）自洽
> **结论**：**PASS**（内容零阻塞 · 范围/非范围闭合 · 验收可机断 · 锚点全实证 · 旧测影响面实证为空 · 思考轮 R0–R5 闭合 · 非阻塞观察项 3 条 · 流程闸 HG-AUDIT-R1 / HG-GRAPH-MODULES pending 待维护者签）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS · 零内容阻塞**——两观察项嫌疑点逐行核真与 task 记述一致；范围 F1–F4 与非范围六条互斥闭合；验收 TC1–TC5 均可机断；failure_paths 六行覆盖误伤/伪造/吞错/抢跑四类主险；思考轮控制表完整、early_stop at R5 理由具体 |
| **流程闸** HG-TASK-DRAFT | `approved`（00 联调链委派令代录 · web PR #61 报回链在案 · 本审查不质疑其程序） |
| **流程闸** HG-AUDIT-R1 | `pending`（本审查文落盘即其前置交付 · 维护者签后方 approved · blocks 30） |
| **流程闸** HG-GRAPH-MODULES | `pending`（`graph_change_layer=G-L1` 预判与闸表口径一致 · blocks 30） |
| lint 复跑 | `npx spec-wave@3.3.0 task lint --file docs/tasks/active/task_hitl_resume_replay_contract.md` → **LINT: PASS** exit 0（2026-10-12 本帽复跑 ✓） |
| draft 洁净度 | ✓ PR #246 纯 docs（两文件 +217 行 · 零 app/ 改动）——与 task 非范围首条「起草阶段零改码」一致 |

本审查文按结论机读口径书写：「结论」起首节 · 通过词落节内 · 实质内容充足 · 无否定共现。

---

## 审查要点逐项核对

### 1. 锚点实证（task 依赖节五锚 + 必读列表 · 全部逐行亲读复核 · master `cff3660`）✅

| 锚点 | 实证结果 |
|------|----------|
| `app/ops/hitl/resume.py:124-134` | ✓ `ResumeEventSink.close()` 终帧 done payload 确仅四键 `{run_id, thread_id, status, events_persisted}`——F-OBS-1 缺口核真，与 task 记述逐字一致 |
| `app/ops/hitl/resume.py:85` | ✓ **支持性发现（task 未列）**：`__init__` 已有 `self._started = time.perf_counter()`，且 `_emit` :97 已用 `(perf_counter() - self._started) * 1000` 计 ts_ms——F1 `latency_ms` 修复可直接复用既有计时面，与 sse_stream.py:471/:488 口径天然对齐，30 无需新开计时（观察项 O2） |
| `app/ops/lg_rag/router.py:332-373` | ✓ replay 端点全貌核真：`:344-348` InvalidCursorError→422 · `:350-356` try/except **仅捕** `LgRagRunNotFoundError`→404——「其余异常逃逸即 500」机理成立，与 F-OBS-2 实证（在飞瞬返 500）互洽 |
| `app/ops/lg_rag/event_store.py:139-169` | ✓ `load_events_after` 核真：归属校验 `:145`（`assert_run_owned` :128-136 抛 RunNotFound）→ SQLAlchemy select `:146-156` → `format_sse_event` :157-169。在飞态具体逃逸异常类型此处不可静态钉死——task「根因刻意不锁死留 30 实证」的处置**正确**（R1/R3 留痕一致） |
| `app/ops/lg_rag/sse_stream.py:465-490` | ✓ 对照面核真：waiting_approval done `:465-474` 含 `latency_ms`+status；正常 done `:482-490` 含 `latency_ms`；口径 `int((time.perf_counter() - started) * 1000)` |
| `app/ops/chat/streaming.py:290-297` | ✓ chat done 含 `latency_ms`+`model`（model 来自 `self.run_model`）——前端徽标字段期望形态来源核真 |
| `app/ops/hitl/router.py:418-521` | ✓ `_execute_decided_resume` 起 :418（文件 562 行 · 范围内），docstring「手动 resume 端点与自动触发同源」——非范围第五条「F1 修复天然同源覆盖」有码面支撑 |
| `app/ops/hitl/auto_resume.py:193-235` | ✓ `_claim_and_execute` 内 :229 惰性 import + :231 调用 `_execute_decided_resume(row)`——task 写 `:229-231` 与实际一致 |
| 必读先例 | ✓ `docs/tasks/done/task_lg_rag_sse_subtask_message.md` 与 `task_lg_rag_sse_resume.md` 均在案（freeze `lg-rag-sse-v1` 扩展先例可溯） |

### 2. 旧测 grep 影响面（行为变更类 checklist · F2 改 replay 错误语义属行为变更）✅ 实证为空

20-task-audit K7 提醒：行为变更类 task 验收须含「旧测 grep 影响面」项。本 task 未单列该项，**本帽代查实证影响面为空，裁定不退回 10-task 补列**（TC4 全量对拍 + FP-5「既有 SSE 断言零新增红 CI 拦」实质兜底，且下述实证比 grep 枚举更强）：

| 代查项 | 实证结果 |
|--------|----------|
| 旧测断言「在飞 replay → 500」 | **零命中**——`tests/` 全量 grep replay + 状态码：`test_lg_rag_sse_resume.py:138`（422 非法 cursor）· `:145`（404 未知 run）· `test_multi_replica_dualproc.py:431-445`（跨用户 404 双实例）· `test_lg_rag_sse_token_stream.py:488`（404 unchanged）——全部钉的是 404/422 存续，恰与 TC3 零 diff 断言同向，F2 语义化（在飞 500→409）对旧测**零破坏面** |
| `test_admin_memory_purge.py:184` 409 断言 | admin purge 场景（非 lg-rag replay 在飞面），F2 不触及 |
| `tests/test_hitl_resume_events.py:246/:275` | 断言 `events_persisted` 既有键——F1 增可选键不动既有键，零破坏（FP-5 钉死一致） |
| 红测挂载面 | `test_hitl_resume_events.py` / `test_lg_rag_sse_resume.py` 在案——TC1/TC2 红测先行有现成 fixture 面可挂 |

### 3. 范围 / 非范围闭合 ✅

范围 F1（终帧增 latency_ms 必 · model 裁定）/ F2（在飞 409+Retry-After 或等价语义化）/ F3（契约测试红测先行）/ F4（invoke·图谱·经验捕获·web 回执口径）与非范围六条（起草零改码 / live·chat 对照面零 diff / event_store 写入面不动 / 前端兜底去留归 web 仓 / auto_resume 同源不另立面 / resume 状态机·stranded 守卫零触达）逐条互斥，无越界项。freeze 处置（承 `lg-rag-sse-v1` · 增可选键不新 event_type · 不新 freeze）与先例引用一致。

### 4. 验收可机断性 ✅

| # | 验收 | 可机断性核验 |
|---|------|--------------|
| TC1 | 终帧字段契约（红测先行） | ✓ RED 签名钉死（缺 latency_ms · 与 F-OBS-1 同形）→ GREEN；RED→GREEN 时序 git 可查；model 键按 FP-1 裁定分支断言，两分支证据形态均写明（补则非空串 · 不补则钉案留痕） |
| TC2 | 在飞 replay 语义化 | ✓ 状态机断：409（或裁定等价 4xx）+ Retry-After 正整数 + **500 消失**——三断言均可机断 |
| TC3 | 沉降后零 diff | ✓ 帧序对 master 同输入零 diff + 404/422 存续（router.py:344-356 既有语义锚已核真） |
| TC4 | 反回归全量对拍 | ✓ pytest 基线零新增红 + ruff 触及路径零新增 + graph-compile.sh EXIT=0，三条均命令可查 |
| TC5 | live 对照（40 帽） | ✓ 复现 web S2/S3 同形态 + 回执联调链闭环，照登口径承前例；依赖 live 环境已作 residual risk 明示（R4） |

### 5. failure_paths 覆盖 ✅

六行覆盖四类主险：FP-1 model 不可得（禁伪造 · 裁定留痕）· FP-2 在飞判定误伤沉降主路径（TC3 互锁）· FP-3 409 旧客户端兼容（Retry-After 退避语义 · 影响面写明）· FP-4 在飞根因非单一（fail-closed 不吞错 · 未识别仍 500）· FP-5 增键破坏既有断言（可选键先例 + CI 拦）· FP-6 闸未签即 30（拒开工 · 与本审查流程闸口径一致）。每条均有「可重试/用户可见」双列，无空泛行。

### 6. 思考轮审查（控制表 + 回填闭合）✅

- 控制表五列齐（轮 / 结论 / early_stop / reason / residual_risks），R0–R5 五行无空壳。
- R0–R5 各节正文回填与控制表互洽：R0 框定（同源同面合并为一 task 的裁定有据）· R1 证据（对照面钉死 + 根因不锁死留 30）· R2 方案（开放性显式：model 裁定 · 409 或等价）· R3 反例（零 diff / fail-closed / 可选键三钉）· R4 可测 · R5 收口。
- **early_stop at R5 理由具体**（机理单一明确 · 锚点全亲读核真 · 方案开放性显式留 30 · 再轮无新增信息），residual_risks 诚实（在飞 500 根因未锁死——刻意 · graph_delta 为预判）。本帽复核：两缺口确为契约面小缺口，R5 停轮合理，无被压下的未决分叉。

---

## 非阻塞观察项（不退回 · 30/维护者知会即可）

- **O1**：resume.py:85 `_started` 计时面已存在（见锚点表第 2 行）——F1 实现成本比 task 行文暗示的更低，30 可直接复用；建议在 30 invoke 中照登此实证。
- **O2**：TC2 在飞形态构造方式（如何机断「在飞」）刻意留 30——R3 residual risk 已明示，本帽认可；提醒 30：判定面建议优先复用 `event_store.run_is_terminal`（auto_resume.py:210-212 已用）或沉降标记，避免新造状态面。
- **O3**：TC5 live 对照依赖 web 联调环境，若环境不可得按承前例照登口径处理即可，不构成 TC1–TC4 的替代。

## 阻塞清单

**内容阻塞：零。**

**流程闸（待维护者签 · blocks 30）**：

- HG-AUDIT-R1：pending（本审查文即其前置交付）
- HG-GRAPH-MODULES：pending（G-L1 预判 · 30 按实判回写义务已钉死在 task 元信息）

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-GRAPH-MODULES 改为 approved（维护者 · 日期 · G-L1 预判已与本审查核对一致）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-12 | R1 · 20-task-audit：结论 PASS（内容零阻塞）· 锚点 9 行全实证（master `cff3660`）· 旧测影响面代查实证为空（不退回补列 · TC4 兜底）· 思考轮 R0–R5 闭合（early_stop 理由成立）· 非阻塞观察项 O1–O3 · HG-AUDIT-R1/HG-GRAPH-MODULES pending 待维护者签 · lint 复跑 PASS |
