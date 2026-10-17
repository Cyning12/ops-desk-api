---
hat: 30
task_slug: host_v1_sli_dashboard
date: 2026-10-17
---

# invoke · 30 落地 · host_v1_sli_dashboard（Langfuse 四项 SLI 看板 · 降级路径实证）

## 摘要

- **GATE_VERIFY PASS**：三闸 approved（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · 2026-10-17 维护者授权 00 代录 m00238）；`npx spec-wave verify` 输出 `VERIFY: PASS · task_host_v1_sli_dashboard.md`。
- **D1 走 FP-1 降级路径**：**照登：无实证（无 Langfuse 项目权限）**——env 无 `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`OPS_LANGFUSE_HOST`，`.env.example:120-131` 全注释占位，`localhost:3000` curl=000 无自建实例；禁伪造截图/数字，零伪造。
- **D2 查询钉死已文档化**：四项 widget（名=dict_key 逐字：`latency.e2e_p99_ms`/`avail.success`/`avail.capability_ok`/`host.cost_per_successful_task`）UI 入口/筛选字段/时间窗/导出列钉死于 `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3（D2 允许落 reports 或回写 GUIDE，择前者，GUIDE 零改动）。
- **D3 聚合对拍留档**：GUIDE §步骤 3.2 命令实跑（fixture 主样例）四键齐：p99=400.0ms · success=0.6 · capability=0.75 · cost=0.004；新增 `evals/agent/sli/fixtures/sli_sample_unknown.json` 实证 unknown 语义：缺 `ok` → `avail.capability_ok="unknown"`、缺单价 → `host.cost_per_successful_task="unknown"`（均非 0，FP-6 铁律可跑证据）。真实导出对拍：**照登：无实证**（降级路径无真实导出）。
- **D4 离线闸绿**：`uv sync --extra dev && uv run pytest tests/eval/test_host_v1_sli.py -q` → `9 passed in 0.09s`；零 `.py` 改动，ruff 触及面净增 0（`tests/eval/` 现存 7 处存量错误与本棒 diff 零交集，不修不扩面）。
- **D5/D6 自检 PASS**：diff 白名单仅触 `docs/reports/host_v1_exit_review/` + fixture 新增样例 + 本 task + invoke/review 档；键名逐字一致、成功口径承 V1-C、无另发明公式。

## 证据

| TC | 结论 | 证据落点 |
|---|---|---|
| TC-D1 Dashboard 实证 | 降级照登（无实证 + fixture 证据） | 证据文 §2（探测表：env/.env.example/tracing.py/curl） |
| TC-D2 查询钉死 | ✅ 文档化 | 证据文 §3 四项筛选表（widget 名=dict_key 逐字） |
| TC-D3 聚合对拍 | ✅ fixture 两组并列 + unknown 实证 | 证据文 §4.1/§4.2 命令与输出摘录；真实导出照登无实证 |
| TC-D4 离线闸 | ✅ 9 passed | 证据文 §5 输出摘录 |
| TC-D5 零越界 | ✅ | 证据文 §6 diff 白名单表 |
| TC-D6 口径一致 | ✅ | 证据文 §7 自检 |

## 过程

1. 亲读 task 全文 + GUIDE + SLI 定义表 + aggregate_sli.py + fixture + test_host_v1_sli.py；闸扫描 `npx spec-wave verify` → PASS。
2. Langfuse 可得性探测：env 变量空 · `.env.example` 全注释 · tracing.py 双 key 门控 · localhost:3000 不可达 → 判定 FP-1 降级路径（未尝试伪造截图/数字）。
3. `uv sync`（首次缺 pytest：落在 optional-dependencies `dev` extra）→ `uv sync --extra dev` → pytest 9 passed。
4. 实跑 GUIDE §3.2 聚合命令（fixture 主样例）四键齐；新增 `sli_sample_unknown.json` 并实跑，unknown 语义实证。
5. 落证据文 `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` + 本 invoke；task 档状态/自检/修订记录回填；commit + push + PR。

## 偏差

- **D1 无真实 Dashboard 实证**：Langfuse 项目权限不可得（FP-1 声明路径），走降级；获权后按证据文 §3 钉死条件补 widget + 截图。
- `uv run pytest` 首次解析到 conda 的 pytest（`/Users/cyning/miniconda3/bin/pytest`，缺 asyncpg）→ 需 `--extra dev` 装 dev extra 后绿；非代码问题，记此备查。
- ruff 存量错误（`tests/eval/test_capability_redlines.py` F811 等 7 处）不修：越 task 范围即 STOP；「ruff 触及面净增 0」以零 `.py` diff 断言成立。
