# 本地验收记录 · chat-history-hitl-ux（B1 会话历史 API + B2 HITL 浏览器决策面）

| 字段 | 值 |
|---|---|
| 日期 | 2026-10-09（Asia/Shanghai） |
| 验收人 | 维护者（00 代录） |
| 码面真值 | PR [#204](https://github.com/Cyning12/ops-desk-api/pull/204) MERGED `eb22a66`（B1 `9904f81` + B2 `c39e659`）· CLOSE PR [#205](https://github.com/Cyning12/ops-desk-api/pull/205) MERGED `822bf9d` |
| task | `docs/tasks/done/task_chat_history_api.md` · `docs/tasks/done/task_hitl_browser_decide.md`（双 done） |
| 结论 | **PASS（checklist 阶段 1–4 全勾 · 阶段 5 未验 · 红线零违反）** |

---

## 环境形态（验收时）

- 混合模式：docker compose `db`（PG15+pgvector · :5432）+ `qdrant`（:6333）健康；api = 本机 `uvicorn app.main:app --port 8000`（代码=master）
- 关键前置：本机原生 Homebrew PG 18.6 与 Docker 端口映射**同抢 5432**（原生绑 localhost 优先截胡）→ 已 `brew services stop postgresql`，`localhost:5432` 归 Docker 真数据库

## 验收证据

### 阶段 1 · 登录 ✅

- `scripts/create_initial_user.py` 幂等建 admin/maintainer + 邀请令牌；`POST /api/ops/auth/login` 落 `ops_session` cookie；`/auth/me` 200
- 反断言：未登录 `GET /api/ops/hitl/pending` → **401** ✅

### 阶段 2 · chat + A1 帧形 ✅

- 前端发 chat（`#2140 这个 issue 在说什么？如何来解决` 等 3 run）正常出最终回复
- `run.start` payload 携 `query`（A1）：threads 列表 title = `#2140 这个 issue 在说什么？如何来解决`（生产实证标题真源）

### 阶段 3 · HITL 审批面（部分 · 见偏差登记）

- 当前能力注册表**全只读**（`side_effect: read` · `deny_write` 过滤 · 可见集 8 个 tool）→ `LG_RAG_DELEGATION_TOKEN_MODE=enforce` 下按 Q2 裁定「只读自动放行」，**无真实挂起可触发**（设计真态，非缺陷）
- 手工补录路径（`POST /api/ops/hitl/requests` · cookie maintainer 可及）已确认可用；pending/decide 机断语义由 B2 交付测试覆盖（20 用例含 409/404/422/归属过滤/decide→resume 图替身全链/真 PG 重启链）

### 阶段 4 · 历史回放（B1 面）✅

- `GET /api/ops/chat/threads?limit=5`：3+ thread · 字段族齐 · `last_activity_at` 倒序 · title 来自 query ✅
- `GET .../threads/ee91e4f6.../history`：3 run 升序重建（query + answer + terminal_status）✅
- SSE 帧落盘口径：事件表 `ops_lg_rag_run_events` 每帧独立 commit 即真值；导出同形 sse.log 用 psql 一行（见下「操作便签」）

## 偏差/遗留登记

| # | 项 | 处置 |
|---|---|---|
| 1 | 阶段 3「真实图挂起 → decide → resume 解锁」全链未验（全只读能力面无可审对象） | 如需要：注册非只读测试 capability（manifest 增条目 · side_effect≠read）→ 另立 task |
| 2 | 阶段 5（重启持久化 · `OPS_HITL_PERSISTENCE=db`）未走本机验收；B2 交付测试已真 PG 覆盖（未 skip） | 如需 compose 形态验：compose `api.environment` 补 `OPS_HITL_PERSISTENCE` 透传 → 另立 task |
| 3 | docker api 容器曾 exit 127（10 天前调试残留 `/tmp/serve_info.py` 脏 bind mount） | 已删容器；镜像为旧码，如用全 docker 形态须先 `docker compose build api` |
| 4 | 本机 PG `ops` 角色带 CREATEDB（为跑绿 `test_import_from_supabase.py` 所加 · 非仓内改动） | 留置；回滚 `ALTER ROLE ops NOCREATEDB;`（回滚后该文件 3 个环境性 error 复现 · CI 无感） |
| 5 | `test_import_from_supabase.py` 在无 CREATEDB 环境下环境性 error | 存量 · conftest F4 已注记 · CI 无 PG 时 skip |

## 操作便签（复跑用）

```bash
# SSE 帧导出（同形 sse.log · 真值在事件表）
docker exec ops-desk-api-db-1 psql -U ops -d opsdesk -t -A \
  -c "SELECT 'event: '||event_type||E'\n'||'data: '||payload::text||E'\n' FROM ops_lg_rag_run_events WHERE run_id='<run_id>' ORDER BY seq;" > /tmp/sse.log

# 可用工具目录（cookie maintainer）
curl -s -b /tmp/ops.jar 'http://127.0.0.1:8000/api/ops/admin/capability/catalog' | jq .

# 401 自查顺序：cookie 文件存在？→ 会话过期？→ 是不是连错了 PG（本机原生 vs docker）
```

## 签录

维护者令：「此次任务的 checklist 算通过，落盘并 PR 到 main」（2026-10-09）· 00 代录
