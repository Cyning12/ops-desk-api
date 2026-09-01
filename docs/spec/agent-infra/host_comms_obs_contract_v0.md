# 契约：Host C4 · /obs 沟通入口（obs-comms-v0）

> **契约 id**：`obs-comms-v0`  
> **状态**：draft（**文档级契约 · 未实现不冻结行为**；真源实现另 task）  
> **上游**：[`06_host_comms_boundary_spec_v0.md`](./06_host_comms_boundary_spec_v0.md)（**signed** · #111）§4（意图路由）· §6（闸纪律）· §7（Capability 白名单 `harness.status`）· §9（session 隔离）· §10（C4 行）· §11（/obs 主入口钉）  
> **本波 task**：[`task_host_obs_comms_ui`](../../tasks/active/task_host_obs_comms_ui.md)（active · api 无码 · docs-only）  
> **消费方**：ops-desk-web `/obs` 页（跨仓只读参照 `ops-desk-web/src/api/obs.ts` · 对齐 kit `obs_status.v1` / `obs_timeline.v1`）

---

## 1. 范围 / 非范围

**范围**：`/obs` 只读投影的 status/timeline JSON 字段契约 + 示例 + 数据源决策点 + 发起沟通语义 + 依赖注记。

**非范围**：api 真源端点实现（另 task）· 数据源 A/B 选定（本波不拍板）· web Vue 实现（另 task · 见 web Prompt）· `harness.status` Capability 实现（C1 留白 · 真源波补做）· 改 05 freeze `lg-rag-sse-v1`。

---

## 2. ObsStatus 字段表（对齐 web `ObsStatus` / kit `obs_status.v1`）

| 字段 | 类型 | 必填 | 语义 | web 对齐 |
|---|---|---|---|---|
| `schema_version` | string | 是 | 字面 `"obs_status.v1"` | ✅ |
| `task_slug` | string | 是 | task slug（kebab） | ✅ |
| `task_path` | string | 是 | 仓内相对路径 `docs/tasks/active/task_*.md` | ✅ |
| `status` | string | 是 | task 状态（如 `draft` / `in_progress` / `completed`） | ✅ |
| `gates` | ObsGate[] | 是 | 人工闸投影（可空数组） | ✅ |
| `gates[].id` | string | 是 | 闸 id（`HG-*`） | ✅ |
| `gates[].status` | string | 是 | `approved` / `pending` / `n/a` 等 task 表真值字面 | ✅ |
| `gates[].blocks_hats` | string | 是 | 被阻塞帽（如 `"30"` · `"22-R1"`） | ✅ |
| `may_start_30` | boolean | 是 | 全部 blocks-30 闸 approved 且 R1 审查在 → true | ✅ |
| `blockers` | string[] | 是 | 阻塞项清单（如 `"HG-AUDIT-R1=pending"`；无则空数组） | ✅ |
| `last_invoke` | object | 是 | 最近 invoke 投影 | ✅ |
| `last_invoke.path` | string \| null | 是 | 最近 invoke 仓内路径；无 → null | ✅ |
| `last_invoke.hat_id` | string \| null | 是 | 最近 invoke 帽 id；无 → null | ✅ |
| `reviews` | object | 是 | 审查落盘投影 | ✅ |
| `reviews.R1` | boolean | 是 | `docs/harness/reviews/` 存在该 task 的 R1 审查文 | ✅ |
| `reviews.CLOSE` | boolean | 是 | CLOSE 审查/关账落盘 | ✅ |
| `verify_preview` | object | 是 | **只读预览**（非正式 verify） | ✅ |
| `verify_preview.ok` | boolean | 是 | 预览结论 | ✅ |
| `verify_preview.reason` | string | 是 | 人读理由（含「30 前仍须正式跑」类提示） | ✅ |
| `hgm` | object | 是 | 事件投影摘要 | ✅ |
| `hgm.event_count` | number \| null | 是 | 事件数；未知 → null | ✅ |
| `hgm.last_at` | string \| null | 是 | 最近事件 ISO8601；无 → null | ✅ |
| `kpi_section` | boolean | 是 | task 是否含 KPI 节 | ✅ |
| `next_hint` | string | 是 | 下一步人读提示 | ✅ |

## 3. ObsTimeline 字段表（对齐 web `ObsTimeline` / kit `obs_timeline.v1`）

| 字段 | 类型 | 必填 | 语义 | web 对齐 |
|---|---|---|---|---|
| `schema_version` | string | 是 | 字面 `"obs_timeline.v1"` | ✅ |
| `task_slug` | string | 是 | 同 §2 | ✅ |
| `task_path` | string | 是 | 同 §2 | ✅ |
| `event_count` | number | 是 | 事件总数 | ✅ |
| `returned` | number | 是 | 本次返回条数 | ✅ |
| `limit` | number \| null | 是 | 截断上限；未限 → null | ✅ |
| `ingested` | boolean | 是 | 是否已入事件库 | ✅ |
| `ingest` | object \| null | 是 | ingest 详情；无 → null | ⚠️ 偏离（见 §4） |
| `events` | ObsTimelineEvent[] | 是 | 事件列表（可空） | ✅ |
| `events[].event_id` | string | 否 | 事件 id | ✅ |
| `events[].type` | string | 是 | 事件类型（如 `TaskCreated` / `GateApproved`） | ✅ |
| `events[].occurred_at` | string | 是 | ISO8601 时间戳 | ✅ |
| `events[].subject` | string | 否 | 主体（如 `task:<slug>`） | ✅ |
| `events[].summary` | string | 否 | 人读摘要 | ✅ |
| `events[].data` | object | 否 | 扩展载荷 | ✅ |

## 4. 与 web 类型逐字段核对结论（偏离清单）

核对基准：`ops-desk-web/src/api/obs.ts`（2026-09-01 只读快照）。

| # | 字段 | web 类型 | 本契约 | 偏离与理由 |
|---|---|---|---|---|
| 1 | `ObsTimeline.ingest` | `unknown` | `object \| null` | **偏离（收窄）**：web 侧 `unknown` 是 fixture 期占位宽类型；契约收敛为 `object \| null` 以便真源生成与文档化。TS `unknown` 是任意类型的超集，web 现有类型 **兼容无需改**；web 真源切换波可把类型收窄为 `Record<string, unknown> \| null`（类型层面收紧 · 运行时无破坏） |
| — | 其余全部字段 | — | — | **逐字段一致**（字段名 · 可空性 · 嵌套结构 · `schema_version` 字面均对齐；fixture `ingest: null` 与本契约相容） |

**结论**：ObsStatus 14 字段（含嵌套）+ ObsTimeline 9 字段（含 events 6 子字段）全核对；唯一偏离 = `ingest` 收窄，理由如上，web 侧零改动。

## 5. 示例 JSON

### 5.1 ready（闸齐可开 30）

```json
{
  "schema_version": "obs_status.v1",
  "task_slug": "demo-ready",
  "task_path": "docs/tasks/active/task_demo_ready.md",
  "status": "in_progress",
  "gates": [
    { "id": "HG-GRAPH-MODULES", "status": "approved", "blocks_hats": "30" },
    { "id": "HG-TASK-DRAFT", "status": "approved", "blocks_hats": "22-R1" },
    { "id": "HG-AUDIT-R1", "status": "approved", "blocks_hats": "30" }
  ],
  "may_start_30": true,
  "blockers": [],
  "last_invoke": { "path": "docs/harness/invokes/by-task/demo-ready/invoke_30.md", "hat_id": "30" },
  "reviews": { "R1": true, "CLOSE": false },
  "verify_preview": { "ok": true, "reason": "只读预览 PASS（非正式 verify · 30 前仍须正式跑）" },
  "hgm": { "event_count": 2, "last_at": "2026-07-27T12:00:00.000Z" },
  "kpi_section": false,
  "next_hint": "闸已齐 · 跑 harness verify --task … 后开 30"
}
```

### 5.2 blocked（缺 R1 审查 · HG-AUDIT-R1 pending）

```json
{
  "schema_version": "obs_status.v1",
  "task_slug": "demo-blocked",
  "task_path": "docs/tasks/active/task_demo_blocked.md",
  "status": "draft",
  "gates": [
    { "id": "HG-GRAPH-MODULES", "status": "approved", "blocks_hats": "30" },
    { "id": "HG-TASK-DRAFT", "status": "approved", "blocks_hats": "22-R1" },
    { "id": "HG-AUDIT-R1", "status": "pending", "blocks_hats": "30" }
  ],
  "may_start_30": false,
  "blockers": ["HG-AUDIT-R1=pending"],
  "last_invoke": { "path": "docs/harness/invokes/by-task/demo-blocked/invoke_10.md", "hat_id": "10" },
  "reviews": { "R1": false, "CLOSE": false },
  "verify_preview": { "ok": false, "reason": "missing R<n> review（docs/harness/reviews/ 无该 task 的 _audit_R 文件）" },
  "hgm": { "event_count": 0, "last_at": null },
  "kpi_section": false,
  "next_hint": "补 20 R1 审查文后再 verify / 开 30"
}
```

> 两示例与 web fixture `status_ready.json` / `status_blocked.json` 同形（web fixture 即按本契约形态制作）；timeline 示例见 web fixture `timeline_empty.json` / `timeline_events.json`，真源波在本契约补正式示例。

## 6. 数据源决策点（A/B · **本波不选定**）

| 项 | 方案 A：api 直读仓内 docs | 方案 B：GHA sync 落库 · api 读表 |
|---|---|---|
| 机制 | api 端点实时解析 `docs/tasks/active/task_*.md` 人工闸表 + `docs/harness/invokes/` + `docs/harness/reviews/` 投影出 ObsStatus/ObsTimeline | GHA 工作流在 task/invoke/review 变更时跑 sync，把投影写入 DB 表；api 端点只读表 |
| 新鲜度 | 实时（读即真值） | 依赖 sync 触发与频率（分钟级延迟可接受） |
| **风险** | **部署容器无 `docs/`**：生产镜像只带 `app/`，仓内 docs 不在容器内 → 端点无数据源。真源波选 A 须先解决（镜像打包 docs/ 只读副本 · 或挂载卷 · 或改读 git 仓 API） | 新增表 + Alembic 迁移 + GHA 工作流维护；sync 失败时投影陈旧（须暴露 `synced_at` 供 UI 提示） |
| 与 C1 `harness.status` 关系 | 可在 api 进程内直读文件，亦可走 Capability（Policy 默认关须显式开） | 不依赖 Capability（sync 在 GHA 侧跑） |
| 与闸真值纪律 | ✅ 真值仍在 task 表（SPEC 06 §6），api 仅投影 | ✅ 同（表是 task 表的只读镜像，不回写） |

**钉死**：本波 **不选定** A/B；真源实现 task 开工第一棒由 00 拍板并回填本节。

## 7. 发起沟通语义（/obs → comms）

| 项 | 钉死 |
|---|---|
| 入口 | `/obs` 页提供 **显式**「发起沟通」入口（按钮/结构化 UI 入口 = SPEC 06 §4 的显式意图信号）；**无显式点击不进 comms**（默认 product 原则不变） |
| session | 点击 → 新建/切换 **comms session**（C2 `pack=comms` · `session_scope="comms"`）；与 product **分 thread**（SPEC 06 §9）；互不注入历史 |
| 写盘 | comms 内起草 task → C3 writer **dry-run diff 预览** → **人显式确认**后才落盘（SPEC 06 §6 C3 前置；`apply_task_write(confirmed=True)`）；未确认零落盘 |
| 禁代签 | comms/UI 任何位置输出「已签收 / approved / **已代签**」字样 → **违规**（SPEC 06 §6）；可输出「待人签」提示与缺失闸清单；闸真值 **SoT 在 task 表**，UI 只读投影 |
| 浏览器红线 | **浏览器侧禁止执行 npx / 任何 CLI**；status/timeline 一律经 api 端点（真源波）或 fixture（当前波）；`verify_preview` 仅只读预览，正式 verify 在 api/CLI 侧跑 |

## 8. 依赖注记

| 依赖 | 状态 | 注记 |
|---|---|---|
| `harness.status` Capability | **C1 留白**（SPEC 06 §7 可选 · C1 自检显式注明不做） | 真源实现波 **需要时补做**（白名单三条已含 `harness.status` · 不触发 SPEC §7 白名单变更；Policy 默认关沿用）；数据源选 B 时可能不需要 |
| 真源 status/timeline 端点 | **另 task** | 本波仅钉契约；端点形态（路由 · 鉴权 · 数据源 A/B）由真源 task 定 |
| kit `obs_status.v1` / `obs_timeline.v1` | 沿用 | `schema_version` 字面沿用 kit；kit 升级由 `DSH_CODING_KIT_VERSION` env 钉（SPEC 06 §7） |
| web fixture → 真源切换 | 另 task（web 侧） | 切换点与红线见 `docs/harness/invokes/by-task/_prompts/PROMPT_web_00_c4_obs_comms_ui.md` |
| C2 pack=comms / C3 writer | 已 CLOSE（#116/#118） | 发起沟通语义的消费方；本契约只钉交互语义，不改 C2/C3 交付物 |

## 9. failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 部署容器无 docs/（选 A 未解） | 契约决策点 A 已标风险；真源波须先解决（打包 docs 或改选 B） | — | 契约条文 |
| web 抢先接真源（端点未实现） | 契约先于实现；web 未接前仍 fixture | — | web Prompt 红线 |
| 沟通入口误判 | 显式发起才进 comms；默认 product（SPEC 06 §4） | 是 | 契约条文 |
| 未人确认的写盘 | C3 writer 不落盘；仅 dry-run diff | 确认后重试 | diff 预览 |
| UI 出现「已代签」字样 | 违规（SPEC 06 §6 禁令）；闸真值以 task 表为准 | — | 契约条文 |

---

## 10. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **10-task 起草**：字段表逐字段对齐 web `ObsStatus`/`ObsTimeline`（唯一偏离 = `ingest` 由 `unknown` 收窄 `object\|null` · web 兼容零改）· 示例 JSON ready/blocked（与 web fixture 同形）· 数据源决策点 A（部署容器无 docs/ 风险写明）/B（GHA sync 落库）本波不选定 · 发起沟通语义（显式发起 → comms 分 session · 人确认落盘 · 「已代签」违规 · 浏览器禁 npx）· 依赖注记（`harness.status` C1 留白 · 真源实现另 task） |
