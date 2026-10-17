# CLOSE：host-v1-sli-dashboard（04 测评轨 · Host v1.0 SLI 四项看板落地 · D5 降级路径照登）（2026-10-17）

> **task**：[../done/task_host_v1_sli_dashboard.md](../done/task_host_v1_sli_dashboard.md)（已归档 done/）
> **类型**：observability / eval follow-up（docs+ops 面 · 零 `app/` 生产改动 · `graph_change_layer=none`）
> **关账日期**：2026-10-17 · 帽位：CLOSE（50 · 三 task 批量关账 · 分支 `close/active-batch-20261017-pm` · 授权链：维护者 2026-10-17 m00238「授权00签收后续文档，开始下面的任务」· 00 代录 · 20 R1 书面审经授权豁免）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `host_v1_sli_dashboard` |
| 依据 | `docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md`（看板操作真值）· `docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md`（定义 signed 2026-09-24）· `docs/tasks/done/task_host_v1_sli_four_metrics.md`（四指标定义/有数/GUIDE 已 done · **Dashboard 实证未交付**） |
| 背景 | 上一棒把「看板」交付到 GUIDE（操作手册）层即 CLOSE：四项 SLI 定义表 signed、有数落点（`aggregate_sli.py` + fixture）、离线 CI 测试、操作手册均在；缺口 = Langfuse 项目里真实保存的四项 Dashboard widget 与可复现查询/导出证据未落地（`docs/reports/host_v1_exit_review/` 原仅 2026-09-24 三件，无看板证据） |
| 目标 | 按 GUIDE §三步落地四项看板（widget 名=dict_key）+ 钉死可复现查询/导出 + 证据入 `docs/reports/host_v1_exit_review/`；**无权限时走 GUIDE 声明的 fixture 降级路径并诚实照登，禁伪造截图/数字** |
| 分支 | `task/host-v1-sli-dashboard` |
| 帽链 | 10-task → 20-task-audit R1 书面审签收（授权豁免 · 址A 落盘）→ 三闸 approved（00 代录 · m00238）→ 30 落地（FP-1 触发 → **D5 降级路径** · `invoke_20261017_30_sli_dashboard.md`）→ PR #261 → **CLOSE（本档 · 40 轨未走照登）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#261](https://github.com/Cyning12/ops-desk-api/pull/261) · **MERGED 2026-10-17T05:50:13Z · squash commit `19a32d5`** |
| 证据文（D1–D6 载体） | `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md`：§2 探测表（env/.env.example/tracing.py/curl 四面）· §3 四项筛选表（widget 名=dict_key 逐字 · UI 入口/筛选字段/时间窗/导出列钉死）· §4.1/§4.2 聚合对拍 · §5 pytest 摘录 · §6 diff 白名单 · §7 口径自检 |
| fixture 新增（D3） | `evals/agent/sli/fixtures/sli_sample_unknown.json`：unknown 语义实证样例——缺 `ok` → `avail.capability_ok="unknown"` · 缺单价 → `host.cost_per_successful_task="unknown"`（均非 0 · FP-6 铁律可跑证据）；`aggregate_sli.py` 零改动（非范围遵守） |
| 降级照登（D1/D5） | **照登：无实证（无 Langfuse 项目权限）**——探测四面：env 无 `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`OPS_LANGFUSE_HOST` · `.env.example:120-131` 全注释占位 · `tracing.py` 双 key 门控 · `localhost:3000` curl=000 无自建实例；零伪造截图/数字 |
| 离线闸（D4） | `uv sync --extra dev && uv run pytest tests/eval/test_host_v1_sli.py -q` → **9 passed in 0.09s**；零 `.py` 改动，ruff 触及面净增 0 |
| invokes | `docs/harness/invokes/by-task/host-v1-sli-dashboard/`（10_task_draft / 20_task_audit_r1 / 30_sli_dashboard · 40 缺位照登 · 本批 CLOSE 纪律不另立 50 invoke） |
| 审查文 | 址A `docs/harness/reviews/task_host_v1_sli_dashboard_audit_R1_20261017.md`（书面审签收 · 授权豁免） |
| **CLOSE 增量** | task 档归档 done/ · 本档落盘（**本批纪律：仅新增 `docs/tasks/close/close_*.md` · 零 git 操作 · 不改其他任何文件**） |

## 三 · 核验结论（验收终态摘要 · TC-D1–TC-D6 逐项）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC-D1 Dashboard 实证 | ✅（**降级路径照登成立**） | FP-1 触发（无 Langfuse 项目权限）→ D5 降级：「照登：无实证（无 Langfuse 项目权限）」钉死句式 + fixture 聚合作有数证据（证据文 §2 探测表）；禁伪造遵守 |
| TC-D2 可复现查询钉死 | ✅ | 证据文 §3 四项筛选表：`latency.e2e_p99_ms` / `avail.success` / `avail.capability_ok` / `host.cost_per_successful_task` 各自 UI 入口/过滤字段/时间窗钉死，第三者按文档可复开同视图；GUIDE 零改动（D2 允许落 reports 或回写 GUIDE，择前者） |
| TC-D3 聚合对拍 | ✅（真实导出照登无实证） | GUIDE §步骤 3.2 命令实跑（fixture 主样例）**四键齐：p99=400.0ms · success=0.6 · capability=0.75 · cost=0.004**；`sli_sample_unknown.json` 实证 unknown 语义（缺 `ok`/缺单价均输出 `unknown` 非 0）；真实导出对拍：照登：无实证（降级路径无真实导出） |
| TC-D4 离线闸 | ✅ | `pytest tests/eval/test_host_v1_sli.py -q` → **9 passed**；零 `.py` 改动 ruff 净增 0（`tests/eval/` 现存 7 处存量错误与本棒 diff 零交集，不修不扩面） |
| TC-D5 零越界 | ✅ | 证据文 §6 diff 白名单：仅触 `docs/reports/host_v1_exit_review/` + `evals/agent/sli/fixtures/` 新增样例 + task/invoke/review 档；`app/` / `aggregate_sli.py` / SLI 定义表零 diff |
| TC-D6 口径一致 | ✅ | 证据文 §7 自检：四项键名与 `SLI_host_v1_four_metrics_v1.md` §2 dict_key 列逐字一致；成功口径=终态 `done`（承 V1-C）；无另发明公式字样 |

**CLOSE 质量钉复跑（本帽 · 2026-10-17 · 分支 `close/active-batch-20261017-pm` 归档后仓态）**：

- `npx --yes spec-wave verify --target .` → **EXIT=0 · VERIFY: PASS**（裸 verify · 仓级 reviews 扫描 · 4 条存量基线豁免命中留痕 · 2026-10-11 授权 m01606/m00255 在案）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_host_v1_sli_dashboard.md` → **EXIT=0 · LINT: PASS**。

## 四 · 偏差与 nit（如实照登）

1. **TC-D1 走 FP-1 降级 · 真实 Dashboard 实证缺口残留（可重试）**：Langfuse 项目权限不可得（探测四面见证据文 §2），widget 保存/截图未落地——**获权后按 `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3 钉死条件补四项 widget + 截图**（FP-1 明文可重试路径）；补实证前 07 §4「有看板」的出口语义以本降级照登为准，禁对外声称看板已落地。
2. **真实导出对拍无实证（降级伴随缺口）**：D3 真实 Traces/Scores 导出映射 fixture 形状样例未入仓（无权限无真实数据），fixture 主样例 + unknown 样例聚合已并列留档；获权后与 D1 一并未雨补证。
3. **`uv run pytest` 环境坑留痕**：首次解析到 conda 的 pytest（`/Users/cyning/miniconda3/bin/pytest` · 缺 asyncpg）→ 需 `uv sync --extra dev` 装 dev extra 后绿；非代码问题，复跑须知。
4. **ruff 存量错误不修（零扩面纪律）**：`tests/eval/test_capability_redlines.py` F811 等 7 处存量错误与本棒 diff 零交集——越 task 范围即 STOP，「ruff 触及面净增 0」以零 `.py` diff 断言成立。
5. **40 轨未走照登**：task orchestration 原列 40 可复现性核验；本批交付由 30 → PR 直连，40 invoke 缺位；D2 文档化钉死 + D4 离线闸绿已覆盖可复现性主体，残余风险 = 真实环境复开未验（与 §四.1 同一权限根因）。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-17 维护者授权 00 代录（m00238） |
| HG-AUDIT-R1 | **approved** | 同上（20 R1 书面审经授权豁免） |
| HG-GRAPH-MODULES | **approved** | 同上（全局真值 approved · `docs/_tech_graph/l1/01_modules.md:63` · `graph_change_layer=none`） |
| 20 R1 审查 | **签收（书面审豁免）** | 址A `docs/harness/reviews/task_host_v1_sli_dashboard_audit_R1_20261017.md` |
| invokes | — | `by-task/host-v1-sli-dashboard/`（10/20/30 · 40 缺位照登） |
| 合并 | **MERGED** | PR [#261](https://github.com/Cyning12/ops-desk-api/pull/261) · squash `19a32d5` · 2026-10-17T05:50:13Z |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**（本批纪律零 git 操作）：分支 `task/host-v1-sli-dashboard`（已 squash 合入 master `19a32d5` · 删除安全 · 远端一并清）与本批 CLOSE 分支 `close/active-batch-20261017-pm` 移交 00/维护者统一清理。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（00 代录 · 授权链同上 · 需人抽验项）

- [ ] **证据文抽验**：`docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §2–§7 六节齐备（探测表 / 四项筛选表 / 聚合对拍 / pytest 摘录 / 白名单 / 口径自检）。
- [ ] **unknown 语义抽验**：`sli_sample_unknown.json` 实跑聚合 → 缺 `ok` / 缺单价面输出 `unknown` 非 0（FP-6 铁律）。
- [ ] **离线闸抽验**：`uv sync --extra dev && uv run pytest tests/eval/test_host_v1_sli.py -q` → 9 passed。
- [ ] **（获权后）D1 补实证**：获 Langfuse 项目权限后按证据文 §3 钉死条件保存四项 widget（名=dict_key 逐字）+ 截图入 `docs/reports/host_v1_exit_review/`（文件名含日期）——补实证前本 task 以降级照登为准。

### 后续建议

1. **Langfuse 权限申请（补实证前置）**：D1 真实 Dashboard 实证 + D3 真实导出对拍同根因（无项目权限），建议维护者排期授权后一次性补两件证据，回填证据文 §2/§4 并修订本档照登行。
2. **ruff 存量收口（可选 · 另案）**：`tests/eval/` 7 处存量错误可并入仓级测试卫生 task 统一处置。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（50 close 棒 · 三 task 批量关账 · 分支 `close/active-batch-20261017-pm`）：九节沿仓内先例 · 验收终态承 30 invoke TC-D1–D6（D1 走 FP-1/D5 降级照登 · D3 fixture 四键齐 + unknown 实证 · D4 pytest 9 passed）· 质量钉复跑（verify EXIT=0 PASS · task lint done/ 档 EXIT=0 PASS）· 降级缺口（真实 Dashboard / 真实导出）与获权补实证路径如实照登 · 40 轨缺位照登 · 维护者 checklist 00 代录（授权链 m00238） |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| task（已归档） | `docs/tasks/done/task_host_v1_sli_dashboard.md` |
| CLOSE 档 | `docs/tasks/close/close_host_v1_sli_dashboard_20261017.md`（本档） |
| 证据文 | `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md`（§3 = 获权后补实证操作真值） |
| fixture 新增 | `evals/agent/sli/fixtures/sli_sample_unknown.json`（unknown 语义样例） |
| 操作/定义真值 | `docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md` · `docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md`（+ yaml 机读副本） |
| 审查文（址A） | `docs/harness/reviews/task_host_v1_sli_dashboard_audit_R1_20261017.md` |
| invokes | `docs/harness/invokes/by-task/host-v1-sli-dashboard/`（10_task_draft / 20_task_audit_r1 / 30_sli_dashboard） |
| 上游 task（done） | `docs/tasks/done/task_host_v1_sli_four_metrics.md` |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave verify --target . > /tmp/verify_close_batch_pm.log 2>&1; echo "EXIT=$?"   # EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_host_v1_sli_dashboard.md           # EXIT=0 · LINT: PASS
```
