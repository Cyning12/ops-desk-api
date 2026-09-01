# PROMPT · web 00 · C4 /obs 沟通入口（fixture → 契约真源 + 发起沟通）

> **产出者**：api 10-task（C 轨末波 · 维护者 Prompt 授权）· 2026-09-01  
> **执行仓**：`ops-desk-web`（本仓 ops-desk-api **不改 Vue**；本 Prompt 为跨仓交付物）  
> **前置**：api C1–C3 CLOSE（#114/#116/#118）· 契约 `obs-comms-v0`（api 仓 `docs/spec/agent-infra/host_comms_obs_contract_v0.md`）已落盘 · web `src/api/obs.ts` 契约类型已在（对齐 kit obs_status.v1 / obs_timeline.v1 · 现 fixture 加载）  
> **上游**：SPEC 06 §4（意图路由 · 默认 product）· §6（闸纪律 · 禁代签）· §9（session 隔离）· §11（/obs 主入口钉）

---

## 背景

api C 轨（C0 边界 SPEC → C1 harness CLI Capability → C2 comms Prompt Pack → C3 受控 task writer）已全部 CLOSE。C4 是末波：`/obs` 页从 fixture 切到契约真源，并加「发起沟通」入口。**api 真源端点本波未实现**（数据源决策点 A/B 未选定 · 另 task）——web 侧先做 UI 与切换点预留，真源端点就绪后再拨开关。

## 建议范围（web task 草稿点）

1. **fixture → 契约真源切换点**：
   - `src/api/obs.ts` 现走 `loadObsStatusFixture` / `loadObsTimelineFixture`（`src/fixtures/obs/*.json`）；抽象一层数据源接口（如 `ObsDataSource`：fixture 实现 + http 实现），切换走 **单一开关**（feature flag / env，如 `VITE_OBS_SOURCE=fixture|api`）
   - http 实现的目标端点形态以契约 `obs-comms-v0` 为准（`ObsStatus` / `ObsTimeline` 字段已逐字段对齐；唯一偏离 `ingest` 收窄 `object|null`，web 现 `unknown` 兼容，切换波可顺手收窄为 `Record<string, unknown> | null` · 运行时无破坏）
   - fixture 保留为默认与 fallback（真源端点未上线前 **不拨开关**）
2. **发起沟通入口 UI**：
   - `/obs` 页显式「发起沟通」按钮（显式意图信号 · SPEC 06 §4）；无点击不进 comms
   - 点击 → 跳 comms 会话入口（**分 session**：comms thread 与 product Chat thread 隔离 · 不共用历史 · SPEC 06 §9）；当前 api 侧 comms 会话接线未完成时，入口可先落 **过渡形态**（提示文案/禁用态 tooltip 说明），不得静默混进 product 会话
   - 状态区展示 `blockers` / `next_hint` / 「待人签」类提示；**闸状态只读投影**
3. **联调确认**：fixture 四场景（ready/blocked/empty/events）渲染正确；开关未拨时零 api 请求（DevTools Network 勾选）

## 红线（沿用 · 违反即退回）

- **浏览器侧禁止执行 npx / 任何 CLI**：status/timeline 只经 fixture 或 api 端点；`verify_preview` 是只读预览，正式 verify 在 api/CLI 侧跑
- **禁代签**：UI 任何位置不得出现「已签收 / approved / **已代签**」的模型生成字样；只渲染 task 表投影；可显示「待人签」（SPEC 06 §6）
- **人确认**：任何 task 落盘必须经 C3 writer dry-run diff + 人显式确认；UI 不提供「跳过确认」路径
- **comms / product 分 session**：不混线 · 不互注历史；误判回退 product（SPEC 06 §4/§9）

## 非范围

- 改 api（契约已落盘 · 真源端点另 task）· 数据源 A/B 拍板 · 实现 comms 会话接线（api 侧另 task）· iOS

## 状态

api C4 契约波进行中（分支 `task/host-obs-comms-ui`）；契约合入后本 Prompt 可派 web 00 起草 web task。
