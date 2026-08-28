# Task：Strategy Builder S3 · Catalog manifest YAML

> **状态**：completed（2026-08-28 · 00 机械验收 PASS）  
> **类型**：feature / strategy-and-intent · S3  
> **上游规划**：`docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md` §6  
> **ROADMAP**：`docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md` §5 / §8  
> **前置**：S1 [#78](https://github.com/Cyning12/ops-desk-api/pull/78) · S2 [#80](https://github.com/Cyning12/ops-desk-api/pull/80) MERGED  
> **分支**：`task/catalog-manifest-yaml`  
> **无关**：勿与 `task_ops_sync_sender_migration` · `task_rag_answer_mixed_evidence` · `task_retrieval_longquery_analysis` 混改；禁止改 `chat/graph.py` 拓扑；禁止 Agently；禁止动态 compile；禁止把 Host 校验做成模型可选 tool。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `catalog-manifest-yaml` |
| **git_branch** | `task/catalog-manifest-yaml` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | fixture YAML/JSON load → register；非法 adapter 整文件失败；无密钥；defaults 幂等 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_capability.graph.yaml` |
| **graph_delta_note** | `capability` 行备注：manifest 加载；不新增一级模块；**不**改 lg_rag 图拓扑 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约在 spec/agent-infra；无 coding_wiki 条文变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | strategy-and-intent 第三棒 = S3 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-28 · **00 代签 · 维护者会话授权续 S3**（R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-28 · **00 代签** · 见 `docs/harness/reviews/task_catalog_manifest_yaml_audit_R1_20260828.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅 G-L1 `capability` 备注 + flow；不新增一级模块 · **00 代签** |

---

## 背景与目标

目录仍写死在 `defaults.py`。S3 让 Host 从 YAML/JSON manifest **register**；Builder 仍只裁剪。defaults 迁为「内置 manifest 优先 + 硬编码 fallback」。

---

## 范围 / 非范围

**范围（S3-a–b）**：

- **S3-a**：`load_capability_manifest(path)` → Host `register`；builtin YAML 对齐三枚默认 local_fn；`ensure_default_capabilities` 优先 load builtin
- **S3-b**：manifest `version` + `capability_manifest_count` metadata；显式 `reload_capability_manifest`（测试/运维）；**不**每请求加载
- adapter 白名单；非法整文件失败；无密钥进仓
- 单测 + G-L1 capability 备注 + `10_flow_capability` + graph-compile + ruff

**非范围**：

- S4 Critic · Eval · Skill 引擎  
- 改 supervisor / router / `chat/graph.py` 拓扑  
- 从 YAML 注册 MCP/sandbox/cli  
- 请求路径热加载 / 动态 compile  

### 00 定夺（摘 ROADMAP §8）

| 项 | 值 |
|---|---|
| kind | 仅 `local_fn` |
| adapter | `local_fn:app.ops.capability.defaults:<attr>` 仅此前缀 |
| 失败 | 整文件失败（不半套注册） |
| 热加载 | 禁止每请求；显式 reload 可测 |

### 实现落点

- `app/ops/capability/manifest.py`  
- `app/ops/capability/manifests/builtin.v1.yaml`  
- `app/ops/capability/defaults.py`（ensure 接 loader）  
- 可选 GUIDE 一行指针回 ROADMAP §8  

---

## 验收标准

- [x] S3-a：fixture YAML/JSON load 后 `list_capabilities` 含声明 id；builtin 与 `utc_now_iso` 等三枚对齐
- [x] S3-a：非法 adapter / 非白名单 module / 非 local_fn → **整文件失败**，不留下半套
- [x] S3-a：`enabled: false` 跳过；无密钥字段
- [x] S3-a：`ensure_default_capabilities` 幂等（YAML 优先，缺文件回退硬编码）
- [x] S3-b：load 暴露 version + count；显式 reload 可测；无 HTTP/每请求钩子
- [x] G-L1 `capability` 备注 + flow + graph-compile
- [x] ruff / pytest 触及路径绿；`chat/graph.py` 与 lg_rag 图拓扑零 diff

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 非法 adapter / 未知 kind | 整文件失败，已注册条目不因本文件部分成功 | N |
| builtin YAML 缺失 | 回退 `_DEFAULT_SPECS` | N |
| 重复 id | 沿用 registry：已存在 skip 或 ValueError（与现 `register` 一致；ensure 路径 skip） | N |
| YAML 含密钥形字段 | 禁止进仓；loader 不读 env 密钥 | N |

---

## test_strategy

```text
required · fixture YAML/JSON · 无外网
pytest：manifest loader / defaults 幂等 / 非法 adapter
ruff 触及路径
./scripts/graph-compile.sh
chat/graph.py 与 multi/graph.py 拓扑 0 diff
```

---

## 自检结论

> 2026-08-28 · 00 机械复检 · **PASS**

- [x] 验收勾选 S3-a–b
- [x] pytest 触及路径 63 passed（1 skipped · langchain.debug smoke 非本棒）
- [x] ruff 0 · graph-compile exit 0 · `chat/graph.py` 与 `multi/graph.py` 零 diff

**50 结论**：PASS · 下一棒 S4 `critic-rebind`（非本轨除非维护者另开）

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-28 |
| 定稿 | Host YAML/JSON manifest → register；builtin 优先；adapter 白名单 |
| 归档 | `docs/tasks/done/task_catalog_manifest_yaml.md` |
| PR | 待开（本分支） |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 00 拆 S3 task · R1 pass · HG 代签 |
| 2026-08-28 | 30/40 PASS · 00 机械验收 PASS · CLOSE |
