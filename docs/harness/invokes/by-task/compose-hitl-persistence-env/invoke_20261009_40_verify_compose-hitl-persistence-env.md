# Invoke：40 核验 · compose 透传 OPS_HITL_PERSISTENCE（compose-hitl-persistence-env）

| 项 | 值 |
|---|---|
| **帽** | 40（核验 · 逐项独立复跑 · 不采信 30 自报） |
| **日期** | 2026-10-09 |
| **task** | `docs/tasks/active/task_compose_hitl_persistence_env.md` |
| **核验对象** | commit `77382b8`（docker-compose.yml +3 行透传）+ `57f7b9b`（30 invoke + task N1 修正） |
| **分支** | `fix/compose-hitl-persistence-env`（worktree `d1-compose-hitl-persistence` · base `57fbf84`） |
| **30 证据** | `invoke_20261009_30_implement_compose-hitl-persistence-env.md`（自报 A1–A5 全 PASS） |
| **审查文** | `docs/harness/reviews/task_compose_hitl_persistence_env_audit_R1_20261009.md`（PASS-WITH-NITS · N1–N3） |

---

## 核验结论总表

| # | 核验项 | 结论 | 方式 |
|---|--------|------|------|
| 1 | diff 面核验（仅 docker-compose.yml + harness 文档 · +3 行 · 插入位 :65/:66 · 无 `:-db`） | **PASS** | 40 独立复跑 |
| 2 | A1② 不设 env 与 master `57fbf84` 渲染 diff 仅此一键 | **PASS** | 40 独立复跑（N2 参考命令） |
| 3 | A1① `OPS_HITL_PERSISTENCE=db` 渲染含精确键名 | **PASS** | 40 独立复跑 |
| 4 | A2 db 态 `/api/ops/hitl/runtime` 三键断言 | **PASS** | 40 独立复跑（docker 可用） |
| 5 | A5 回归零新增红（N3 注记化裁量） | **PASS** | 40 独立复跑 + 裁量 |
| 6 | 闸面终态（spec-wave verify EXIT=0 · task lint PASS） | **PASS** | 40 独立复跑 |
| 7 | 回填 task「自检结论（执行者）」段 A1–A5 | **已回填** | 本 commit |

**总裁定：PASS（7/7）· 30 证据全部属实 · 可进 PR 队列**（合并前仍须 `graph-compile.sh` + CI 绿，见「留转」）。

---

## 逐项核验记录

### 1. diff 面核验 — PASS

```console
$ git diff master --stat
 docker-compose.yml                                 |   3 +
 ...9_00_human_sign_compose-hitl-persistence-env.md |  36 +++++
 ...0261009_10_task_compose-hitl-persistence-env.md |  26 +++
 ...9_20_task_audit_compose-hitl-persistence-env.md |  37 +++++
 ...09_30_implement_compose-hitl-persistence-env.md | 171 ++++++++++++++++++++
 ...mpose_hitl_persistence_env_audit_R1_20261009.md | 121 ++++++++++++++
 .../active/task_compose_hitl_persistence_env.md    | 175 +++++++++++++++++++++
 7 files changed, 569 insertions(+)
$ git diff master --name-only -- app/ tests/ alembic/ .github/ | wc -l
0
```

- `docker-compose.yml` 改动精确 +3 行（两行中文注释 + `OPS_HITL_PERSISTENCE: ${OPS_HITL_PERSISTENCE:-}`），插入位在 `LG_RAG_DELEGATION_TOKEN_TTL_SECONDS`（原 :65）与 RAG_VECTOR_BACKEND 注释（原 :66）之间 —— 与 task R2 钉死位置一致。
- 默认值 `:-`（空），**无 `:-db`**（钉死契约遵守）；注释范式对齐 LG_RAG_DELEGATION_TOKEN_* 两行中文块（默认值语义 + 指向 persistence.py）。
- 其余 6 文件全部为本 task harness 文档（task 本体 / 00·10·20·30 invoke / R1 审查文）；`app/` `tests/` `alembic/` `.github/` 零 diff。

### 2. A1② 复跑对拍（N2 参考命令） — PASS

```console
$ git show 57fbf84:docker-compose.yml > /tmp/40_master-compose.yml
$ unset OPS_HITL_PERSISTENCE
$ docker compose -f /tmp/40_master-compose.yml --project-directory . config --format json | jq -S '.services.api.environment' > /tmp/40_env_master.json
$ docker compose -f docker-compose.yml --project-directory . config --format json | jq -S '.services.api.environment' > /tmp/40_env_branch.json
$ diff /tmp/40_env_master.json /tmp/40_env_branch.json
10a11
>   "OPS_HITL_PERSISTENCE": "",
$ diff <(docker compose -f /tmp/40_master-compose.yml --project-directory . config) <(docker compose -f docker-compose.yml --project-directory . config)
30a31
>       OPS_HITL_PERSISTENCE: ""
```

environment 块与全量渲染 diff 均**仅此一键**（空串形，task R3 residual_risk 兼容断言命中）。与 30 自报输出逐字一致。

### 3. A1① 复跑 — PASS

```console
$ OPS_HITL_PERSISTENCE=db docker compose config --format json | jq -S '.services.api.environment | with_entries(select(.key=="OPS_HITL_PERSISTENCE"))'
{
  "OPS_HITL_PERSISTENCE": "db"
}
$ grep -n 'ENV_PERSISTENCE' app/ops/hitl/persistence.py
22:ENV_PERSISTENCE = "OPS_HITL_PERSISTENCE"
```

渲染键名与 `persistence.py:22` 常量逐字一致（无 `PERSISTANCE` 类拼写回归）。

### 4. A2 抽检复跑（本机 docker 可用） — PASS

**环境处置（按 30 留痕与 40 指令）**：

- 本机 docker 29.3.1 + compose v5.1.1 可用；`ops-desk-api` project db/qdrant 在跑且 healthy（Up 4h）。
- 8000 端口有维护者残留 uvicorn（PID 80612 · main 仓 .venv）→ **不动**，用 `/tmp/40-override.yml`（`ports: !override` → `18000:8000` + `image: d1-compose-hitl-persistence-api:latest`）换端口复跑。镜像先经 `docker run --rm grep` 实证内含 `ENV_PERSISTENCE` 代码。
- 插曲（如实留痕）：首版 override 未加 `!override`，compose 对 ports 序列**合并追加**导致容器同时绑定 8000（com.docker `*:8000` 与 uvicorn `127.0.0.1:8000` 按最具体绑定分流，uvicorn 实际未受影响）；立即以 `!override` 重建，重建后 `lsof` 实证 8000 仅剩 uvicorn。

```console
$ OPS_HITL_PERSISTENCE=db docker compose -p ops-desk-api -f docker-compose.yml -f /tmp/40-override.yml up -d api   # EXIT=0
$ docker exec ops-desk-api-api-1 python scripts/create_initial_user.py   # 幂等建号 admin/maintainer
$ curl -s -c /tmp/40_a2.jar -X POST http://127.0.0.1:18000/api/ops/auth/login -d '{"username":"admin","invite_token":"<redacted>"}'
{"ok":true, "role":"maintainer"}
$ curl -s -b /tmp/40_a2.jar http://127.0.0.1:18000/api/ops/hitl/runtime | jq .
{
  "mode": "db",
  "store": "DbHitlStore",
  "persists": true,
  "callback_secret_configured": false
}
$ jq -e '.mode=="db" and .store=="DbHitlStore" and .persists==true' → true · A2_ASSERT=PASS
```

三键与 `describe_hitl_persistence()`（`persistence.py:85-92`）逐键吻合；`callback_secret_configured` 为端点多出键（本次 false = 本 shell 未设 LG callback secret，与 30 的 true 差异纯环境所致），不影响三键断言（审查文 C5 已预判）。

### 5. A5 复跑 + N3 注记化裁量 — PASS

40 独立复跑（worktree 无 .venv，用 main 仓 .venv 跑 worktree tests；`tests/` 零 diff 故等价）：

```console
$ python -m pytest tests -k hitl -q
98 passed, 1550 deselected in 4.64s
```

与 30 自报（98 passed）一致。另按审查文 N3 做注记化裁量，三要件全部 40 复跑成立：

1. `tests/` 对 docker-compose grep **零命中**（40 复跑 · rg 全目录）；
2. `tests/` 对 master **零 diff**（核验项 1）；
3. 全量 pytest 回归由 PR CI 兜底（合并必经 CI 绿，增量成本≈0；CI DB skip 现状按 test-baseline-reds F4 注记不视为真跑）。

**裁量依据**：审查文 Q3/N3 明确「A5 对纯 config 改动实质是零变化断言，40 可裁为『CI 绿 + tests/ 零 diff + 耦合面 grep 零命中』」；本 task 零码面改动，本地 hitl 子集 98 passed 已额外实证无即近回归 → **A5 满足**。

### 6. 闸面终态 — PASS

```console
$ npx spec-wave verify --target . --task docs/tasks/active/task_compose_hitl_persistence_env.md
VERIFY: PASS · task_compose_hitl_persistence_env.md   # EXIT=0（三闸全 approved）
$ npx spec-wave task lint --file docs/tasks/active/task_compose_hitl_persistence_env.md
LINT: PASS · task_compose_hitl_persistence_env.md     # EXIT=0
```

### 7. task 自检结论回填 — 已完成

task「自检结论（执行者）」段已按 30 留转项 2 回填 A1–A5 结论表（含 40 复跑证据指针），并补修订行；回填后 `task lint` 复跑 PASS。

### 补充 · A3 运行层 40 复跑（超出指令下限的加固）

```console
$ unset OPS_HITL_PERSISTENCE; docker compose -p ops-desk-api -f docker-compose.yml -f /tmp/40-override.yml up -d api
$ curl -s -b <maintainer cookie> http://127.0.0.1:18000/api/ops/hitl/runtime | jq .
{
  "mode": "null",
  "store": "NullHitlStore",
  "persists": false,
  "callback_secret_configured": false
}
$ jq -e '.mode=="null" and .store=="NullHitlStore" and .persists==false' → true · A3_ASSERT=PASS
$ docker logs ops-desk-api-api-1 | grep 'HITL 持久化未配置'
HITL 持久化未配置（OPS_HITL_PERSISTENCE 未设）：**审批申请不会落库**，不可上生产
```

告警文案与 `persistence.py:54-57` 逐字一致 → A3 三层（渲染/码面/运行）全部 40 复跑闭环。

---

## 30 证据真实性裁定

| 30 自报 | 40 复跑结果 | 裁定 |
|---------|-------------|------|
| A1① `"OPS_HITL_PERSISTENCE": "db"` | 逐字一致 | 属实 |
| A1② diff 仅 `10a11` / `30a31` 一键 | 逐字一致 | 属实 |
| A2 三键 db/DbHitlStore/true | 复跑一致（多出键 `callback_secret_configured` 值因环境异，不影响断言） | 属实 |
| A3 三键 null/NullHitlStore/false + 告警文案 | 复跑一致 | 属实 |
| A4 diff --stat 白名单 | 复跑一致 | 属实 |
| A5 98 passed, 1550 deselected | 复跑一致（98 passed） | 属实 |
| N1 修正（19→16 键）· N2 命令实跑 · N3 留 40 | task L52 已为「16 个键」· N2 命令 40 按同款复跑成立 · N3 本 invoke 裁量闭环 | 属实 |

**未发现证据造假；无复跑不过项。**

## 环境复原留痕

- api 容器已 `rm -sf` 删除（验收前本机无 api 容器）；db/qdrant 保持 Up·healthy 原状。
- 8000 端口仅剩维护者 uvicorn（PID 80612 · `/docs` 200 实证）；18000 无监听。
- 临时文件（`/tmp/40-override.yml` · cookie jar · runtime 快照 · 渲染对拍文件）已全部销毁；invoke 中令牌已脱敏。
- 验收产生两条 invite token（A2/A3 各一）残留于 db `ops_invite_tokens` 表（365 天过期 · 与 30 验收同型 · 维护者可按既有卫生流程清理）。

## 留转清单

| # | 项 | 归属 |
|---|----|------|
| 1 | 验收 checklist 阶段 5 全链实跑（重启后审批单仍在）属 task 非范围 | 维护者按 `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 另行组织 |
| 2 | 本 task 未 push 未开 PR；合并前须 `./scripts/graph-compile.sh` 通过 + CI 绿（AGENTS.md 流程） | 维护者 / 00 |
| 3 | task 仍驻留 `docs/tasks/active/`；PR 合并后按流程归档 | CLOSE 帽 |

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-09 | 40 核验落盘：7 核验项全 PASS（diff 面 / A1② / A1① / A2 / A5+N3 裁量 / 闸面 / task 回填）+ A3 运行层加固定复跑 · 30 证据六项逐字属实零造假 · 环境复原（api 容器删 · 8000 uvicorn 未动 · 临时件销毁）· 总裁定 PASS · 可进 PR 队列 |
