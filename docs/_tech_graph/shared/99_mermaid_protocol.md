# Mermaid 拓扑协议（通用 · v3）

> **用途**：`docs/_tech_graph/shared/99_mermaid_protocol.md` — flowchart 边标记、节点形状与 YAML-first 生成真值。

## 0. YAML-first 工作流

- **唯一人工编辑源**：`docs/_tech_graph/**/*.graph.yaml`（如 `l0/00_main.graph.yaml`、`l1/10_flow_*.graph.yaml`）。
- **生成物**：同名 `*.md` 由 `./scripts/graph-compile.sh`（当前：`npx dsh-coding-kit graph yaml compile`；默认 `GRAPH_CLI=dsh-coding-kit`，env 可切回）生成；kit 1.6.1 emit 直接满足 §0.1 契约，不再需要 post-compile 改写。
- **禁止手写编译产物 `.md`**：改 YAML 后重跑 compile；手改会在下次 compile 被覆盖。
- **`--check` 语义**：kit `graph yaml check` 比对 YAML 与 `shared/graph.json` 切片；另跑 `graph_mermaid_normalize.py --check`（check-only 护栏，不改写）断言 mermaid 围栏无 `//` 注释、无旧边 `--"…"-->`。
- **export**：`shared/graph.json`（C1；根目录过渡双写）。
- **历史 `.ai.md` 双轨已弃用**：结构化信息集中在 YAML 源中。
- **命令面已切换（2026-08-25）**：`@cyning/harness` → `dsh-coding-kit` 1.6.1（`docs/spec/SPEC-harness-to-dsh-kit-graph-migrate_v0.md` §6 执行完毕；回滚备份 `scripts/legacy/*.20260825.pre-cmd-switch.bak`；V3 对照材料 `docs/harness/evidence/V3_mermaid_compare_dsh_kit_1_6_1_20260825.md`）。

---

## 0.1 IDE 预览兼容（编译器 / 归一化输出契约）

| 项 | 禁止（旧 harness emit） | 要求（kit ≥1.6.1 emit 已满足；normalize 仅作 check 护栏） |
|----|-------------------------|----------------------------------|
| 注释 | `// → path` | `%% → path`（[Mermaid 注释](https://mermaid.js.org/intro/syntax-reference.html)） |
| 带标签边 | `A --"label"--> B` | `A -->|"label"| B`（[flowchart 边上文字](https://mermaid.js.org/syntax/flowchart.html)） |
| 特殊字符标签 | `id[含空格/()/ >…]` | `id["…"]` |
| class | 仅 classDef、无赋值 | 按 yaml `kind` 补 `class … phase/doc/infra`（可选增强） |

语法真值以官网 + 本地 mermaid 仓 docs 为准，禁止凭记忆改 emit。

---

## 1. 边标记

### 1.1 执行流

| 标记 | 语义 | 何时用 |
|------|------|--------|
| `->` | 同步顺序执行 | 普通调用 |
| `~>` | 异步 / await | 非阻塞 I/O |
| `=>` | 赋值 / 映射 | 数据转换 |
| `?>` | 条件分支 | if / switch / 路由 |

### 1.2 状态与可靠性

| 标记 | 语义 | 示例 |
|------|------|------|
| `[ok]` | 成功路径 | `validate() -->|"[ok]"| save()` |
| `[err]` | 失败 / 异常 | `parse() -->|"[err]"| fallback()` |
| `[retry=N]` | 重试 | `call_api() -->|"[retry=3]"| call_api()` |
| `[timeout]` | 超时降级 | `fetch() -->|"[timeout]"| cache_get()` |

### 1.3 元关系（`::` 命名空间）

| 标记 | 语义 |
|------|------|
| `::yields` | 流式 / 生成器产出 |
| `::triggers` | 触发子流程或后台任务 |
| `::gates` | 门禁 / 鉴权 / 依赖注入 |
| `::branches` | 并行分支 |
| `::merges` | 多路归并 |
| `::signoff` | 持久化确认 / 事务提交 |
| `::archives` | 日志 / 审计归档 |

---

## 2. 节点形状（flowchart）

| 形状 | 含义 | 示例 |
|------|------|------|
| `[[...]]` | 阶段 / 流程块 | `[[Query Phase]]` |
| `[...]` | 函数 / 操作 | `[process_request]` |
| `[(...)]` | 数据 / 模型 | `[(UserRecord)]` |
| `{...}` | 判断 / 路由 | `{authorized?}` |
| `>...]` | 里程碑 / 文档指针 | `>10_flow_MAIN.md]` |
| `((...))` | 循环 / 归档 | `((write_log))` |

---

## 3. 锚点规则（YAML 源强制）

每条 **硬边** 须可追溯到代码或文档，写在 YAML `edges[].anchors` 中：

```yaml
edges:
  - from: "Q"
    to: "E"
    anchors:
      - path: "src/main.py"
        line: 1
      - path: "app/router/index.ts"
        symbol: "Router"
```

- 跨模块调用：使用 `::triggers` 或虚线，**不**展开对方内部。
- 未知锚点：保留 `path: TBD` 并开 task 补全。

---

## 4. 分层与折叠

| 条件 | 操作 |
|------|------|
| 子图节点 ≤ 7 | 可在主图展开 |
| 子图节点 > 7 | 折叠为 `[[Phase]]`，链独立 `10_flow_*.md` |
| 异常分支 | 挂侧链；Happy Path 走主干 |

---

## 5. 禁止项

- **禁止**维护 `.ai.md` 双轨文件。
- **禁止**在生成的 `.md` 中直接手写 flowchart（会被下次编译覆盖）。
- 禁止虚构文件路径；未知处用 `path: TBD` 并开 task 补锚点。
- **禁止** onboarding 默认「全仓扫描生图」。

---

## 6. YAML 字段到 Mermaid 映射

| YAML 字段 | Mermaid 输出 | 说明 |
|-----------|--------------|------|
| `nodes[].id` | 节点 ID | 必须唯一 |
| `nodes[].label` | 节点显示文本 | 决定节点形状 |
| `edges[].from` / `to` | 边两端 | 必须引用存在的节点 |
| `edges[].label` | 边标签 | `"->"` 表示裸执行边 |
| `edges[].mark` | 元关系标记 | 如 `::triggers`、`::branches` |
| `edges[].type` | 边类型 | 与 `mark` 命名空间对应 |
| `edges[].anchors` | 不渲染，写入 table | 代码追溯 |

---

## 7. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-30 | v3：YAML-first，删除 `.ai.md` 双轨，新增 YAML → Mermaid 映射 |
| 2026-08-24 | §0/§0.1：post-compile normalize + IDE 契约；§1.2 示例改 `-->|"…"|`；挂迁移预留 SPEC |
| 2026-08-25 | §0：命令面切至 dsh-coding-kit 1.6.1（emit 治根）；normalize 降级 check-only 护栏 |
| YYYY-MM-DD | 嵌入用户仓时填写首次版本 |
