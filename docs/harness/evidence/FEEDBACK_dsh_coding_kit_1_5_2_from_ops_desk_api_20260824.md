# FEEDBACK · dsh-coding-kit 1.5.2 · from ops-desk-api（patch 升级 + FEEDBACK 项修复核对）

> **日期**：2026-08-24（执行落盘 2026-08-25 UTC+8）
> **业务仓**：`ops-desk-api`（分支 `task/dsh-coding-kit-1-5-2`）
> **task**：`docs/tasks/active/task_dsh_coding_kit_upgrade_1_5_2.md`
> **起点**：manifest `1.5.1` → 目标 `dsh-coding-kit@1.5.2`
> **对照**：1.5.1 包 vs 1.5.2 包全量 diff（`/tmp/kit-151/package` vs `/tmp/kit-152/package`，npx 均带 `npm_config_cache=/tmp/npm-cache-lg`）
> **执行**：30 子 agent · 禁 git commit · 未动 graph-compile.sh / CI 默认命令面

---

## 1. 结论（验收）

| 项 | 结果 |
|----|------|
| manifest | **1.5.2**（from_version=1.5.1 · preset=fullstack-node-py / ide 保留） |
| AGENTS/CLAUDE local 块 | **零字节变化**（diff 空 · §4） |
| refresh-ide-blocks | rewrites=0 / files_written=0（1.5.1 波已改写，本波零改写）；幂等二刷 dry-run rewrites=0 |
| upgrade 幂等 | **PASS**（二跑 1.5.2→1.5.2 · from_version 保持 1.5.1） |
| `verify --task <本task>` | 严格态 BLOCKED（缺 R<n>，20 序内预期）；`--allow-no-review` 留痕豁免 **PASS exit 0**（10/30 invoke 已补齐，不再需要 --allow-invoke-gap） |
| graph-compile.sh（harness 面） | **exit 0**（未动；产物 diff 仅 generated_at/freeze_id 日期戳，已 git checkout 还原） |
| pytest tests -q | 3 failed / 242 passed = 既有基线（chat_ws/chat_router 缺表）· 无新增 |
| severity=block | **无** |

**判定**：1.5.1→1.5.2 patch 升级在本仓成立；**D1/D2/D3/R6 全部未修**（`lib/cli-graph-yaml.js` 与 1.5.1 **字节级一致**，diff 0 行）；1.5.2 实际增量为 **DEF-028（修 K1 check 误报）** 与 **DEF-029（修 K4 mdc 无 marker 检出报告）**——均为本仓 1.5.1 FEEDBACK §6 反哺项。

---

## 2. 1.5.1→1.5.2 包 diff（全量）

| 文件 | 变化 | 对应反哺项 |
|------|------|-----------|
| `lib/cli-graph-yaml.js` | **0 diff lines** | D1/D2/D3/R6 **全未修**（详见 §3）；DEF-023 已修三条**未回退**（详见 §4） |
| `lib/cli.js`（6 diff lines） | **DEF-028**：`check` 遇 `from_version != null` 的「manifest 高于包版本」分支，输出「跨产品线迁移：@cyning/harness X → dsh-coding-kit Y（跨产品线版本号不可比）」并建议 upgrade（L210-214），不再误报「可能为降级安装」 | **修 1.5.1 FEEDBACK K1** |
| `lib/cli-refresh-ide-blocks.js`（44 diff lines） | **DEF-029**：0 product 块文件做整文只读扫描（复用 rewriteBody 纯函数），命中入报告「无 marker 检出（仅报告，不刷写）」段 + `--json` top-level `plain_mentions[]` / `totals.plain_mentions`（schema 保持 @1 向后兼容增量）；不触发 preflight fail-fast、不改 exit 码 | **修 1.5.1 FEEDBACK K4** |
| README / README.zh-CN | 版本号 + DEF-028/DEF-029 文档化 + preflight untracked 语义明示 + backups 建议 gitignore | — |
| assets（discipline-coverage.yaml / ontology.yaml） | 版本戳 1.5.1→1.5.2 | — |
| 其余 lib（checks/graph/graph-hgm/lifecycle/shared/skills/status/sync/task-extra/timeline/wiki/index/yaml） | 0 diff | — |

**本仓实证**：dry-run 与 --yes 均输出「无 marker 检出（仅报告，不刷写）: .cursor/rules/05-harness-starter.mdc: A1 npx @cyning/harness → npx dsh-coding-kit: 1」——1.5.1 FEEDBACK §5 记录的 mdc 滞留字面问题，1.5.2 起有只读检出报告（仍不刷写，B 组仅报告，与建议一致）。

---

## 3. FEEDBACK 项修复核对（D1/D2/D3/R6 · 实读 1.5.2 `lib/cli-graph-yaml.js`）

> 前提证据：`diff /tmp/kit-151/package/lib/cli-graph-yaml.js /tmp/kit-152/package/lib/cli-graph-yaml.js` = **0 diff lines**（字节级一致）。下列行号为 1.5.2 包内行号。

| ID | 现象（1.5.1 FEEDBACK §6） | 1.5.2 状态 | 证据行号 |
|----|--------------------------|-----------|---------|
| D1（P2） | export 丢边 label：`edgeToGraphV2` 对 mark=`?>`/`::…`/`~>`/`[…]` 强制 `baseLabel=''` | **未修** | L196-199（`~>`）、L201-205（`?>`）、L206-210（`::…`）、L211-215（`[…]`）仍 `baseLabel = ''`；仅 `->` 与未知 mark 分支保留 label（L216-224） |
| D2（P2） | export 自根递归 graph_id 用路径命名空间（`l0/00_main`）而非 yaml 声明值（`00_main`） | **未修** | `buildGraphPayload` L268-279/283-296 仍用 `allGraphIds` 路径 id 写 nodes/edges/graphs，不读 `data.graph_id`；`validateGraphYaml` L40-41 仍禁 `/`（与路径 id 自相矛盾依旧） |
| D3（P3） | `check --all` 与 kit 自产根 json 不互认（裸 id 过滤 vs 命名空间 id） | **未修**（同源 D2） | `check` L527-528 仍按 graphId 过滤 json nodes/edges；D2 未修则 D3 必存 |
| R6 | `generateMermaid` class 应按 yaml `kind`（1.5.1 为硬编码 id 白名单） | **未修** | L395-397 仍硬编码 `['Q','E','U1','U2','RAG','T2S','RPC','FTS']` / id 含 `DOC` / `['AUTH','EV_TYPES']`，不读 `nodes[].kind`（`generateNodeTable` L410 读 kind 仅供表格，class 段不消费） |

**结论**：反哺建议（kit `generateMermaid` class 消费 `nodes[].kind`；export 保留 label；export graph_id 用声明值）在 1.5.2 **均未落地**。graph 命令面切换判定维持 1.5.1 波结论：**不切**（`graph-compile.sh` / CI 保持 @cyning/harness 面，`graph_mermaid_normalize.py` 的 R6 class 补全仍是本仓增量价值）。

---

## 4. DEF-023 已修三条回退抽查（1.5.2 证据行号）

| # | 规则 | 1.5.2 状态 | 证据 |
|---|------|-----------|------|
| 1 | 锚点注释 `%% → path[#Ln|::symbol]` | **未回退** | `formatAnchorComment` L326-338（注释自述 DEF-023） |
| 2 | 带标签边 `src -->|"text"| dst`（禁 `--"…"-->`） | **未回退** | L380-381 官方形态；全 lib `grep -- '--"'` **0 命中** |
| 3 | 节点标签一律双引号 + entity code 转义 | **未回退** | L356-358（一律加引号）+ `escapeMermaidText` L344-349（`#35;`/`#quot;`/`#124;`，先转 #） |

另：`label: "->"` 裸边渲染（L376）与 `|`→`#124;` 保守转义仍在。

---

## 5. 升级实录（命令 · 退出码）

| # | 命令 | exit | 说明 |
|---|------|------|------|
| 1 | `npx dsh-coding-kit@1.5.2 check --target .` | 0 | 状态：可升级（**DEF-028 生效**：无「可能为降级安装」误报——本波 from_version=2.24.0 非 null 但走「可升级」分支；高于分支实测见下） |
| 2 | `refresh-ide-blocks --dry-run` | 0 | rewrites=0；**DEF-029 生效**：plain_mentions=1（mdc A1 字面） |
| 3 | `git stash push -u`（untracked task_rag 文件）→ `refresh-ide-blocks --yes` → `git stash pop` | 0 | preflight 过；rewrites=0 / files_written=0（零写入，未产生新备份代）；untracked 恢复 |
| 4 | `git diff AGENTS.md CLAUDE.md` | — | **空**（local 块零字节变化，§6） |
| 5 | `upgrade --target . --yes` | 0 | manifest 1.5.1→1.5.2 · from_version=1.5.1 |
| 6 | `upgrade` 二跑 + `refresh` 二刷 dry-run + `check` | 0 / 0 / 0 | 幂等；check=已是最新 |
| 7 | `verify --task <本task>`（严格） | 2 | BLOCKED：missing R<n> review（20 序内未审，预期） |
| 8 | `verify --task <本task> --allow-no-review --allow-invoke-gap`（首跑）/ `--allow-no-review`（10/30 invoke 补齐后） | **0** | 留痕豁免 PASS；invoke 补齐后 --allow-invoke-gap 不再需要 |
| 9 | `./scripts/graph-compile.sh` | 0 | harness 面未动；产物 diff 仅 generated_at + freeze_id 日期戳（0824→0825），`git checkout --` 还原 |
| 10 | `.venv/bin/pytest tests -q` | 1 | 3 failed / 242 passed = 基线（chat_ws/chat_router 缺表） |

---

## 6. local 块零手恢复证据

`git diff AGENTS.md CLAUDE.md`（升级后 vs HEAD）**输出为空**：1.5.1 波已把产品块 A1 字面改为 `npx dsh-coding-kit`，本波 refresh rewrites=0 / files_written=0，两个文件零字节变化。`cyning-harness-local:begin/end` 块（pre-30 invoke 拒改码 / HG-PILOT-OPSDESK-GLAYER / G-L0 / graph_modules_path）内容完整；refresh 报告自述「跳过 local 块: 1」（AGENTS）。

---

## 7. 剩余缺口与 severity

| ID | 现象 | severity | 说明 |
|----|------|----------|------|
| D1/D2/D3 | export 丢 label / graph_id 命名空间 / check-export 不互认 | **P2/P2/P3**（沿用） | 1.5.2 未修（§3）；继续以本仓 `graph_yaml_to_json.py` 产物为 graph.json 真值 |
| R6 | class 不按 yaml kind | P3（沿用） | 1.5.2 未修；`graph_mermaid_normalize.py` 保留 |
| K7（新） | `upgrade` 将 from_version 改写为直接前驱（2.24.0→1.5.1→**1.5.1 被覆盖为 1.5.1→1.5.2** 时记 1.5.1） | info | 语义=直接前驱；但 DEF-028 的 check 分支以 `from_version != null` 判跨产品线，**此后任何「manifest 高于包版本」场景都会输出跨产品线迁移文案**（即使 from_version=1.5.1 已是 kit 线版本号）——DEF-028 判据过宽，建议 kit 以 from_version 是否属 harness 产品线词表为准 |
| K8（新） | graph-compile 产物 freeze_id 按日滚动（`..._20260824_V1`→`_20260825_V1`） | info | 本仓 `graph_yaml_to_json.py` 行为，非 kit 项；跨日跑 graph-compile.sh 会产生日期戳 diff，需还原或入库决策（沿用 1.5.1 波处置：checkout 还原） |

---

## 8. 验收清单

- [x] manifest = 1.5.2（from 1.5.1 · `.cyning-harness/` 约定不变）
- [x] AGENTS/CLAUDE local 块完整（diff 空 · §6）
- [x] refresh-ide-blocks --yes 落盘（零写入）+ 幂等复检
- [x] `verify --task` 跑通（豁免留痕 PASS · 严格态缺口为序内 20 补件）
- [x] graph-compile.sh exit 0（harness 面未动）
- [x] pytest 无新增失败（3/242 = 基线）
- [x] D1/D2/D3/R6 修复核对（§3 · 全未修 · 证据行号）
- [x] DEF-023 已修三条回退抽查（§4 · 未回退）
- [ ] 00：20 R<n> 审查 · 统一 commit
