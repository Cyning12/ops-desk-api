# Task：hitl-resume-replay-contract（HITL resume 终帧字段补齐 + 在飞 replay 语义化状态码 · web 联调 FP-1 报回两观察项）

> **状态**：done（CLOSED 2026-10-17 · PR [#248](https://github.com/Cyning12/ops-desk-api/pull/248) MERGED（squash `acac5e6` · 2026-10-13T03:40:29Z · 交付分支 `task/hitl-resume-obs-drafts`）· F-OBS-1/2 闭环（终帧 latency_ms 钉死 · 在飞 replay 409+Retry-After:2 · 500 消失）· TC1–TC5 全勾 · 40 live 对照 PASS（附件 16 件）· 20 R1 落盘 PASS · 三闸 approved · CLOSE 归档 done/ · 细节见 CLOSE 文档 [`../close/close_hitl_resume_replay_contract_20261017.md`](../close/close_hitl_resume_replay_contract_20261017.md)）  
> **类型**：契约缺口收口（ops-desk-web 联调链 T-W2 FP-1 报回 · web PR #61 · 纯后端 SSE/HTTP 契约面）  
> **依据**：ops-desk-web 联调链 T-W2 invoke 留痕（2026-10-11 · S3 replay seq18 / S2 断线 replay 实测）· 本仓锚点亲读核真（base master `92a8526`）  
> **分支**：`task/hitl-resume-obs-drafts`（base master `92a8526`）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl_resume_replay_contract` |
| **git_branch** | `task/hitl-resume-obs-drafts` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 契约测试口径：resume 终帧字段断言（红测先行：现形状 RED → 补齐 GREEN）+ 在飞 replay 状态码断言（409/Retry-After）；live 复跑对照留 40 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（改 `app/ops/hitl/resume.py` 终帧组装 + `app/ops/lg_rag/router.py` replay 错误语义 · 图谱模块行为表述面 · 30 按实判回写） |
| **graph_delta** | 预期 `docs/_tech_graph/l1/01_modules.md` hitl / lg_rag 行备注回写（按实判 · 无模块增删） |
| **graph_delta_note** | 若 30 实证后确认零图谱表述面变化，改填 `none` 并注理由 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站/WikiTrack 变更（SSE 帧字段 + HTTP 错误语义收口） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（红测先行）→ 40（含 live 对照）→ PR+CI 绿 → CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**不**新 freeze；不新 event_type；resume 终帧 done payload 增 `latency_ms`/`model` 可选键 · replay HTTP 增在飞态 409 语义 · 承 `task_lg_rag_sse_subtask_message` payload 增可选键先例 · 回写 05 按实判） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 初稿人扫 · 00 联调链委派令代录（web 联调链 T-W2 FP-1 报回 · web PR #61 · 2026-10-11） |
| HG-AUDIT-R1 | approved | 30 | 20 R1 落盘 PASS（`docs/harness/reviews/task_hitl_resume_replay_contract_audit_R1_20261012.md` · 内容零阻塞）· 维护者签 2026-10-13 |
| HG-GRAPH-MODULES | approved | 30 | G-L1 预判与 20 R1 核对一致 · 30 按实判回写义务存续 · 维护者签 2026-10-13 |

---

## 背景与目标

### 来源（FP-1 纪律报回）

ops-desk-web 联调链 T-W2（2026-10-11 · invoke 留痕在案）实证暴露两个后端观察项，按 FP-1 纪律报回本仓另立 task；来源标注：**「ops-desk-web 联调链 T-W2 FP-1 报回（web PR #61）」**。前端已做零迁就兜底（缺字段显示 0/''），显示瑕疵仍在，后端契约面收口在本仓。

### F-OBS-1：resume 终帧 done 缺 latency_ms/model

- **实证**：web 联调 S3 replay seq18（2026-10-11 · T-W2 invoke 留痕）：HITL resume 终帧 `done{status:'resumed'}` 无 `latency_ms`/`model` 字段 → 前端 lastDone 徽标显示「完成 · 耗时 0ms」。
- **嫌疑点（10 亲读核真 · base master `92a8526`）**：`app/ops/hitl/resume.py:124-134` `ResumeEventSink.close()` 终帧 payload 仅 `{run_id, thread_id, status, events_persisted}`——确无 `latency_ms`/`model`。
- **对照面**：
  - lg-rag live 流终帧 `app/ops/lg_rag/sse_stream.py:482-490`（done 含 `latency_ms`）与 `:465-474`（waiting_approval done 含 `latency_ms`+status）；
  - chat 流终帧 `app/ops/chat/streaming.py:290-297`（done 含 `latency_ms`+`model`——前端徽标字段期望的形态来源）。
- **影响**：前端徽标恒显「耗时 0ms」· 模型名空；前端已兜底（零迁就），纯显示瑕疵，契约不齐是根因。

### F-OBS-2：run 在飞时 replay 瞬返 500

- **实证**：web 联调 S2 断线 replay 实测（run `640d68970a564fbb8459d8d40cb1c5f6`）：run 在飞（未沉降）时 `POST /lg-rag/replay` 瞬返 `500 Internal Server Error`；沉降后恢复 `200` 流式。
- **嫌疑点（10 亲读核真）**：`app/ops/lg_rag/router.py:350-356` replay 端点 try/except **仅捕** `LgRagRunNotFoundError`→404；在飞形态下 `load_events_after`（`app/ops/lg_rag/event_store.py:139-169`）读取路径抛出的其他异常无捕 → 逃逸为 500。**根因（在飞态具体异常类型）刻意不锁死，留 30 实证钉案**。
- **建议语义**：409 Conflict + `Retry-After` 头（run 在飞 = 资源状态冲突 · 客户端可语义化退避重试，而非把 500 当致命错误）。

**目标**：(1) HITL resume 终帧 done payload 补齐 `latency_ms`（必）与 `model`（可取得则补 · 不可得则裁定留痕），与 live 流/chat 流终帧字段口径对齐；(2) replay 端点在飞形态返回语义化状态码（409 + Retry-After · 或 30 实证后裁定的等价语义化方案），500 仅在真实内部错误时出现；两改动对既有沉降后行为零 diff。

## 范围

- **F1**：`app/ops/hitl/resume.py` `ResumeEventSink.close()` 终帧 done payload 增 `latency_ms`（自 open/构造起计 · 对齐 sse_stream.py:471/:488 口径）；`model` 键补齐可行性 30 实证裁定（resume 路径是否持有 run_model · 不可得则钉案照登不硬造）。
- **F2**：`app/ops/lg_rag/router.py` replay 端点在飞形态语义化：识别在飞态（30 实证钉死判定面）→ 409 + `Retry-After`（或等价语义化 4xx · 裁定留痕）；既有 404/422 语义零 diff。
- **F3**：契约测试（红测先行）：resume 终帧字段断言（修复前 RED · 修复后 GREEN）+ 在飞 replay 状态码断言；沉降后 replay 200 流式行为零 diff 断言。
- **F4**：invoke 留档 / 图谱备注按实回写 / 经验捕获；web 侧联调复跑口径回填（40 · 告知 web 仓可去兜底非本 task 范围）。

## 非范围

- **app/ 代码本任务起草阶段零改动**（本 PR 纯 docs）；30 改码须 HG-AUDIT-R1 approved 后另棒。
- **live 流/chat 流终帧形状**（sse_stream.py:465-490 · chat/streaming.py:290-297）——对照面，零 diff。
- **replay 落盘/读取机制本体**（event_store.py 写入面 · cursor 协议）——非本 task 面。
- **前端兜底逻辑去除**（web PR #61 已落 0/'' 兜底 · 去留由 web 仓自裁）。
- **auto_resume 路径终帧**与手动 resume 同源（`router._execute_decided_resume` · auto_resume.py:229-231）——F1 修复天然同源覆盖，不另立面。
- **resume 状态机 / stranded_checkpoint 守卫 / 护栏机制**——历 task 已收口，零触达。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 resume 路径无 run_model 可取（model 键无法真实填充） | 30 实证裁定：填真实模型名或钉案不补（**禁硬编码/伪造值**）；裁定留痕入 30 invoke | 是 | 无（前端兜底存续） |
| FP-2 在飞态判定误伤沉降后 replay 主路径 | 验收 TC3 钉死：沉降后 replay 200 流式帧序对 master 零 diff；pytest 断言拦截 | 是（回退 diff） | 无 |
| FP-3 409+Retry-After 被旧客户端当致命错误 | web 端联调链已具备语义化处理动机（FP-1 报回方）；旧客户端视 409 为失败重试即可 · Retry-After 仅提示 | 是（客户端按 Retry-After 退避重试） | 断线重连场景由「500 报错」变为「退避后自动恢复」 |
| FP-4 在飞态根因非单一（多种异常皆可逃逸 500） | 30 实证枚举在飞态异常类型；语义化映射表照登；未识别异常仍 500（fail-closed 不吞错） | 是 | 无 |
| FP-5 终帧增键破坏既有契约测试/replay 自解释 | 增键为可选键（承 subtask_message 先例 · 不新 event_type）；`tests/` 既有 SSE 断言零新增红（CI 拦） | 是 | 无 |
| FP-6 HG-AUDIT-R1 pending 即 30 改码 | 执行 Agent **拒开工**（GATE_VERIFY · task 人工闸表为真值） | 是 | 须先 20 R1 + 维护者签 |

---

## 验收标准

- [x] **TC1 终帧字段契约（红测先行）**（30：RED a30b3d3 `KeyError 'latency_ms'` 与 F-OBS-1 同形 → GREEN e4a54d9 · 时序 git 可查 · `model` 不补钉案=FP-1 裁定留痕 30 invoke）：构造 HITL approve→resume 场景断言终帧 `done{status:'resumed'}` payload 含 `latency_ms`（int ≥ 0）；修复前 RED（缺键 · 与 F-OBS-1 缺口同形签名）→ 修复后 GREEN；RED→GREEN 时序在 git 历史可查。`model` 键按 FP-1 裁定结果断言（补则断言非空串 · 不补则钉案文档在案）。
- [x] **TC2 在飞 replay 语义化**（30：409 + `Retry-After: 2` 正整数 · 在飞面整体不再触达读路径故 500 消失 · router 测+DB 三态测在案）：构造 run 在飞（未沉降）形态 `POST /lg-rag/replay` → 断言返回 409（或 30 裁定的等价语义化 4xx）+ `Retry-After` 头存在且为正整数；**不再出现 500**。
- [x] **TC3 沉降后零 diff**（30：terminal 放行/挂起放行 DB 测 · `refuse_in_flight` 默认关全仓唯一生产调用方 · 404/422 既有断言零新增红存续）：run 沉降后 replay 200 流式帧序列对 master 同输入零 diff；resume 流既有帧序（hitl.resumed → … → done）除终帧增键外零 diff；未知 run_id 仍 404、非法 cursor 仍 422（router.py:344-356 既有语义存续）。
- [x] **TC4 反回归全量对拍**（30：全量 1803 passed + 5 failed 经 clean tree stash 对拍同 5 红同名同因=既有环境性 · 零新增；ruff 触碰文件 All checks passed；graph-compile EXIT=0 · graph.json 再生噪音已还原）：`pytest tests` 全量对拍 master 基线零新增红（环境性红逐枚同名同因照登）；`ruff check app tests` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0（再生噪音文件一律还原）。
- [x] **TC5 live 对照（40 帽）**（40：live 六条全实证 · 在飞 replay **409 + Retry-After: 2** 两 run 三打（run `d0d824d4` 在飞窗 + 孤儿 run `22b65ce2` 复打 · 500 消失）· S3 全链 18 帧连续 · seq18 `done{status:'resumed', latency_ms:135574}` 实值 **无 model 键**（FP-1 钉案 live 一致）· 挂起 replay 200 七帧 / completed run 200 一百十二帧零 diff · 环境三坑留痕 · 40 invoke + 附件 16 件落盘）：复现 web 联调 S2/S3 同形态（在飞 replay + approve→resume 终帧），观测 409/Retry-After 与终帧 `latency_ms` 实值；结果如实照登，回执 web 联调链（T-W2 FP-1 闭环证据）。

## 依赖

- 来源实证：ops-desk-web 联调链 T-W2 invoke 留痕（2026-10-11 · S3 replay seq18 · S2 run `640d68970a564fbb8459d8d40cb1c5f6`）· web PR #61（前端兜底已落）。
- 锚点亲读（base master `92a8526` · 行号逐字复核）：`app/ops/hitl/resume.py:124-134`（close 终帧现状）· `app/ops/lg_rag/sse_stream.py:465-490`（live done 对照面）· `app/ops/chat/streaming.py:290-297`（chat done 含 latency_ms/model）· `app/ops/lg_rag/router.py:332-373`（replay 端点 · :350-356 单异常捕获）· `app/ops/lg_rag/event_store.py:139-169`（load_events_after 读取面）。
- 无代码面阻塞依赖；web 侧不阻塞（前端已兜底 · 本 task 收口后 web 可自裁去留）。

## 给执行帽的必读列表

1. 本 task 全部锚点行（`app/ops/hitl/resume.py:112-159` / `app/ops/lg_rag/router.py:332-373` / `app/ops/lg_rag/event_store.py:128-169` / 对照面 `sse_stream.py:455-491` · `chat/streaming.py:280-297` · 逐一亲读复核 · 禁信转述 · 行号漂移按实校正）。
2. `app/ops/hitl/router.py:418-521`（`_execute_decided_resume` 同源恢复路径 · resume 端点组装）。
3. `docs/standards/CODING_BACKEND_L2_v1_zh.md`（涉码 task）。
4. freeze 先例：`docs/tasks/done/task_lg_rag_sse_subtask_message.md`（payload 增可选键不新 freeze）· `docs/tasks/done/task_lg_rag_sse_resume.md`（replay HTTP 面在 lg-rag-sse-v1 扩展先例）。
5. `app/ops/hitl/auto_resume.py:193-235`（auto 触发同源 · F1 修复覆盖确认面）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 问题框定：两观察项同源（web 联调 T-W2 FP-1 报回）· 均为 SSE/HTTP 契约面缺口 · 锚点亲读核真（resume.py:124-134 确缺键 · router.py:350-356 单异常捕获） | false | — | 无 |
| R1 | 证据收集：对照面钉死（live done 含 latency_ms · chat done 含 latency_ms+model · streaming.py:290-297）；在飞 500 根因不锁死留 30 | false | — | 在飞态异常类型未实证（留 30） |
| R2 | 方案生成：F1 终帧增键（latency_ms 必 · model 裁定）/ F2 409+Retry-After（建议 · 等价语义化开放）；合并为一 task（同源同面 · 小而齐） | false | — | model 可得性未知（FP-1 裁定面） |
| R3 | 反例与边界：沉降后主路径零 diff 钉死（FP-2/TC3）· 未识别异常仍 500 fail-closed（FP-4）· 增键为可选键不新 event_type（FP-5） | false | — | 在飞态判定面（如何机断「在飞」）留 30 钉 |
| R4 | 验收/可测性：TC1 红测先行 + TC2 状态码断言 + TC3 零 diff + TC4 全量对拍 + TC5 live 对照 · 全可机断 | false | — | TC5 依赖 live 环境（承前例照登口径） |
| R5 | 收口：范围/非范围/失败路径/依赖/必读齐备 · HG-TASK-DRAFT approved（00 委派令代录）· HG-AUDIT-R1/HG-GRAPH-MODULES pending 不代签 · graph_change_layer=G-L1 预判 | true | 两缺口机理单一明确 · 锚点全亲读核真 · 方案开放性显式留 30 · 再轮无新增信息 | 在飞 500 根因未锁死（刻意）· graph_delta 为预判 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

web 联调链 T-W2（2026-10-11）按 FP-1 纪律报回两后端观察项：F-OBS-1 resume 终帧缺字段（S3 replay seq18 实证 · 前端徽标「耗时 0ms」）、F-OBS-2 在飞 replay 瞬返 500（S2 run `640d68970a564fbb8459d8d40cb1c5f6` 实证）。10 亲读 base master `92a8526` 核真：`resume.py:124-134` close() 终帧确仅四键（run_id/thread_id/status/events_persisted）；`router.py:350-356` replay 仅捕 LgRagRunNotFoundError，其余异常逃逸即 500。两缺口同处 lg-rag/hitl SSE 契约面、同源同批报回、各自面极小——裁合并为一 task（F1/F2 双范围项）。

### R1 · 证据收集

对照面钉死：lg-rag live 流 done 含 `latency_ms`（sse_stream.py:471/:488）；chat 流 done 含 `latency_ms`+`model`（chat/streaming.py:290-297）——前端徽标字段期望的形态来源即此。F-OBS-2 在飞态具体异常类型未实证（load_events_after :139-169 读取面在飞形态行为留 30 亲测），根因不锁死。

### R2 · 方案生成

F1：close() 终帧增 `latency_ms`（perf_counter 口径对齐 sse_stream.py）；`model` 键取决于 resume 路径是否持有 run_model——可得则补、不可得则钉案照登（FP-1 禁伪造）。F2：建议 409 Conflict + `Retry-After`（在飞=资源状态冲突 · 客户端可退避）；等价语义化 4xx 方案开放，30 实证后裁定留痕。两案均刻意不锁死实现细节。

### R3 · 反例与边界

- 沉降后 replay/resume 主路径必须零 diff——FP-2/TC3 钉死，防「顺手统一」误伤。
- 未识别异常仍 500（fail-closed 不吞错）——FP-4：语义化映射仅限实证确认的在飞态异常，禁宽泛 except 吞一切。
- 增键为可选键、不新 event_type——承 task_lg_rag_sse_subtask_message 先例（FP-5），freeze 不升。
- 前端兜底已落（web PR #61）——本 task 修根因，不依赖前端配合，亦不要求前端同步改动。

### R4 · 验收/可测性

TC1 红测先行防恒绿假象（RED 签名 = F-OBS-1 缺口同形：终帧缺 latency_ms）；TC2 状态机断（409+Retry-After · 500 消失）；TC3 零 diff 双断言（沉降后帧序 + 404/422 存续）；TC4 仓级反回归对拍基线；TC5 live 对照复现 web S2/S3 形态，回执联调链闭环。

### R5 · 收口

范围 F1–F4、非范围六条、失败路径六行、验收五条勾选、依赖三条、必读五项齐备；HG-TASK-DRAFT approved（00 联调链委派令代录 · web PR #61 报回），HG-AUDIT-R1/HG-GRAPH-MODULES pending 不代签；graph_change_layer=G-L1 预判（hitl/lg_rag 行行为表述面 · 30 按实判回写）。lint 形态对齐历 task 实证教训（验收 - [ ] 清单 · 思考轮控制表五列 · 闸表四列纯 status）。裁定收口，early_stop at R5。

### 自检结论（执行者）

**30（2026-10-13）**：红测先行时序成立（a30b3d3 五红签名全预期：KeyError/AttributeError/TypeError×3 → e4a54d9 全绿 · 目标两文件 29 passed）；FP-1 裁定 **model 不补**（sse_stream.py 全文零 model 引用 · resume 全链无来源 · 表无列 · 对照测试钉死禁伪造）；F2 判定面新谓词 `run_stream_closed` 刻意不复用 `run_is_terminal`（挂起 replay 合法零 diff · R1 观察项 O2 回复在 30 invoke）；全量对拍零新增红（5 既有红 clean tree 实证同名同因）；TC1–TC4 勾选，**TC5 待 40 帽 live 对照**。

**40（2026-10-13）**：TC5 live 对照 **PASS**——S2 同形态在飞 replay 两 run 三打实证 `409 + retry-after: 2` + 语义化 body（run `d0d824d4` 在飞窗 · 孤儿在飞 run `22b65ce2` 14:20 复打 · fail-closed 活样本 · **500 消失**）；S3 同形态 decide approved（inherit）→ resume 200（**JSON 面非 SSE** 照登 · replay cursor `:18`）→ 全量 replay **18 帧 seq 连续** · seq18 `done{status:'resumed', latency_ms:135574, 无 model 键}`（与 T-W2 形同构）；挂起 replay 200 七帧 · completed run 200 一百十二帧（TC3 零 diff live 面）；环境三坑留痕（langfuse 引号炸 port / NO_PROXY 裸 `::1` 同炸 / strategy 候选 env 追加口 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`）；回执 T-W2 联调链 F-OBS-1/F-OBS-2 闭环照登（40 invoke `invoke_20261013_40_verify.md` + attachments 16 件）。**TC1–TC5 全勾 · task 验收面收口。**

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-13 | 40 交付：TC5 live 对照 **PASS**（六条全实证 · 附件 16 件 · 环境三坑留痕 · 回执 T-W2 联调链照登 F-OBS-1/F-OBS-2 闭环）· **TC1–TC5 全勾 · task 验收面收口** · 40 invoke `invoke_20261013_40_verify.md` 落盘 |
| 2026-10-13 | 30 交付：RED a30b3d3（5 红签名全预期）→ GREEN e4a54d9 · 图谱回写 61094bf · 全量 1803 passed 零新增红（clean tree stash 对拍同 5 既有红同名同因）· ruff 触碰文件全绿 · graph-compile EXIT=0 · 30 invoke 落盘 · TC1–TC4 勾选（TC5 待 40 live 对照） |
| 2026-10-13 | 20-task-audit R1 落盘：结论 **PASS**（内容零阻塞 · 锚点 9 行全实证 master `cff3660` · 旧测影响面代查实证为空不退回补列 · 思考轮 R0–R5 闭合 · 非阻塞观察项 O1–O3）· 审查文 `docs/harness/reviews/task_hitl_resume_replay_contract_audit_R1_20261012.md` · 20 invoke 落盘（required_invoke_hats 含 20）· **维护者签 HG-AUDIT-R1 / HG-GRAPH-MODULES approved → 30 放行（红测先行 · TC1–TC5）** |
| 2026-10-11 | v0 · 10 落稿：ops-desk-web 联调链 T-W2 FP-1 报回两观察项（F-OBS-1 S3 replay seq18 终帧缺 latency_ms/model · F-OBS-2 S2 run 640d68970a564fbb8459d8d40cb1c5f6 在飞 replay 500）· 锚点亲读核真（base master `92a8526` · resume.py:124-134 / router.py:350-356 / 对照面 sse_stream.py:465-490 · chat/streaming.py:290-297）· TC1–TC5 验收 · R0–R5 思考轮（early_stop at R5）· HG-TASK-DRAFT approved（00 委派令代录）· HG-AUDIT-R1/HG-GRAPH-MODULES pending 待人签 · 来源：ops-desk-web 联调链 T-W2 FP-1 报回（web PR #61） |
| 2026-10-17 | CLOSED：PR #248 MERGED（squash `acac5e6` · 2026-10-13 · 交付分支 `task/hitl-resume-obs-drafts`）· TC1–TC5 全勾 · 归档 done/ · CLOSE 档 `../close/close_hitl_resume_replay_contract_20261017.md` · 批量关账 PR 待开（close/active-batch-20261017） |
