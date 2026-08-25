# FEEDBACK · dsh-coding-kit 1.6.1 · from ops-desk-api（minor 升级 + FEEDBACK 项修复核对）

> **日期**：2026-08-25
> **业务仓**：`ops-desk-api`（分支 `task/dsh-coding-kit-1-6-1`）
> **task**：`docs/tasks/active/task_dsh_coding_kit_upgrade_1_6_1.md`
> **起点**：manifest `1.5.2` → 目标 `dsh-coding-kit@1.6.1`
> **对照**：1.5.2 包 vs 1.6.1 包全量 diff（`/tmp/kit-152/package` vs `/tmp/kit-161/package`，npx 均带 `npm_config_cache=/tmp/npm-cache-lg`）
> **执行**：30 子 agent · 禁 git commit · 未动 graph-compile.sh / CI 默认命令面

---

## 1. 结论（验收）

| 项 | 结果 |
|----|------|
| manifest | **1.6.1**（from_version=1.5.2 · preset=fullstack-node-py / ide 保留） |
| AGENTS/CLAUDE local 块 | **零字节变化**（diff 空 · §4） |
| refresh-ide-blocks | rewrites=0 / files_written=0；幂等二刷 dry-run rewrites=0 |
| upgrade 幂等 | **PASS**（二跑 1.6.1→1.6.1 · from_version 保持 1.5.2 · upgraded_at 不变） |
| `verify --task <本task>` | 严格态 BLOCKED（缺 R<n>，20 序内预期）；`--allow-no-review` 留痕豁免 **PASS exit 0**（10/30 invoke 已就位，无需 --allow-invoke-gap） |
| graph-compile.sh（harness 面） | **exit 0**（未动；产物 diff 仅 generated_at 时间戳，已 git checkout 还原） |
| pytest tests -q | 3 failed / 242 passed = 既有基线（chat_ws/chat_router 缺表）· 无新增 |
| severity=block | **无** |

**判定**：1.5.2→1.6.1 minor 升级在本仓成立；**D1/D2/D3/R6 全部已修、K7 判据收窄已修**（`lib/cli-graph-yaml.js` 与 1.5.2 diff **79 行**——1.5.2 波对 1.5.1 为 0 行）；CLI 面仅增量（verify --spec 模式），**无破坏性变更**。

---

## 2. CLI 面探查（1.6.1 对照 1.5.2 · minor 跳版检查）

顶层 `--help` diff 唯一变更：

```diff
-  npx dsh-coding-kit verify [--target PATH] [--task FILE] [--json]
+  npx dsh-coding-kit verify [--target PATH] [--task FILE | --spec FILE] [--json]
```

| 子命令 | 1.5.2 → 1.6.1 | 破坏性？ |
|---|---|---|
| verify | 新增 `--spec FILE` 模式（PRD_DEF-003 后续棒：SPEC→00 前审查文存在性闸 · 与 --task 互斥）+ `--allow-no-spec-review` 豁免旗标（canonical，`--allow-no-review` 作别名） | 否（纯增量） |
| upgrade / refresh-ide-blocks / check | help 零变更 | 否 |
| graph yaml compile/check/export · ingest/snapshot/axioms | help 零变更（参数面同 1.5.1 记忆） | 否；**行为修正**见 §3（README.zh-CN L108 自述「消费者注意」） |
| task lint / lint-done / lint-wiki-delta / close / check · gate-check · audit · status · timeline · lifecycle · discipline · skills · wiki · sync | 未全量复验；lib diff 未触及命令面 | 否 |

新增 lib 能力（cli-checks.js）：`findSpecReview` / `shouldSkipSpecAudit` / `extractSpecSlug` / `evalSpecReviewsRetention` / `evalCloseWikiPromotion`；cli-lifecycle.js 接线 `spec_reviews_retention` 与 `close_wiki_promotion` 守卫（DEF-003 登记守卫十一项全部接线）。新增 `RELEASING.md`（publish 前硬步骤 checklist）。无参数删除、无语义反转 → **未触发停下报 00 条件**。

---

## 3. FEEDBACK 项修复核对（D1/D2/D3/R6 · 实读 1.6.1 `lib/cli-graph-yaml.js`）

> 前提证据：`diff /tmp/kit-152/package/lib/cli-graph-yaml.js /tmp/kit-161/package/lib/cli-graph-yaml.js` = **79 diff lines**（1.5.2 波对 1.5.1 为 0 行，本波实质改动）。行号为 1.6.1 包内行号；README.zh-CN L108 官方自述对应行为修正。

| ID | 现象（1.5.1/1.5.2 FEEDBACK） | 1.6.1 状态 | 证据行号 |
|----|------------------------------|-----------|---------|
| D1（P2） | export 丢边 label：`edgeToGraphV2` 对 mark=`?>`/`::…`/`~>`/`[…]` 强制 `baseLabel=''` | **已修（DEF-031）** | L200-201 注释「拓扑协议标记作为边属性呈现，不丢弃 label 文本」+ `baseLabel = label`：`~>` L201、`?>` L206、`::…` L211、`[…]` L216；`->` L221 与未知 mark L226 保持。残留 `baseLabel=''` 仅 `classDiagram` 结构标记（L196）与 label-as-mark 兼容形态（L240/244/248），语义正确 |
| D2（P2） | export 自根递归 graph_id 用路径命名空间（`l0/00_main`）而非 yaml 声明值（`00_main`） | **已修（DEF-032①③）** | `buildGraphPayload` L281-283 注释 + `const declaredId = data.graph_id != null ? String(data.graph_id) : graphId`（L283）；graphs.id L285 / nodes.graph_id L290 / edges.graph_id L302 均写声明值；`validateGraphYaml` L40-44（DEF-032③）改为校验声明值须裸 slug，与输出口径自洽 |
| D3（P3） | `check --all` 与 kit 自产根 json 不互认 | **已修（DEF-032②）** | `check` L548-551：`declaredId` 同源取值（L549），json nodes/edges 过滤口径与 export 输出对齐（L550-551） |
| R6 | `generateMermaid` class 应按 yaml `kind` | **已修（DEF-033）** | L401-424：`KIND_TO_CLASS = { flow: 'phase', struct: 'doc', external: 'infra' }`（L403），逐节点 `node.kind` 映射（L406），无 kind/未知 kind 保留 id 推断兜底（L407-415，历史行为） |

**结论**：1.5.1 波反哺建议 **全部落地**。graph 命令面切换判定的主要阻力（D1/D2/D3/R6 未修）已消除；切换仍属 probe task 范围，本 task 未动 `graph-compile.sh` / CI。

---

## 4. K7 / K8 核对（实读 1.6.1 `lib/cli.js` 与 `cli-graph-yaml.js`）

| ID | 现象（1.5.2 FEEDBACK §7） | 1.6.1 状态 | 证据行号 |
|----|---------------------------|-----------|---------|
| K7 | upgrade 将 from_version 改写为直接前驱；且 DEF-028 判据过宽（任何 from_version != null 的「高于」场景都输出跨产品线文案） | **判据过宽已修（DEF-030）**；from_version=直接前驱语义**不变**（本波 1.5.2→1.6.1 记 from_version=1.5.2） | cli.js L85-89 `isLegacyHarnessLineVersion`（`/^2\./` 词表）；L213-215 注释「判据收窄——kit 线（1.x）from_version 不走本分支」。本仓实证：升级前 check 输出「状态：可升级」（from_version=1.5.1 kit 线未触发迁移文案） |
| K8 | graph-compile 产物 freeze_id 按日滚动 | **kit 侧有固定项**：freeze_id 为常量 `TECH_GRAPH_S2_FREEZE_20260519_V2_3`，支持 `opts.freezeId` 覆盖；日滚动系本仓 `graph_yaml_to_json.py` 自脚本行为，非 kit 项 | cli-graph-yaml.js L5（常量）/ L270（`opts.freezeId ?? FREEZE_ID`）/ L318（写出）。本波同日运行未产生 freeze_id diff；沿用 1.5.1 波处置（checkout 还原时间戳 diff） |

---

## 5. DEF-023 已修三条回退抽查（1.6.1 证据行号）

| # | 规则 | 1.6.1 状态 | 证据 |
|---|------|-----------|------|
| 1 | 锚点注释 `%% → path[#Ln\|::symbol]` | **未回退** | `formatAnchorComment` L332-338（注释自述 DEF-023） |
| 2 | 带标签边 `src -->|"text"| dst`（禁 `--"…"-->`） | **未回退** | L380 注释官方形态 + L387 实现；全 lib `grep -- '--"'` **0 命中** |
| 3 | 节点标签一律双引号 + entity code 转义 | **未回退** | L363-364（一律加引号）+ `escapeMermaidText` L350-354（`#35;`/`#quot;`/`#124;`，先转 #） |

---

## 6. 升级实录（命令 · 退出码）

| # | 命令 | exit | 说明 |
|---|------|------|------|
| 1 | `npx dsh-coding-kit@1.6.1 --help` + 子命令 help diff | 0 | CLI 面唯一变更 = verify --spec（§2）；无破坏性变更 |
| 2 | `npx dsh-coding-kit@1.6.1 check --target .` | 0 | 状态：可升级（from_version=1.5.1 kit 线 → DEF-030 收窄生效，无迁移/降级误报） |
| 3 | `refresh-ide-blocks --dry-run` | 0 | rewrites=0；DEF-029 检出报告仍在（mdc A1 字面 plain_mentions=1） |
| 4 | `git stash push -u`（untracked task_rag 文件）→ `refresh-ide-blocks --yes` → `git stash pop` | 0 | preflight 过；rewrites=0 / files_written=0（零写入，无新备份代）；untracked 恢复 |
| 5 | `git diff AGENTS.md CLAUDE.md` | — | **空**（local 块零字节变化） |
| 6 | `upgrade --target . --yes` | 0 | manifest 1.5.2→1.6.1 · from_version=1.5.2 |
| 7 | `upgrade` 二跑 + `refresh` 二刷 dry-run + `check` | 0 / 0 / 0 | 幂等（from_version 保持 1.5.2 · upgraded_at 不变）；check=已是最新 |
| 8 | `verify --task <本task>`（严格） | 2 | BLOCKED：missing R<n> review（20 序内预期） |
| 9 | `verify --task <本task> --allow-no-review` | **0** | 留痕豁免 PASS（10/30 invoke 就位，无需 --allow-invoke-gap） |
| 10 | `./scripts/graph-compile.sh` | 0 | harness 面未动；产物 diff 仅 generated_at 时间戳（同日，freeze_id 未滚动），`git checkout --` 还原 |
| 11 | `.venv/bin/pytest tests -q` | 1 | 3 failed / 242 passed = 基线（chat_ws/chat_router 缺表）· 无新增 |

**环境备注**：`/tmp/npm-cache-lg/_npx` 曾出现 1.6.1 缓存半成品（`sh: dsh-coding-kit: command not found`，疑并发 npx 安装踩踏），`rm -rf /tmp/npm-cache-lg/_npx` 后串行重跑恢复；与本仓升级无关，记录备查。

---

## 7. local 块零手恢复证据

`git diff AGENTS.md CLAUDE.md`（升级后 vs HEAD）**输出为空**：1.5.1 波已把产品块 A1 字面改为 `npx dsh-coding-kit`，1.5.2/1.6.1 两波 refresh 均 rewrites=0 / files_written=0，两个文件零字节变化。`cyning-harness-local:begin/end` 块（pre-30 invoke 拒改码 / HG-PILOT-OPSDESK-GLAYER / G-L0 / graph_modules_path）内容完整；refresh 报告自述「跳过 local 块: 1」（AGENTS）。

---

## 8. 剩余缺口与 severity

| ID | 现象 | severity | 说明 |
|----|------|----------|------|
| K8 | 本仓 `graph_yaml_to_json.py` 产物 freeze_id 按日滚动 | info（沿用） | kit 侧已提供固定常量（§4）；日滚动属本仓自脚本，跨日跑 graph-compile.sh 需还原或入库决策（沿用 checkout 还原） |
| K9（新） | `.cursor/rules/05-harness-starter.mdc` 无 marker，A1 旧字面 `npx @cyning/harness verify` 滞留（DEF-029 仅报告不刷写） | P3（沿用 K4 处置建议） | 1.6.1 维持 B 组仅报告语义（plain_mentions=1）；是否手工改字面属仓决策，本波记录不动 |
| 行为修正提示 | kit `graph yaml export` 输出 graph_id 改为声明值、边 label 保留（README.zh-CN L108「消费者注意」） | info | 本仓 graph.json 真值仍为 `graph_yaml_to_json.py` 产物，未消费 kit export 输出，无即时影响；graph 命令面切换 probe task 需据此做行为等价回归 |

D1/D2/D3/R6/K7 **全部关闭**（§3/§4）。

---

## 9. 验收清单

- [x] manifest = 1.6.1（from 1.5.2 · `.cyning-harness/` 约定不变）
- [x] AGENTS/CLAUDE local 块完整（diff 空 · §7）
- [x] refresh-ide-blocks --yes 落盘（零写入）+ 幂等复检
- [x] `verify --task` 跑通（豁免留痕 PASS · 严格态缺口为序内 20 补件）
- [x] graph-compile.sh exit 0（harness 面未动）
- [x] pytest 无新增失败（3/242 = 基线）
- [x] D1/D2/D3/R6 修复核对（§3 · **全已修** · 证据行号）
- [x] K7/K8 核对（§4 · K7 已修 / K8 kit 侧固定项确认）
- [x] DEF-023 已修三条回退抽查（§5 · 未回退）
- [x] CLI 面变更点记录（§2 · 仅 verify --spec 增量，无破坏性）
- [ ] 00：20 R<n> 审查 · 统一 commit
