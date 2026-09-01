# Invoke：10-task · host-comms-task-writer（C3）

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `host-comms-task-writer` |
| task_paths | `docs/tasks/active/task_host_comms_task_writer.md` |
| related_review_or_none | 无（本帽结束后交 20-task-audit） |
| git_branch | `task/host-comms-task-writer` |
| created_utc_or_local | 2026-09-01 |
| notes | 00 已起草 C3 初稿（00 定夺钉死 · invoke_20260901_00 已落盘）；10 补全/审校 + 现网事实核对，**不实现代码** |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：host-comms-task-writer  
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1、不改 `app/` / `tests/`、不改人工闸表状态

必读：`docs/harness/prompts/10-task-requirements.md` · 已落盘 task 初稿（00 定夺钉死）· SPEC `06_host_comms_boundary_spec_v0.md`（signed · §5/§6/§7/§10/§15）· C1 关账链（#114/#115）· C2 关账链（#116/#117）

只做什么：
1. `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_task_writer.md`；FAIL 则补结构（验收 / failure_paths / wiki_delta 已有则勿删）
2. 核对 00 定夺与非范围：slug=`host-comms-task-writer`；落点 `app/ops/capability/task_writer.py` 纯服务（**不是** Gateway Capability · 不进 registry/manifest · 不触发 SPEC §7 白名单变更）；API=`plan_task_write(slug, content, *, kind, repo_root) -> WritePlan` + `apply_task_write(plan, *, confirmed=False)`（dry-run 默认不落盘 · confirmed=True 人确认后落盘）；**无 HTTP 路由**；allowlist 仅三目录（`docs/tasks/active/` · `docs/tasks/draft/` 不存在可创建 · `docs/harness/invokes/by-task/<slug>/`）；文件名 `task_<kebab-slug>.md` / `invoke_*.md` · kind/目录错配拒；禁代签机械挡（content 人工闸节 HG-* 写 approved → `invalid_content` 拒）；结构自检（不真跑 npx）；overwrite 默认拒；不新增一级模块（须增 → 退回 00）
3. 现网事实核对（只读）：`app/ops/capability/` 布局（harness_cli.py 风格）· `docs/_tech_graph/l1/01_modules.md` capability 行 glob `app/ops/capability/**` · `docs/tasks/` 目录（active/done · 无 draft/）· `docs/harness/invokes/by-task/` 结构；与现网不符才修正并记录
4. 补遗漏验收钩（不改 00 定夺实质）：原子写不留半截文件 · allowlist 目录可创建
5. 思考轮：本 task 由 SPEC 06 §15「思考轮控制」承载，**不必**强行加 R0–R5（无节仅 W4 · 合法）
6. 补 `### 自检结论`；修订记录追加 10-task 行；回填本 invoke 交付摘要；下一棒 20-task-audit

禁止扩 scope。禁止改 `app/` / `tests/`。禁止改人工闸表状态（HG-AUDIT-R1 保持 pending）。禁止切分支 / push。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权（C 轨串行 · C3 波）· 2026-09-01

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_task_writer.md` → exit **0** · **PASS**（W4：无思考轮节 · SPEC 06 §15 承载合法）；`npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → exit **0** · **PASS** |
| **变更路径** | `docs/tasks/active/task_host_comms_task_writer.md`（验收钩 +2 · `### 自检结论` · 修订记录 10-task 行）；本 invoke |
| **事实核对** | **现网与 task 陈述全部一致 · 零事实修正**：`app/ops/capability/` 包在（harness_cli.py 风格参照 ✓ · C1 走 gateway.register 而 C3 定夺为纯服务不进 registry——差异已由 00 定夺明示）· `01_modules.md` capability 行 glob=`app/ops/capability/**`（L26）✓ 落既有 glob 不新增一级模块 · `docs/tasks/` 无 `draft/`（仅 _views/active/deferred/done）✓ 与「不存在可创建」一致 · `docs/harness/invokes/by-task/host-comms-task-writer/` 在且 invoke_20260901_00 已落盘 ✓ · 前置 C1/C2 done 文件均在 ✓ · 必读列表引用（SPEC 06 §5/§6/§7/§10/§15 · prompts/packs.py · CODING_BACKEND_L2）全部存在 ✓ |
| **未改** | `app/` · `tests/` · CI · 图谱正文 · 00 定夺范围实质（slug / 落点纯服务非 Gateway Capability · 不进 registry·manifest / plan+apply API · dry-run 默认 confirmed=False / allowlist 三目录 / 文件名·slug 校验 / 禁代签机械挡 / 结构自检不真跑 npx / overwrite 默认拒 / 无 HTTP 路由 / 不新增一级模块 **全部保留**）· `HG-AUDIT-R1`（仍 pending） |
| **内容可交 20** | **是**（结构齐全；00 定夺钉死项保留；现网事实已对齐；无内容阻塞） |
| **需 00 定夺** | **none**（无退回意见；验收钩补充属已钉行为的可检验化，非范围变更；未触发「新增一级模块退回 00」条件） |
| **下一棒** | **20-task-audit**（落盘 R1 review 后由 00 代签 `HG-AUDIT-R1`） |
