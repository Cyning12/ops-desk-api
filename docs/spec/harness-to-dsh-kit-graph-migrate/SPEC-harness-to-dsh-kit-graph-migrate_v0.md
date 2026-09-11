# SPEC · cyning-harness → dsh-coding-kit · Graph 编译迁移（预留 · v0）

| 字段 | 值 |
|------|----|
| SPEC ID | SPEC-harness-to-dsh-kit-graph-migrate_v0 |
| 状态 | **executed（2026-08-25 §6 已执行：命令面切至 dsh-coding-kit 1.6.1）** |
| 日期 | 2026-08-24 |
| 关联缺陷 | kit 侧 **DEF-023 / PROP-12（P0-HOT）** · 本仓过渡：`scripts/graph_mermaid_normalize.py` |
| 上游调查 | `Projects/docs/dsh_coding_kit_optimization/`（DEF-023 调查 / PRD / Prompt） |
| 本仓 Open Folder | `ops-desk-api/` |

---

## 0. 目的

在 **dsh-coding-kit** 修好 `generateMermaid` 之前，本仓用 post-compile 归一化保证 IDE 可预览。  
本 SPEC 预留 **正式迁移** 路径：从 `npx @cyning/harness` 切到 `npx dsh-coding-kit`，并规定 **脚本备份 → 验证完成度 → 必要时反哺 kit**。

**非目标（v0）**：不在本 SPEC 内改 kit 源码；不一次性切换消费者全仓；不改 Inform 拓扑语义。

---

## 1. 现状（2026-08-24）

| 组件 | 现状 |
|------|------|
| 编译入口 | `./scripts/graph-compile.sh` → `npx @cyning/harness graph yaml compile/check` |
| 过渡层 | compile 后 `python3 scripts/graph_mermaid_normalize.py`（`//`→`%%`、`--"…"-->`→`-->|"…"|`、标签引号、`class` 按 kind） |
| 脚本备份 | `scripts/legacy/graph-compile.sh.20260824.pre-mermaid-normalize.bak` · `graph_yaml_to_json.py.20260824.bak` |
| CI | `.github/workflows/tech-graph.yml` → `graph-compile.sh`（含 normalize --check） |
| kit 治根 | DEF-023 未合入前，**禁止**假设 npm 上的 kit emit 已正确 |

---

## 2. 迁移前置条件（全部满足才开切）

- [ ] dsh-coding-kit 已发布含 DEF-023 的版本（changelog 明示 Mermaid emit 变更）
- [ ] 本仓 `scripts/legacy/` 已存在 **迁移日** 新备份（见 §3）
- [ ] 用新 kit 对本仓 4 张 `*.graph.yaml` 做 **无 normalize** 试编译，通过 §4 完成度矩阵
- [ ] 维护者在 `decision_log` / 本仓 task 人工闸签收「切命令面」

---

## 3. 迁移日脚本备份纪律（强制）

在改 `graph-compile.sh` 指向 `dsh-coding-kit` **之前**：

```bash
STAMP=$(date +%Y%m%d)
mkdir -p scripts/legacy
cp scripts/graph-compile.sh \
  "scripts/legacy/graph-compile.sh.${STAMP}.pre-dsh-kit-migrate.bak"
cp scripts/graph_mermaid_normalize.py \
  "scripts/legacy/graph_mermaid_normalize.py.${STAMP}.pre-dsh-kit-migrate.bak"
cp scripts/graph_yaml_to_json.py \
  "scripts/legacy/graph_yaml_to_json.py.${STAMP}.pre-dsh-kit-migrate.bak"
```

- 备份文件 **入库**（便于回滚与反哺对照）。
- 回滚：用对应 `.bak` 覆盖回 `scripts/` 并重跑 `./scripts/graph-compile.sh`。

---

## 4. 修复完成度验证矩阵（kit 合入后）

对 `docs/_tech_graph` 下全部 `*.graph.yaml`（当前：`l0/00_main` · `l1/10_flow_auth` · `10_flow_chat` · `11_flow_sync_to_chat`）：

| # | 检查 | 通过标准 |
|---|------|----------|
| V1 | `npx dsh-coding-kit graph yaml compile --all`（按子目录） | exit 0 |
| V2 | **关闭** normalize 步后，mermaid 围栏内无 `// →`、无 `--"…"-->` | `graph_mermaid_normalize.py --check` 在「仅 harness/kit 产物」上仍绿，或 grep 为 0 |
| V3 | IDE（Cursor）预览：auth / chat / sync / main **均有边、非单行孤岛** | 人工勾选 |
| V4 | `graph yaml check` + `shared/graph.json` | exit 0 · 与 yaml 切片一致 |
| V5 | 与「本仓 normalize 后产物」对照边集合 | yaml edges 条数一致；允许 id 大小写策略差异须记入报告 |

**判定**：

| 结果 | 动作 |
|------|------|
| V1–V5 全过且 IDE ≥ normalize 方案 | **退役**本仓 normalize（或改为 no-op 开关）；changelog 记「emit 已由 kit 承担」 |
| kit 仍差、本仓 normalize 更好 | **保留** normalize；开反哺 PR（§5） |
| 部分失败 | 不切默认命令面；问题单挂回 DEF-023 |

---

## 5. 反哺 kit（本仓方案更好时）

若本仓 `graph_mermaid_normalize.py` 的规则集（或实测预览）优于 kit emit：

1. 将规则整理为 **emit 契约**（禁止 `//`、默认 `-->|"label"|`、特殊字符 `id["label"]`、可选 kind→class）。
2. 对照官方文档后再提 PR（禁止凭记忆）：
   - https://mermaid.js.org/intro/syntax-reference.html
   - https://mermaid.js.org/syntax/flowchart.html
   - 本地：`Projects/mermaid/packages/mermaid/src/docs/syntax/flowchart.md`
   - 远端：https://github.com/mermaid-js/mermaid
3. 目标文件：`dsh-coding-kit/src/cli-graph-yaml.ts`（`generateMermaid` / `formatAnchorComment`）。
4. 参考入口：`Projects/docs/dsh_coding_kit_optimization/prompts/PROMPT_DEF-023_mermaid_emit_P0HOT_v1.md`。
5. 反哺 PR 须附：本仓 fixture（至少 chat 图）+ mermaid-cli 或 IDE 截图说明。

---

## 6. 建议切换步骤（未来执行棒）

1. §3 备份  
2. 临时分支：`graph-compile.sh` 增加 `GRAPH_CLI="${GRAPH_CLI:-dsh-coding-kit}"`（或 env 切换 harness/kit）  
3. 关 normalize 试跑 §4  
4. 通过 → 删/旁路 normalize；更新 `99_mermaid_protocol.md` §0 命令面  
5. 更新 CI / AGENTS 中仍写 `@cyning/harness` 的 graph 命令  
6. 失败 → 恢复 bak，写失败报告，反哺或等下一版 kit  

---

## 7. 与 Inform 补齐包关系

- 本 SPEC **不替代** `docs/spec/inform-graph-backfill/SPEC-inform-graph-backfill_v1.md`。  
- W1/W2 仍改 `.graph.yaml`；compile 路径以本仓 `graph-compile.sh` 为准。  
- Phase β「回灌」原指 harness 上游；现统一指向 **dsh-coding-kit**（`@cyning/harness` deprecate）。

---

## 8. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-24 | v0 预留：normalize 过渡 + 备份纪律 + 完成度矩阵 + 反哺条款 |
| 2026-08-25 | §6 执行（task_dsh_kit_graph_command_switch）：矩阵 V1/V2/V4/V5 PASS；命令面切 dsh-coding-kit 1.6.1（GRAPH_CLI 回退口保留）；normalize 降 check-only 护栏；graph.json 保留本仓脚本（kit export 缺 layer 字段 / freeze_id 语义异 / 无根双写）；备份 scripts/legacy/*.20260825.pre-cmd-switch.bak |
