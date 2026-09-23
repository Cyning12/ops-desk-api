# FEEDBACK · spec-wave 3.0.1（from ops-desk-api）

> **日期**：2026-09-23  
> **from**：ops-desk-api · `task/specwave-3-0-1`（base `origin/master` 6ddd9c7）  
> **kit**：`3.0.1`（from `3.0.0` · patch）

## 摘要

- `upgrade --yes` 正确迁移 manifest（`version=3.0.1` · `from_version=3.0.0`）；`sync prompts` dry-run 零写入（11 skip + 1 conflict 仓内 TASK_TEMPLATE 定制保留）。
- 验证全绿：check「已是最新」零 WARN · verify --task PASS · graph-compile exit 0 · pytest harness_cli 32 passed（mock 钉 3.0.1）。
- 消费者须：package exact + CI `@3.0.1`（3 处）+ 单测 mock 钉版（16 处字面）。

## 无阻塞摩擦

无（patch 升级路径零破坏）。

---

## 长程任务反馈（2026-09-10 上次反馈后 · 四条）

> 来源：本仓 09-10 后长程任务链（memory-facts p0/p1 · llm-layer-hardening · session-summary-fallback · security-input-isolation · tech-graph-recent-sync · test-baseline-reds · agent-host-framework-alignment 等）中反复出现的 spec-wave 触点观察。

### F-1 · graph 词汇登记档告警噪音（高频 · 每次 compile 必现）

- **现象**：`graph yaml check` 对 `branches` / `triggers` 两类 edge type 逐条告警「未在 tech-graph 词汇登记档（tech: namespace）」。本仓 6 个 flow yaml 共用 `branches` **37 处**、`triggers` **16 处**——全部是仓内标准用法（条件分支 / 触发子图），每次 `graph-compile.sh` 产生 ~20 行永不可行动的 warning。
- **影响**：告警疲劳——真正的新 warning 会被淹没在噪音里（「Warning 不咬 exit」反而训练使用者忽略 warning 面）。
- **建议**（二选一）：① 内置词汇登记档收录 `branches` / `triggers`（LangGraph 系图谱的普适类型）；② 支持仓级词汇扩展文件（如 `.spec-wave/graph-vocab.yaml`）登记本地 type，check 时合并判定。

### F-2 · 图谱漂移缺机械闸（中频 · 事后追平成本高）

- **现象**（`task_tech_graph_recent_sync` 实证）：2026-09-20~21 两日 29 个提交脱离 task 过程集中开发，`docs/_tech_graph/` 完全未同步——实测对 `hitl` / `配额` / `output_schema` / `幂等` / `interrupt` 等已落地概念**零命中**，需要一个专门追平 task 才恢复。
- **建议**：提供 `spec-wave graph drift --target .` 类机械检查——从代码侧提取锚点概念（新模块目录 / 新路由前缀 / 新表名 / 新 SSE 事件类型），核对 `_tech_graph` 覆盖率，漂移即 exit 2；可挂 CI 提醒「改了路由/表/模块但没动图谱」。哪怕初版只做「新一级包目录必须出现在 modules 表」一条也够兜底。

### F-3 · 消费侧钉版散落四面，无机械保鲜闸（每次升级手工）

- **现象**：本仓每次升级须手工对齐四个面：① `package.json` devDependencies exact；② CI `.github/workflows/lint-wiki-delta.yml` 三处 `spec-wave@x.y.z` 字面；③ `tests/test_capability_harness_cli.py` 16 处 mock 钉版字面；④ env `DSH_CODING_KIT_VERSION` 文档面。任一面漏改都是静默漂移（测试 mock 旧版但 CI 新版）。
- **现状**：`spec-wave pins check` 存在，但消费仓实测 `exit 2 · PINS: BLOCKED · 声明源缺失: assets/release-pins.yaml（F-A1-01 failClosed）`——该命令面向 spec-wave 发布仓自身，消费仓无此资产即不可用。
- **建议**：提供 consumer 模式 pins check（或独立 `pins check --consumer`）：以 `package.json` devDependencies 钉版为真值，扫描常见字面面（CI workflow `spec-wave@` 字面、可配置的测试文件清单）报漂移；`pins fix` 顺带改写。

### F-4 · pins 真值源假定 package.json 必有 version 字段（隐患 · 与 F-3 联动）

- **现象**：3.0.1 `cli-pins.js readTruthVersion` 读 `package.json` 的 `version` 字段，缺失即 `PINS: BLOCKED · 缺 version 字段`。但消费仓常为 `private: true` 无 `version`（本仓即如此：仅 name/private/description/devDependencies）。
- **影响**：若 F-3 的 consumer 模式落地，按现行真值源逻辑本仓会被误 BLOCK。
- **建议**：consumer 场景真值源回退顺序：`devDependencies["spec-wave"]` → `dependencies["spec-wave"]` → `version`；或允许 `--truth <path#jsonpath>` 显式指定。

## 正向确认（非摩擦）

- 3.0.1 `parseHumanGates` 空闸表显式告警（有节 0 行 → warning 不改 exit）方向正确——本仓 task 模板闸表为 4 列粗体 id，可正常解析。
- 思考轮结构判定 lint/verify 共享 `evalThinkingRoundStructure` 单一实现源（W5–W7 warn 与 G4 闸不双写），本仓 verify PASS 路径受益。

## 本仓后续动作（自建 · 非上游）

- `harness.verify` capability（`app/ops/capability/harness_cli.py`）可考虑透传 3.0.1 新增 `warnings` 数组（空闸表告警）到调用方面——另起 task，不在本波。
- 若上游落地 F-3 consumer pins check，本仓 CI 接入作为钉版保鲜闸。
