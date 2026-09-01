# Invoke：30（含 40）· host-harness-cli-capability（C1）

| 字段 | 值 |
|---|---|
| hat_id | 30（含 40） |
| task_slug | `host-harness-cli-capability` |
| task_paths | `docs/tasks/active/task_host_harness_cli_capability.md` |
| related_review_or_none | `docs/harness/reviews/task_host_harness_cli_capability_audit_R1_20260901.md` |
| git_branch | `task/host-harness-cli-capability` |
| created_utc_or_local | 2026-09-01 |
| notes | 00 代签 HG-AUDIT-R1 后派发；**仅 C1 两条白名单 Capability**（verify / task_lint · status 可选）；禁止通用 shell · 改 adapters/cli.py mock-only 语义 · 接进产品 lg-rag/Chat 主路径 · Policy 默认开 · 真 npx 进 CI · 切分支/push/开 PR |

---

## 人工闸扫描（GATE_VERIFY · 30 重填 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 pass | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 不新增一级模块 · 00 代签 · 仅 capability 行/flow 备注 | Y | N | Y |

reviews：`task_host_harness_cli_capability_audit_R1_20260901.md` 存在且内容 pass？ **是**（内容零阻塞 · 非阻塞 5 条 30 知情并逐项处置）

pre-30 invoke：00 + 10 已落盘？ **是**

机械：`npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_host_harness_cli_capability.md` → **VERIFY: PASS**（exit 0 · 开工前与收尾各跑一次均 PASS）

结论：**可进入读码/改码**（30 首输出已重扫本表）

---

## 可复制 Prompt 快照

hat_id：30（含 40 自检）  
task_slug：host-harness-cli-capability  
本帽禁区：通用 shell / 任意命令 npx 封装（永久禁令 A）；改 `adapters/cli.py` mock-only 语义；接进产品 lg-rag/Chat 主路径；Policy 默认开；真跑 npx 进 CI/本地默认路径；切分支/push/开 PR。

首动作：GATE_VERIFY（FRAGMENT_30_gate_verify）→ 通过再改码。

00 定夺摘要：
- `harness.verify` + `harness.task_lint` 必做（`harness.status` 可选，不做须自检显式注明）
- 命令向量硬编码 `npx --yes dsh-coding-kit@<env pin>` 三形态 · `asyncio.create_subprocess_exec` 禁 shell · 参数白名单（task_path 限 `docs/tasks/` 内 · 拒 ../、绝对路径、shell 元字符）
- env `DSH_CODING_KIT_VERSION` 缺失 → `capability_unavailable`；Policy 默认关 → `policy_blocked`；注册走 `gateway.register` 代码路径（非 manifest）；`CapabilityResult.output`（非 data）
- 超时 ≤180s + stdout/stderr 截断（30 定数值并写断言）；adapter `kind="cli"` 字面钉死（双键 allow_high_risk+allow_cli）

验证：verify · ruff 触及路径 · pytest（CI 等价口径 · capability 旧测零破坏）· graph-compile · lint-wiki-delta。

完成后：回填本 invoke 交付摘要 + task「自检结论（执行者）」；**不 CLOSE（留给 00）**；commit 不 push。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-09-01 · VERIFY PASS

---

## 交付摘要

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS · 可开工（三闸 approved · verify exit 0 · 开工前与收尾各复跑一次均 PASS） |
| 实现 | 新模块 `app/ops/capability/harness_cli.py`：`HarnessCliAdapter`（kind="cli" 字面钉死 · `asyncio.create_subprocess_exec` 逐 argv 禁 shell）· 命令向量三形态硬编码（verify --json / task lint --file / task lint-wiki-delta --target .）· `_validate_task_path` 白名单（`docs/tasks/` 内 · 拒绝对路径/../逃逸/反斜杠/shell 元字符/空格）· `_kit_pin` env 钉版（缺失/非法 → capability_unavailable）· 超时 120s（≤180s 上限内）→ `cli_failed: timeout` · stdout/stderr 各截断 64KiB · 错误前缀族 `invalid_args:`/`cli_failed:`/`capability_unavailable:`（R1 非阻塞 ⑤）；`register_harness_cli_capabilities()` 幂等注册走代码路径 `gateway.register`（**不**挂 ensure/probes 默认目录，保业务默认目录仅 local_fn · 旧测零破坏） |
| 测试 | 新 `tests/test_capability_harness_cli.py` **32 用例**全 mock subprocess（零真 npx/装 npm/断网）：verify JSON 透传+argv 逐元素断言 · task_lint/lint-wiki-delta 两子操作 · policy_blocked 默认关+adapter 零调用计数 · 双键（单开各 blocked）· ctx 与 env 双开启通道 · env 缺失/非法 pin 不可用 · 13 参数化逃逸拒绝（不执行）· 超时（adapter 直测+gateway 路径 · proc.kill）· 非零退出+截断 stderr · invalid_json · 截断断言 · 常量断言（120s/64KiB）· 禁 shell grep 断言 · 同步 invoke 入口 |
| 自检 | verify exit 0 · ruff 触及路径 exit 0（全量 `ruff check app tests` 亦 0）· pytest **CI 等价 exit 0**（496 passed · 39 skipped · capability 旧测 57 passed 7 skipped 零破坏）· graph-compile exit 0（9 graphs）· task lint PASS（W4 合法豁免）· lint-wiki-delta PASS（exit 0） |
| 图谱 | `01_modules.md` capability 行备注 harness.* 白名单三条 + 人签记录行；`10_flow_capability.graph.yaml` description 备注 + version→2026-09-01（生成物随 graph-compile 刷新）；未增 implementedBy → G-L2 indexes 无需同步；不新增一级模块 |
| R1 非阻塞 5 条 | 全部处置（① 字段名为准 ② 120s/64KiB 落断言 ③ kind="cli" 断言 ④ status 不做显式注明 ⑤ `invalid_args:` 前缀族）——明细见 task 自检结论（执行者） |
| 已知未测项 | 真 npx 执行（task 钉死仅 mock · CI 不装 npm 不断网）；`harness.status`（**不做** · C4 开工时补）；业务侧接线（C4 obs 显式调 `register_harness_cli_capabilities()` · 本波不进产品主路径） |
| 禁区核对 | 无通用 shell 通道 · `adapters/cli.py` 零 diff（mock-only 语义未动）· 产品 lg-rag/Chat 零 diff · Policy 默认未改开 · 未切分支/未 push/未开 PR |
| 收尾 | task 验收 13 条勾选 + 自检结论（执行者）表 + 修订记录 30+40 行 + 文末「不 CLOSE（留给 00）」；分笔 commit · 未 push |

关键路径：
- `app/ops/capability/harness_cli.py`（新增）· `tests/test_capability_harness_cli.py`（新增）
- `docs/_tech_graph/l1/01_modules.md` · `10_flow_capability.graph.yaml`（+生成物 `10_flow_capability.md` · `shared/graph.json`）
- `docs/tasks/active/task_host_harness_cli_capability.md`（验收勾选 · 自检结论（执行者）· 修订记录）
