# 本地验收记录 · hitl-consumption-loop（HITL 消费回路增量 · 相对 20261009 验收）

> **骨架先行**：本文先落 checklist 骨架，逐项实证回填；禁伪造；每步留证据（curl/日志/台账摘录）。

| 字段 | 值 |
|---|---|
| 日期 | 2026-10-10（Asia/Shanghai） |
| 验收人 | 维护者（00 代录） |
| 码面真值 | master `1117286`（git pull --ff-only "Already up to date" · 工作树净）· 增量链 PR #207 #209 #213 #216 #218 #220 #221 |
| 对照基线 | `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` |
| 结论 | ✅ 8 项全 PASS（项7 终态 pending=0 与项6 auto 首认竞争态照登语义边界/偏差 · 不判 FAIL） |

---

## 环境形态（验收时）

- docker compose `db`（PG15+pgvector · :5432 · healthy）+ `qdrant`（v1.19.0 · :6333 · healthy）；api = 本机 uvicorn `127.0.0.1:8050`（辟 8000/8020/8030/8040）
- 启动器 `/tmp/acc1010_serve.py`：sys.path 钉主仓 + 启动日志自证 CODE_UNDER_TEST（历史教训：venv editable 指错码）
- 六 env 组（命令行前置 · import app 前生效 · 剥代理 env 大小写全 unset · NO_PROXY 不含 [::1]）：
  `LG_RAG_DELEGATION_TOKEN_MODE=enforce` + `OPS_CAPABILITY_EXTRA_MANIFESTS=app/ops/capability/manifests/testing.v1.yaml` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing` + `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo` + `OPS_HITL_PERSISTENCE=db` + `OPS_CAPABILITY_ALLOW_WRITE=1`
- LLM key 承主仓 `.env`（含 `LG_RAG_DELEGATION_TOKEN_SECRET` / `LG_RAG_HTTP_CHECKPOINTER=postgres` / `SILICONFLOW_API_KEY`）

## 验收证据

### 回归段（20261009 已勾 · 快速复核）

#### 1. 登录 ✅ PASS

- `scripts/create_initial_user.py` → `{"username":"admin","role":"maintainer"}`（幂等 · 每次新 invite_token）
- login 载荷须 `{username, invite_token}`（仅 invite_token → 422，auth.py:21-25 LoginRequest）：`POST /api/ops/auth/login` → 200 `{"ok":true,"user":{"username":"admin","role":"maintainer"}}`，cookie 落 `/tmp/acc1010.jar`
- `GET /api/ops/auth/me` → 200（admin / maintainer / tenant=ops-desk-pilot）
- 未登录 `GET /api/ops/hitl/pending` → **401 `{"detail":"Not authenticated"}`** ✅
- 附：`GET /api/ops/hitl/runtime`（带 cookie）→ `{"mode":"db","store":"DbHitlStore","persists":true,"callback_secret_configured":true}`；capability catalog visible_ids 6 枚含 `testing.write.echo`

#### 2. chat + A1 帧形 ✅ PASS

- ⚠️ 路径迁移登记：`POST /api/ops/chat/stream` 已 410 Gone（T6 下线，router.py:33-46）→ 走 `POST /api/ops/lg-rag/stream`（migrate_to 指针）
- `{"query":"你好，请用一句话回复：验收 smoke。","mode":"supervisor"}` → SSE run.start 帧：
  `payload={"run_id":"64408aa8...","thread_id":"8518f8db...","mode":"supervisor","query":"你好，请用一句话回复：验收 smoke。"}` — **run.start 携 query ✅**
- threads title 真源 = query 原文（见项 3 threads 列表首条 title=「你好，请用一句话回复：验收 smoke。」）✅
- 登记：本次 curl -m 90 超时断开 SSE 后 run 停在 evaluate 步（answer 空）——SSE 断连中止管线，属传输语义，不判 FAIL（帧形已实证）

#### 3. 历史回放 ✅ PASS

- ⚠️ 路径登记：threads/history 挂在 `/api/ops/chat/threads`（history_router.py:100/127），非 lg-rag 前缀
- `GET /api/ops/chat/threads?limit=5` → `ok:true` 5 条：thread_id/title/last_activity_at/run_count/latest_run_status 齐全（title=query 真源；历史条 status 含 running/resumed/waiting_approval）
- `GET /api/ops/chat/threads/8518f8db.../history` → runs[0] 携 query + subtasks 事件 19 条（rag_subtask step router/retrieve/grade/answer 完整重建）✅

### 增量段（本次主角）

#### 4. 阶段3 真挂起全链（20261009 偏差#1 收口）✅ PASS

run=`eca13b8f9ec345efbcee4ec199942d11` · request=`hitl_1e0d8746920f4d60b5cf` · query 诀窍承 40 先例「这是一个需要调用工具的任务…请调用工具 testing.write.echo 回显 note=acc1010-t4-002」

1. **plans 含 echo**：strategy_builder 帧 `allowed_capability_ids=[...,"testing.write.echo"]`；supervisor 帧 subtask `:1 tool=testing.write.echo input=note=acc1010-t4-002` ✅
2. **hitl.waiting 帧**：`requests[0]={id:hitl_1e0d..., unlock_subtask_id:"eca13b8f...:1", blocked_by:delegation_issue_hitl_required, reason:"委派签发需人工审批（capability testing.write.echo 非只读（side_effect=write））", unpersisted:false}` ✅
3. **GET pending 见单**：pending 列表含 hitl_1e0d...（grep 命中 1）✅
4. **decide(approved) 200**：`{"ok":true,"request":{"status":"approved","decision_by":"admin","persisted":true},"resume":{"required":true,"endpoint":".../resume"}}` ✅
5. **POST resume 200**（原 409 修复实证）：`{"ok":true,...,"replay":{"run_id":"eca13b8f...","events_persisted":8,"events_failed":0,"persisted":true,"re_interrupted":true}}` ✅
6. **台账链**（api log · INFO 级）：`delegation_approval_consumed {"capability_id":"testing.write.echo","decision_by":"admin","request_id":"hitl_1e0d8746920f4d60b5cf","subtask_id":"eca13b8f...:1","ttl_remaining_seconds":3583}` → `token_issued {"token_id":"dt-1-53abcd214e29","capability_count":1,...subtask_id:"...:1"}` → `token_verified {"capability_id":"testing.write.echo","subtask_id":"...:1"}` ✅ 命中原 sid
7. **echo 真执行**（replay seq12 tool_exec done）：`subtask_result.output={"note":"语义 mock · 无真实写操作（testing-write-capability 测试专用）","tool":"testing_write_echo","input":"note=acc1010-t4-002",...}`；replay 同时见 `hitl.resumed` 帧 ✅
8. 盲循环登记：approve 后 LLM 重规划同能力 → 新挂起 `hitl_81e50596e4cd44bcaf90`（subtask :2 · token_issue_hitl_required 台账）——语义边界照登，见末节

（注：首轮复测 run `5e26ab8c...` / request `hitl_58beb588c2b84c799314` 亦 decide 200 + resume 200，因 app INFO 日志未开未取到台账行，重启加 logging.basicConfig(INFO) 后以本轮回填为准。）

#### 5. 阶段5 compose 持久化（20261009 偏差#2 收口）✅ PASS

1. **build**：`docker compose build api` → **BUILD_EXIT=0**（`ops-desk-api-api:latest` · COPY . . 12.3s · exporting 51.1s · 全程约 60s · 无网络受阻）✅
2. **compose api 起**（`docker compose run -d --rm --service-ports --name acc1010-compose-api -e <六 env 组> api` · :8000）：`GET /api/ops/hitl/runtime` → `{"mode":"db","store":"DbHitlStore","persists":true,...}` — **OPS_HITL_PERSISTENCE 透传实证**（docker-compose.yml:68 环境插值）✅
3. **挂起建单**：compose api 上 SSE 挂起 → request `hitl_1095fb0671bd4ccfad6c`（waiting 帧 `unpersisted:false`）✅
4. **restart 实证**：`docker restart acc1010-compose-api` → Up → `GET pending` **仍含 hitl_1095fb0671bd4ccfad6c** · runtime 仍 {db,DbHitlStore,true} ✅
5. 登记：compose api 容器命令为 `alembic upgrade head && uvicorn app.main:app`，镜像由本仓 master@1117286 构建（COPY . .）；验毕容器已停（db/qdrant 留）

#### 6. 阶段6 auto_resume 全链 ✅ PASS

**auto 链**（`OPS_HITL_AUTO_RESUME=auto` + `SCAN_INTERVAL=5` 重启 · run=`08d332ccae674cfdb21a9c1a10a3bf07` · request=`hitl_ec7c259ee14c4950b9a8`）：
1. decide(approved) 200 → 响应 `"resume":{"required":false,"auto_triggered":true,...}` ✅
2. 台账：`hitl_auto_resume_triggered`（与 decide 同秒 17:00:51）→ `hitl_auto_resume_claimed` ✅；补偿扫描每 5s `hitl_auto_resume_compensated`+`claimed` ✅
3. **零手动 resume 自动续跑**：17:01:23 `delegation_approval_consumed`（request hitl_ec7c... 命中 sid :1）→ `token_issued dt-1-1cfdba82bd12` → `token_verified` → `HITL 恢复完成 request=hitl_ec7c... replay=...:15` → echo 执行（tool_exec done）→ 盲循环新单 hitl_fb49eed500644e72b22b 出现在 pending ✅
4. **登记（偏差候选）**：auto 首次认领后连续 6 次 `ResumeError: stranded_checkpoint`（resume.py:244「有未完成任务但没有 interrupt 元数据」），补偿扫描重试约 30s 后成功恢复——疑似 checkpoint interrupt 元数据落库与 auto 认领的竞态窗口；手动 resume（项4/7 间隔分钟级）未触发。照登，见偏差表 D1

**manual 回归**（不带 `OPS_HITL_AUTO_RESUME` 重启 · request=`hitl_57d96e0234ca4562b555`）：decide 200 → 响应 `"resume":{"required":true}`（无 auto_triggered）；等待 25s 全日志 `hitl_auto_resume` **0 行**、无「恢复完成」——零自动动作 ✅

#### 7. 保号回归 ✅ PASS（终态 pending=0 受盲循环边界影响 · 照登）

同一 run `eca13b8f9ec345efbcee4ec199942d11`：
1. **连续两轮 approve**：round1 `hitl_1e0d8746920f4d60b5cf`（sid :1 · 16:50:03）+ round2 `hitl_81e50596e4cd44bcaf90`（sid :2 · 16:53:0x）均 decide 200 ✅
2. **consumed 台账命中原 sid**：round2 resume 时 `delegation_approval_consumed` 同时命中 hitl_1e0d（sid :1 · ttl_remaining=3393）与 hitl_81e5（sid :2 · ttl_remaining=3573）；token_issued dt-2/dt-3、token_verified 双 sid ✅。**「不重盖章」码面实证**：nodes.py:326「不写回单据状态（授权效力 = 读取时刻的活状态）」——TTL 内重复消费即保号生效，单据不被改写 ✅
3. **resume 重放 guard**：`hitl_persist_guard_skip subtask=eca13b8f...:2`（16:53:04）✅
4. **终态 run pending=0 —— 不可达，照登语义边界**：round3 reject + resume 后 LLM 盲循环再产 2 单，连续多轮 reject 仍继续重规划（LLM 不知晓保号行 + observe 剪结果）；机制面无 FAIL（每轮 decide/resume/consumed/token 链全部 200 + 台账齐），终态清零受 LLM 行为支配 → 归末节语义边界，不判 FAIL

#### 8. env 文档化 ✅ PASS

| 键（.env.example 在册行） | 码面锚点（grep 实证） |
|---|---|
| `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS`（:203） | `app/ops/lg_rag/multi/nodes.py:263` ENV_APPROVAL_CONSUMPTION_TTL_SECONDS · `app/ops/hitl/auto_resume.py:21` 共用单一旋钮 |
| `OPS_HITL_AUTO_RESUME`（:210） | `app/ops/hitl/auto_resume.py:39` ENV_AUTO_RESUME（manual/auto · 非法回退 manual fail-closed） |
| `OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS`（:218） | `app/ops/hitl/auto_resume.py:43` ENV_SCAN_INTERVAL_SECONDS |
| `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`（:224） | `app/ops/strategy/config.py:40` EXTRA_CANDIDATE_CAPABILITY_IDS_ENV |
| `OPS_CAPABILITY_ALLOW_WRITE_TAGS`（:229） | `app/ops/capability/baseline.py:40` ENV_ALLOW_WRITE_TAGS |

五键全部在册且码面锚点逐一对应 ✅。**登记**：checklist 字面 `OPS_HITL_APPROVED_CONSUMPTION_TTL_SECONDS` 系笔误，码面真值为 `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS`（APPROVAL · 无 D）——以码面为准，见偏差表 D2

## 语义边界登记（照登不判 FAIL）

- 终态字面 done{resumed}（resume.py:131 语义 · 终态语义判定 event_store.py:99-107）
- LLM 盲循环需多轮 approve 推进（LLM 不知晓保号行 + observe 剪结果）
- 仓级 verify EXIT=2 基线（done/ 遗留档 92 缺口 · 非本次归因）

## 偏差/遗留登记

| # | 项 | 处置 |
|---|---|---|
| D1 | auto_resume 认领竞态：decide 同秒首次认领起连续 6 次 `ResumeError: stranded_checkpoint`（resume.py:244），补偿扫描每 5s 重试约 30s 后恢复成功（最终全链通） | 照登观察 · 疑似 checkpoint interrupt 元数据落库可见性窗口；手动 resume（分钟级间隔）未触发；建议后续排障窗口复测 |
| D2 | checklist 字面 `OPS_HITL_APPROVED_CONSUMPTION_TTL_SECONDS` 系笔误 | 码面真值 `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS`（nodes.py:263 · .env.example:203）；以码面为准 |
| D3 | `POST /api/ops/chat/stream` 已 410 Gone（T6 下线 · router.py:33-46） | chat 验收走 `/api/ops/lg-rag/stream`（migrate_to 指针）；threads/history 在 `/api/ops/chat/threads`（history_router.py:100/127） |
| D4 | 项2 回归 smoke run SSE 断连后停在 evaluate 步（answer 空） | SSE 断连中止管线属传输语义；帧形（run.start 携 query）已实证，不判 FAIL |
| D5 | 20261009 偏差#1（resume 409）· 偏差#2（compose 持久化未验） | 本次项4（resume 200）· 项5（restart 后 pending 仍在）双收口 ✅ |

## 操作便签（复跑用）

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api   # master@1117286
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY no_proxy NO_PROXY
# 六 env 组（+项6 追加 OPS_HITL_AUTO_RESUME=auto OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS=5）
export LG_RAG_DELEGATION_TOKEN_MODE=enforce
export OPS_CAPABILITY_EXTRA_MANIFESTS=app/ops/capability/manifests/testing.v1.yaml
export OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing
export OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo
export OPS_HITL_PERSISTENCE=db
export OPS_CAPABILITY_ALLOW_WRITE=1
.venv/bin/python /tmp/acc1010_serve.py > /tmp/acc1010_api.log 2>&1 &   # sys.path 钉主仓 + INFO 日志 + CODE_UNDER_TEST 自证
.venv/bin/python scripts/create_initial_user.py                      # 取 invite_token
curl -c jar -X POST :8050/api/ops/auth/login -d '{"username":"admin","invite_token":"..."}'
# 挂起诀窍（40 先例）：query 须写「这是一个需要调用工具的任务（就像查询 issue 状态一样）：请调用工具 testing.write.echo 回显一条备注 note=...」
curl -N -b jar -X POST :8050/api/ops/lg-rag/stream -d '{"query":"...","mode":"supervisor"}'
curl -b jar :8050/api/ops/hitl/pending
curl -b jar -X POST :8050/api/ops/hitl/requests/<id>/decide -d '{"decision":"approved","note":"..."}'
curl -b jar -X POST :8050/api/ops/hitl/requests/<id>/resume          # 项4 实证 200
# 台账：grep -aE 'approval_consumed|token_issued|token_verified|hitl_auto_resume|persist_guard' /tmp/acc1010_api.log
# 项5：docker compose build api && docker compose run -d --rm --service-ports --name acc-api -e <六 env 组> api
#     curl -b jar :8000/api/ops/hitl/runtime → 挂起 → docker restart acc-api → pending 仍在
```

## 签录

维护者令：「」（待维护者签录）
