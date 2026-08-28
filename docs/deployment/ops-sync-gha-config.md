# 配置路线：本仓 GHA → POST `/api/ops/admin/sync`

> **日期**：2026-08-28  
> **给谁**：维护者（合入 [PR #88](https://github.com/Cyning12/ops-desk-api/pull/88) 之后做生产同验）  
> **对照**：`.github/workflows/ops_sync_kimi_code.yml` · `scripts/ops_sync_kimi_code.py` · workspace `docs/04-infrastructure/02-prod-env-reload.md`  
> **禁止**：把 token 写进 git、聊天、GHA 日志；`echo $OPS_ADMIN_SYNC_TOKEN`

---

## 0. 这条链路在干什么

```text
GitHub Actions（ops-desk-api · workflow ops-sync-kimi-code）
        │  1. GITHUB_TOKEN 拉 MoonshotAI/kimi-code 的 Issue/PR
        │  2. （可选）PAT checkout ISSUE_SCAN / graph.json
        │  3. 组装 SyncPayload
        ▼
POST https://www.cynaya.cn/api/ops/admin/sync
     Header: Authorization: Bearer <OPS_ADMIN_SYNC_TOKEN>
        │
        ▼
Nginx /api/  →  127.0.0.1:8000  api 容器
        │  校验 Bearer == 容器里的 OPS_ADMIN_SYNC_TOKEN
        ▼
PostgreSQL  upsert ops_repos / ops_issues / ops_pull_requests / ops_sync_runs
```

Cookie 登录的 maintainer **仍然能**打同一接口。GHA 不能走邀请码登录，所以必须机读 Bearer。

**token 必须三处同一串：**

| 位置 | 键 | 谁读 |
|---|---|---|
| GitHub Actions Secret（api 仓） | `OPS_ADMIN_SYNC_TOKEN` | GHA job 当 Bearer 发出 |
| 服务器 `/opt/ops-desk/.env` | `OPS_ADMIN_SYNC_TOKEN` | compose 展开进容器 |
| 现网 `docker-compose.prod.yml` → `api.environment` | 必须有这一行（见 §2） | 容器进程 `settings.ops_admin_sync_token` |

缺任一处：GHA 401，或容器里 token 为空（Bearer 整条禁用）。

---

## 1. 前置（按顺序）

1. **合入** api 仓 PR #88（`master` 上才有 `ops-sync-kimi-code.yml`）。合入会触发 `deploy-api`：只 rsync **api 源码**并重建 api 容器，**不会**更新现网 compose、**不会**改 `/opt/ops-desk/.env`。
2. 准备一台能 SSH 生产机、能改 GitHub Secrets 的维护者账号。
3. 生成 token（本地执行，**不要**贴到聊天）：

    openssl rand -hex 32

    得到 64 位 hex。下文记为 `<TOKEN>`。三处都贴这一串。

---

## 2. 现网 compose 必须透传（否则 §3 白配）

仓内 `ops-desk-workspace/deploy/docker-compose.prod.yml` 的 `api.environment` **目前没有** `OPS_ADMIN_SYNC_TOKEN`。生产 api **没有** `env_file:`，只吃 yaml 里写明的键。只改 `.env`、compose 没这一行 → 容器 `printenv` 看不到，Bearer 一直 401。

在 **workspace** 仓该文件 `api.environment` 里增加（建议放在 `OPS_DESK_SECRET` 附近）：

    OPS_ADMIN_SYNC_TOKEN: ${OPS_ADMIN_SYNC_TOKEN:-}

空默认 = 未配置时容器键存在但是空串 = Bearer 禁用（与代码一致）。配了 `.env` 之后必须 recreate 才进容器。

然后把 yaml **scp 到现网**（`deploy-api` **不会**自动同步 compose）：

    scp ops-desk-workspace/deploy/docker-compose.prod.yml \
      ubuntu@<主机>:/opt/ops-desk/deploy/docker-compose.prod.yml

同步后先**不要** `up`，先做 §3 写 `.env`，再 §4 一次重载。

对照：`ops-desk-workspace/docs/04-infrastructure/02-prod-env-reload.md`。

---

## 3. 生产 `.env`

SSH 上编辑（不要用 `docker compose restart`，那一步在 §4）：

    sudo vim /opt/ops-desk/.env

追加（值换成 §1 的 `<TOKEN>`）：

    # Admin sync · GHA Bearer（与 GitHub Secret 同源）
    OPS_ADMIN_SYNC_TOKEN=<TOKEN>

建议同时把同一行补进 workspace `deploy/.env.example`（空值注释），避免下次对照表漏键。

核对文件里有键、**不要** `cat` 整份 `.env` 发到别处：

    grep '^OPS_ADMIN_SYNC_TOKEN=' /opt/ops-desk/.env

---

## 4. 重载 api 容器并核对

在生产机：

    cd /opt/ops-desk/deploy

    docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
      up -d --no-deps api

    docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
      exec -T api python -c "import os; v=os.getenv('OPS_ADMIN_SYNC_TOKEN') or ''; print('len', len(v), 'set', bool(v))"

期望：`len 64 set True`（若你用了 `openssl rand -hex 32`）。  
**不要** `print` token 本身。

若 `len 0`：compose 没透传，或 scp 的仍是旧 yaml，或 `.env` 键名拼错。回到 §2。

`restart` / `docker restart` **不会**重新展开 `.env`。禁止为改 env 使用 `docker compose down`（会停 db）。

---

## 5. GitHub Actions Secrets（ops-desk-api 仓）

仓库：**Cyning12/ops-desk-api** → Settings → Secrets and variables → Actions。

或本机（在 api 仓根，已 `gh auth`）：

    # 公网 API 根：脚本会再拼 /api/ops/admin/sync
    # 不要写成 https://www.cynaya.cn/api ，也不要尾斜杠
    gh secret set OPS_API_BASE_URL --body "https://www.cynaya.cn"

    # 与 /opt/ops-desk/.env 同一串；从本地文件读，避免进 shell history
    printf '%s' '<TOKEN>' | gh secret set OPS_ADMIN_SYNC_TOKEN

`GITHUB_TOKEN` **不用配**（workflow 用内置）。

### 5.1 可选：scan / graph 快照

不配也能跑通 Issue/PR；GHA 会 warning 后 skip 对应 snapshot。

| Secret | 用途 | 不配时 |
|---|---|---|
| `WORKSPACE_REPO_TOKEN` | checkout `Cyning12/cyning-ink-workspace` 的 ISSUE_SCAN md | 无 `scan_snapshot` |
| `KIMI_META_REPO_TOKEN` | checkout `Cyning12/kimi-code` 分支 `cyning/meta` 的 `graph.json` | 无 `graph_snapshot` |

需要 PAT：`repo` 读权限（私有仓）；公钥仓也可用有 `contents:read` 的 fine-grained token。旧仓若已有同名 secret，可复用到 **本仓**（新 workflow 读的是 **ops-desk-api** 的 secrets，不会自动继承旧仓）。

---

## 6. 第一次生产触发（建议 incremental）

1. GitHub → **ops-desk-api** → Actions → **ops-sync-kimi-code** → Run workflow。
2. `sync_mode` 选 **incremental**（`utcnow-48h`）。第一次水位旧，48h 窗口可能条数不多；要灌全量再考虑 `full`（见 §8）。
3. 等 job 绿。日志应类似：`sync ok status=202 type=incremental issues=… prs=…`。出现 `POST sync HTTP 401` = token 三处不一致或容器未重载。

cron 已写：每日 **UTC 02:00**（约北京时间 10:00）。secrets 配齐后不必每天手点。

---

## 7. 怎么确认落库

登录 https://www.cynaya.cn （maintainer cookie），看 Overview 的最近 `sync_run`（`finished_at` 应为刚跑完的时间），或 Issues 列表是否出现窗口内更新的 kimi-code 条目。

也可用只读接口（需 cookie）：

    GET https://www.cynaya.cn/api/ops/overview
    GET https://www.cynaya.cn/api/ops/issues

服务器上（不要在公网暴露）：

    cd /opt/ops-desk/deploy
    docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
      exec -T db psql -U ops -d opsdesk -c \
      "select sync_type, status, started_at, finished_at, summary from ops_sync_runs order by started_at desc limit 5;"

---

## 8. `full` 与体积风险

| 模式 | since | 适用 |
|---|---|---|
| `incremental`（默认 / cron） | UTC 现在减 48 小时 | 日常；与上次重叠，upsert 幂等 |
| `full` | 不限制 | 补洞、长期没跑之后 |

Nginx `client_max_body_size` 现网是 **10m**。`full` 会带上每条 `raw_payload`，Issue 量大时可能 **413**。若 413：先继续用 incremental 多跑几天补水位，或临时提高 Nginx 该值后 reload（改完记得改回去或留合理上限）。workflow `timeout-minutes: 30`，全量分页也可能顶满 30 分钟。

---

## 9. 关掉旧仓日更（避免双写）

新路径写的是 **本仓 PG**。旧路径仍写 **Supabase**：

    Cyning12/ai-ink-brain-api-python
    .github/workflows/ops_sync_kimi_code.yml

新路径跑绿并 §7 确认后：旧仓 Actions → 该 workflow → Disable workflow（或删 cron，只留手动）。本仓文档只标注 deprecated，**不会**替你关另一仓库。

回滚：再启用旧仓 workflow；新仓 workflow 可 Disable。两边不要长期同时 cron。

---

## 10. 本机试跑（可选，不打生产）

需要：本机 API 已起、`.env` 里 `OPS_ADMIN_SYNC_TOKEN` 非空、有 `GITHUB_TOKEN`（读公开仓即可）。

    export GITHUB_TOKEN=ghp_...          # 或 gh auth token
    export OPS_API_BASE_URL=http://127.0.0.1:8000
    export OPS_ADMIN_SYNC_TOKEN='与本地 .env 相同'
    export SYNC_MODE=incremental
    python scripts/ops_sync_kimi_code.py

期望退出码 0。不要把生产 token 用在本机日志里。

---

## 11. 键清单（总表）

### 生产 API / compose / `.env`

| 键 | 必填 | 说明 |
|---|---|---|
| `OPS_ADMIN_SYNC_TOKEN` | 要 GHA 能 POST 则必填 | 空 = 只允许 cookie maintainer |

### GHA（ops-desk-api Secrets）

| 键 | 必填 | 说明 |
|---|---|---|
| `OPS_API_BASE_URL` | 是 | `https://www.cynaya.cn` |
| `OPS_ADMIN_SYNC_TOKEN` | 是 | 与生产 `.env` 同源 |
| `GITHUB_TOKEN` | 否（内置） | 读公开 `MoonshotAI/kimi-code` |
| `WORKSPACE_REPO_TOKEN` | 否 | ISSUE_SCAN |
| `KIMI_META_REPO_TOKEN` | 否 | graph.json |

### 脚本还可读、GHA 未设的 env

| 键 | 默认 |
|---|---|
| `OPS_SYNC_REPO` | `MoonshotAI/kimi-code` |
| `SYNC_MODE` | workflow：`incremental` 或输入 `full` |
| `OPS_SCAN_INDEX_PATH` | workflow 已写相对路径 |
| `OPS_GRAPH_JSON_PATH` | workflow 已写相对路径 |

**不要**再配旧仓那套 `NEXT_PUBLIC_SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`（新 sender 不写 Supabase）。

---

## 12. 失败对照

| 现象 | 先查 |
|---|---|
| `POST sync HTTP 401` | 三处 token 是否同一串；容器 `len` 是否非 0；compose 是否已 scp |
| `缺少 OPS_API_BASE_URL` | GHA Secret 名/空值 |
| `缺少 GITHUB_TOKEN` | 不应发生（内置）；若 fork 私有需检查 permissions |
| `sync failed: The write operation timed out` | 海外 GHA → 国内 API 写 body 超时。#88 默认 60s；应已改为 write/read 180s。重跑 incremental；日志看 `POST sync bytes=` |
| `POST sync HTTP 500` · `value out of int32 range` | GitHub node id 超过 int32。#91 已把 ORM/列改为 BIGINT；合入部署后再跑 |
| job 绿但 Overview 没新 run | 打到了错的 `OPS_API_BASE_URL`（预发/本地） |
| cron 到点没跑 | workflow 在非 default 分支；或 Actions 被 disable |
| scan/graph skip | 可选 secret 未配，属预期 |

轮换 token：同时改 GitHub Secret + `/opt/ops-desk/.env`，再 §4 `up -d --no-deps api`，然后手跑一次 incremental。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 初版：合入 #88 后的生产配置路线（含 compose 透传缺口） |
| 2026-08-28 | 补失败对照：写超时 #89、github id int32 #91；生产 incremental 已见看板更新 |
