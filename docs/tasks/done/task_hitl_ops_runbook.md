# task_hitl_ops_runbook · HITL 生产使用流程手册 + 残留收口

> **状态**：done（CLOSED 2026-10-17 · PR #264 MERGED squash dd6e02d · mergedAt 2026-10-17T05:50:24Z · CLOSE 档 docs/tasks/close/close_hitl_ops_runbook_20261017.md）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl_ops_runbook` |
| **git_branch** | `task/hitl-ops-runbook`（建议 · 执行帽开工前切 · 禁止直改 master） |
| **implement_repo** | ops-desk-api（本仓） |
| **test_strategy** | 人工 checklist 型（docs 新增 + docker compose 验收复走 · 无新增自动化用例） |
| **test_strategy_note** | 复走验收以 curl/docker 命令输出机断断言为准（见 TC-2/3/4）；文档交付以 spec-wave task lint + grep 节名断言为准（TC-1/6/7/8） |
| **code_quality_bar** | n/a（纯文档 + 验收复走 · 不改 app/） |
| **graph_change_layer** | none |
| **graph_delta** | n/a |
| **graph_delta_note** | 零路由/表/SSE 事件新增 · freeze lg-rag-sse-v1 只读引用不升级 |
| **wiki_delta** | n/a |
| **wiki_delta_note** | runbook 落 docs/guides/ 属 guides 面 · 不触 standards/wiki（承 task_host_v1_delegation_token_observe 先例） |
| **review_hat** | 20 |
| **required_invoke_hats** | 10（本稿）→ 20（R1 书面审）→ 人签 HG-AUDIT-R1 → 40（执行 + 验收复走） |
| **invoke_retention_profile** | standard |
| **experience_capture** | close 时回填 CLOSE 文档（承 close_hitl_resume_replay_contract_20261017 先例 · 经验钉入 runbook 坑位节） |
| **kpi_aggregator** | n/a |
| **orchestration** | 单 task · 不拆批 |
| **freeze_id** | lg-rag-sse-v1（只读引用 · 零新 SSE 事件 · 不升级） |
| **related_tasks** | 见「依赖」节 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20, 40 | 2026-10-17 维护者授权 00 代录（m00238 · 补行对齐同批兄弟档口径 · 本 task orchestration 无 30 棒） |
| HG-AUDIT-R1 | approved | 30/40 | 2026-10-17 维护者授权 00 代录（m00238 · 20 R1 书面审豁免） |
| HG-GRAPH-MODULES | n/a | — | graph_change_layer=none · 不触图谱闸（承 task_compose_hitl_persistence_env 先例） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点改码 |

## 背景与目标

HITL（Human-in-the-Loop）链路在本仓已全量落地：SPEC chat-history-hitl-ux B1/B2 signed 且 done；compose env 透传 OPS_HITL_PERSISTENCE 已 CLOSE（PR #207）；其后三连架构合并改变运维面——PR #250 RunWorker（squash 56e4a9f）、PR #248 replay 409+latency_ms（squash acac5e6）、PR #252 resume 异步化（squash 0e5f6b1）。残留四处收口：

1. **无生产操作手册**：HITL 运维知识散落在 4+ 份验收/CLOSE/SPEC 文档（六 env 组、挂起 query 诀窍、坑位清单、409 退避纪律），运维者无单一入口。
2. **阶段 5 复走遗留**：20261009 本地验收偏差#2（compose 重启持久化）虽已由 20261010 验收项5 在 master 1117286 收口（restart 后 pending 仍在 PASS），但三连架构合并后现行 master（579d283）compose 形态全链未复走——resume 已异步化、replay 已有 409+Retry-After 契约，旧实证不覆盖新链路。
3. **FP-1 钉案未入操作面**：resume 终帧 done 无 model 键之「不补」裁定（禁伪造钉死）仅在 CLOSE 文档，需钉入 runbook 防回流。
4. **F1/F2 交接无锚点**：SPEC Q4 裁定前端概要移交 ops-desk-web 专项 SPEC，本仓缺契约指针文档。

目标：产出 docs/guides/RUNBOOK_hitl_ops_v1_zh.md 作为 HITL 生产使用单一入口，并在现行 master 上复走 compose 形态重启持久化全链，证据落盘验收记录。

## 范围

- **F1 · 新增 HITL 操作 runbook**：`docs/guides/RUNBOOK_hitl_ops_v1_zh.md`，必备五节：
  1. 全链菜谱：触发审批（六 env 组 + 挂起 query 诀窍）→ hitl.waiting 挂起帧 → GET /api/ops/hitl/pending → POST /api/ops/hitl/requests/{id}/decide（approved|rejected · decide 默认不自动 resume 两步钉死）→ POST .../resume（异步受理秒回 200 携 replay.cursor）→ POST /api/ops/lg-rag/replay 追帧至终帧 done。
  2. 409 + Retry-After 重试纪律：在飞 replay → 409 + Retry-After:2 退避重试、沉降后同请求零 diff（app/ops/lg_rag/router.py:384-420 · 判定谓词 run_stream_closed 本体在 app/ops/lg_rag/event_store.py:132 · 挂起 run 的 replay 属合法零 diff 面）；resume 在飞重复提交 → 409「该申请的恢复正在执行中」。
  3. OPS_HITL_PERSISTENCE=db 重启恢复：docker compose 透传（docker-compose.yml:68 环境插值）· GET /api/ops/hitl/runtime 三键 {mode,store,persists} 机断 · 缺省/空串 = null 不落库 + 启动告警「不可上生产」。
  4. 常见 failure 排查表：承 20261009/20261010 验收坑位（旧镜像须先 docker compose build api · 本机原生 PG 抢 5432 · app 无 logging 初始化须 basicConfig 启动器 · env 启动瞬间生效 · curl 全 URL + JSON header · /api/ops/chat/stream 已 410 Gone 走 /api/ops/lg-rag/stream · threads/history 挂 /api/ops/chat/threads）。
  5. FP-1 钉案 + F1/F2 交接锚点（见 F3/F4）。
- **F2 · 现行 master compose 形态阶段 5 复走**：docker compose build api → 六 env 组起 compose api → runtime 机断 {db,DbHitlStore,true} → 挂起建单 → docker restart → pending 仍在 → decide → resume 异步受理 200 携 replay.cursor → replay 追帧终帧 done{status:'resumed', latency_ms:int≥0, 无 model 键}。证据落盘 docs/acceptance/ 新验收记录（含环境形态/命令输出摘录/偏差登记）。
- **F3 · FP-1 model 字段钉案入 runbook**：裁定溯源 close_hitl_resume_replay_contract_20261017.md（sse_stream.py 零 model 引用 · resume 全链无来源 · 表无列 · 禁伪造钉死 · 前端兜底 0/'' 存续 ops-desk-web PR #61）· runbook 钉「展示层 model 显示 0/'' 为契约行为 · 后端不补」。
- **F4 · ops-desk-web F1/F2 交接锚点节**：本仓只出契约指针——B2 决策面端点族（GET /api/ops/hitl/pending · POST /requests/{id}/decide · POST /requests/{id}/resume）+ SSE 契约 freeze lg-rag-sse-v1 + SPEC Q4 裁定移交记录（前端专项 SPEC 归 ops-desk-web）· 不实现前端。

## 非范围

- 改 app/ 任何代码：复走暴露新缺口 → **停派升级新 task，不顺手修**（FP-7）。
- 前端实现（F1/F2 属 ops-desk-web · 本仓仅锚点指针）。
- 改 docker-compose.yml / .env.example（透传已 CLOSE · 仅引用）。
- 图谱 / standards / coding_wiki 改动（graph_change_layer=none · wiki_delta=n/a）。
- HMAC 对接面（GET /requests · POST /callback · POST /requests 手工补录）运维手册化——跨系统对接面，另立 task。
- OPS_HITL_AUTO_RESUME=auto 运维化（auto 认领竞态已由 PR #224 收口 · 生产默认 manual · 本 task 菜谱以 manual 为准，auto 仅作附录提示）。

## 失败路径（failure_paths）

| FP | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|---|
| FP-1 | runbook 照抄 20261010 便签中本机绝对路径/旧端口写法 | task lint E6 拦截 / curl 连接拒绝 | 可重试（改写仓内相对路径 · 端口以 compose ps 实映射为准） | lint E6 报错 / connection refused |
| FP-2 | 复走未先 docker compose build api | 旧镜像跑旧码 · 三连架构变更不在镜像内 | 可重试（先 build 再起） | runtime 三键或端点行为不符预期（承 20261009 偏差#3） |
| FP-3 | 本机原生 PG 抢 5432 | compose db 起不来 / healthy 永不达 | 可重试（停原生 PG 或改端口映射） | compose ps 非 healthy（承 20261009 坑位） |
| FP-4 | 在飞 replay 轮询不退避 | 409 + Retry-After:2 持续返回 | 可重试（按 Retry-After 退避 · 沉降后同请求 200 零 diff） | 连续 409 响应 |
| FP-5 | resume 在飞重复提交 | 409「该申请的恢复正在执行中」（异步受理并发守卫） | 可重试（等沉降 + replay 追帧确认终帧） | 409 + 中文 detail |
| FP-6 | OPS_HITL_PERSISTENCE 缺省/空串 | null store 不落库 · 重启丢申请 · 启动告警「不可上生产」 | 不可重试（重启后申请已丢 · 须重建） | runtime {mode:null,persists:false} + 启动告警日志 |
| FP-7 | 复走暴露新缺口（三连架构变更后回归缺陷） | 本 task 停派升级 · 不顺手修 | 另立 task | 复走 checklist 对应项 FAIL + 验收记录偏差登记 |

## 验收标准

- [ ] **TC-1**：`docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 存在且含 F1 五必备节；断言：`grep -cE '全链菜谱|409.*Retry-After|重启恢复|排查表|钉案' docs/guides/RUNBOOK_hitl_ops_v1_zh.md` ≥ 5。
- [ ] **TC-2**：复走 compose api 上 `GET /api/ops/hitl/runtime` 输出含 `"store":"DbHitlStore"` 与 `"persists":true`；断言：curl 输出 grep 双命中。
- [ ] **TC-3**：挂起建单后 `docker restart <compose-api>`，`GET /api/ops/hitl/pending` 输出仍含复走建单 request id；断言：curl 输出 grep 命中。
- [ ] **TC-4**：decide(approved) → resume 200 响应携 replay.cursor → replay 追帧终帧 done 含 `"status":"resumed"` 与整数 `latency_ms` 且**无 model 键**；断言：jq 三断言（.status=="resumed" · .latency_ms|type=="number" · has("model")|not）。
- [ ] **TC-5**：复走证据落盘 `docs/acceptance/<执行日>_hitl_ops_runbook_compose_rewalk.md`，含环境形态（master commit · compose ps）/ 命令输出摘录 / 偏差登记（无偏差须写「零偏差」）。
- [ ] **TC-6**：runbook FP-1 钉案节含裁定溯源链接 [close_hitl_resume_replay_contract_20261017.md](../close/close_hitl_resume_replay_contract_20261017.md) + 「禁伪造 model 键」钉文 + 前端兜底 0/'' 存续说明；断言：grep 命中三要素。
- [ ] **TC-7**：runbook F1/F2 交接锚点节含 ops-desk-web 专项 SPEC 指针 + SPEC Q4 裁定移交记录 + freeze lg-rag-sse-v1 声明；断言：grep 命中三要素。
- [ ] **TC-8**：`npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_ops_runbook.md` 输出含 `LINT: PASS`（E 级清零 · W 级照登）。
- [ ] **TC-9**：零 app/ 改动断言：执行分支 `git diff --name-only master...HEAD` 输出仅 docs/ 下文件（若复走暴露缺口走 FP-7 停派 · 不在本分支修）。

## 依赖

- [SPEC-chat-history-hitl-ux_v0.md](../../spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md)（B1/B2 done · F1/F2 Q4 裁定移交 · FP-5/FP-6 契约）
- [20261009_chat-history-hitl-ux_local_acceptance.md](../../acceptance/20261009_chat-history-hitl-ux_local_acceptance.md)（阶段 1–4 PASS · 偏差#2/#3 原登记）
- [20261010_hitl-consumption-loop_local_acceptance.md](../../acceptance/20261010_hitl-consumption-loop_local_acceptance.md)（项5 阶段 5 首收口 · 六 env 组 · 挂起 query 诀窍 · 操作便签坑位——便签含本机绝对路径，禁照抄入 runbook，仅作事实溯源）
- [task_compose_hitl_persistence_env.md](../done/task_compose_hitl_persistence_env.md)（compose 透传 CLOSE · runtime 三键机断先例）
- [task_lg_rag_sse_run_worker.md](../done/task_lg_rag_sse_run_worker.md)（模板真值 · RunWorker 架构）
- [close_hitl_resume_replay_contract_20261017.md](../close/close_hitl_resume_replay_contract_20261017.md)（F-OBS-1 终帧契约 · FP-1 不补裁定 · F-OBS-2 409+Retry-After）
- [close_lg_rag_sse_run_worker_co_disconnect_20261017.md](../close/close_lg_rag_sse_run_worker_co_disconnect_20261017.md)（经验钉三条 · 在飞 replay 409 纪律 · 补偿扫描）
- [RUNBOOK_delegation_token_observe_local_v1_zh.md](../../guides/RUNBOOK_delegation_token_observe_local_v1_zh.md)（runbook 命名/结构先例 · §10 已有 HITL 批准链坑位行）
- 码面锚点（只读 · 执行帽复走前亲读）：`app/ops/hitl/router.py`（端点族 :76/:161/:185/:530）· `app/ops/hitl/persistence.py:22,40,54-57` · `app/ops/lg_rag/router.py:384-420` · `app/ops/lg_rag/event_store.py:132`（run_stream_closed 谓词本体）· `docker-compose.yml:68`

## 给执行帽（40）的必读

1. 本 task 人工闸表：HG-AUDIT-R1 须维护者签 approved 方可开工。
2. F2 复走全程命令须留证据（curl/docker 输出摘录）· 禁伪造 · 拿不准写「照登：无实证」。
3. runbook 全文禁绝对本机路径（lint E6）· 端口一律写「以 compose ps 实映射为准」。
4. 复走暴露新缺口 → FP-7 停派升级 · 本分支不顺手修。

## 思考轮控制表

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 问题锁定：runbook 缺失 + 现行 master 复走遗留 + FP-1/F1F2 两处钉案锚点 · 纯文档零改码 | no | — | 复走实证质量依赖 40 执行 · 诚实纪律兜底 |
| R1 | 四候选发散：A 单 task 全收 / B 拆两 task / C 追加旧验收档 / D 全量菜谱含 HMAC+auto | no | — | 候选 D 划界待 R2 收敛 |
| R2 | 取 A 弃 B/C/D · HMAC 对接面 + auto 运维化划非范围另立 · FP-7 停派裁定钉死 | no | — | HMAC 对接面文档仍空缺（另立 task 跟进） |
| R3 | FP-1..7 七条成表 · 坑位时效性残留以「端口以 compose ps 实映射为准」兜底 | no | — | 20261010 便签坑位时效性（启动器/端口为当时形态） |
| R4 | TC-1..9 全机断 · TC-4↔FP-1 钉案互锁 · TC-9↔FP-7 停派互锁 | no | — | 无 |
| R5 | 五件套闭合 · 六轮全走不 early_stop（含复走实证面 + 多坑位设计决策 · chore 轨豁免不适用） | no | — | 闸面 HG-AUDIT-R1 已 00 代录 approved · 内容阻塞以 R 轮审查为准 |

actual_last_round：R5（六轮全走 · 无 early_stop）

### R0 · 问题重述

HITL 链路经三连架构合并（PR #250 RunWorker · #248 replay 409+latency_ms · #252 resume 异步化）后，运维知识散落在 4+ 份验收/CLOSE/SPEC 文档，生产侧无单一操作入口；阶段 5 重启持久化虽已于 20261010 在 master 1117286 收口，但现行 master（579d283）compose 形态全链未复走，旧实证不覆盖异步 resume + 409 契约新链路；FP-1「resume 终帧 model 键不补」裁定与 F1/F2 前端移交（SPEC Q4）缺操作面钉案与锚点。问题界定 = 一份生产 runbook + 一次现行 master 复走 + 两处钉案/锚点，纯文档零改码（graph_change_layer=none）。

### R1 · 方案发散

候选 A：单 task 全收四项范围（runbook 五必备节 + 复走 + FP-1 钉案 + F1/F2 锚点）。候选 B：拆两 task（runbook 文档 / 复走验收各自独立）。候选 C：复走证据追加进 20261010 旧验收档。候选 D：runbook 全量菜谱，连 HMAC 对接面（GET /requests · POST /callback · 手工补录）与 OPS_HITL_AUTO_RESUME=auto 运维化一并收录。

### R2 · 方案收敛

取 A 弃 B/C/D。弃 B：四项同源（皆 HITL 操作面），复走证据本要回流 runbook 菜谱，拆批徒增闸面成本无收益。弃 C：验收记录按日落盘系仓惯例，追加旧档破坏其历史快照性质——故 F2 证据落新档 docs/acceptance/<执行日>_hitl_ops_runbook_compose_rewalk.md。弃 D 并划非范围：①HMAC 面受众是外部系统对接方而非浏览器决策面运维者，契约形态（密钥分发/重放防护）与运维菜谱不同构，另立 task；②auto resume 生产默认 manual（app/ops/hitl/auto_resume.py:6-7 非法值 fail-closed 回退 manual）、认领竞态已由 PR #224 收口，其运维化（扫描间隔/补偿观测）超出本 task 范围，菜谱以 manual 为准、auto 仅作附录提示。**FP-7 停派裁定**：复走若暴露三连架构回归缺口，顺手修会污染纯文档边界并击穿 TC-9 零 app/ diff 断言——故钉死「停派升级新 task，不顺手修」。

### R3 · 风险审查

七条失败路径成表：FP-1 照抄 20261010 便签本机绝对路径触发 lint E6（只溯源不照抄）· FP-2 旧镜像未先 build（承 20261009 偏差#3）· FP-3 本机原生 PG 抢 5432 · FP-4 在飞 replay 不退避 409 风暴 · FP-5 resume 在飞重复提交撞并发守卫 · FP-6 OPS_HITL_PERSISTENCE 缺省/空串丢单不可重试 · FP-7 复走暴露新缺口停派。残留风险如实照登：便签坑位时效性（临时启动器/8050 端口为当时本机形态），runbook 一律写「端口以 compose ps 实映射为准」规避；复走实证质量依赖 40 诚实纪律（拿不准写「照登：无实证」· 禁伪造命令输出）。

### R4 · 验收对齐

TC-1/6/7 对 F1/F3/F4 文档面（grep 节名与三要素机断）· TC-2/3/4 对 F2 复走面（curl/jq 机断：runtime 双键 · restart 后 pending 命中 · 终帧三断言）· TC-5 证据落盘位 · TC-8 本档 lint PASS · TC-9 零 app/ diff。互锁设计两处：TC-4 has("model")|not ↔ FP-1 钉案（禁伪造 model 键）· TC-9 ↔ FP-7（顺手修即击穿 diff 断言）。

### R5 · 终审

五件套（范围/非范围/验收/failure_paths/依赖）闭合；码面锚点全部亲读命中（hitl router 端点族 · persistence.py:22,40,54-57 · lg_rag/router.py:384-420 · event_store.py:132 · docker-compose.yml:68）；依赖档全在。六轮全走不 early_stop——本 task 含复走实证面与多坑位设计决策，chore 轨「无思考轮节」豁免不适用，既开节则实填闭合。

### 自检结论（执行者）

40 执行完成（2026-10-17）· TC-1..9 全 PASS：

| TC | 结论 | 证据 |
|---|---|---|
| TC-1 | PASS | grep 节名命中 20 处 ≥5（五必备节全在） |
| TC-2 | PASS | runtime `{"mode":"db","store":"DbHitlStore","persists":true}` 双键 grep 命中 |
| TC-3 | PASS | docker restart 后 pending grep 命中复走建单 `hitl_a1cef212bf354860a3bc` |
| TC-4 | PASS | 终帧 seq18 done `status:resumed` · `latency_ms:435584` 整数 · payload 无 model 键 |
| TC-5 | PASS | 证据落盘 `docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md`（环境形态/命令摘录/偏差两条登记） |
| TC-6 | PASS | FP-1 钉案节三要素 grep 全命中（溯源链接 · 禁伪造 · 前端兜底 0/''） |
| TC-7 | PASS | F1/F2 锚点节三要素 grep 全命中（ops-desk-web 指针 · SPEC Q4 移交 · freeze lg-rag-sse-v1） |
| TC-8 | PASS | `npx spec-wave task lint` → `LINT: PASS`（回填后 W3 亦消） |
| TC-9 | PASS | diff 面仅 docs/（runbook + 验收档 + 本档 + invokes + R1/R2 审查文）· 零 app/ 改动 |

附：FP-4（在飞 replay 409 + retry-after:2）与 FP-5（resume 在飞 409 中文 detail）均获 live 实证（验收档 S5/S7）；R2 N-1 顺手修已落（auto_resume.py:39 → app/ops/hitl/auto_resume.py:6-7）；复走暴露零回归缺口，FP-7 未触发；复走新增实测 nuance（resume 段追帧 200 携部分帧而非 409）已回填 runbook §1.5。

## 修订记录

| 日期 | 记录 |
|---|---|
| 2026-10-17 | 10-task 帽起草初稿：背景证据全部亲读（两份验收 + 两份 CLOSE + SPEC + compose task + hitl router/persistence 码面锚点）· 范围四项对齐委派 · 人工闸全 pending 待维护者签 |
| 2026-10-17 | 20 R1 退回（B-1 思考轮 R0–R5 全占位 · 全仓零先例）→ 10 回填：R0–R5 控制表+正文六节实填闭合（actual_last_round=R5）· 补 HG-TASK-DRAFT 闸行对齐兄弟档（N-1）· 补 event_store.py:132 谓词本体锚点（N-4）· 验收/failure_paths/范围实质未迁就改动 |
| 2026-10-17 | 20 R2 增量复核 PASS-WITH-NITS 签收（审查文 docs/harness/reviews/task_hitl_ops_runbook_audit_R2_20261017.md）→ 40 执行：R2 N-1 顺手修（auto_resume.py:39 → :6-7 真址）· F1 runbook 落稿五必备节+F3/F4 钉案锚点 · F2 现行 master compose 复走 TC-2/3/4 PASS + FP-4/FP-5 live 实证（验收档 20261017_hitl_ops_runbook_compose_rewalk.md）· §1.5 追帧 nuance 实测回填 · 自检结论回填 TC-1..9 全 PASS |
| 2026-10-17 | CLOSED：PR #264 MERGED squash dd6e02d（2026-10-17T05:50:24Z）· 批量关账 · CLOSE 档 close_hitl_ops_runbook_20261017.md |
