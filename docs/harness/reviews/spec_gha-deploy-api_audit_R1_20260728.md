# SPEC Audit R1：gha-deploy-api

> **hat_id**：20-spec-audit  
> **SPEC**：`docs/spec/SPEC-gha-deploy-api_v1.md`（status: `accepted`）  
> **日期**：2026-07-28  
> **对照金样**：`ops-desk-web/.github/workflows/deploy-web.yml` · `ops-desk-web/docs/deployment/gha-frontend-deploy.md`  
> **对照现状**：`ops-desk-workspace/deploy/deploy.sh`（`--skip-web`）· `docker-compose.prod.yml`（仅 `db`+`api`，无 web 容器）

---

## 结论

| 项 | 值 |
|---|---|
| **判定** | **conditional_pass** → 条件已落盘 |
| **HG-SPEC-SIGNOFF** | **approved**（维护者 2026-07-28 指示签收） |
| **下一棒** | 00 起草 task `gha-deploy-api` |

### 签收备注（C1–C3 决议）

| 条件 | 决议 |
|---|---|
| C1 | 远端锁死 `up -d --build **api**`；不重建 db；schema 靠 alembic |
| C2 | 本波不 reload Nginx；改 conf 走 `deploy.sh --nginx-only` |
| C3 | 维护者一次性 chown；workflow 默认不每次 sudo chown |

---

## 元信息核对

| 字段 | SPEC 值 | 审阅 |
|---|---|---|
| `spec_slug` | `gha-deploy-api` | OK |
| `test_strategy` | `recommended` | OK（去 probe 单测必测；真 SSH 不进 CI） |
| Open Folder | `ops-desk-api/` | OK |
| 默认分支 | `master`（对照 web `main`） | OK |
| `HG-SPEC-SIGNOFF` | **approved** | 维护者签收 |
| 思考轮 | R0–R5 · `early_stop=no` | 闭合充分，轻量 R1 足够 |

---

## 核对表（重点项）

### 1 · 范围 / 非范围

| 检查点 | 结果 | 说明 |
|---|---|---|
| D1 去 probe 同波必做 | **pass** | `app/main.py` + `tests/test_health.py` + 关闭 `task_health_temp_probe`；与上游「顺便删除 probe」一致 |
| D2 GHA 发版通道 | **pass** | push `master` + `workflow_dispatch`；Secrets 门闩；rsync 排除项对齐 `deploy.sh` |
| D3 文档 | **pass** | 对照 web `gha-frontend-deploy.md` 形态清晰 |
| D4 Secrets/权限属维护者 | **pass** | Agent 不写私钥；可选 Secret 命名与 web `DEPLOY_PATH` 区分得当 |
| 非范围（不改 web / 不搬 deploy / 不改业务） | **pass** | §3 明确；与金样边界互补 |
| 与 `deploy.sh --skip-web` 等价声明 | **conditional** | 见阻塞/条件 #1、#2 |

### 2 · 与 web 边界 · 不误伤 web dist

| 检查点 | 结果 | 说明 |
|---|---|---|
| 同步目标仅 `/opt/ops-desk/api/` | **pass** | 与 web 的 `/opt/ops-desk/web/dist` 路径分离 |
| 验收显式「未改 web/dist」 | **pass** | §4 清单有勾选项 |
| 并发部署 failure_path | **pass** | §5「勿互相 `--delete` 错目录」 |
| compose 无 web 服务 | **pass** | 现网 `docker-compose.prod.yml` 仅 db+api；重建容器本身不碰静态 dist |
| 非范围含「不改 deploy-web」 | **pass** | 明确 |

### 3 · docker / sudo 失败路径

| 检查点 | 结果 | 说明 |
|---|---|---|
| 相对 web 的权限增量 | **pass** | §2 D4 三种方案（docker 组 / sudoers / 封装脚本） |
| 未配齐 → 红属 failure_path | **pass** | 非代码 bug；residual_risks ① 已记 |
| §5 表覆盖 Secrets / SSH / docker / compose 缺失 / health 超时 | **pass** | 可重试标注合理 |
| 密钥不落日志 / 不入仓 | **pass** | R3 + 非范围 |

### 4 · 去 probe 同波

| 检查点 | 结果 | 说明 |
|---|---|---|
| D1 与 D2 同波 | **pass** | 一句话目标 + D1「同波必做」 |
| 验收可测 | **pass** | `pytest tests/test_health.py` + 远端 curl 无 `probe` |
| 与现行 probe 状态一致 | **pass** | 现状 `probe=20260728-a`（PR #16）与 SPEC 描述吻合 |

### 5 · 思考轮 / 方案 / 可测性

| 检查点 | 结果 | 说明 |
|---|---|---|
| R2 方案 A 推荐合理 | **pass** | 对齐现网；B/C/D 弃因充分 |
| 不引入 Registry（本波） | **pass** | 非范围清晰 |
| `test_strategy=recommended` | **pass** | Secrets 门闩可机械测；真连生产靠人 |

---

## 条件（conditional_pass · 签收前接受或补进 SPEC）

以下 **非** 方案级否决，但若不锁死，30 易与 `deploy.sh` / 「仅 api」字面冲突：

### C1 · compose 命令字面 vs「仅 api」

- SPEC 写：`up -d --build`（**仅重建/重启 api 相关**）。
- 现网 `deploy.sh` 为 **无服务名** 的全栈 `up -d --build`（db+api）；compose **无** web 服务，故 **不会**误伤 dist。
- **要求**：人签前在 SPEC 或后续 task 写死二选一：
  - **推荐**：与 `deploy.sh` 同：`up -d --build`（全栈；语义=不碰 web dist，非 `docker compose … api` 过滤）；或
  - 显式：`up -d --build api`（并说明 db 不重建的取舍）。
- 禁止实现时误用会扫到 `/opt/ops-desk/web/` 的路径或 `--delete`。

### C2 · 相对 `deploy.sh --skip-web` 的 Nginx 差量

- `deploy.sh --skip-web` 在 api 之后仍跑 `--nginx-only`。
- 本 SPEC 未写 Nginx；金样 web 也不碰 Nginx。
- **要求**：非范围补一句「本波 **不** reload Nginx / 不改 nginx conf」（应急仍靠 `deploy.sh`），避免 30「对齐 skip-web」时顺带扩 scope。

### C3 · 远端目录属主（实现提示）

- `deploy.sh` 在 rsync 前：`sudo mkdir -p … && sudo chown -R $USER:$USER`。
- SPEC 未写；若 `/opt/ops-desk/api` 属 root，GHA 用户 rsync 会红，且 **不等于** 已文档化的 docker/sudo 缺口。
- **要求**：文档/D4 或 failure_paths 增一行「api 目录须对 `DEPLOY_USER` 可写（首次 chown）」；或 workflow 内在已授权前提下做等价准备（仍禁止把私钥写入仓）。

---

## 阻塞 / 非阻塞

| 级别 | 项 |
|---|---|
| **阻塞签收** | 无（方案 A、范围、web 边界、probe 同波、sudo/docker 失败路径主体成立） |
| **条件（上表 C1–C3）** | **已落盘**进 SPEC（2026-07-28）；闸表 `approved` |
| **非阻塞备注** | timeout 建议 ≥20min 已写；compose 不同步 workspace 已在 residual_risks；复用 web key 扩大权限面已提示 |

---

## HG-SPEC-SIGNOFF

```text
状态：approved（维护者 2026-07-28：「按照上面的落盘并签收」）
SPEC status：accepted
```

---

## 下一棒

1. ~~人签收 SPEC~~ **完成**
2. **00**：按 SPEC §9.2 起草 `task_gha_deploy_api`（分支 `task/gha-deploy-api`；含去 probe + workflow + 文档）。
3. **20-task-audit** → 人签 `HG-AUDIT-R1` → **30**（本审 **不**附 30 Prompt）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 20-spec-audit R1：conditional_pass；建议人签（附 C1–C3） |
| 2026-07-28 | 维护者接受 C1–C3；SPEC 落盘并 HG-SPEC-SIGNOFF=approved |
