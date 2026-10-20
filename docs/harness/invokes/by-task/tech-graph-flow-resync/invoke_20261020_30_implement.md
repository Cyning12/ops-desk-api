# invoke：tech-graph-flow-resync · 30_implement · 2026-10-20

- **hat**：30（改码实施 · 本 task 纯 docs · 零 app/ 零 tests 铁律）
- **task**：`docs/tasks/active/task_tech_graph_flow_resync.md`（draft v0.1 · HG-SPEC-SIGNOFF=approved · HG-AUDIT-R1=approved 00 代签 · HG-GRAPH-MODULES=approved · graph_change_layer=docs）
- **基线钉锚（R1-N1 吸收）**：task 文原写 master tip `c17e63b`；亲读实测 master tip=`35200d0`（R1 后新增合并所致基线漂移）→ 以 `35200d0` 为实际基线
- **分支**：`task/tech-graph-flow-resync` 自 `35200d0` 切出；`docs/task-tech-graph-flow-resync`（tip `c9df67f` · task+R1 审查文+invokes 三件）以 `git merge --no-ff` 并入（承 #1–#4 先例：docs 线并入 task 分支同 PR 全链）→ merge commit `9630d33`；切分支前核 `git status` 干净（共享工作树纪律）

## 一、开工闸核验（真值在 task 闸表 · 非聊天字面）

| 闸 | 状态 | 依据 |
|---|---|---|
| HG-SPEC-SIGNOFF | approved | task 闸表 |
| HG-AUDIT-R1 | approved（00 代签 · N4 收窄已确认） | task 闸表 + invoke_20261020_gate_sign_hg_audit_r1.md |
| HG-GRAPH-MODULES | approved | `docs/_tech_graph/l1/01_modules.md` |
| 阻塞项 | 0 | R1 审查文 conditional_pass · 阻塞 0 |

## 二、R1-N1–N3 吸收实录

| 移交项 | 吸收 |
|---|---|
| N1（开工 invoke 钉实际基线） | 本文件基线钉锚段：`35200d0`（非 task 文 `c17e63b`） |
| N2（START 边整块含 anchors :497-499 · 边块实起 :494） | D1 摘除按整块 :494-499（`from: "sup_graph"` 起 · 含两 anchor 行）处理；出边块 :501-506 一并摘除；替换为新边 sup_graph→s_strategy_builder（anchor `multi/graph.py:96`） |
| N3（l2 s_intent 实跨坐标） | by_path_lg_rag.yaml 实跨 :197-200（四行含缩进尾行）· by_symbol_lg_rag.yaml 实跨 :216-219——按实跨落 dormant `note` 字段 |

## 三、D1–D4 实施实录

### D1 拓扑重画（真值面 = `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml`）
- version `"2026-10-14"` → `"2026-10-20"`
- description 追加：「2026-10-20 supervisor-first 图谱重同步（PR #282 · task tech-graph-flow-resync）：supervisor 图实际拓扑 START → strategy_builder → supervisor → subtask_join（Send 分发）→ observe → aggregator → critic_node（去前置 intent_node）；IntentV1 保留未挂载（dormant · app/ops/strategy/intent.py:52 intent_node 在册 · 代码保留不删 · 承 01_modules.md:18 legacy/dormant 一律不删约定）」
- 摘除：s_intent 节点块（原 :159-165）· START→s_intent 边整块（原 :494-499）· s_intent 出边块（原 :501-506）· s_intent anchors 两块（原 :730-744）
- 新增边：sup_graph→s_strategy_builder · label「START → strategy_builder（supervisor-first · 去前置 intent_node）」· anchor graph.py:96（对拍 `multi/graph.py:96` `add_edge(START, "strategy_builder")` 亲读在册）
- 锚点核销（旧→新 · 全对拍 35200d0 亲读）：75→97 · 76→98 · 42/43/44→99（dispatch Send×3）· nodes.py 238→1339（×3）· multi/graph.py 78→100（工人回环×3 · `app/ops/lg_rag/graph.py` 同名 line:78/:79 router 图锚未动）· 79→103 · 80→104 · 51→104 · 52→104 · 266→1420 · 200→1193 · 299→1529 · 361→2147
- 拓扑校验：python yaml parse 32 nodes / 56 edges / s_intent 零残留
- 重跑链：`./scripts/graph-compile.sh` EXIT=0（compile 9 图 OK · spec-wave@3.3.0 check 全 OK · mermaid normalize check-only OK）→ `python3 docs/arch-browser/scripts/build_site.py` EXIT=0；生成物三件（10_flow_lg_rag.md · shared/graph.json · dist/site-data.json）重生成覆盖

### D2-a 冻结声明（l2 两索引 · 重生成禁做）
- 两文件头注各插冻结声明四要素注释块：**冻结日期**=version `"2026-08-31"` 维持原值不 bump（声明走注释不动 version 字段）· **覆盖边界**=截至 2026-08-31 的 implementedBy 面 + 显式缺口（Wave B run_worker.py/sse_subscribe.py · observe_node/_join_subtasks/_persist_hitl/_issue_plan · hitl 模块）· **冻结原因**=维护者 2026-10-19 D2-a 裁定（索引维护成本高、审核引用少 · SpecWave #40 未落地）· **解冻条件**=#40 落地或维护者另行裁定 → 走 D2-b 另案
- s_intent 条目各加 `note` 字段标 dormant（`note` 字段有 chat 侧先例 schema 兼容）；l2 重生成禁做（仅头注+note 注释面）

### D3 现行文档面（R1 空转实证确认）
- 全仓 `grep -rn "START → intent_node" docs/`：命中 = 历史文档豁名单（tasks/done 两件 · GUIDE:17 · ROADMAP:123 · 旧 SPEC · SPEC 自引 · reviews/invokes 历史记录 · task 自引）+ 生成物三件（重生成后 **0 命中**）；**名单外现行文档零命中**——D3 面实测空转，与 R1 实证一致；TC7 按「（可选）空转」口径诚实表述，历史豁名单按「标注历史版本归属」不追溯改写

### D4 移交挂账（维持不动 · 零 app/ 铁律）
- `app/ops/lg_rag/sse_stream.py:63-66` `_ROLE_ALIAS` :64 `"intent_node": "intent"` 死键——dormant 死键 · 零行为 · 不删（承 01_modules.md:18 一律不删约定 · 移交后续 app 面 task）
- `app/ops/lg_rag/multi/__init__.py:5` docstring 旧拓扑——注释-only 修正移交后续 app 面 task（与同包 graph.py:82 注释冲突在册）

## 四、TC 逐项（全机断 · FP-4）

| TC | 断言 | 结果 |
|---|---|---|
| TC1 | 重跑 graph-compile 幂等：三件生成物与首次重生成快照逐字节一致 | **PASS**（md · graph.json 字节一致；site-data.json 唯一 diff=顶层 `generated_at` 时间戳（build_site.py:557 固有设计 · datetime.now UTC），逐键 walk 确认除该字段外零 diff——时间戳非手改，幂等口径=无手改混入成立） |
| TC2 | graph-compile EXIT=0 + 三重生校验 | **PASS**（compile 9 图 OK · check 全 OK · mermaid normalize `[ok] mermaid normalize check: 9 md file(s)` · EXIT=0） |
| TC3 | supervisor 图拓扑与 `multi/graph.py:96-104` 一致 | **PASS**（新边 label START → strategy_builder anchor :96；全图 32 nodes/56 edges parse 通过；亲读 :96-104 逐行对拍命中） |
| TC4 | intent dormant 三面一致 | **PASS**（yaml s_intent 节点/边/anchors 摘除 + description dormant 说明段指向 intent.py:52；生成物 md grep `START → intent_node` 0 命中；l2 两索引 s_intent 条目 `note` dormant 在册） |
| TC5 | 生成物三件旧拓扑串零命中 | **PASS**（10_flow_lg_rag.md:0 · graph.json:0 · site-data.json:0） |
| TC6 | 零 app/ 零 tests 改动 | **PASS**（`git status --short` 仅 docs/ 六件 + 本 invoke；app/、tests/ 零触碰；sse_stream.py:64 死键与 __init__.py:5 docstring 原样在册） |
| TC7 | D3 现行文档面修正 | **PASS（空转 · 诚实表述）**（名单外现行文档零命中；历史豁名单不追溯改写） |
| TC8 | 改动面白名单内 | **PASS**（改动 = 10_flow_lg_rag.graph.yaml · 10_flow_lg_rag.md · by_path_lg_rag.yaml · by_symbol_lg_rag.yaml · graph.json · site-data.json · 本 invoke · docs 线并入三件——全白名单） |

## 五、验证输出尾部

```
$ ./scripts/graph-compile.sh（末行摘录）
[custom] generating shared/graph.json from yaml sources (recursive)
generated docs/_tech_graph/shared/graph.json: 9 graphs, 142 nodes, 207 edges
  freeze_id=OPS_DESK_API_TECH_GRAPH_FREEZE_2746c8600a8addc6_V1
[spec-wave@3.3.0] checking graph consistency
  check --input docs/_tech_graph/l0 → OK: 00_main
  check --input docs/_tech_graph/l1 → OK × 8（含 10_flow_lg_rag）
[normalize] guard: verify mermaid fences (check-only, no rewrite)
[ok] mermaid normalize check: 9 md file(s)
done   （EXIT=0）

$ npx --yes spec-wave@3.3.0 task lint-wiki-delta --target .
scope: all · scanned: 190 · strict: false · missing: 0 · issues: 0
LINT-WIKI-DELTA: PASS   （EXIT=0）
```

ruff 不涉及（零 app/tests 改动 · 与 task 预跑面一致）。

## 六、裁定链与纪律

- 基线漂移（c17e63b→35200d0）：按 R1-N1 钉实际基线 · 未越权改 task 文本
- 枚举外冲突：无（全程未触发 STOP；未新发现枚举外冲突项）
- 共享工作树纪律：切分支前 `git status` 干净核验在册；本窗零并发切树
- 代签纪律：零代签；HG-AUDIT-R1 沿用 00 代签既有 approved

## 七、遗留挂账（移交后续 app 面 task · 本 task 不收口）

1. `app/ops/lg_rag/sse_stream.py:63-66` `_ROLE_ALIAS` `"intent_node": "intent"` 死键（dormant · 零行为 · 不删）
2. `app/ops/lg_rag/multi/__init__.py:5` docstring 旧拓扑（注释-only 修正移交）
3. l2 索引 D2-b 扩面（run_worker.py/sse_subscribe.py/observe_node/_join_subtasks/_persist_hitl/_issue_plan/hitl 模块）——待 SpecWave #40 落地或维护者裁定后另案
