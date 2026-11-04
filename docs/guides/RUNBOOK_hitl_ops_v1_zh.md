# RUNBOOK · HITL 生产使用流程手册（v1 · 2026-10-17）

> **范围**：HITL（Human-in-the-Loop）审批链路生产/联调运维单一入口——触发审批 → 挂起 → 决策 → 恢复 → 追帧全链菜谱 · 409+Retry-After 重试纪律 · OPS_HITL_PERSISTENCE=db 重启恢复 · 常见 failure 排查 · FP-1 钉案 · ops-desk-web 交接锚点。
> **真值锚点（码面 · 只读引用）**：`app/ops/hitl/router.py`（端点族 :76 runtime / :161 pending / :185 decide / :530 resume）· `app/ops/hitl/persistence.py:22,40,54-57`（env 装配三模式）· `app/ops/lg_rag/router.py:384-420`（replay 409+Retry-After）· `app/ops/lg_rag/event_store.py:132`（run_stream_closed 谓词本体）· `docker-compose.yml:68`（OPS_HITL_PERSISTENCE 环境插值透传）。
> **上游实证**：20261009/20261010 本地验收（`docs/acceptance/`）· PR #250 RunWorker（squash 56e4a9f）· PR #248 replay 409+latency_ms（squash acac5e6）· PR #252 resume 异步化（squash 0e5f6b1）· 现行 master compose 形态复走证据 `docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md`。
> **铁律**：审批申请不落库 = 人永远等不到（宁可显式告警，不给成功假象）· decide 与 resume 是两步（默认不自动续跑）· 在飞 409 一律退避重试不硬闯 · 恢复帧只经事件流落盘（前端 replay 追帧）。

---

## §0 速览（TL;DR）

```bash
# 0. 前置：六 env 组（shell export · compose 插值透传 · 详见 §1.0）
export LG_RAG_DELEGATION_TOKEN_MODE=enforce
export OPS_CAPABILITY_EXTRA_MANIFESTS=app/ops/capability/manifests/testing.v1.yaml
export OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing
export OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo
export OPS_HITL_PERSISTENCE=db          # 生产钉死 db · 缺省=不落库（§3）
export OPS_CAPABILITY_ALLOW_WRITE=1

# 1. 起栈（旧镜像须先 build · 见 §4 坑位 1）
docker compose build api
docker compose up -d api                # 端口以 docker compose ps 实映射为准

# 2. 机断持久化生效（§3）
curl -b jar http://127.0.0.1:8000/api/ops/hitl/runtime
# 期望：{"mode":"db","store":"DbHitlStore","persists":true,...}

# 3. 全链（§1）：触发挂起 → pending → decide → resume → replay 追帧
```

---

## §1 全链菜谱（触发审批 → 挂起 → 决策 → 恢复 → 追帧）

> 以下示例统一以 `http://127.0.0.1:8000` 为 api 入口——**端口一律以 `docker compose ps` 实映射为准**，本文示例按默认 8000:8000 写实；cookie jar 路径自定（示例用 `jar`）。

### §1.0 前置 · 六 env 组

HITL 触发依赖能力面 + 委派闸 + 持久化六键齐配（缺一则挂起不发生或申请不落库）：

| env | 作用 | 缺省行为 |
|---|---|---|
| `LG_RAG_DELEGATION_TOKEN_MODE=enforce` | 委派令牌闸强制验签（触发 HITL 的前提） | off = 零 diff 不触发 |
| `OPS_CAPABILITY_EXTRA_MANIFESTS=app/ops/capability/manifests/testing.v1.yaml` | 载入测试能力清单（含 testing.write.echo） | 无测试能力 |
| `OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing` | 放开 testing 标签写能力 | 写能力全拒 |
| `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo` | strategy 候选池追加测试能力 | LLM 规划不出 echo |
| `OPS_HITL_PERSISTENCE=db` | 审批申请落库（§3） | **null = 不落库 · 不可上生产** |
| `OPS_CAPABILITY_ALLOW_WRITE=1` | 写能力总开关 | 关 |

另需：`LG_RAG_DELEGATION_TOKEN_SECRET`（enforce 模式验签密钥 · 禁入库 · 走 .env）· `LG_RAG_HTTP_CHECKPOINTER=postgres`（**重启后 resume 的前置**——checkpoint 落 PG 才能跨进程恢复；不设则 resume 显式失败 `app/ops/hitl/resume.py:317`）· LLM key（`SILICONFLOW_API_KEY` 等，compose 白名单透传见 `docker-compose.yml:51-73`）。

**坑位预警**：env 只在**启动瞬间**生效——export 与起栈必须同一 shell；改 env 须重启容器/进程（§4 坑位 4）。

### §1.1 触发审批（挂起 query 诀窍）

```bash
curl -N -b jar -X POST http://127.0.0.1:8000/api/ops/lg-rag/stream \
  -H 'Content-Type: application/json' \
  -d '{"query":"这是一个需要调用工具的任务（就像查询 issue 状态一样）：请调用工具 testing.write.echo 回显一条备注 note=<标记>","mode":"supervisor"}'
```

**挂起 query 诀窍**（40 先例实证）：query 须同时含「需要调用工具的任务」语义锚 + 显式工具名 + 参数值，LLM 才稳定规划出 `testing.write.echo` 子任务。纯知识库检索类问题走 RAG 链路不过委派闸，**零挂起**。

预期 SSE 帧序：run.start → strategy_builder / supervisor 规划帧（plans 含 `testing.write.echo`）→ **hitl.waiting 挂起帧**：

```json
{"event_type":"hitl.waiting","payload":{"requests":[{"id":"hitl_<hex>","run_id":"<run_id>","unlock_subtask_id":"<run_id>:1","blocked_by":"delegation_issue_hitl_required","reason":"委派签发需人工审批（capability testing.write.echo 非只读（side_effect=write））","unpersisted":false}]}}
```

- `unpersisted:false` = 申请已落库（若 `true` 立即查 §3——persistence 没配 db）。
- 挂起帧即终态前最后一帧：run 停在 checkpoint interrupt 上等决策。

### §1.2 查看待批列表

```bash
curl -b jar http://127.0.0.1:8000/api/ops/hitl/pending
# {"items":[{"id":"hitl_<hex>","run_id":"...","thread_id":"...","reason":"...","blocked_by":"...","created_at":"..."}],"count":1}
```

- 端点 `app/ops/hitl/router.py:161` · cookie maintainer 鉴权 · **只返回归属当前用户的申请**（归属经 run_id 反查事件表 · 解析不到则排除不泄露）。
- 未登录 = 401 `{"detail":"Not authenticated"}`——先走登录（`scripts/create_initial_user.py` 取 invite_token → `POST /api/ops/auth/login` 载荷 `{username, invite_token}` · 仅 invite_token 会 422）。

### §1.3 决策（decide · 两步钉死第一步）

```bash
curl -b jar -X POST http://127.0.0.1:8000/api/ops/hitl/requests/<id>/decide \
  -H 'Content-Type: application/json' \
  -d '{"decision":"approved","note":"<批注>"}'
# 200 {"ok":true,"request":{"status":"approved",...},"resume":{"required":true,"endpoint":".../resume"}}
```

- `decision` 只收 `approved` / `rejected`（非法值 Pydantic 422）；可选键 `resume_mode` ∈ {inherit, immediate, manual}（未知值 400 · SPEC FP-10/A10）。
- **两步钉死（SPEC Q2）**：默认（manual）decide **只置已决不自动 resume**——图仍挂 checkpoint；响应 `resume.required:true` 把第二步说出来。
- 边界：未知 id / 归属他人 → 404（不泄露存在性）；重复 decide / 已决 → 409。

### §1.4 恢复（resume · 异步受理秒回 200）

```bash
curl -b jar -X POST http://127.0.0.1:8000/api/ops/hitl/requests/<id>/resume
# 200 {"ok":true,"request":{...},"resume":{"status":"accepted",...},"replay":{"run_id":"...","cursor":"<run_id>:<seq>"}}
```

- 端点 `app/ops/hitl/router.py:530` · **异步受理（hitl-resume-async · PR #252）**：请求内只做守卫 preflight，投递后台执行后秒回 200（同步执行实测 130–310s 远超前端 30s 超时）。
- 响应 `replay.cursor` = 投递时刻游标——**恢复段事件都排在它后面**，前端拿它追帧即得「批准之后跑完的那段」（best-effort · 取不到为空串不阻塞受理）。
- **驳回也必须能 resume**：图挂在 interrupt 上等人，rejected 后 resume 收工出结论（不恢复 = run 永远挂在等待授权帧）。
- 守卫映射：非已决状态 409 · 在飞重复提交 409「该申请的恢复正在执行中」（§2）· checkpoint 未配置 503 · stranded_checkpoint 409（提示人重开，不是重试）。

### §1.5 追帧（replay 至终帧 done）

```bash
curl -N -b jar -X POST http://127.0.0.1:8000/api/ops/lg-rag/replay \
  -H 'Content-Type: application/json' \
  -d '{"cursor":"<resume 响应里的 replay.cursor>"}'
```

- 端点 `app/ops/lg_rag/router.py:384` · body 收 `{cursor}` 或 `{run_id, after_seq}`（非法 422 · 未知/跨用户 run 404）。
- resume 后追帧预期：hitl.resumed → tool_exec（echo 真执行）→ … → **终帧 done**：

```json
{"event_type":"done","payload":{"status":"resumed","latency_ms":<int≥0>}}
```

- 终帧契约钉死：`status:"resumed"` + `latency_ms` 整数 ≥0 + **无 model 键**（FP-1 钉案见 §5）。
- 追帧实测 nuance（20261017 复走）：挂起 run 的 stream 已被 done{waiting_approval} 收尾（§2.1 判定谓词），故 resume 段执行期间 replay **返 200 携部分帧而非 409**——客户端须以末帧 event_type 判定是否到终帧，未到则携末帧 cursor 继续追（2s 间隔），直到 done{resumed}。
- 台账链（须 §4 坑位 3 起法才可见 INFO 日志）：`delegation_approval_consumed`（命中原 subtask_id + TTL 剩余）→ `token_issued` → `token_verified`。

### §1.6 重启恢复全链（生产验证路径）

持久化形态完整验证顺序（复走实证见 `docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md`）：

1. compose api 挂起建单（§1.1）→ 记下 request id；
2. `docker restart <compose-api 容器名>`；
3. 重启后 `GET /api/ops/hitl/pending` **仍含该 request id**（DbHitlStore 跨重启）；
4. decide(approved) → resume 200 携 replay.cursor → replay 追帧终帧 done{resumed, latency_ms, 无 model 键}。

### §1.7 sync invoke 面 HITL 审批链（行为差异声明 · fix-hitl-decide-owner-fallback · issue #315）

`POST /api/ops/lg-rag/invoke`（同步面）触发写闸时与 SSE 面**行为不同，属契约声明而非缺陷**：

- **invoke 不落 run 事件帧**——事件帧是 SSE RunWorker 路径专属产物（维护者裁：永不补帧，sync 补帧会扩大事件面并牵连 #311 冻结面）。
- **归属反查走末位兜底**：无帧 run 的 `run_owner` 返 None 时，按单据自身 `thread_id` 反查 `ops_lg_rag_threads.user_id`（`app/ops/hitl/router.py _run_owner_of` · invoke 面建单前已拦跨用户 thread，单据 thread 必属 run 发起者）。事件表仍是第一真源，有帧 run 绝不走兜底；thread 行缺失/反查失败维持 404（fail-closed 不变）。
- **decide 可达**：sync 面写闸单据的属主可在 `GET /hitl/pending` 看到单据并 decide（404 断点已修，红测负样本「sync invoke 触发写闸 → decide 不再 404」钉死）。
- **resume 执行但无 replay 追帧面**：`_open_event_sink` 不兜底（直引 `run_owner`），无帧 run resume 时 sink=None——执行继续（写真实执行），但恢复段事件不落盘，**没有 replay 追帧可看**；结果经线程历史 / 再次 invoke 可见。
- 排障锚：单据 decide 仍 404 且日志「HITL 归属反查：run … 查不到归属用户」+「兜底反查失败」→ 查 `ops_lg_rag_threads` 是否有该 thread 行（invoke 中断场景 persist 失败等极端路径会缺）。

---

## §2 409 + Retry-After 重试纪律

两类 409 语义**完全不同**，处理纪律分开钉：

### §2.1 在飞 replay → 409 + Retry-After: 2（退避重试 · 沉降后零 diff）

- **语义**（F-OBS-2 · PR #248）：run 仍在流式写入时 replay 读路径不稳定，前置判定为 `409 Conflict` + 响应头 `Retry-After: 2` + 语义化 body「Run is still in flight; retry after it settles.」（`app/ops/lg_rag/router.py:384-420`）。
- **判定谓词**：`run_stream_closed`（本体 `app/ops/lg_rag/event_store.py:132`）——存在 done 或 error 帧即收尾；刻意不复用 `run_is_terminal`，**挂起 run（done{waiting_approval}）的 replay 是合法零 diff 面**，只有「有帧无收尾帧」才是真在飞。
- **客户端纪律**：收到 409 按 `Retry-After` 秒数退避重试；**沉降后同请求 200 零 diff**（同 cursor 拉到的帧流完全一致）——禁止改为轮询轰炸或换 run 重开。
- 未识别异常仍 500（fail-closed）——见到 500 不是重试面，是缺陷面，须登记排查。

### §2.2 resume 在飞重复提交 → 409（并发守卫 · 等沉降）

- **语义**：resume 已异步化，同一申请恢复在飞 ⇒ `409` + 中文 detail「**该申请的恢复正在执行中，待沉降后再试**」（`app/ops/hitl/router.py:561-566` · `_RESUME_IN_FLIGHT` 登记 · 执行体 finally 摘登记）。
- **客户端纪律**：撞此 409 = 上一次恢复还在跑——**等沉降 + 用 replay.cursor 追帧确认终帧**，不要并发重提。若长时间（分钟级）仍 409，查 api 日志「HITL 异步恢复执行失败」（执行失败只落日志，结果经事件流可见）。

---

## §3 OPS_HITL_PERSISTENCE=db 重启恢复

### §3.1 三模式语义（`app/ops/hitl/persistence.py` 装配表）

| `OPS_HITL_PERSISTENCE` | 存储 | 适用 |
|---|---|---|
| `db` | `DbHitlStore`（跨实例、跨重启） | **生产** |
| `memory` | `InMemoryHitlStore`（进程内，重启即丢） | 单实例 / 联调 |
| 不设 / 空串（默认） | `NullHitlStore`（不落库 + 显式标记） | 开发；**不能上生产** |

为什么默认不是 memory：内存存储会让「审批申请」看起来提交成功，重启后却消失——而「申请丢了」和「没人申请过」在观测上完全一样，人会一直等。宁可显式告警，不给成功假象。

### §3.2 compose 透传

`docker-compose.yml:68` 环境插值：`OPS_HITL_PERSISTENCE: ${OPS_HITL_PERSISTENCE:-}`——shell export 或 .env 写值即透传进容器；**缺省渲染为空串 = null store 不落库**，生产必须显式设 `db`。

### §3.3 机断校验（起栈后必做）

```bash
curl -b jar http://127.0.0.1:8000/api/ops/hitl/runtime
```

三键机断（`app/ops/hitl/router.py:76`）：

| mode | store | persists | 判定 |
|---|---|---|---|
| `db` | `DbHitlStore` | `true` | ✅ 生产形态 |
| `memory` | `InMemoryHitlStore` | `false` | ⚠️ 联调可用 · 重启丢单 |
| `null` | `NullHitlStore` | `false` | ❌ **不落库 · 启动日志告警「不可上生产」** |

缺省/空串形态除 runtime 三键外，启动日志有 `HITL 持久化未配置（OPS_HITL_PERSISTENCE 未设）：**审批申请不会落库**，不可上生产` 告警（`persistence.py:54-57`）；非法值 fail-closed 按 null 处理并 error 日志。**重启丢单不可重试**——申请已丢须重建（FP-6）。

### §3.4 重启恢复验证

见 §1.6 四步。核心断言：restart 后 pending 仍含复走建单 request id · runtime 三键不变 · resume/replay 全链通（前置 `LG_RAG_HTTP_CHECKPOINTER=postgres`，否则 checkpoint 不跨进程、resume 显式失败）。

---

## §4 常见 failure 排查表

承 20261009 / 20261010 验收坑位（按时效性如实照登 · 端口一律以 `docker compose ps` 实映射为准）：

| # | 症状 | 根因 | 处置 |
|---|---|---|---|
| 1 | compose api 行为不符预期（runtime 三键错 / 端点旧形态） | **旧镜像跑旧码**——三连架构变更不在镜像内 | `docker compose build api` 先构建再起（20261009 偏差#3 在案 · FP-2） |
| 2 | compose db 起不来 / healthy 永不达 | 本机原生 PG 抢 5432（compose 默认映射 5432:5432） | 停原生 PG 或改端口映射；`docker compose ps` 看实映射（FP-3） |
| 3 | api 无 INFO 台账（approval_consumed / token_issued 全看不到） | **app 无 logging 初始化**（全仓零 basicConfig）——裸 uvicorn root=WARNING 吞 INFO | 启动器加 `logging.basicConfig(level=logging.INFO)` 再起；compose 面用 override 换启动命令 |
| 4 | 改了 env 不生效 | env **只在启动瞬间生效** | export 与起服务同一 shell；改 env 须杀进程/重启容器 |
| 5 | curl 422 / 连接异常 | curl 未写全 URL · 缺 `Content-Type: application/json` | 全 URL + JSON header；login 载荷须 `{username, invite_token}`（仅 token 422） |
| 6 | `POST /api/ops/chat/stream` 410 Gone | T6 已下线旧端点 | 走 `POST /api/ops/lg-rag/stream`（migrate_to 指针）；threads/history 挂 `/api/ops/chat/threads`（非 lg-rag 前缀） |
| 7 | replay 连续 409 | run 在飞，未退避 | 按 `Retry-After: 2` 退避重试（§2.1 · FP-4） |
| 8 | resume 409「该申请的恢复正在执行中」 | 在飞重复提交撞并发守卫 | 等沉降 + replay 追帧确认终帧（§2.2 · FP-5） |
| 9 | 重启后 pending 空 / runtime `persists:false` | `OPS_HITL_PERSISTENCE` 缺省或空串 | 显式设 `db` 重启；**已丢申请不可恢复须重建**（§3 · FP-6） |
| 10 | resume 503 / stranded_checkpoint 409 | `LG_RAG_HTTP_CHECKPOINTER` 未设 postgres，或 interrupt 元数据竞态窗口（PR #224 已收口 auto 认领面） | 配 postgres checkpointer 重启；stranded 系旧格式残留，提示人重开而非重试 |
| 11 | capability catalog 看不到 testing.write.echo | 六 env 组缺 manifest/allow 键；jq 路径错 | catalog 返回对象非数组——jq 路径是 `.visible_ids` 不是 `.[].id` |
| 12 | SSE 挂起后客户端断连，run「卡死」假象 | RunWorker 已解耦（PR #250）：断连只取消订阅不杀执行；补偿扫描补 `done{disconnected}` | 用 replay 追帧确认真实终态；勿以连接状态判 run 生死 |

---

## §5 FP-1 钉案：resume 终帧 model 键「不补」裁定

> **裁定**：resume 终帧 `done{status:"resumed"}` **无 model 键是契约行为，后端不补**——禁伪造钉死。

- **裁定溯源**：[close_hitl_resume_replay_contract_20261017.md](../tasks/close/close_hitl_resume_replay_contract_20261017.md)（F-OBS-1 收口 · PR #248）。
- **事实链**：`sse_stream.py` 全文零 model 引用 → resume 全链无 model 来源 → 事件表无此列——**可取得则补、不可得钉案**，model 属后者。
- **禁伪造**：对照测试钉死禁伪造 model 键；任何「顺手补一个假值」即击穿钉案。
- **前端兜底存续**：展示层 model 显示 `0` / `''` 为契约行为（ops-desk-web PR #61 已落零迁就兜底），运维见到「耗时 0ms / model 空」**不是 bug**，不要报缺。
- live 一致性：40 复走实证终帧 `done{status:'resumed', latency_ms:int≥0, 无 model 键}` 与钉案一致（`docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md` TC-4）。

---

## §6 ops-desk-web F1/F2 交接锚点（契约指针 · 本仓不实现前端）

> SPEC Q4 裁定移交记录：「先在后端落盘合并的spec，实际spec后续交给前端agent再专项落盘」——前端 F1/F2 专项 SPEC 归 **ops-desk-web** 仓专项落盘（[SPEC-chat-history-hitl-ux_v0.md](../spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md) §4 Q4 · 本 SPEC 只钉契约面与后端范围）。

前端对接本仓 HITL 决策面的契约指针（只读引用 · 单源真值在本仓码面）：

| 面 | 契约 | 锚点 |
|---|---|---|
| 待批列表 | `GET /api/ops/hitl/pending`（cookie maintainer · 归属过滤） | `app/ops/hitl/router.py:161` |
| 决策 | `POST /api/ops/hitl/requests/{id}/decide`（approved/rejected · 默认不自动 resume 两步钉死） | `app/ops/hitl/router.py:185` |
| 恢复 | `POST /api/ops/hitl/requests/{id}/resume`（异步受理 200 携 `replay.cursor`） | `app/ops/hitl/router.py:530` |
| 追帧 | `POST /api/ops/lg-rag/replay`（cursor 追帧 · 在飞 409+Retry-After:2 退避） | `app/ops/lg_rag/router.py:384-420` |
| SSE 帧契约 | **freeze `lg-rag-sse-v1`**（hitl.waiting / done{status} 已在 freeze 内 · 零新事件类型 · 只读引用不升级） | SPEC §3 Q3 裁定 |

终帧渲染纪律：`done{status:"resumed", latency_ms}` 无 model 键（§5 钉案 · 前端兜底 0/'' 存续 web PR #61）。

---

## §7 附录：OPS_HITL_AUTO_RESUME=auto（提示 · 非本手册主线）

- 生产默认 `manual`（`app/ops/hitl/auto_resume.py:6-7` docstring：manual 默认现状零 diff · **非法值 fail-closed 回退 manual**）。
- `auto` 形态：decide(approved) 持久化成功后派发进程内后台任务走**同一条恢复路径**（`router._execute_decided_resume`）；行锁认领竞态已由 PR #224 收口（只读就绪校验 · 等下轮不报错）。
- 本手册菜谱一律以 manual 为准；auto 运维化（扫描间隔 / 补偿观测）与 HMAC 对接面（GET /requests · POST /callback · 手工补录）属另立 task 范围，不在此手册。

---

## 修订记录

| 日期 | 记录 |
|---|---|
| 2026-10-17 | 40 执行帽落稿（task_hitl_ops_runbook · F1/F3/F4）：全链菜谱 + 409 纪律 + 重启恢复 + 排查表 + FP-1 钉案 + F1/F2 锚点五必备节成文 · 坑位承 20261009/20261010 验收按时效性照登 · 端口一律以 compose ps 实映射为准 |
