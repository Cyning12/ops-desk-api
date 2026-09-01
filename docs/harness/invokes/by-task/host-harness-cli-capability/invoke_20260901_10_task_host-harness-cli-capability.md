# Invoke：10-task · host-harness-cli-capability（C1）

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `host-harness-cli-capability` |
| task_paths | `docs/tasks/active/task_host_harness_cli_capability.md` |
| related_review_or_none | 无（本帽结束后交 20-task-audit） |
| git_branch | `task/host-harness-cli-capability` |
| created_utc_or_local | 2026-09-01 |
| notes | 00 已起草 C1 初稿（00 定夺钉死 · invoke_20260901_00 已落盘）；10 补全/审校 + 现网事实核对，**不实现代码** |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：host-harness-cli-capability  
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1、不改 `app/` / `tests/`、不改人工闸表状态

必读：`docs/harness/prompts/10-task-requirements.md` · 已落盘 task 初稿（00 定夺钉死）· SPEC `06_host_comms_boundary_spec_v0.md`（signed · §3/§7/§8/§10/§15）· C0 关账链（#111/#112）

只做什么：
1. `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_harness_cli_capability.md`；FAIL 则补结构（验收 / failure_paths / wiki_delta 已有则勿删）
2. 核对 00 定夺与非范围：slug=`host-harness-cli-capability`；全集=`harness.verify`+`harness.task_lint` 必做 / `harness.status` 可选；命令向量硬编码 `npx --yes dsh-coding-kit@<pin>` · 禁 shell=True · 参数白名单（拒 `../`/绝对路径/shell 元字符）；env 钉 `DSH_CODING_KIT_VERSION` 缺失即 `capability_unavailable`；Policy `risk_level=high` 默认关 → `policy_blocked`；**永久禁**通用 shell；不复用 mock-only `adapters/cli.py`；不新增一级模块
3. 现网事实核对（只读）：`registry.py` · `policy.py`（`PolicyDecision` / `_host_policy` / env 键）· `types.py`（`CapabilitySpec` / `CapabilityResult` 字段名）· `gateway.py`（policy 门先于 adapter）· `defaults.py` · `manifest.py`（kind 白名单）· `manifests/builtin.v1.yaml` · `adapters/cli.py`（mock-only）；与现网不符才修正并记录
4. 补遗漏验收钩（不改 00 定夺实质）：注册可见性 · Policy 门先于 adapter · cli+high 双键
5. 思考轮：本 task 由 SPEC 06 §15「思考轮控制」承载，**不必**强行加 R0–R5（无节仅 W4 · 合法）
6. 补 `### 自检结论`；修订记录追加 10-task 行；回填本 invoke 交付摘要；下一棒 20-task-audit

禁止扩 scope。禁止改 `app/` / `tests/`。禁止改人工闸表状态（HG-AUDIT-R1 保持 pending）。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权（串行波次 4）· 2026-09-01

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_harness_cli_capability.md` → exit **0** · **PASS**（W4：无思考轮节 · SPEC 06 §15 承载合法）；`npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → exit **0** · **PASS** |
| **变更路径** | `docs/tasks/active/task_host_harness_cli_capability.md`（事实修正 2 处 + 验收钩 +2 + `### 自检结论` + 修订记录 10-task 行）；本 invoke |
| **事实核对** | **2 处不符已修正 · 其余一致**：① `CapabilityResult` 字段为 `output`（types.py L38）**无 `data`** → 00 定夺「返回」与验收钩已改；② `manifest.py` 仅支持 `kind=local_fn` + adapter 前缀白名单 defaults/lookups → cli adapter 不能经 builtin.v1.yaml 注册，00 定夺「落点」已改为代码路径 `gateway.register`。一致项：`PolicyDecision(allowed, reason)` ✓ · `_host_policy` 读 `ctx["_host_policy"]` + env `OPS_CAPABILITY_ALLOW_*` ✓ · check_invoke 先 high_risk 后 cli（双键事实已补验收钩）✓ · registry 拒重复 id ✓ · builtin.v1.yaml 5 枚 local_fn 格式 ✓ · `adapters/cli.py` mock-only ✓ |
| **未改** | `app/` · `tests/` · CI · 图谱 · 00 定夺范围实质（slug / 全集 / 命令向量 / 参数白名单 / env 钉版 / Policy 默认关 / 禁通用 shell **全部保留**）· `HG-AUDIT-R1`（仍 pending） |
| **内容可交 20** | **是**（结构齐全；00 定夺钉死项保留；现网事实已对齐；无内容阻塞） |
| **需 00 定夺** | **none**（无退回意见；00 定夺全部钉死项与现网机制兼容，字段名/注册路径修正属事实对齐非范围变更） |
| **下一棒** | **20-task-audit**（落盘 R1 review 后由 00 代签 `HG-AUDIT-R1`） |
