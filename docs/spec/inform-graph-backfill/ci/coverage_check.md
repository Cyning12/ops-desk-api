# CI · 覆盖检查（warn 一期）

> **Wave**：W5 · **另开 task 实现**  
> **原则**：文档自洽 CI 已存在；本脚本补 **语义覆盖** 可观测性，一期 **warn only**

---

## 1. 背景

`EVAL_tech_graph_third_party_20260730.md` 定稿：

- `tech-graph.yml` 不读 `app/` 源码
- 漏画 flow 时 `graph-compile.sh` 仍可 exit 0

---

## 2. 建议脚本

**路径**：`scripts/graph_coverage_check.py`（待建）

**输入**：

- `app/ops/router.py` — 解析 `include_router` 导入的 router 变量（正则/AST 二选一 · 轻量优先正则）
- `docs/_tech_graph/l0/00_main.graph.yaml` — `ops_router` 出边目标节点 id 集合
- `docs/_tech_graph/l1/01_modules.md` — 一级 `module_id` 表
- `docs/_tech_graph/**/*.graph.yaml` — 是否存在 `10_flow_{domain}` 或 G-L0 `::triggers` POINTER

**输出**：

- stdout 人类可读 WARN 列表
- exit 0（warn）· 未来 `--strict` exit 1（维护者拍板后）

---

## 3. 检查规则（一期）

| 规则 id | 检查 | 级别 |
|---------|------|------|
| R1 | `router.py` 每个 include 在 G-L0 有对应子路由节点 | warn |
| R2 | 有 HTTP 旁路模块（lc_evidence · lg_rag）存在 `10_flow_*` yaml | warn |
| R3 | `module_id` 在 `chat`/`rag`/`lc`/`lg` 且备注含 `START→` 长拓扑但无 flow 文件 | warn |
| R4 | `10_flow_chat` yaml 是否含 `retrieve` 节点 id | warn |

**不做（二期）**：

- anchors 行号与源码比对
- indexes ↔ implementedBy 双向 diff
- 全仓 path glob 覆盖

---

## 4. CI 接入（可选）

在 `.github/workflows/tech-graph.yml` **追加 step**（W5 维护者授权后）：

```bash
python3 scripts/graph_coverage_check.py || true   # 一期永不 fail job
```

或独立 workflow `tech-graph-coverage.yml` on `workflow_dispatch`。

---

## 5. task 字段建议

| 字段 | 值 |
|------|-----|
| `graph_change_layer` | `none` |
| `test_strategy_note` | 脚本单测 + 本地 warn 快照 |

---

## 6. 验收清单

- [ ] 脚本对当前仓运行产生 **预期 warn**（lc/lg 无 flow · chat 无 retrieve）
- [ ] W2/W1 完成后 rerun warn 数量下降
- [ ] 文档写明「warn ≠ CI fail」

---

## 7. 非范围

- 替代 `harness graph yaml check`
- 强制 PR fail（二期 `--strict`）
