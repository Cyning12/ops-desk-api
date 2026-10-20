# 40 审查：tech-graph-flow-resync 实施 diff（收官棒 5/5）

> **hat_id**：40（实施审查 · 只审不改）
> **审查对象**：分支 `task/tech-graph-flow-resync` · diff `35200d0..HEAD`（merge `9630d33` 带入文档线 + 实施 `47e51f6` · 7 文件 +207/-243 · 全链 12 文件全 docs/）
> **对照依据**：`docs/tasks/active/task_tech_graph_flow_resync.md`（闸全 approved）· SPEC v0 signed · `docs/harness/reviews/task_tech_graph_flow_resync_audit_R1_20261020.md`（R1 conditional_pass · N1–N4）· `docs/harness/invokes/by-task/tech-graph-flow-resync/invoke_20261020_30_implement.md`
> **审查日期**：2026-10-20 · **审查人**：Harness 40
> **结论**：**approve**（阻塞 0 · 非阻塞观察 O1/O2）
> **独立复验方式**：亲读 diff 全文 + graph.py/nodes.py 逐行对拍 + 重跑 `./scripts/graph-compile.sh` 与 `build_site.py` 幂等断言 + 生成物三件 grep + l2 yaml parse + 白名单 diff --stat（全部本窗实测，非转述 30 声称）

## 一、结论摘要

| 维度 | 裁定 | 摘要 |
|---|---|---|
| yaml 源 × 生成物一致性 | ✅ | 摘除面（s_intent 节点/START 边整块/出边/anchors 两块）与生成物 md/graph.json/site-data.json 同源派生；md 侧每处变更与 yaml 变更一一对应，无手改痕迹（TC1 幂等机断佐证） |
| 拓扑真值对拍 | ✅ | 新拓扑 START→strategy_builder→supervisor 对 `app/ops/lg_rag/multi/graph.py:96-104` 逐行命中（30 报 TC3 逐行命中，本窗独立复验全中） |
| D2-a 冻结声明 | ✅ | l2 两索引头注四要素齐；version `"2026-08-31"` 不 bump；s_intent dormant note 两处在册 |
| TC1 幂等独立复验 | ✅ | 重跑 compile EXIT=0；md+graph.json 逐字节零 diff；site-data.json 唯一 diff=generated_at 一行（豁免合理 · `build_site.py:557` 亲读核实） |
| 零 app/ 零 tests | ✅ | diff 12 文件全 docs/；app/tests/scripts/alembic 零改动；生成物旧拓扑串 grep 0 命中 |
| 挂账三件口径 | ✅ | sse_stream.py:63-66 死键 / __init__.py:5 docstring 原样在册未碰；l2 D2-b 扩面列移交——与 task D4 表述一致 |
| R1-N1/N2/N3 吸收 | ✅ | 基线钉 35200d0 · START 边整块 :494-499 摘除 · s_intent 行跨按实校正落 note |

## 二、逐项实证

### 1 · yaml 源 × 生成物一致性（委托要点 1）

- **yaml 源摘除面**（`10_flow_lg_rag.graph.yaml` diff 亲读）：s_intent 节点块（原 :159-165 七行含 implementedBy）· START→s_intent 边整块（原 :494-499，含 `from: "sup_graph"` 起 + to/label/anchors line:73）· s_intent→s_strategy_builder 出边块（label "intent dict" · anchor :74）· s_intent 两条 triggers/depends 边（原 :730-744 · acomplete_structured ::triggers + complete 细意图）——四块全部摘除，替换为新边 sup_graph→s_strategy_builder（label「START → strategy_builder（supervisor-first · 去前置 intent_node）」· anchor graph.py:96）。
- **生成物同源核验**：md diff 与 yaml diff 逐块对应（mermaid 节点行/边行/class 行/节点表/边表五面同步摘除与替换 · front-matter version 2026-10-14→2026-10-20 与 generated_at sha256 联动更新）；graph.json 同面镜像（freeze_id/generated_at 联动 `2746c8600a8addc6`）；site-data.json 镜像 graph.json + l2 note 透传（:6102/:6471 hunk）。**无手改 .md 痕迹**——TC1 幂等重跑逐字节一致是最强反证（见 §4）。
- python yaml parse：32 nodes / 56 edges · s_intent 节点/边零残留（`any(id=='s_intent')` / `from/to=='s_intent'` 均 False）· 新 START 边 anchor=`[{path: multi/graph.py, line: 96}]`——与 invoke 声称 32/56 一致。

### 2 · 拓扑真值对拍（委托要点 2 · graph.py:96-104 逐行）

| 行 | 代码（本窗 awk 实测） | yaml/md 对应 | 裁定 |
|---|---|---|---|
| :96 | `add_edge(START, "strategy_builder")` | sup_graph→s_strategy_builder · anchor :96 | ✅ |
| :97 | `add_edge("strategy_builder", "supervisor")` | allowed_capability_ids 边 · anchor :97 | ✅ |
| :98 | `add_edge("supervisor", "subtask_join")` | subtasks（≤4）边 · anchor :98 | ✅ |
| :99 | `add_conditional_edges("subtask_join", route_next_subtask, _DISPATCH_MAP)` | 三条 Send 分支边 anchor :99（×3）+ observe 分支 `_DISPATCH_MAP` | ✅ |
| :100-101 | `for name in _AGENT_NODES: add_edge(name, "subtask_join")` | 工人归并回 join 边 ×3 · anchor :100 | ✅ |
| :102 | `add_conditional_edges("observe", route_after_react, _REACT_MAP)` | observe replan/settle 边 · `_REACT_MAP` 引用 | ✅ |
| :103 | `add_edge("aggregator", "critic_node")` | 综合后进入 Critic 边 · anchor :103 | ✅ |
| :104 | `add_conditional_edges("critic_node", route_after_critic, _CRITIC_MAP)` | critic 三分支（pass/end→END · retry_planner · rebind）· anchor :104（×3） | ✅ |

三 MAP：`_DISPATCH_MAP` :53-60（:53 起 · observe :59）· `_REACT_MAP` :63-66（replan :64/settle :65）· `_CRITIC_MAP` :69-74（pass :70/retry_planner :71/rebind :72/end :73）——逐行在册。

nodes.py 符号锚（本窗 grep 实测 · 全部精确命中 def/调用行本身）：`route_next_subtask` :1339 · `rag_subtask_node` :1420 · supervisor `provider.complete` :1193（归属 supervisor_node :1125 起）· info_extract `provider.complete` :1529 · aggregator `complete_answer_streaming` :2147。R1 漂移清单五条（sup 边 / s_rag / s_supervisor complete / Send 边 / critic 回环）全部核销 ✔（TC3 ≥10 条 ±10 行要求——本窗实测 13 条全为精确行，零漂移）。

### 3 · D2-a 冻结声明（委托要点 3）

- 两索引头注各插五行冻结声明块（:5-9），四要素齐：**冻结日期**=version `"2026-08-31"` 维持原值不 bump（python parse 实测 version="2026-08-31" 两文件 · diff 中 version 行零触碰）· **覆盖边界**=截至 2026-08-31 implementedBy 面 + 显式缺口（Wave B run_worker.py/sse_subscribe.py · observe_node/_join_subtasks/_persist_hitl/_issue_plan · hitl 模块）· **冻结原因**=维护者 2026-10-19 D2-a 裁定 · **解冻条件**=SpecWave #40 落地或另行裁定 → D2-b 另案。
- s_intent dormant note 两处：by_path_lg_rag.yaml :202-206 条目（note 落 `kind: method` 后 · 覆盖 R1-N3 实跨 :197-200 全条目）· by_symbol_lg_rag.yaml :221-226 intent_node 条目——note 文案两文件逐字一致，含「保留未挂载 · 三图零挂载 · 承 01_modules.md:18」三要素。
- l2 两文件 python yaml parse OK（注释面改动不破坏 schema · note 字段随 build_site 透传 site-data.json 在册）。

### 4 · TC1 幂等独立复验（委托要点 4 · 本窗重跑）

```
$ ./scripts/graph-compile.sh  →  EXIT=0
  compile 9 图 OK（含 10_flow_lg_rag）· spec-wave@3.3.0 check l0/l1 全 OK
  [ok] mermaid normalize check: 9 md file(s)
$ git diff --exit-code -- 10_flow_lg_rag.md shared/graph.json  →  0（逐字节一致 · 无手改混入）
$ python3 docs/arch-browser/scripts/build_site.py  →  EXIT=0（freeze_id=2746c8600a8addc6_V1 · host_modules=34 graphs=9）
$ git diff -- dist/site-data.json  →  1 insertion(+), 1 deletion(-)：
  -  "generated_at": "2026-10-20T09:56:20Z",
  +  "generated_at": "2026-10-20T10:03:48Z",
```

**generated_at 时间戳豁免合理性**：`build_site.py:557` 亲读 `"generated_at": datetime.now(timezone.utc).strftime(...)`——墙钟时间戳为固有设计，非手改混入；幂等口径「无手改混入」成立（除该字段外逐键零 diff）。复验后已 `git checkout --` 还原，工作树干净（只审不改纪律）。

### 5 · 零 app/ 零 tests + 生成物 grep（委托要点 5）

- `git diff 35200d0..HEAD --stat`：12 文件全 docs/（图谱 6 + invoke 4 + R1 审查文 1 + task 1）；`-- app/ tests/ scripts/ alembic/` 空 diff ✔。
- 生成物三件 grep `START → intent_node`：**0 / 0 / 0 命中** ✔；yaml+md grep `s_intent`（排除新边 label「去前置 intent_node」）零残留 ✔；site-data.json `s_intent` 2 命中 = l2 dormant note 透传（有意保留）✔。
- D3 全仓 grep 命中 15 文件全落豁名单（tasks/done 两件 · GUIDE:17 · ROADMAP:123 · 旧 SPEC/SPEC 自引 · reviews/invokes 历史记录与自引 · task 自引）——**名单外现行文档零命中**，D3 空转口径诚实 ✔。

### 6 · 挂账三件口径（委托要点 6）

| # | 残留 | 本窗实证 | 移交表述一致性 |
|---|---|---|---|
| 1 | `sse_stream.py:63-66` `_ROLE_ALIAS` :64 `"intent_node": "intent"` 死键 | sed :60-68 原样在册 · diff 零触碰 | 与 task D4 表第 1 行 + invoke §七.1 一致 ✔ |
| 2 | `multi/__init__.py:5` docstring 旧拓扑「START → intent_node → strategy_builder → supervisor」 | sed :1-8 逐字在册 · diff 零触碰 | 与 task D4 表第 2 行 + invoke §七.2 一致 ✔ |
| 3 | l2 D2-b 扩面（run_worker.py/sse_subscribe.py/后期四符号/hitl 模块） | 未做（冻结声明解冻条件指向另案） | 与 task 非范围 ③ + invoke §七.3 一致 ✔ |

### 7 · R1-N1/N2/N3 吸收落实（委托要点 7）

- **N1 基线钉锚**：invoke 基线段钉 `35200d0`（非 task 文 `c17e63b`）· 锚点核销全对拍 35200d0 亲读——吸收 ✔。
- **N2 START 边整块**：摘除按整块 :494-499（`from: "sup_graph"` 起 · 含 anchors :497-499 两行）处理 + 出边块一并摘除——diff 实证整块移除 ✔。
- **N3 l2 s_intent 行跨**：by_path 实跨 :197-200（`kind: method` :200）→ note 落其后（现 :202-206 条目完整覆盖）· by_symbol 实跨 :216-219 → 现 :221-226 覆盖——按实跨落 note ✔。

## 三、阻塞项

**无（阻塞 0）。**

## 四、非阻塞观察

| ID | 内容 | 处置建议 |
|---|---|---|
| O1 | TC8 要求 invoke 落「重生成时点 commit hash」：invoke 钉的是基线 `35200d0`（本 task 为 docs-only diff，app/ 面与 `47e51f6` 逐字节一致，作漂移判定基准等价有效），未字面落实施 commit `47e51f6` | 00 收口 invoke 或 PR 描述补记 `47e51f6` 为重生成落盘点即可，不阻塞合并 |
| O2 | site-data.json 顺带带入 rag/memory/lg_rag 三模块 note 更新（api-embedder-internal-batching · memory-injection-consumer ④b · supervisor-first-fail-closed 等基线前已合并条目）——实证：note 源自 `01_modules.md`（build_site.py:385-409 解析面 · 基线 35200d0 已含这些条目），前一版 site-data.json 生成于 2026-10-17T02:15:26Z 滞留未追平；本次重生成属合法派生追平，非手改、非越面（TC1 幂等复验佐证：重跑后唯一 diff=generated_at 一行） | 记录在案：FP-7「生成物 diff=拓扑修正面」口径本次含「输入滞留追平」分量；后续 task 若求 site-data.json 最小 diff，可在实施前先单独重跑 build_site 追平基线 |

## 五、复验数字汇总（报 00 口径）

- graph-compile 尾部：compile 9 图 OK · check l0(1)+l1(8) 全 OK · mermaid normalize 9 md OK · **EXIT=0**
- 幂等 diff：md + graph.json 逐字节 0 diff；site-data.json 1 行（generated_at 豁免 · build_site.py:557 固有设计）
- 生成物旧拓扑串 grep：`START → intent_node` 0/0/0 命中（md / graph.json / site-data.json）
- 拓扑对拍：graph.py :96-104 八行 + 三 MAP :53/:63/:69 逐行命中 · nodes.py 五符号锚（:1339/:1420/:1193/:1529/:2147）精确命中 · 13 锚零漂移
- 白名单：12 文件全 docs/ · app/tests/scripts/alembic 零改动
- yaml parse：32 nodes / 56 edges / s_intent 零残留 / 两 l2 索引 version="2026-08-31" 未 bump

## 修订记录

| 日期 | 摘要 |
|---|---|
| 2026-10-20 | 40 审查：**approve**（阻塞 0 · O1/O2 非阻塞）；七大委托要点全过；TC1 幂等独立复验 PASS；拓扑逐行对拍 13 锚零漂移；挂账三件口径一致；R1-N1/N2/N3 吸收实证在册 |
