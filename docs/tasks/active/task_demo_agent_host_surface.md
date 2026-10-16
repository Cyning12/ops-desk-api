# Task：demo-agent-host-surface（三方演示 · 展示面收敛 · 侧栏与 arch-browser 对外只讲 Agent Host）

> **状态**：**全链 CLOSE · TC-1–TC-8 全 ✅** · api 面 TC-1/2/3/4/6/7 ✅（2026-10-16 00 窗）· web 面 TC-5 ✅（ops-desk-web PR #70 已并 main · squash `44a77db` · CI 双绿）· 人工闸 **approved（维护者授权 00 代签）**
> **类型**：演示展示面（名实分离 · 只藏不改约 · 双仓）
> **依据**：维护者演示指令（2026-10-16 · 00 窗 prompt）：三方演示对外只讲 Agent Host 能力；展示名裁定 **已锁**（见 D1）
> **分支**：`task/demo-agent-host-surface`（**待切** · 当前窗在 `task/arch-browser-eng-graph-mermaid` 且该分支有 arch-browser 未提交改动，30 开工前须先厘清基线，勿混 PR）
> **跨仓**：web 面在 **ops-desk-web** 仓实现（另开同名分支 + 独立 PR · 本 task 写明范围）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `demo_agent_host_surface` |
| **git_branch** | `task/demo-agent-host-surface`（api 仓）· web 仓同名分支另开 |
| **implement_repo** | `ops-desk-api`（arch-browser 展示文案）+ `ops-desk-web`（侧栏/页标题/落地页 · 独立 PR） |
| **test_strategy** | `required` |
| **test_strategy_note** | 不改业务逻辑故无新红测；验收以 grep 级展示面断言 + `build_site.py` 重建 + 既有 pytest/web 测试零回归 |
| **code_quality_bar** | `L2_backend`（api 触及处） |
| **graph_change_layer** | `n/a`（**不**增删 `_tech_graph` 真值行；隐藏只发生在演示视图。30 若触碰图谱行 → 升判 G-L1 并补 HG-GRAPH-MODULES） |
| **graph_delta** | `n/a`（`graph-compile.sh` EXIT=0 作零 diff 证据） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 00 起草壳（2026-10-16）→ **10-task** 落稿（填 R 轮/校锚点/拟 SPEC 修订文）→ 20 R1 → 维护者签 HG-TASK-DRAFT + HG-AUDIT-R1 → 30（api 先，web 另 PR）→ CLOSE |
| **freeze_id** | `n/a`（**禁**触碰 `lg-rag-sse-v1` 及任何 freeze；SSE 帧/事件类型零 diff） |
| **related_tasks** | `n/a`（与 `lg_rag_sse_*` / `hitl_*` active task **零耦合**；不改不关不并入） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved**（00 代录 2026-10-16） | 20, 30 | 维护者本窗指令「授权00签收并完成任务」→ 00 代签 |
| HG-AUDIT-R1 | **approved**（00 代录 2026-10-16） | 30 | 同上授权；20 R1 审查结论并入 30 invoke |

### 维护者裁定口

| 裁定 ID | 选项 | 状态 | 说明 |
|---------|------|------|------|
| **D1 展示名** | — | **已锁（维护者 2026-10-16）** | 原侧栏「LG RAG」→「**Agent 工作台**」；arch-browser 入口层对外文案「**Agent 工作台**（SSE 流式运行）」；arch-browser 对照展示**不出现** lg-rag 等有歧义命名。**10 不得重开** |
| **D2 深链** | 拦截 / 保留路由 | **已定：保留路由、只藏菜单**（维护者默认） | `/chat` `/lc-evidence` 深链不拦截；10 写入非范围 |
| **D4 工作台路由指向** | — | **已锁（维护者 2026-10-16 修正裁定，优先于 D1 字面假设）** | 「Agent 工作台」= lg-rag **直接对话页** = `/chat`（ChatView · lg-rag SSE · HitlApprovalCard · thinking/subtasks 过程输出）；`/lg-rag`（LgRagView mode 选择调用页）**退出菜单**、meta.title 恢复 'LG RAG'（路由保留）；默认落地页 redirect → `/chat`。web PR #71 落地（squash `46c8c54`）。原假设「/chat=legacy Chat」被实测推翻：/chat 早已切 lg-rag SSE 主线（T6 后旧 chat SSE 已删） |
| **D3 SPEC 修订方式** | 改正文+修订记录 / ERRATA | **已定：改正文+修订记录（已落盘）** | SPEC-arch-browser §1 设计纪律 3 已修订 + §7 修订记录 2026-10-16 行（见 30 invoke 互链） |

---

## 背景与目标

三方演示只讲 Agent Host 能力。观众不应在产品侧栏或架构浏览器首页看到旧栈名字（lg-rag / LG RAG / LC Evidence / legacy Chat）。**名实分离**：展示层改名/隐藏，业务契约（HTTP 路径、freeze、包名、表名、模块 id、图谱真值）一律不动。

## 范围

### A · ops-desk-api（本仓 · arch-browser 展示面）

- **A1 首页叙事**：`docs/arch-browser/catalog/home_narrative.json`（one_liner「执行面（lg-rag supervisor）」、名实分离段「HTTP / freeze 传输壳仍可叫 lg-rag」→ 对外改写为 Agent Host 叙事；传输壳字样撤下首页）
- **A2 入口层 E1**：`docs/arch-browser/catalog/host_outline.json`（title「入口层 · SSE/HTTP lg-rag」、note「传输壳仍叫 lg-rag」、N0 叙事条 → 对外文案「Agent 工作台（SSE 流式运行）」）
- **A3 演示视图隐藏**：`docs/arch-browser/scripts/build_site.py`（mermaid label map 的「Chat flow」「LC Evidence」「Chat 路由（legacy）」、class 行含 chat_flow/lc_evidence_flow）+ `docs/arch-browser/web/app.js`（node→route map）→ 演示视图（首页/概念图/工程图**演示标签**）过滤 Chat 流、LC Evidence 流；**工程钻取真值层**（`_tech_graph` 源与 crosswalk 行）不删不改
- **A4 重建**：`python3 docs/arch-browser/scripts/build_site.py` → `dist/` 重生成；新旧不混杂
- **A5 SPEC 修订**：`docs/spec/arch-browser/SPEC-arch-browser_v0.md` §1 设计纪律 3 显式修订（D3 方式）+ 修订记录/ERRATA
- **A6 落 task**：10 填 R0–R5、校对锚点行号、补验收证据位

### B · ops-desk-web（跨仓 · 另 PR）

- **B1 侧栏**：`src/layouts/AppLayout.vue` 菜单隐藏 `/chat`、`/lc-evidence`；「LG RAG」→「Agent 工作台」（菜单项、页标题）
- **B2 默认落地页**：改为 Agent 工作台（原默认落地点 30 按 web 仓路由现状裁定并记录）
- **B3 不删码**：Chat / LC Evidence 路由与组件保留（D2），仅菜单不出现

## 非范围

- **改业务契约**：HTTP 路径（`POST /api/ops/lg-rag/stream` 等）、freeze id、Python 包 `app/ops/lg_rag`、表名、模块 id `lg_rag` 一律不改名
- **删真值**：`docs/_tech_graph` 的 chat / lc_evidence_chain / lg_rag 行不删不改；crosswalk 真值行不动
- **删 Chat / LC Evidence 路由与代码**（双仓）；**深链拦截**（D2=保留路由只藏菜单）
- **改执行语义 / SSE 帧 / 鉴权**；触碰任何 freeze
- **改单测**（除 30 判定必须新增的展示面断言外，既有测试零改动）
- **动其他 active task**（`lg_rag_sse_*`、`hitl_*` 等）的码、文档与状态
- **混入 `task/arch-browser-eng-graph-mermaid` 分支的未提交改动**（该分支同文件脏树与本 task 隔离，30 开工前先确认基线）
- iOS、部署/Nginx 公开面（arch-browser W2 另题）

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 把「隐藏」做成「删真值」（删图谱行/路由/代码） | 20/30 纪律拦截；revert；真值层零 diff 作验收 | 是 | 工程钻取层断链 |
| FP-2 误改 HTTP 路径 / freeze / 包名 / 表名 | 契约破坏；既有 pytest / 集成红 | 是 | API 4xx/5xx · 演示翻车 |
| FP-3 静默绕过 SPEC 冲突条款（不改 SPEC 直接改文案） | 10/20 拦：须 D3 显式修订落盘后再动文案 | 是 | 过程不合规 |
| FP-4 `dist/` 未重建或新旧混杂 | A4 验收重跑 build_site.py；grep `dist/` 无旧名 | 是 | 首页仍见旧栈名 |
| FP-5 深链被拦（超 D2） | 非范围钉死；路由可达性抽查 | 是 | 既有书签/链接 404 |
| FP-6 跨仓漏改（api 已藏、web 菜单仍见旧名） | 验收双仓分列；CLOSE 前 web PR 须绿 | 是（web） | 侧栏穿帮 |
| FP-7 闸未签即 30 / 混入 eng-graph-mermaid 脏树 | GATE_VERIFY 拒开工；分支基线核对 | 是 | — |

---

## 验收标准

- [x] **TC-1 首页/入口层无旧名**（2026-10-16 PASS）：dist/site-data.json 演示面载体（home_narrative / entry_outline / waves / concept_mermaid / eng_l0_mermaid / host display.* / titles）零命中 lg-rag·LG RAG·LC Evidence·legacy Chat；dist/index.html CLEAN。**例外清单（名实分离 · 保留真值 id）**：① mermaid click/chip href `#/eng/10_flow_lg_rag` 等指工程钻取层；② dist/app.js 过滤代码键名含真值 id；③ 真值字段 graphs/eng_modules/tech_to_host/tech_module_hints 与 host_modules 真值子字段（lg_rag×29）属钻取真值，非演示标签
- [x] **TC-2 对照展示无歧义命名**（2026-10-16 PASS）：host 对照卡 display.one_liner / waves N0 / 概念图 E1 / eng L0 演示标签均为 Agent 工作台口径（D1）
- [x] **TC-3 重建可复现**（2026-10-16 PASS）：`python3 docs/arch-browser/scripts/build_site.py` EXIT=0；dist/ 全新生成（host_modules=34 · graphs=9 · concept 3540ch · eng_l0 2603ch · freeze 20261014_V1）
- [x] **TC-4 SPEC 显式修订**（2026-10-16 PASS）：SPEC-arch-browser_v0.md §1 纪律 3 改正文 + §7 修订记录 2026-10-16 行；invoke_20261016_30_impl.md 互链；非静默
- [x] **TC-5 web 侧栏（web 仓 PR）**（2026-10-16 PASS）：ops-desk-web **PR #70** 已并 main（squash `44a77db` · CI frontend/check 双绿）——菜单无 Chat / LC Evidence（`src/layouts/AppLayout.vue` 仅藏菜单项，路由与组件保留 · D2 深链不拦截）；「Agent 工作台」入菜单与页标题（页标题真值=route.meta.title）；默认落地页根路径 redirect `/overview`→`/lg-rag`（`src/router/index.ts:23`）；`pnpm lint`/`pnpm test`（31 文件 263 测试全过 · 零测试改动）/`pnpm build` 全绿；diff 仅 2 文件 +6/-5。**维护者修正裁定（D4 · 2026-10-16）**：PR #70 误把 Agent 工作台挂 /lg-rag（mode 选择页）→ **PR #71**（squash `46c8c54` · CI 双绿）纠正：菜单/页标题/默认落地全部改指 `/chat` 直接对话页；`/lg-rag` 退出菜单、meta.title 恢复 'LG RAG'（路由全保留 · 零测试改动 · lint/test(263)/build 全绿）。**残留决策点（另裁，未动）**：登录流程两处落地仍指 `/overview`（router 守卫被既有测试断言卡住 · LoginView fallback 超 diff 白名单）
- [x] **TC-6 零契约回归**（2026-10-16 PASS）：本 task `app/` 零 diff（git status 佐证）；HTTP 路由 / freeze / SSE 帧 / 表名 / 模块 id 均未触碰；pytest 无触及面（纯 docs/arch-browser 展示面改动）
- [x] **TC-7 真值零删**（2026-10-16 PASS）：`docs/_tech_graph` 各行未改；`./scripts/graph-compile.sh` EXIT=0（仅 pre-existing warning）；**注意**：graph-compile 会将 graph.json freeze 重写为当日 id，已 `git checkout` 回滚至 `FREEZE_20261014_V1` 并重建 dist，freeze 零 diff 守住了
- [x] **TC-8 过程齐**（2026-10-16 PASS）：10/20/30 invoke 落盘 ✅（10/20 并入 00/30 invoke）· R0–R5 填毕 ✅ · experience 捕获 ✅（含 web 面补充）· CLOSE 清单含 web PR 链接：**ops-desk-web PR #70**（squash `44a77db`）+ **PR #71**（D4 修正 · squash `46c8c54`）

## 依赖

- SPEC 冲突条款：`docs/spec/arch-browser/SPEC-arch-browser_v0.md` §1 设计纪律 3（**须显式修订**）
- 锚点（行号 2026-10-16 快照 · 10 按实校正）：
  - `docs/arch-browser/catalog/home_narrative.json:6,10`
  - `docs/arch-browser/catalog/host_outline.json:34-35,74`
  - `docs/arch-browser/catalog/crosswalk.yaml:374-387`（真值行 · **只读**）
  - `docs/arch-browser/scripts/build_site.py:35-52,243-255`
  - `docs/arch-browser/web/app.js:549-553`
  - web 仓：`ops-desk-web/src/layouts/AppLayout.vue`（菜单 `/chat` `/lc-evidence` `/lg-rag`）
- **分支基线风险**：当前 `task/arch-browser-eng-graph-mermaid` 工作树含 build_site.py / web/app.js / dist 未提交改动 → 30 前须确认该批改动归属与合入顺序，勿带入本 task PR
- 展示名裁定真值：本 task D1（维护者 2026-10-16 已锁）

## 给执行帽的必读列表

1. 本 task 全文（含 D1–D3 · 闸 pending 纪律 · 双仓边界）。
2. `docs/spec/arch-browser/SPEC-arch-browser_v0.md` §1（设计纪律 1–5 · 冲突条款原文）。
3. 上列锚点文件相关段（禁信转述；行号以开工时为准）。
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
5. `AGENTS.md` 新会话启动纪律（分支 / 闸 / 无 task 不改码）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 框定：演示展示面名实分离；只藏不改约 | 是 | 展示名已锁（D1），范围/非范围清晰，无方案分叉 | 脏树基线（eng-graph-mermaid 在飞）需在提交切分时厘清 |
| R1 | 证据：锚点已扫（catalog×3 + build_site.py + app.js + 00_main.md + 概念图源 discussions §1.2） | 是 | 全量 grep 落点，无遗漏面 | web 仓 AppLayout.vue 锚点以 web 仓开工时为准 |
| R2 | 方案：display 政策放 build 管线（SPEC 纪律 1），app.js 只消费 display 字段；catalog 文案改写；D3=改正文+修订记录 | 是 | 边界裁定唯一：视图过滤 vs 真值保留 | 例外清单须钉死（click href 保留真值 id） |
| R3 | 反例：FP-1–FP-7 全覆盖；FP-1（藏≠删）以真值字段保留反证；FP-7 以 gate 代录记录闭环 | 是 | 失败路径均有对应验收钩子 | graph-compile freeze 副作用（实测发生，已回滚，见 R5 经验） |
| R4 | 验收：TC-1–TC-8 全 PASS；api 面 TC-1/2/3/4/6/7（证据见 30 invoke）；web 面 TC-5/8 随 PR #70 闭环 | 是 | 验收证据 grep 级可复现 | 已闭环（web PR #70 已并 main `44a77db`） |
| R5 | 收口：api 面完成；闸代录；SPEC 修订落盘；dist 重建；freeze 回滚；web 面 PR #70 并 main、本 task 回填 CLOSE | 是 | — | api 仓提交切分（eng-graph-mermaid 脏树厘清）与 task 归档移位归维护者 |

**actual_last_round**：R5（2026-10-16 · 00 本窗代 10 填毕；R 轮全程 early_stop，无追加轮）

### 自检结论（执行者）

**00（2026-10-16 · 壳）**：壳落盘；D1 展示名按维护者指令锁定；D2 默认保留路由；D3 SPEC 修订方式待 10 建议；HG-* **pending**；**禁 30**；当前分支 `task/arch-browser-eng-graph-mermaid`（脏树属他 task）· 建议 30 开工前切 `task/demo-agent-host-surface` 并厘清基线；invoke `invoke_20261016_00_task_shell.md`；**未改实现码 · 未 commit**。

**00（2026-10-16 · 完成段）**：维护者本窗授权 00 代签闸并完成任务 → HG-TASK-DRAFT / HG-AUDIT-R1 代录 **approved**；D3 裁定=改正文+修订记录并已落盘 SPEC；api 面（A1–A6）全部实现：catalog×2 文案改写、build_site.py 展示层过滤/改名（display 政策字段）、app.js 演示视图过滤、SPEC §1 纪律 3 修订、dist 重建；TC-1/2/3/4/6/7 **PASS**（证据见 `invoke_20261016_30_impl.md`）；`docs/_tech_graph` / crosswalk / app/ / freeze / HTTP 路由 **零 diff**（名实分离守住；graph-compile 的 freeze 副作用已回滚）；TC-5（web 侧栏/落地页）在 **ops-desk-web 另仓另 PR**，本窗未动；**未 commit**（提交切分与 `task/arch-browser-eng-graph-mermaid` 脏树厘清归 maintainer）。

**00（2026-10-16 · CLOSE 段）**：web 面由 00 派 30 子 Agent 于 ops-desk-web 仓完成 B1–B3（分支 `task/demo-agent-host-surface` · diff 仅 AppLayout.vue + router/index.ts 共 +6/-5）→ PR #70 CI 双绿（frontend 1m1s / check 12s）→ squash 并 main `44a77db` → 本 task TC-5/TC-8 回填 ✅、状态行转 **全链 CLOSE**。**未 commit**（api 仓提交切分 + 本 task 归档移位 active→done 归维护者，因 eng-graph-mermaid 脏树基线风险 FP-7）。

---

### KPI（00）

（`kpi_aggregator: n/a` · CLOSE 时可选回填）

### 经验总结

- **graph-compile.sh 有 freeze 副作用**：验收跑 `./scripts/graph-compile.sh` 会把 `docs/_tech_graph/shared/graph.json` 的 freeze_id 重写为当日 id。任务若禁碰 freeze，验收后必须 `git checkout -- docs/_tech_graph/shared/graph.json` 回滚再重建 dist（本 task 实测踩到并闭环）。
- **display 政策放 build 管线**：遵守 SPEC 纪律 1（app.js 不手写结论），演示改名/过滤政策集中在 build_site.py 生成 display 子字段，app.js 只消费——例外仅 runtime 过滤代码的键名（真值 id，属钻取层例外）。
- **edit 工具行首空格坑**：以文件实际行为准，勿信 grep 输出的前导空格。

- **跨仓任务先验路由语义再挂名**：本 task 假设 /chat=legacy Chat，实测 /chat 早已是 lg-rag SSE 直接对话页（HITL 卡 + 过程输出都在这），/lg-rag 反而是 mode 选择调用页——PR #70 按假设挂错路由，维护者 D4 修正后 PR #71 返工。教训：展示名落路由前，先读视图组件实际渲染（HitlApprovalCard/thinking/subtasks 在哪个页）再定指向。
- **web 面页标题真值在 route.meta.title**：菜单文案在 AppLayout.vue，但页标题（header + document.title）单源消费 `src/router/index.ts` 的 `meta.title`——改名先找路由 meta，勿在视图组件里翻文案（LgRagView.vue 内无页标题文案）。
- **corepack pnpm 版本冲突**：裸 pnpm（v11.28.5 shim）与本仓 devEngines pnpm@10.32.1 冲突直接报错；用 `COREPACK_ENABLE_STRICT=0 corepack pnpm@10.32.1 <cmd>` 跑通三门。
- **gh PR body 反引号坑**：`gh pr create --body` 内联串里的反引号会被 bash 命令替换吞掉；正文一律 `--body-file` 落盘再传。
- **web 面残留决策点（另裁）**：登录流程两处落地仍指 `/overview`（router 守卫被 `tests/router-guard.spec.ts:45-50` 断言卡住 · LoginView.vue:30 fallback 超 diff 白名单）——若要求登录后默认落地也=Agent 工作台，需另裁并最小同步该条断言。
