# invoke：arch-browser-wave5-sync · docs_sync · 2026-10-20

- **角色**：docs 子 Agent（委派制 · 非 30 改码帽 · 纯 docs 面）
- **变更请求来源**：维护者变更请求（父会话 m00670）——五棒波次（#2 memory-injection-consumer · #3 scenario-stage-rewire · #4 delegation-naming-boundary · #5 tech-graph-flow-resync）全 merged 后，同步 docs/arch-browser 人维目录至真值
- **分支**：`docs/arch-browser-wave5-sync` 自 master `96251c7` 切出（切前 `git status` 干净）
- **铁律**：零 app/ 零 tests 零 scripts 改动（build_site.py 只跑不改）

## 一、三处裁定落点（docs/arch-browser/catalog/crosswalk.yaml）

| host | 位置 | 改动 | 裁定依据 |
|---|---|---|---|
| 3 可见集两阶段 | :30-38 | gap_summary 空 → 「scenario stage 已摘除（2026-10-20 #3 · scenario.py dormant 保留 · 可见集两阶段真值走 lg_rag visibility）」；status 维持 **已落地**（概念仍成立 · 实现路径变了）；paths 不动（scenario.py 文件仍在） | #3 scenario stage 恒短路摘除（builder 三处）· scenario.py 本体 dormant 保留 |
| 9 记忆管理 | :91-99 | gap_summary「情景/事实已有默认关」更正为「注入面已休眠（2026-10-20 #2 ④b 裁定 · 实证三模式零消费 · 真构建走 DEF-005 另案）；跨进程记忆 D3 属 v2.0」；status 维持 **部分** | #2 Phase A 实证三模式 9 消费点全零收到注入块 → ④b 全模式收窄+功能休眠 · 对接 docs/tasks/deferred/task_memory_facts_build_4a.md（DEF-005） |
| 15 意图解析 | :151-159 | status **已落地 → 部分**；gap_summary 空 → 「supervisor 拓扑已摘除 intent 节点（2026-10-20 #3 摘除 + #5 dormant 标注 · intent.py:52 留尸不删）；恢复/重接需另案」 | #3 intent_node 未挂载（supervisor 拓扑 START→strategy_builder · graph.py:96-104）+ #5 s_intent 标 dormant · intent.py:52 存在但留尸不删 |

## 二、生成物重跑与核验实录

- `python3 docs/arch-browser/scripts/build_site.py` EXIT=0（freeze_id=OPS_DESK_API_TECH_GRAPH_FREEZE_2746c8600a8addc6_V1 · host_modules=34 graphs=9 · 脚本零改动）
- `dist/site-data.json` diff：**7 行增 7 行删**，全部 catalog 派生段 + 顶层 `generated_at` 时间戳（09:56:20Z → 10:16:06Z · build_site.py 固有设计）：
  1. host 3 future_gap 新注（:287）
  2. host 9 future_gap 更正（:587）
  3. host 15 status/status_raw 已落地→部分 + future_gap 新注（:820-821, :839）
  4. concept_mermaid class 行派生变化：INTENT 自 ok 组移入 partial 组（host 15 status 派生）
- **host_outline.json / home_narrative.json 实测无需改**：两文件仅含概念层 slug/标题/分层（host_outline.json:46/:52/:69 · home_narrative.json 场景叙述），无 status/gap/拓扑具体陈旧——核验 grep（intent|scenario|记忆|注入）命中均为概念名与叙述层，非真值漂移面
- **#5 新拓扑核验**（dist/site-data.json）：
  - `START --> intent_node` / `START → intent_node`：**0 命中**
  - `START → strategy_builder` / `START-->strategy_builder`：**2 命中在册**（含 label「START → strategy_builder（supervisor-first · 去前置 intent_node）」）
  - 残留 6 处 `intent_node` 均为 dormant 语义（symbol 索引 ×2 · 休眠标注 dict ×2 · 说明文字 ×2），非 START 边

## 三、纪律核验

| 项 | 结果 |
|---|---|
| 改动面 | `git status --short`：仅 crosswalk.yaml + dist/site-data.json + 本 invoke——白名单内 |
| app/ tests/ scripts/ | 零触碰 |
| 生成物 diff 范围 | 仅 catalog 派生段 + generated_at，无手改混入 |

## 四、遗留

- host 15 恢复/重接 intent 节点需另案（invoke 已载明）
- host 9 记忆真构建走 DEF-005 另案（docs/tasks/deferred/task_memory_facts_build_4a.md）
