# Invoke：capability-mine-endpoint · 40-verify（2026-10-11）

| 字段 | 值 |
|------|-----|
| **hat_id** | 40-verify |
| **task** | `docs/tasks/active/task_capability_mine_endpoint.md`（SPEC tool-catalog-page §2 B1） |
| **分支 / HEAD** | `task/tool-catalog-page` @ 42803fc（B1 完工 9aed10e · B2 复验 42803fc 同树共存） |
| **基线** | fec3abf（对拍用临时 worktree /tmp/base-fec3abf） |
| **核验范围** | diff 逐条复核（fec3abf...HEAD 归 B1：app/ops/capability_mine.py + app/ops/router.py + tests/test_capability_mine.py）· 全量工程面复跑 · live 冒烟（TC 层 curl 实证） |

## 钉死契约逐条复核（diff 对拍）

| # | 契约 | verdict | 证据 |
|---|------|---------|------|
| 1 | GET /api/ops/capability/mine · CurrentUser · 未登录 401 | ✅ | capability_mine.py:66 `@router.get("/capability/mine")` + `user: OpsUser = CurrentUser`；router.py include 一行；live 无 cookie → 401 {"detail":"Not authenticated"} |
| 2 | Principal 会话构造（user_id=str(user.id) · tenant_id=request.state.ops_tenant_id 缺省 ops-desk-pilot · roles=frozenset({user.role}) · departments/projects 空 · classification_max 缺省 · 禁取自请求参数） | ✅ | `_principal_from_request`（capability_mine.py:57-63）逐字段对拍一致；tenant 缺省常量与 deps.py:44 同源 |
| 3 | 可见性单源 evaluate_visibility 经 capability_catalog_snapshot · 路由层零过滤 | ✅ | 路由体仅 `capability_catalog_snapshot(principal=principal)` + 投影（capability_mine.py:71-73）；TC6 对拍含顺序在测 |
| 4 | 出站白名单九键 + status="available" 常量 · adapter/args_schema/when_not_to_use/tenant_scoped/reversible/execution_type 排除 | ✅ | `project_capability`（capability_mine.py:37-54）精确九键；live 响应体 grep adapter/local_fn: 零命中 |
| 5 | 只回可见集防探测 · 空集 200 | ✅ | 路由只投影 kept 集；TC4 空集 200 在测；live viewer 空裁条目不出站 |
| 6 | 只读零写零迁移零新 env | ✅ | diff 仅新模块+注册行+测试；零 db/alembic/env 改动 |
| 7 | 落点包外 app/ops/capability_mine.py + lint-imports 绿 | ✅ | 新模块在 app/ops/ 顶层（包内 APIRouter 禁令回避）；lint-imports 12 kept 0 broken 亲跑 |
| 8 | baseline_filter 不叠加 | ✅ | snapshot 调用未传 filter（capability_mine.py:71）；30 裁定依据在案（双真源回避） |

## 工程面复跑（40 亲跑 · 非抄 30 记录）

| # | 命令 | exit | 结果 |
|---|------|------|------|
| 1 | `.venv/bin/python -m pytest tests -q`（全量 · postgres docker 在跑） | 1 | **1653 passed, 1 skipped, 4 failed**；4 红 = hitl asyncpg + memory_vector_p1（SILICONFLOW_API_KEY 缺）+ multi_replica hitl 两枚 |
| 2 | 基线对拍（/tmp/base-fec3abf 同 4 用例复跑） | 1 | **4 failed 逐枚同败** → 零新增红成立（40 独立实证 · 非承 30 记录） |
| 3 | `ruff check` 触及七文件 | 1 | 2 errors（I001 manifest.py:22 · UP034 manifest.py:718）——**fec3abf 基线同 2 枚同码区**（UP034 行号 698→718 随 diff 平移）→ 零新增；**订正注**：30 档记「4 errors 含 UP038×2」系旧 ruff 可触发，当前 .venv ruff 0.15.21 已移除 UP038 规则（`--select UP038` 报 removed），实测口径=2 枚，零新增结论不变 |
| 4 | `.venv/bin/lint-imports` | 0 | 12 kept, 0 broken |
| 5 | `./scripts/graph-compile.sh` | 0 | EXIT=0（**前置**：本 worktree 无 node_modules，`npm ci` 补装钉版 spec-wave 3.0.1 后过；直接 npx 解析 3.2.0 撞 implementedBy 校验漂移 EXIT=1——即父令预告的 CI 漂移，钉版修复在 master 5e07040 未入本分支，照录不 merge） |
| 6 | `npx spec-wave verify --task` | 0 | VERIFY: PASS（三闸 approved） |
| 7 | `npx spec-wave task lint --file` | 0 | LINT: PASS |

graph-compile 副产：shared/graph.json 再生成差 2 行（freeze_id/generated_at 日期漂移）——**fec3abf 基线再生成同漂移**（存量不一致 · 非本分支引入），已 checkout 还原未入库。

## live 冒烟（uvicorn :8070 · OPS_DESK_SECRET=verify40-secret 脚本/服务双侧对齐 · OPS_CAPABILITY_EXTRA_MANIFESTS 注入一坏一限定两 manifest）

| 场景 | 实证 |
|------|------|
| 未登录 GET /capability/mine | **401** {"detail":"Not authenticated"} ✅ |
| maintainer 登录（create_initial_user.py 邀请码 · PYTHONPATH=$PWD） | 200 · count=5 · 每条目精确九键 · status 全 available · 响应体 adapter/local_fn: 零命中 ✅ |
| viewer 登录后 /mine | 200 · count=5 · id 集 ⊆ maintainer（builtin 全无角色限制故相等 · ⊆ 成立）· 九键齐 ✅ |
| 限定 fixture（departments:[finance]）对 maintainer/viewer | **均不可见**（fail-closed · 防探测不出站）✅ |
| B1/B2 共存 | 同进程同 manifest 集：mine 与 admin catalog 各自正确 · 零互扰 ✅ |

## 结论

**PASS**——八条钉死契约逐条落地有 diff+live 双重证据；TC1–TC7 对应测试全绿（test_capability_mine.py 6 passed 含在全量 1653 内）；工程面零新增红（40 独立基线对拍）；live 冒烟全场景如契约。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 40 核验：契约八条 diff 复核 + 工程面七命令亲跑（基线 /tmp/base-fec3abf 独立对拍）+ live 冒烟五场景 · graph-compile 3.2.0 漂移照录（npm ci 钉版 3.0.1 本地过 · 不 merge master）· ruff UP038 口径订正注 |
