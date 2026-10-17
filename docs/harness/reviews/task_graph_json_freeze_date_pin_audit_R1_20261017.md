# Task Audit R1：graph-json-freeze-date-pin · 签收（零内容阻塞）

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_graph_json_freeze_date_pin.md`（slug: graph_json_freeze_date_pin · 174 行 draft · TC×6 · FP×6）  
> **日期**：2026-10-17 · 审查人：20-task-audit（00 委派 · 子 Agent 书面审）  
> **分支**：本帽零 git 操作 · 未切分支 · 未 commit · 未改 task 正文/人工闸表/任何既有仓内文件（仅新增本审查文 + 20 invoke）  
> **task lint**：本帽亲跑 `npx --yes spec-wave task lint --file docs/tasks/active/task_graph_json_freeze_date_pin.md` → **LINT: PASS · EXIT=0**（仅 W3 自检结论占位 · draft 期合法 · close 前回填）  
> **verify**：本帽亲跑 `npx --yes spec-wave verify --target . --task docs/tasks/active/task_graph_json_freeze_date_pin.md` → **VERIFY: BLOCKED · EXIT=2**（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 pending —— draft 期待签态的正确阻断，非内容缺陷；维护者签闸后复跑应转 PASS）  
> **required_invoke_hats**：`10,20,30,40`（含 20）· 本轮已落 20 invoke：`docs/harness/invokes/by-task/graph_json_freeze_date_pin/invoke_20261017_20_task_audit_r1.md`

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **签收** · 零内容阻塞 · 非阻塞观察 N-1~N-4 照登 |
| **流程闸** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 **pending**（task 人工闸表亲读 · 未代签 · verify EXIT=2 BLOCKED 实证）；HG-GRAPH-MODULES **全局真值 approved** 经本帽核实（`docs/_tech_graph/l1/01_modules.md:63` 起 40+ 行 approved 记录）——task 表 pending 系本 task 维度闸位，与全局真值不冲突，30 开工前按表核验即可 |
| **30 授权** | 本帽不签发（task 表 approved 才是真值）；内容零阻塞，闸签后可进入 30 |

**总评**：仓卫生 chore task，把 graph.json 仅存非确定性面（freeze_id 日期段 + generated_at，`graph_yaml_to_json.py` `datetime.now(UTC)`）收口为确定性来源。出处链完整（CLOSE §四·2 照录 + §七·1 另立案建议，本 task 即该另立案）；实证锚点 6/6 亲读命中；TC-1~6 全可机断；FP-1~6 互锁（校验语义 / 消费方兼容 / 不稳定源 / 闸 / CI-本地分裂 / diff 白名单）；思考轮 R0–R5 实填闭合，R5 early_stop 理由成立。可执行。

## 审查核对（对照面逐项）

| # | 审查点 | 结论 |
|---|--------|------|
| 1 | 漂移源锚点 `scripts/graph_yaml_to_json.py:65-69` | **通过**。亲读：`:65-68` freeze_id 拼 `datetime.datetime.now(datetime.UTC).strftime('%Y%m%d')`（`:67`），`:69-71` generated_at 同取 `datetime.now(UTC)`——`:65-69` 区间覆盖两处 wall-clock 起点 ✓；`json.dump(ensure_ascii=False, indent=2)`（`:81`）序列化参数在案（FP-3 不稳定源排查相关）✓ |
| 2 | 调用链锚点 | **通过**。亲读 `scripts/graph-compile.sh:58-59` 恰为「echo + python3 graph_yaml_to_json.py」两行 ✓；`:61-66` check 带 `--graph-json`（FP-1 引用的校验面真实存在）✓；`.github/workflows/tech-graph.yml:33` = `run: ./scripts/graph-compile.sh`，trigger = PR + master push（`:3-7`）✓ |
| 3 | 消费方兼容面 | **通过**。亲读 `build_site.py:558-559` = `graph.get("freeze_id")` / `graph.get("generated_at")` 纯透传进 site-data.json，无格式解析 ✓；`web/app.js:55` = `${DATA.freeze_id || "?"} · gen ${DATA.generated_at || ""}` 纯字符串展示 ✓；`dist/app.js:55` 同构拷贝亲读一致 ✓ |
| 4 | 内容戳先例 | **通过（表述过宽见 N-2）**。亲读 `99_mermaid_protocol.md:137` 记载「generated_at 改为 yaml 源内容戳（kit ≥1.9.2 幂等；本仓钉 1.10.0）」✓；`sha256-<16hex>` 字面实证：`l0/00_main.md:4` = `sha256-f41174be4a57581b` · `l1/10_flow_lg_rag.md:4` = `sha256-3b81f56b18d5d6dd`（均 16 hex）✓ |
| 5 | 出处钉案对照 | **通过（照录 fidelity 见 N-1）**。CLOSE §四·2 原文（close `:52`）与 task §风险照录语义 1:1（freeze_id 20261014→20261017 + generated_at 两字段 · graph_yaml_to_json.py:65-69 datetime.now(UTC) · 与 spec-wave 版本无关 · git checkout 恢复零混入）✓；§七·1（close `:81`）「freeze_id 脱日期化另立 task 收口由维护者裁定」→ 本 task 即另立案 ✓；现仓 graph.json:3 = `OPS_DESK_API_TECH_GRAPH_FREEZE_20261014_V1` 与骨架断言一致 ✓ |
| 6 | TC 可执行可断言性 | **通过**。TC-1 双跑 cmp + `TZ=America/New_York` 扰动字节断言（可机断）✓；TC-2 骨架 grep + compile 内 check 全 OK ✓；TC-3 build_site.py EXIT=0 + site-data.json 非空串 + 消费方 grep 无解析 ✓；TC-4 CI 绿 + CI/本地字节一致（取证路径见 N-3 · 可断言性成立）✓；TC-5 `grep datetime.now` 生成路径清零 + 可复跑防回归断言 ✓；TC-6 diff 白名单 + 钉版字面零 diff ✓ |
| 7 | FP 覆盖 | **通过**。FP-1 freeze 校验语义「30 先实证 check 矩阵再定案 · 无法两全 STOP 回 10」实证顺序硬 ✓；FP-2 旧消费方兼容（非空 str 透传约束）✓；FP-3 双跑漂移定位（sort_keys/相对路径化 · 禁 wall-clock 回退）✓；FP-4 闸 pending 拒开工 ✓；FP-5 env 注入 CI/本地分裂（默认值确定性）✓；FP-6 diff 白名单拒收 ✓ |
| 8 | 三候选方案框定 | **通过**。内容 hash / env 注入 / git commit 时间三候选均列硬约束（默认值确定性 + freeze_id 骨架兼容），偏离须先回 10；自由度适中不过宽——30 定案 + invoke 载明取舍理由即闭合可追溯 |
| 9 | 钉版 3.3.0 非范围钉死 | **通过**。非范围首条 ❌ 钉版/版本变更（勿动 GRAPH_CLI 与任何 `.github/workflows/` 钉版字面）+ TC-6「钉版字面 spec-wave@3.3.0 零 diff」+ 依赖节 `lint-wiki-delta.yml` 标「钉版已 3.3.0，勿动」——三重钉死 ✓ |
| 10 | CI 浅克隆留痕 | **通过**。亲读 `tech-graph.yml:15` `actions/checkout@v5` 无 fetch-depth → 默认浅克隆；task R2/R3 已留痕「git commit 时间方案 CI 浅克隆风险须 30 实证」「须防浅克隆无历史」——留痕在 R 轮控制表与正文，候选 3 的选择风险有对冲 ✓ |
| 11 | 思考轮控制表 | **通过**。R0–R5 实填闭合；early_stop=true at R5，理由「改动面单一（一脚本两字段）· 证据锚点齐备 · 方案自由度已框定在三候选内，再轮无新信息」成立；residual_risks 在 R0/R1/R2/R3 登记；actual_last_round=R5；正文六节与控制表闭合 |
| 12 | 人工闸未代签 | **通过**。task 人工闸表三闸全 pending 亲读；10 invoke 与 task 正文均无代签字面；本帽亦未代签 |
| 13 | K7 旧测 grep 影响面（行为变更边界类） | **通过（见 N-4）**。本帽全仓 grep `TECH_GRAPH_FREEZE`/`freeze_id`：**无任何代码/测试对骨架格式有断言**；消费面仅 build_site.py 透传 + `:602` print + app.js 展示。另抽验 spec-wave@3.3.0 包 `lib/cli-graph-yaml.js` 全文 `freeze` 仅 3 处（`:7` 常量 `FREEZE_ID='TECH_GRAPH_S2_FREEZE_20260519_V2_3'` · `:453` `opts.freezeId ?? FREEZE_ID` · `:511` 写入 `freeze_id`）——**check 路径零 freeze 字面**，FP-1 隐性格式断言风险经本帽抽验为低；task 仍将实证义务钉给 30（先实证后定案），框架成立不松懈 |

## 非阻塞观察（照登不闸）

- **N-1（照录 fidelity）**：task §风险照录标「§四·2 原文照录」，但句尾插入 CLOSE 原文没有的子句「（ci-pin 棒 6be8f3c2 实证）」——CLOSE `:52` 原文止于「已 git checkout -- 恢复，零混入本 PR。**freeze_id 是否脱日期化另立 task，超本 task 范围，仅照登。**」；CLOSE 记合并为 squash `de3c7d7`，6be8f3c2 系 ci-pin 分支 pre-squash commit（本帽零 git 操作未核）。语义无损，但「原文照录」名下混入新增实证子句，建议 10/30 将该子句改标「（20 注：ci-pin 棒 6be8f3c2）」或移出照录段。不阻塞。
- **N-2（先例表述过宽）**：task §实证面称「l0/l1 各 md :4 均为 sha256-<16hex> 实证」；实测编译产出 md 成立（l0/00_main.md:4 · l1/10_flow_lg_rag.md:4），但 `l1/01_modules.md` 为人工维护文档（G-L1 D4-a 人签真值）无 frontmatter、无 generated_at 行。建议措辞收紧为「编译产出 md :4」；先例锚点本身成立，不阻塞。
- **N-3（TC-4 取证路径提示）**：tech-graph workflow 不上传 graph.json artifact，且 S5/TC-6 diff 白名单不含 workflow / graph-compile.sh 改动——「CI 产出与本地字节一致」无法直接取 CI 字节比对。可行取证：(a) 30 在 `graph_yaml_to_json.py` stdout 增打产出 sha256（脚本在白名单内），40 从 CI run 日志与本地输出比对哈希；或 (b) 40 以干净 clone / 异绝对路径环境复跑模拟 CI 环境差异（兼覆盖 FP-3 绝对路径风险）。建议 30 invoke 载明所选取证法。TC 可断言性不依赖特定手段，不阻塞。
- **N-4（K7 边界 · 已实证覆盖）**：产出值格式变化属行为变更边界类，验收标准无字面「旧测 grep 影响面」项；本帽 grep 实证仓内零旧测/零代码对 freeze_id 骨架断言（核对表 #13），影响面 = arch-browser 展示面 + dist/site-data.json 存量快照（10 invoke 已诚实照登对比口径留 30 裁定），已由 TC-3 + FP-2 功能覆盖，不单独退回。

## 签收

内容零阻塞 · 本帽 R1 **签收**。verify EXIT=2 BLOCKED 系三闸 pending 的正确流程阻断（非内容缺陷），维护者签闸后复跑应转 PASS。

## 维护者签闸（20 后 · 30 前）

```text
- [ ] 已读 R1 审查结论（docs/harness/reviews/task_graph_json_freeze_date_pin_audit_R1_20261017.md）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
```

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 20 R1 书面审：实证锚点 6/6 亲读命中（:65-69 漂移源 · compile.sh:58-59 · tech-graph.yml:33 · build_site.py:558-559/app.js:55+dist 同构 · md 内容戳先例 l0/l1 :4 字面实证）· CLOSE §四·2/§七·1 对照 1:1 · TC-1~6 可机断 · FP-1~6 互锁 · 三候选框定合理 · 钉版 3.3.0 三重钉死 · 浅克隆 R 轮留痕 · 思考轮 R0–R5 闭合 · 三闸 pending 未代签 · task lint EXIT=0 PASS · verify EXIT=2 BLOCKED（pending 正确阻断）· K7 grep 实证零旧测断言 + spec-wave check 路径零 freeze 字面 · 内容零阻塞 **签收** · N-1~N-4 照登不闸 |
