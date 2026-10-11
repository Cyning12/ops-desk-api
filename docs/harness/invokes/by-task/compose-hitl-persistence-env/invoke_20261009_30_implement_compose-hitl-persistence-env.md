# Invoke：30 实现 · compose 透传 OPS_HITL_PERSISTENCE（compose-hitl-persistence-env）

| 项 | 值 |
|---|---|
| **帽** | 30（实现） |
| **日期** | 2026-10-09 |
| **task** | `docs/tasks/active/task_compose_hitl_persistence_env.md`（HG-AUDIT-R1 approved · 三闸全 approved） |
| **分支** | `fix/compose-hitl-persistence-env`（worktree `d1-compose-hitl-persistence` · base `57fbf84`） |
| **审查文** | `docs/harness/reviews/task_compose_hitl_persistence_env_audit_R1_20261009.md`（PASS-WITH-NITS · nit N1–N3） |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|----------|--------|-----------|------------|
| HG-TASK-DRAFT | approved（task 人工闸表 L37）| approved | Y | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved（L38）| approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved（L39 · `graph_change_layer=none`）| approved | Y | Y | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a（L40）| — | Y | N | n/a |

- reviews：R1 审查文存在且结论 PASS-WITH-NITS（零内容阻塞）→ **是**
- pre-30 invoke：`required_invoke_hats=10,20,30,40` ∩ {10,20,00} = {10,20}；10 / 20 / 00 快照均已在 `docs/harness/invokes/by-task/compose-hitl-persistence-env/` 落盘 → **是**
- 机械辅助：`npx spec-wave verify --target . --task docs/tasks/active/task_compose_hitl_persistence_env.md` → **VERIFY: PASS · EXIT=0**；`task lint` → **PASS · EXIT=0**

**结论：可进入改码。**

---

## 实现（钉死范围内 · 最小 diff）

`docker-compose.yml` api.environment 块、`:65`（LG_RAG_DELEGATION_TOKEN_TTL_SECONDS）与 `:66`（RAG_VECTOR_BACKEND 注释）之间插入三行（R2 裁定位置）：

```yaml
      # HITL 审批持久化（默认空 = 不落库 · 生产须显式设 db 跨实例跨重启；
      # 语义与模式表见 app/ops/hitl/persistence.py）
      OPS_HITL_PERSISTENCE: ${OPS_HITL_PERSISTENCE:-}
````

- 默认空（`:-`）· **无** `:-db` 非空默认（钉死契约遵守）
- 注释范式对齐 LG_RAG_DELEGATION_TOKEN_* 两行中文注释块（`:61-62`）：说明默认值语义 + 指向 `persistence.py` 语义表
- app/ · tests/ · alembic/ · .github/ · 其它 docs 零改动

## nits 处置（20 R1 转来）

| nit | 处置 | 实证 |
|-----|------|------|
| N1（task L52「19 个键」实为 16） | ✅ 已修正为「16 个键」（机数：DATABASE_URL…QDRANT_COLLECTION 共 16）· 随本 invoke 同 commit | 修正后 `task lint` 复跑 PASS · EXIT=0 |
| N2（A1② 对拍命令具体化） | ✅ 已按审查文参考命令实跑（`git show 57fbf84:docker-compose.yml` → `docker compose -f /tmp/master-compose.yml --project-directory . config --format json` → `jq -S` → diff），输出见下 A1② | 见验收实证 |
| N3（A5 注记化） | ⏸ 30 不动 · 留 40 处置 | — |

---

## 验收实证（30 自跑 · 全程留证）

### A1① 设 `OPS_HITL_PERSISTENCE=db` 渲染含精确键名

```console
$ OPS_HITL_PERSISTENCE=db docker compose config --format json | jq -S '.services.api.environment | with_entries(select(.key=="OPS_HITL_PERSISTENCE"))'
{
  "OPS_HITL_PERSISTENCE": "db"
}
```

键名与 `app/ops/hitl/persistence.py:22` `ENV_PERSISTENCE = "OPS_HITL_PERSISTENCE"` 逐字一致 → **PASS**。

### A1② 不设该 env 时与 master `57fbf84` 渲染 diff 仅此一键（N2 参考命令实跑）

```console
$ git show 57fbf84:docker-compose.yml > /tmp/master-compose.yml
$ docker compose -f /tmp/master-compose.yml --project-directory . config --format json | jq -S '.services.api.environment' > /tmp/env_master.json
$ docker compose -f docker-compose.yml --project-directory . config --format json | jq -S '.services.api.environment' > /tmp/env_branch.json
$ diff /tmp/env_master.json /tmp/env_branch.json
10a11
>   "OPS_HITL_PERSISTENCE": "",
```

environment 块 diff 仅 `OPS_HITL_PERSISTENCE` 一键（空串形态，task R3 residual_risk 兼容断言命中）。补充全量渲染 diff（非仅 environment 块）亦仅此一键：

```console
$ diff <(docker compose -f /tmp/master-compose.yml --project-directory . config) <(docker compose -f docker-compose.yml --project-directory . config)
30a31
>       OPS_HITL_PERSISTENCE: ""
```

→ **PASS**。

### A3 默认值行为零 diff

- 渲染层：不设 env 时渲染为 `"OPS_HITL_PERSISTENCE": ""`（空串），与 master 渲染 diff 仅此一键（上）。
- 码面层：`persistence.py:40` `os.environ.get(ENV_PERSISTENCE, "").strip().lower() or MODE_NULL` —— 空串 ≡ 缺省，同归 `MODE_NULL`（10/20 已实读闭环，30 复核属实）。
- 运行层（本机 docker 可用，顺带实证）：不设 env `docker compose up -d api` 后：

```console
$ curl -s -b /tmp/ops_a2.jar http://127.0.0.1:8000/api/ops/hitl/runtime | jq .
{
  "mode": "null",
  "store": "NullHitlStore",
  "persists": false,
  "callback_secret_configured": true
}
$ jq -e '.mode=="null" and .store=="NullHitlStore" and .persists==false' → true · A3_ASSERT=PASS
$ docker logs ops-desk-api-api-1 | grep "HITL 持久化未配置"
HITL 持久化未配置（OPS_HITL_PERSISTENCE 未设）：**审批申请不会落库**，不可上生产
````

告警文案与 `persistence.py:54-57` 逐字一致 → **PASS**。

### A2（db 态端点机断 · 本机 docker 可用已实跑）

前置：`docker compose build api`（EXIT=0 · 承接验收登记第 3 行旧镜像坑）；db healthy 复用既有 `ops-desk-api` project（偏差见下）。

```console
$ OPS_HITL_PERSISTENCE=db docker compose -p ops-desk-api up -d api   # EXIT=0
$ docker exec ops-desk-api-api-1 python scripts/create_initial_user.py  # 幂等建号 admin/maintainer
$ curl -s -c /tmp/ops_a2.jar -X POST .../api/ops/auth/login -d '{"username":"admin","invite_token":"<redacted>"}'
{"ok":true,"user":{"id":"...","username":"admin","role":"maintainer"}}
$ curl -s -b /tmp/ops_a2.jar http://127.0.0.1:8000/api/ops/hitl/runtime | jq .
{
  "mode": "db",
  "store": "DbHitlStore",
  "persists": true,
  "callback_secret_configured": true
}
$ jq -e '.mode=="db" and .store=="DbHitlStore" and .persists==true' → true · A2_ASSERT=PASS
```

→ **PASS**（三键与 `describe_hitl_persistence()` `persistence.py:85-92` 逐键吻合；`callback_secret_configured` 为端点多出键，不影响三键断言——审查文 C5 已预判）。

### A4（改动边界）

`git diff master --stat`：`docker-compose.yml` +3 行；其余全部为本 task 的 harness 文档（task 本体 / 10·20·00 invoke 快照 / R1 审查文）。`app/` `tests/` `alembic/` `.github/` 零 diff → **PASS**。

### A5（回归零新增红 · 快速子集）

本 task 零码面改动；`tests/` 对 docker-compose 零引用（20 已机跑实证）。30 实跑 hitl 相关快速子集：

```console
$ python -m pytest tests -k hitl -q
98 passed, 1550 deselected in 6.20s
````

零红 → **PASS**（全量基线对拍由 CI 兜底；N3 注记化裁量留 40）。

### task lint（N1 修正后复跑）

`LINT: PASS · task_compose_hitl_persistence_env.md` · EXIT=0。

---

## 偏差 / 环境处置留痕（不藏）

1. **compose project 名偏差**：worktree 目录名使默认 project = `d1-compose-hitl-persistence`，与已在跑的 `ops-desk-api` project（db/qdrant · 健康 4h）端口（5432/6333）冲突；首次 `up -d api` 误建 `d1-*` 容器（仅 Created 未启动）。处置：改用 `-p ops-desk-api` 复用既有健康 db/qdrant 起 api（同一 compose 文件渲染 api 服务，env 透传路径=验收对象，语义不受影响）；残留 `d1-*` 容器与网络已 `docker compose down` 清理。
2. **8000 端口占用**：维护者本机 uvicorn（PID 45114 · main 仓 .venv · 残留 3h+）占用 8000。处置：临时停止 → 验收完成后已**原样恢复**（`nohup .venv/bin/uvicorn app.main:app --port 8000` · `/docs` 200 实证）。
3. **db 态启动日志**：`HITL 持久化：db` 为 `logger.info`，uvicorn root 默认 WARNING 未显示；A2 以端点三键机断为准（task A2 本就只要求 jq 三键）。A3 告警为 `logger.warning` 故可见。
4. **令牌卫生**：验收产生的 invite token / cookie jar / runtime 快照（`/tmp/hitl_user.json`、`/tmp/ops_a2.jar`、`/tmp/runtime_*.json`、渲染对拍临时文件）已全部销毁；invoke 中令牌已脱敏。
5. **环境复原**：api 容器已删（验收前本机无 api 容器）；db/qdrant 容器保持验收前原状（Up · healthy）。

## 留转 40 清单

| # | 项 |
|---|----|
| 1 | N3：A5 注记化裁量（「CI 绿 + tests/ 零 diff + 耦合面 grep 零命中」即满足）由 40 处置；30 已附 98 passed 子集实证 |
| 2 | task 「自检结论（执行者）」段（L165-167）待 40 回填 A1–A5 结论 |
| 3 | 验收 checklist 阶段 5 全链实跑（重启后审批单仍在）属 task 非范围，由维护者按 `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 另行组织 |
| 4 | 本 task 未 push 未开 PR（按 30 授权边界）；合并前须 `graph-compile.sh` + CI 绿（AGENTS.md 流程） |

## commit 拆分

- commit 1（实现）：`docker-compose.yml` +3 行
- commit 2（文档）：本 invoke + task N1 机数修正（19→16）
