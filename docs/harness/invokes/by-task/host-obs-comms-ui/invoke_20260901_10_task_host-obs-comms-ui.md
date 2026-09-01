# Invoke：10-task · host-obs-comms-ui（C4 · C 轨末波）

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `host-obs-comms-ui` |
| task_paths | `docs/tasks/active/task_host_obs_comms_ui.md` |
| related_review_or_none | 无（本帽结束后交 20-task-audit） |
| git_branch | `task/host-obs-comms-ui` |
| created_utc_or_local | 2026-09-01 |
| notes | 00 已起草 C4 初稿（00 定夺钉死 · invoke_20260901_00 已落盘）；10 审校 + 起草契约 + web Prompt，**不实现代码**（api 无码 · 不改 web 仓） |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：host-obs-comms-ui  
本帽禁区：不实现代码、不改 CI、不改 `app/` / `tests/`、不改 web 仓任何文件（跨仓只读参照 `ops-desk-web/src/api/obs.ts`）、不改人工闸表状态、不切分支、不 push

必读：`AGENTS.md` · harness-10-task skill · task 初稿（00 定夺钉死）· SPEC `06_host_comms_boundary_spec_v0.md` §4/§6/§9/§10/§11（signed）· web `ops-desk-web/src/api/obs.ts`（ObsStatus/ObsTimeline/fixture 类型）· C1–C3 done 文件（能力面事实）

只做什么：
1. 审校 C4 task：00 定夺逐项核对，不符才修正并记录
2. 起草契约 `docs/spec/agent-infra/host_comms_obs_contract_v0.md`（id `obs-comms-v0`）：字段表逐字段对齐 web ObsStatus/ObsTimeline（偏离写明理由）· 示例 JSON ready/blocked · 数据源决策点 A（api 读仓内 docs · 部署容器无 docs/ 风险）/B（GHA sync 落库）不选定 · 发起沟通语义（显式发起 → comms session · 人确认落盘 · 「已代签」违规 · 浏览器禁 npx）· 依赖注记（`harness.status` C1 留白 · 真源另 task）
3. web Prompt 落 `docs/harness/invokes/by-task/_prompts/PROMPT_web_00_c4_obs_comms_ui.md`：fixture→真源切换点 · 发起沟通入口 UI · 红线
4. task 补 `### 自检结论` + 修订记录 10 行
5. `npx dsh-coding-kit@1.10.0 task lint --file <task>` + `lint-wiki-delta --target .` 须 PASS

禁止扩 scope。禁止改 `app/` / `tests/` / web 仓。禁止改人工闸表状态。禁止切分支 / push。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权（C 轨串行 · C4 末波）· 2026-09-01

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_obs_comms_ui.md` → exit **0** · **PASS**（W4 合法：无思考轮节 · SPEC 06 §15 承载）；`npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → exit **0** · **PASS** |
| **变更路径** | `docs/spec/agent-infra/host_comms_obs_contract_v0.md`（新立 · 契约 `obs-comms-v0`）；`docs/harness/invokes/by-task/_prompts/PROMPT_web_00_c4_obs_comms_ui.md`（新立）；`docs/tasks/active/task_host_obs_comms_ui.md`（`### 自检结论` + 修订记录 10 行）；本 invoke |
| **事实核对** | 00 定夺 7 项**全部命中 · 零修正**（api 无码 ✓ · 契约落点 ✓ · status 对齐 web+决策点不选定 ✓ · 显式+人确认 ✓ · harness.status 注记 ✓ · web Prompt 落点 ✓ · 不新增一级模块 ✓）；web `obs.ts` + 四份 fixture 只读核对：ObsStatus 14 字段 + ObsTimeline 9 字段（含嵌套）**逐字段一致**，唯一偏离 `ingest` 收窄 `object\|null`（web `unknown` 超集兼容 · 零改动） |
| **未改** | `app/` · `tests/` · CI · 图谱 · web 仓任何文件 · 人工闸状态（HG-TASK-DRAFT approved / HG-AUDIT-R1 n/a / HG-GRAPH-MODULES n/a 均未动）· 00 定夺实质零改 |
| **内容可交 20** | **是**（task 结构齐全；契约五要素齐：字段表+偏离清单 · 示例 ready/blocked · 决策点 A/B 不选定 · 发起沟通语义 · 依赖注记；web Prompt 红线齐） |
| **需 00 定夺** | **none**（无退回意见；数据源 A/B 按 00 定夺本波不选定 · 留真源 task） |
| **下一棒** | **20-task-audit**（审 task + 契约落 R1 审查文；本波无 30 · HG-AUDIT-R1 n/a） |
