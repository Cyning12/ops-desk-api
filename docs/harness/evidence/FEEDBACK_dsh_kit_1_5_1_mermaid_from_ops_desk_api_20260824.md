# FEEDBACK · dsh-coding-kit 1.5.1 · Mermaid emit / graph 迁移探针 · from ops-desk-api

> **日期**：2026-08-24
> **业务仓**：`ops-desk-api`（分支 `task/dsh-coding-kit-1-5-1`）
> **task**：`docs/tasks/active/task_dsh_kit_graph_migrate_probe.md`（SPEC-harness-to-dsh-kit-graph-migrate_v0 §4 矩阵实测）
> **前置**：kit 1.5.1 已入库；本仓 4 张图 `docs/_tech_graph/{l0/00_main, l1/10_flow_auth, l1/10_flow_chat, l1/11_flow_sync_to_chat}.graph.yaml`
> **执行**：30 子 agent · 禁 git commit · 未动 graph-compile.sh / CI 默认命令面
> **试编译现场**：`/tmp/kit-probe/tg/`（临时目录，本仓 docs/_tech_graph 产物未动）

---

## 1. 结论（判定）

**kit 1.5.1 的 DEF-023 修复「4 条规则中 3 条已修、1 条（class 按 kind）未修」**，另发现 2 个本仓相关差异（export 丢 label、graph_id 命名空间策略）。

按 SPEC §4 判定表 → 属「**kit 仍差、本仓 normalize 更好**（部分维度）」：

- **不切默认命令面**（`graph-compile.sh` / CI 保持 `@cyning/harness` 面）。
- **保留 `scripts/graph_mermaid_normalize.py`**：其 V2 检查项对 kit 产物已全绿（可裁剪为 no-op），但 **class 按 kind 补全是 kit 1.5.1 没有的增量价值**（kit 产物零 class 赋值行，IDE 预览失色板分组）。
- 本文件即 §5 反哺材料（规则集 + fixture 对照 + 差异清单）。

---

## 2. DEF-023 逐条修复结论（证据：dsh-coding-kit@1.5.1 npm 包 `lib/cli-graph-yaml.js` 实读）

| # | 本仓 normalize 规则 | kit 1.5.1 状态 | 证据 |
|---|---|---|---|
| 1 | `// → …` 锚点注释 → `%% → …` | **已修** | `formatAnchorComment` emit `%% → path#Ln`（L326-338，注释自述 DEF-023）；模板 `assets/graph/templates/99_mermaid_protocol.md` §7 契约 L131 |
| 2 | `--"…"-->` → `-->|"…"|` | **已修** | `generateMermaid` L381 emit `src -->"\"text\""| dst`（官方形态）；全 lib grep `--"` **零命中**；契约 L132/L140 明令禁止旧形态 |
| 3 | 特殊字符节点标签加引号 `id["label"]` | **已修（更宽）** | L356-358 **一律**双引号包裹（本仓仅特殊字符时加引号，功能等价、kit 更保守）；转义用官方 entity code `#quot;`/`#124;`/`#35;`（L344-349，契约 L136） |
| 4 | `class` 按 yaml `kind` 赋值（flow/struct→phase · external+db/llm/rag→infra · `>` 指针标签→doc） | **未修** | L395-397 **硬编码 id 白名单启发式**：phase=[Q,E,U1,U2,RAG,T2S,RPC,FTS] · doc=id 含大写 `DOC` · infra=[AUTH,EV_TYPES]；**不读 yaml kind**。本仓 4 张图节点 id 零命中 → kit 产物 **0 行 class 赋值**（仅 3 行 classDef 空转）；本仓 normalize 产物每图 2-3 行 class（phase/doc/infra 全覆盖） |

**kit 额外做对的点（本仓 normalize 未覆盖）**：

- `label: "->"` 按 99_mermaid_protocol §6 渲染为裸边 `-->`（kit L376）；本仓 harness+normalize 链残留 `-->|"->"| `（见 §4 fixture 对照 `context --> answer` 行）。
- 边文本内 `|` 转 entity code `#124;`（`[general#124;overview]`），比本仓原样保留 `|` 更保守安全。

---

## 3. SPEC §4 验证矩阵实测

| # | 检查 | 命令 / 方法 | 结果 |
|---|------|------------|------|
| V1 | kit compile 全图 exit 0 | `npx dsh-coding-kit@1.5.1 graph yaml compile --input /tmp/kit-probe/tg/{l0,l1} --all`（npx 均带 `npm_config_cache=/tmp/npm-cache-lg`） | **PASS**（两目录各 exit 0，4 张 md 全生成） |
| V2 | kit 产物坏模式 | `python3 scripts/graph_mermaid_normalize.py --check /tmp/kit-probe/tg` + awk 围栏内 grep `^\s*//` 与 `--"…"-->` | **PASS**（check exit 0「4 md file(s)」；两类坏模式计数均 0） |
| V3 | IDE 预览 | **人工项**——fixture 对照见 §4，供维护者在 Cursor 勾验「有边、非单行孤岛」 | 待维护者勾 |
| V4 | check + graph.json 一致 | ①kit 自洽模式：`export --input tg` + `check --graph-id l0/00_main …` 4/4 OK exit 0；②本仓兼容模式：`check --input tg/{l0,l1} --all --graph-json <本仓 shared/graph.json>` **4/4 OK exit 0** | **PASS**（两种模式均绿；注意 kit check 只比对 [from,to,mark,type] 四元组，**不比对 label/sync**——故未暴露 §5 差异 D1） |
| V5 | 边集合对照 | kit export payload vs 本仓 `shared/graph.json`：边 76=76（去重集合 71=71，only-in 两侧均空）；节点 id 39=39 完全一致、**无大小写策略差异**；分图边数 26/14/26/10 两侧一致 | **PASS（边集合）**，但见 §5 差异 D1（5 条边 label 丢失）/D2（graph_id 命名空间） |

---

## 4. §5 反哺材料 A：chat 图 fixture 对照（`l1/10_flow_chat` mermaid 块节选）

**kit 1.5.1 产物**（`/tmp/kit-probe/tg/l1/10_flow_chat.md`）：

```mermaid
flowchart TB
    intent["detect_intent"]
    retrieve["hybrid_recall"]
    ...
    intent -->|"[issue_qa]"| context
    %% → app/ops/chat/graph.py#L40
    intent -->|"[general#124;overview]"| retrieve
    context --> answer
    %% → app/ops/chat/graph.py#L49
    ...
    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    （无 class 赋值行 — 硬编码白名单零命中）
```

**本仓 normalize 后产物**（`docs/_tech_graph/l1/10_flow_chat.md` 现行入库版）：

```mermaid
flowchart TB
    intent[detect_intent]
    retrieve[hybrid_recall]
    ...
    intent -->|"[issue_qa]"| context
    %% → app/ops/chat/graph.py#L40
    intent -->|"[general|overview]"| retrieve
    context -->|"->"| answer        ← harness 链残留：label:"->" 应为裸边（kit 已修）
    %% → app/ops/chat/graph.py#L49
    ...
    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px

    class client,chat_stream,chat_ws,event_gen,chat_service,stategraph,intent,context,retrieve,grade,refuse_answer,answer,admin_sync phase
    class main_doc doc
    class rag,llm,db infra
```

**对照结论**：边形态/锚点注释/引号两侧实质一致且均应可渲染；kit 差 **class 赋值整块缺失**（IDE 预览无色板分组，4 图皆然）；本仓差 `-->|"->"|` 残留与 `|` 未转义（小问题）。

---

## 5. §5 反哺材料 B：emit 契约规则集（本仓 `graph_mermaid_normalize.py` 提炼，建议 kit 补第 4 条）

| 规则 | 契约 | 本仓实现 | kit 1.5.1 |
|------|------|----------|-----------|
| R1 锚点注释 | 独立行 `%% → path[#Ln|::symbol]`，禁 `//` | normalize L41-43,91-94 | ✅ 已修 |
| R2 带标签边 | `src -->|"label"| dst`，禁 `--"…"-->` | L35-37,96-100 | ✅ 已修 |
| R3 裸边 | yaml `label: "->"` → `src --> dst`（不渲染文本） | ❌ 未处理（残留 `|"->"|`） | ✅ kit 更好（L376） |
| R4 节点引号 | 含空格/()/[]/{}/\|>/+/\\/#\`'" 之一 → `id["label"]`；或一律加引号 | L33,50-85（条件式） | ✅ 已修（一律加引号） |
| R5 转义 | 标签内 `"`→`#quot;` `\|`→`#124;` `#`→`#35;`（先转 #） | 反斜杠转义（\" \\） | ✅ 已修（entity code，更规范） |
| R6 **class 按 kind** | kind∈{flow,struct}→`phase`；kind=external 且 id 含 db/llm/rag/pg/postgres/qdrant→`infra`，否则→`phase`；label 以 `>` 开头或 id 含 doc/以 _md 结尾→`doc`；重写旧 class 行、保留 classDef | L118-198 | ❌ **未修**（L395-397 硬编码 id 白名单，不读 kind） |

**反哺建议**：kit `generateMermaid` 的 class 赋值改为消费 `nodes[].kind`（规则 R6），或在 yaml schema 增显式 `class` 字段；硬编码 id 白名单对任何真实业务仓零命中。

---

## 6. §5 反哺材料 C：差异清单（kit 1.5.1 新发现，超 DEF-023 原范围）

| ID | 现象 | 证据 | severity | 建议 |
|----|------|------|----------|------|
| D1 | `graph yaml export` **丢弃边 label**：yaml 显式 `mark: "?>"`/`::triggers` 且带 label 时，`edgeToGraphV2` 强制 `baseLabel=''`（L201-210） | `10_flow_chat` 5 条边：`intent→retrieve "[general\|overview]"`、`intent→context "[issue_qa]"`、`grade→refuse_answer "[refuse]"`、`grade→answer "[generate_answer]"`、`retrieve→rag "hybrid_recall"`；本仓 json 有 label、kit payload 为空 | **P2** | mark 与 label 应正交：mark 控制形，label 是文本；`?>`/`::` 边不应吞 label。另 `check` 只比四元组不比 label，无法发现此丢失——check 应补 label 比对 |
| D2 | export 自根目录递归时 graph_id 取**路径命名空间**（`l0/00_main`），而 yaml 声明 `graph_id: 00_main`、本仓 custom `graph_yaml_to_json.py` 用声明值 | kit payload graphs id = `l0/00_main` 等；本仓 json = `00_main` 等；`buildGraphPayload` L268-279 用 `allGraphIds` 路径 id，不读 `data.graph_id` | **P2**（切换命令面时若不保留本仓 json 生成器，下游消费 graph_id 全断） | export 应优先用 yaml 声明 `graph_id`（或至少提供开关）；且 `validateGraphYaml` L40 禁 `/` 与路径 id 自相矛盾 |
| D3 | `check --all` 与 export 自根产物不互认：`check --input <root> --all --graph-json <kit export 的根 json>` 报 JSON=0（check 用裸 id 过滤、export 用命名空间 id） | 实测 exit 1「Nodes only in YAML…JSON=0」；per-dir 模式（export --no-recursive + check --all）互认正常 | P3 | 与 D2 同源，修 D2 即解 |

---

## 7. 迁移日前置核对（SPEC §2）

| 前置 | 状态 |
|------|------|
| kit 发布含 DEF-023 修复（changelog 明示） | **部分**：包内无 CHANGELOG 文件；`assets/graph/templates/99_mermaid_protocol.md` §8 修订记录 2026-08-24 明示 DEF-023；源码实测 3/4 规则已修（§2 表） |
| `scripts/legacy/` 迁移日新备份 | **完成**：`graph-compile.sh.20260824.pre-dsh-kit-migrate.bak` · `graph_mermaid_normalize.py.20260824.pre-dsh-kit-migrate.bak` · `graph_yaml_to_json.py.20260824.pre-dsh-kit-migrate.bak`（untracked，待 00 统一入库） |
| 4 图无 normalize 试编译过 §4 矩阵 | V1/V2/V4/V5 实测通过（V3 人工项待勾）；**但 class 缺失 + D1/D2 差异 → 不满足「IDE ≥ normalize 方案」** |
| 维护者签收「切命令面」 | **不申请**（本波判定不切） |

---

## 8. 收尾核验

- `./scripts/graph-compile.sh`（harness + normalize 现状）跑通 **exit 0**，4 图 check 全 OK；产物 diff 仅 `generated_at` 时间戳，已 `git checkout --` 还原，工作树干净（仅 3 个 legacy 备份 untracked）。
- `graph-compile.sh` / `.github/workflows/tech-graph.yml` 默认命令面**未动**。

## 9. 给 kit 的反哺 PR 指引（按 SPEC §5）

1. 目标文件：`dsh-coding-kit/src/cli-graph-yaml.ts`（`generateMermaid` class 段 ≈ lib L395-397；`edgeToGraphV2` label 段 ≈ lib L201-210；`buildGraphPayload` graph_id 段 ≈ lib L268-279）。
2. fixture：本仓 `docs/_tech_graph/l1/10_flow_chat.graph.yaml`（含 `?>`+label、`::triggers`+label、kind 分布齐全）。
3. 预期产出：class 赋值按 kind（R6）· export 保留 label（D1）· export graph_id 用声明值（D2）。
4. 对照官方文档后再提 PR（禁凭记忆）：https://mermaid.js.org/syntax/flowchart.html。
