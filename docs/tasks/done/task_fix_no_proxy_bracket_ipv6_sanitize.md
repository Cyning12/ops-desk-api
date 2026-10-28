# task（fix · active）：启动期清洗 NO_PROXY 方括号 IPv6 条目（httpx InvalidURL ':1]' 根治）

> **状态**：active（2026-10-28 维护者签收 m00416「也一次性修复了，两个task一起验收吧」，00 转录闸表；与 task_lg_rag_capability_output_schema 合并验收 5 同场复跑）。
> **由来**：2026-10-27 复跑 supervisor-replan-error-feedback 验收场景时，run `0fbebc8e8708459fb8e9e347e0236f62` seq19 `lg_rag.worker_failed`：旁路流式调用失败 `InvalidURL("Invalid port: ':1]'")`。同款钉案先例：`docs/tasks/close/close_vector_waterline_local_rerun_20261017.md` §四.1（当时剥代理重跑绕过，未根治）。
> **分支**：fix/no-proxy-bracket-ipv6-sanitize（fix，非紧急，仍走 task 流程）。

## 根因（已钉案，2026-10-27 实证）

本机 shell 代理配置 `NO_PROXY=localhost,127.0.0.1,::1,[::1]`（Clash 系客户端常见写法）。uvicorn 进程继承 shell env，httpx 处理 proxy bypass 列表时把方括号 IPv6 条目 `[::1]` 当 URL 解析，`:1]` 被截为端口 → `InvalidURL`。凡旁路 LLM 流式调用（`app/llm/providers/base.py:385` `httpx.AsyncClient` 按调用构造、默认 `trust_env=True`）即炸，**每次手动重启进程都可能再踩**（今天 00 用 nohup 重启继承脏 env 即实证第三次）。2026-10-28 **第四实证**：00 重启时仅覆盖大写 `NO_PROXY`，小写 `no_proxy` 仍带 `[::1]` 漏入进程（httpx 按 urllib 惯例小写优先）→ 同 query 复跑 seq 同炸——佐证双写清洗（验收 3）不可省。

## 修复设计（最小面）

app 启动早期（`app/main.py` import 期，承 `_init_logging()` N-40-1 行序先例）新增 `_sanitize_no_proxy_env()`：

1. 读 `NO_PROXY` / `no_proxy` 两键，逐条目剥离方括号 IPv6 形态（`[::1]` → `::1`），其余条目原样保留、顺序不动；
2. 仅当内容实际变化时回写 `os.environ`（无方括号条目 → 零 diff，env 逐字节不变）；
3. 纯 stdlib、幂等、无循环 import 风险（同 _init_logging 约束）。

## 非范围

- 不动 httpx 钉版、不动代理本体配置（http_proxy/7890 保留，外网 LLM 仍走代理）。
- 不管用户 shell rc / 系统代理设置（环境源头由维护者自理）。
- scripts/evals 等不经 `app.main` 入口的直 import 路径不覆盖（另议，主战场是 uvicorn 服务进程）。

## 验收标准

- [ ] 1. 单测：monkeypatch env 注入 `NO_PROXY=localhost,127.0.0.1,::1,[::1]` → 调用清洗后 `[::1]` 变 `::1`、其余条目与顺序不变；httpx 以该 env 构造 client 并做 bypass 判定不抛 InvalidURL（复现今日炸点的回归钉）。
- [ ] 2. 无方括号条目的 env → 清洗后 env 逐字节不变（零 diff 口径，承 preserved_block 先例）。
- [ ] 3. `NO_PROXY`/`no_proxy` 大小写两键同处理；键缺失时 no-op。
- [ ] 4. `.venv/bin/ruff check app tests` 绿；`pytest tests` 不引入新红（基线 28 红口径承 task_supervisor_replan_error_feedback 维护者裁决）。

## failure_paths

- 清洗插入点：`app/main.py` `_init_logging()` 之后（约 :40 后）——必须先于任何 app 包 import（import 链窗口期即可能构造 client 的先例见 N-40-1 注释块）。
- httpx env 读取时机：client **构造时**读 env（trust_env），故 import 期清洗覆盖其后全部构造。
- uvicorn `--reload` 子进程继承 supervisor env——import 期清洗天然覆盖每次 reload。
- 若未来 httpx 上游修复该解析，本清洗保持无害（幂等 + 零 diff）。

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `fix-no-proxy-bracket-ipv6-sanitize` |
| **git_branch** | `fix/no-proxy-bracket-ipv6-sanitize` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | monkeypatch env 单测 + httpx client 构造回归钉；不连真网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `minimal` |
| **close_pr_policy** | `required` |

### 自检结论

结构对齐本仓已合并 task 先例（task_supervisor_replan_error_feedback · PR #293）；元信息块预填含 wiki_delta（承 K4/lint-wiki-delta 首红教训）。dsh-coding-kit task lint 余项 E2（状态行措辞枚举）与 merged 先例同型，属该 lint 在本仓的既有口径差，不阻塞。

## 人工闸表

| 闸 | 状态 | 备注 |
|---|---|---|
| HG-AUDIT-R1 | approved | 2026-10-28 维护者签收（m00416「也一次性修复了，两个task一起验收吧」），00 转录 |
| HG-GRAPH-MODULES | n/a | 不动图谱分层 |
