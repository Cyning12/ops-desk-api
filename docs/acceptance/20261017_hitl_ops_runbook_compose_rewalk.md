# 20261017 HITL ops runbook · 现行 master compose 阶段5全链复走验收记录

> **任务**：task_hitl_ops_runbook F2（复走实证面）· 执行帽 Harness 40
> **关联**：[task_hitl_ops_runbook.md](../tasks/active/task_hitl_ops_runbook.md) · [RUNBOOK_hitl_ops_v1_zh.md](../guides/RUNBOOK_hitl_ops_v1_zh.md)
> **铁律遵守**：零 app/ 改动 · 零 docker-compose.yml/.env.example 改动（全程只读引用）

## 环境形态

| 项 | 值 |
|---|---|
| master commit | `579d283`（worktree `task/hitl-ops-runbook` 分支 base） |
| 镜像 | `docker compose build api` 重建（exit 0 · 承 20261009 偏差#3 教训先 build） |
| compose project | `ops-desk-api`（`--env-file` 指定主仓 .env · db/qdrant 复用运行中容器未重建） |
| api 容器 | `docker compose run -d --rm --publish 18000:8000 --name hitl-rewalk-api -e <六 env 组> -e LG_RAG_HTTP_CHECKPOINTER=postgres api` |
| env | LG_RAG_DELEGATION_TOKEN_MODE=enforce · OPS_CAPABILITY_EXTRA_MANIFESTS=app/ops/capability/manifests/testing.v1.yaml · OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing · OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo · OPS_CAPABILITY_ALLOW_WRITE=1 · OPS_HITL_PERSISTENCE=db（shell export 经 docker-compose.yml:68 插值透传）· LG_RAG_HTTP_CHECKPOINTER=postgres（compose 白名单无此键，须 run -e 显式注入） |
| compose ps（复走时） | ops-desk-api-db-1 Up (healthy) · ops-desk-api-qdrant-1 Up (healthy) · hitl-rewalk-api Up（实映射 18000→8000） |

## 复走步骤与命令输出摘录

### S1 · TC-2 runtime 机断

```
$ curl -b jar http://127.0.0.1:18000/api/ops/hitl/runtime
{"mode":"db","store":"DbHitlStore","persists":true,"callback_secret_configured":false}
```

**TC-2 PASS**：grep 双命中 `"store":"DbHitlStore"` + `"persists":true`。

### S2 · 挂起建单（§1.1 诀窍 query）

```
$ curl -sN -b jar -X POST http://127.0.0.1:18000/api/ops/lg-rag/stream -H 'Content-Type: application/json' \
  -d '{"query":"这是一个需要调用工具的任务（就像查询 issue 状态一样）：请调用工具 testing.write.echo 回显一条备注 note=rewalk20261017-t1","mode":"supervisor"}'
# 帧流：run.start / node.progress×4 / hitl.waiting / done{waiting_approval}
```

hitl.waiting 帧：request id=`hitl_a1cef212bf354860a3bc` · run_id=`d9f1fcf830a24629a45c666da4e71a36` · thread_id=`34118517242b4d81be479ddfe4e16d8f` · `unpersisted:false`。

### S3 · TC-3 重启持久化

```
$ docker restart hitl-rewalk-api   # api ready after restart: 2s
$ curl -b jar http://127.0.0.1:18000/api/ops/hitl/pending | grep -c hitl_a1cef212bf354860a3bc
1
```

**TC-3 PASS**：restart 后 pending 仍含复走建单 request id；runtime 三键重启后不变。（pending 列表另含 2026-10-14 存量 admin 申请——共享开发库预期现象，非本复走产物。）

### S4 · decide → resume（异步受理携 replay.cursor）

```
$ curl -b jar -X POST .../requests/hitl_a1cef212bf354860a3bc/decide -d '{"decision":"approved","note":"rewalk 20261017 TC-4"}'
# 200 · request.status=approved · persisted=true · resume.required=true（两步钉死实证）
$ curl -b jar -X POST .../requests/hitl_a1cef212bf354860a3bc/resume
{"ok":true,...,"resume":{"status":"accepted",...},"replay":{"run_id":"d9f1fcf830a24629a45c666da4e71a36","cursor":"d9f1fcf830a24629a45c666da4e71a36:7","events_persisted":0,"persisted":true,"re_interrupted":false}}
```

### S5 · FP-5 实证（resume 在飞重复提交）

```
$ curl -b jar -X POST .../requests/hitl_a1cef212bf354860a3bc/resume   # 紧接 S4 重复提交
HTTP 409
{"detail":"该申请的恢复正在执行中，待沉降后再试"}
```

并发守卫（`app/ops/hitl/router.py:561-566` `_RESUME_IN_FLIGHT`）行为与 runbook §2.2 钉文一致。

### S6 · TC-4 replay 追帧至终帧

cursor `:7` 起追帧：seq8 `hitl.resumed` → seq9–12 progress（echo 真执行，input `note=rewalk20261017-t1`）→ 推进 `:12`/`:15` → 终帧 seq18：

```json
{"run_id":"d9f1fcf830a24629a45c666da4e71a36","seq":18,"event_type":"done",
 "payload":{"run_id":"d9f1fcf830a24629a45c666da4e71a36","status":"resumed",
            "thread_id":"34118517242b4d81be479ddfe4e16d8f","latency_ms":435584,"events_persisted":10}}
```

**TC-4 PASS**：`status=="resumed"` ✓ · `latency_ms`=435584 整数 ✓ · `has("model")|not` ✓（payload 全文无 model 键——FP-1 钉案实证复核，与 close_hitl_resume_replay_contract_20261017 TC5 live 形态一致）。

追帧 nuance 实证：resume 段执行期间 replay **返 200 携部分帧**（非 409）——挂起 run 的 stream 已由 done{waiting_approval} 收尾，`run_stream_closed` 判定为已收尾，故恢复段追帧走「200 + 推进 cursor」而非「409 退避」。已回填 runbook §1.5。

### S7 · FP-4 实证（在飞 replay 409 + Retry-After）

另起 run（b7d9e4fc0ca843fb80b6a3fd700920bc）在 run.start 后、done 帧前探测：

```
$ curl -b jar -X POST .../api/ops/lg-rag/replay -d '{"run_id":"b7d9e4fc0ca843fb80b6a3fd700920bc","after_seq":0}'
HTTP/1.1 409 Conflict
retry-after: 2
{"detail":"Run is still in flight; retry after it settles."}
```

与 runbook §2.1 钉文（`app/ops/lg_rag/router.py:384-420`）一致。探针残留两笔挂起申请已于复走收尾 decide rejected 清理。

## 台账链摘录（api 容器日志）

```
delegation_approval_consumed {"capability_id":"testing.write.echo","decision_by":"admin","request_id":"hitl_a1cef212bf354860a3bc","subtask_id":"...:1","ttl_remaining_seconds":3399}
delegation token_issued / token_verified（同 subtask_id）
```

## 偏差登记

1. **宿主机 8000 被无关进程占用** → api 以 `--publish 18000:8000` 实映射起栈（复走全程用 18000）。属本机环境形态，非仓面缺陷；runbook 已钉「端口以 compose ps 实映射为准」。
2. **db/qdrant 复用运行中容器**（主仓 .env 形态）未重建——复走目标是 api 面重启持久化全链，db 数据存续恰为验证前提；共享开发库内存 2026-10-14 存量申请已如实照登。
3. 除上述两条外**零偏差**：六 env 组建单即挂起（无盲循环干扰实证）· 重启恢复/decide/resume/replay 全链一次通过 · 三连架构合并后（PR #250/#248/#252）现行 master compose 形态无回归缺口暴露（FP-7 未触发）。

## 结论

TC-2 / TC-3 / TC-4 全 PASS；FP-4 / FP-5 契约行为实测命中；复走容器已 `docker stop` 拆除（--rm 自动清），主仓 db/qdrant 容器未动。
