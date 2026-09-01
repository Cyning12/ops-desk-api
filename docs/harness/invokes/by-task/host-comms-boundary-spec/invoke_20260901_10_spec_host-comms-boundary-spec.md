# Invoke：10-spec · host-comms-boundary-spec

---

## 元信息表

| 字段 | 值 |
|---|---|
| hat_id | 10-spec |
| task_slug / spec_slug | `host-comms-boundary-spec` |
| task_paths | `docs/tasks/active/task_host_comms_boundary_spec.md`（00 已起草 · 定夺钉死） |
| related_review_or_none | 无（本帽结束后交 20-spec-audit） |
| git_branch | `task/host-comms-boundary-spec` |
| created_utc_or_local | 2026-09-01 |
| notes | docs-only SPEC 波 · 无 30；H1–H5 已 CLOSE 不重开；草稿「暂缓 C0」前提已达成（T6 #108 · web T5 #109） |

---

## 裁决

- **从 10-spec 起**：C 轨沟通嵌套 kit 需 SPEC 锁边界（意图路由 / 产物路径 / 闸纪律 / 白名单）后才可拆 C1。
- 真值来源：上游草稿仅 **素材**；语义冲突处 **以 SPEC 为准**。
- 本窗 **禁 30**；不改 `app/` / `tests/`；不改 05 freeze `lg-rag-sse-v1`（05 不回写）；不签发 HG-SPEC-SIGNOFF（人签/00 代签，非本帽）。

## 结论摘要

必入 SPEC：默认 **product** 路由 · 显式意图进 comms · 误判回退 product；comms 写盘仅 `docs/tasks/` + invoke 草稿；禁代签 human_gate（闸真值在 task 表 · 与 00 过程代签区分）；Capability 白名单仅 `harness.*`（verify/task_lint/status · Policy 默认关 · env 钉 `DSH_CODING_KIT_VERSION`）；Skills≠verify；comms/product 分 session；C1→C2→C3 顺序钉死 · C4 可与 C3 尾并行仅 web；待拍板建议钉（写盘=api 仓 docs/tasks · `/obs` 主入口）。  
永久禁令：通用 shell Capability · 模型代签 human_gate。

## 交付

- `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`（draft · 章节齐全 · R0–R5 已回填）
- task 修订记录追加 10-spec 行 + `### 自检结论` 节
- 下一棒：**20-spec-audit**（落盘审查文 → 00 代签 HG-SPEC-SIGNOFF → 00 起草 C1 task）

## 可复制 Prompt 快照（下一棒）

hat_id：20-spec-audit  
task_slug：host-comms-boundary-spec  
本帽禁区：不改 SPEC 实质内容；不代签 human_gate；结论落盘 `docs/harness/reviews/`

必读：`docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md` · `docs/tasks/active/task_host_comms_boundary_spec.md`（00 定夺逐项核对）· 草稿 `docs/discussions/2026-08-31_host_comms_agent_kit_nesting_plan_draft.md`

只做什么：
1. 书面审 SPEC：范围/非范围/验收/failure_paths + R0–R5 思考轮控制完备性
2. 逐项核对 00 定夺落入情况（意图路由 · 产物路径 · 禁代签 · 白名单 · Skills≠verify · 分 session · C1→C2→C3 · 待拍板建议钉）
3. 核对 freeze 声明（05 不回写 · `lg-rag-sse-v1` 字段零改）
4. 审查文落盘 `docs/harness/reviews/`，结论 pass / 阻塞项

禁止代签 HG-SPEC-SIGNOFF。

## 签收栏

（待 20-spec-audit 落盘后 00 代签 · 维护者 Prompt 授权）

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_boundary_spec.md` → exit **0** · **PASS**（W4：无思考轮节 · SPEC §15 承载合法）；`npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → exit **0** · **PASS**（scope=all · scanned=99 · issues=0） |
| **变更路径** | `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`；`docs/tasks/active/task_host_comms_boundary_spec.md`（修订记录 + 自检结论）；本 invoke |
| **未改** | `app/` · `tests/` · 图谱 · 05/02/00 SPEC 正文 · 人工闸状态（HG-SPEC-SIGNOFF 仍 pending） |
| **内容可交 20** | 是 |
| **需 00 定夺** | none（00 定夺各项均已钉死并落入 SPEC；若 20 有实质异议 → 退回 10-spec 修订） |
| **下一棒** | 20-spec-audit |

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | 10-spec 首稿：SPEC 06 落盘（draft）· R0–R5 回填 · task 修订记录 + 自检结论 · lint 双 PASS 回填 |
