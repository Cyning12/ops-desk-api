# Task：arch-browser-eng-graph-mermaid（工程图谱默认 Mermaid 组件 · 缩放/平移/复制源码 · 追溯建档）

> **状态**：done（CLOSED 2026-10-17 · PR [#257](https://github.com/Cyning12/ops-desk-api/pull/257) MERGED（squash `833f605` · 2026-10-17T03:25:13Z）· TC-1–TC-6 全绿（含 TC-6 eng_l0 管线回补 `2b34d08`）· 双闸 approved（追溯 · 维护者 2026-10-16 裁定）· 30 invoke 追溯落盘 · CLOSE 归档 done/ · 细节见 CLOSE 文档 [`../close/close_arch_browser_eng_graph_mermaid_20261017.md`](../close/close_arch_browser_eng_graph_mermaid_20261017.md)）
> **类型**：arch-browser 工程图谱展示增强（纯 web 展示层 · 零业务码）
> **分支**：`task/arch-browser-eng-graph-mermaid`
> **提交**：`0a91268` feat(arch-browser) mermaid 面 + `b34af17` chore(deps) lockfile 卫生 + `e736f4f` 追溯档（2026-10-16 rebase 到 master e00b414 后新 hash · rebase 前为 95a9f4e/5b63f29/edba447）

## 追溯说明（诚实记录）

- 实际工作于 **2026-10-15**（cache-buster `v=20261015-mz3`）在飞未提交，**先于**任何 task/invoke 档案；2026-10-16 维护者裁定（ask_user_question · 选项「追溯建档 + hunk 切分 + mermaid 独立 PR」）补建本档。
- 开工时人工闸缺失为既成事实，维护者 2026-10-16 裁定即为本任务的人审面；R1 审查以「hunk 切分正确性 + 演示面零混入」为实质内容（见 invoke）。

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `arch_browser_eng_graph_mermaid` |
| **git_branch** | `task/arch-browser-eng-graph-mermaid` |
| **implement_repo** | `ops-desk-api`（docs/arch-browser 静态站） |
| **test_strategy** | `required` |
| **test_strategy_note** | 纯展示层：node --check 语法闸 + build_site.py 重建 + dist/web 一致性 diff + 演示面关键词零混入 grep |
| **code_quality_bar** | `L2_backend`（触及处为静态站脚本） |
| **graph_change_layer** | `n/a`（不增删 `_tech_graph` 真值行；eng_l0_mermaid 由既有 build 管线产出） |
| **graph_delta** | `n/a` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `30`（追溯） |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **freeze_id** | `n/a` |
| **related_tasks** | `demo_agent_host_surface`（同文件 app.js 相邻改动 · **hunk 已切分零混入** · demo 面留树待本 PR 合并后切 `task/demo-agent-host-surface`） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved（追溯 · 维护者 2026-10-16 裁定） | 20,30 | 追溯建档，维护者 ask_user_question 选定处理方案即授权 |
| HG-AUDIT-R1 | approved（追溯 · 同上） | 30 | R1 实质=hunk 切分正确性复核（见 invoke 证据） |

### 维护者裁定口

| 裁定 ID | 选项 | 状态 | 说明 |
|---------|------|------|------|
| D1 脏树处理方案 | 追溯建档+hunk 切分+mermaid 独立 PR / 其他 | **已定（2026-10-16）** | app.js 按 hunk 切两任务；本分支只提 mermaid 面；demo 面留树；uv.lock/pnpm-lock 作 hygiene 提交；.pnpm-store 删除 |

## 范围

- **S1 默认 Mermaid 组件**：`web/app.js` 新增 `mermaidPanelHtml`（缩放工具栏 ±/1:1/适应/复制源码 · 滚轮缩放 · 空白拖拽平移 · click 指令解析 `parseMermaidClicks`）；首页概念图 / 工程图谱 / G-L1 flow 页全量切换
- **S2 工程图谱改名**：导航与页头「工程 G-L0」→「工程图谱」；renderEngL0 重写（mermaidBlock 主图 + 节点/边列表折叠 chip 备用 `engL0NodeHref`/`engL0ChipBackupHtml`）
- **S3 mountMermaid 循环改造**：`normalizeMermaidSvg`（viewBox 量宽）+ `attachMermaidZoom` + `bindMermaidNodeNav`
- **S4 样式与壳**：`web/style.css` +96（mermaid-viewer/toolbar/viewport/stage/chip-backup）；`web/index.html` cache-buster `v=20261015-mz3`；README 补「默认 Mermaid 组件」段
- **S5 dist 同步重建**（site-data.json 保持 HEAD 版 · 纯衍生刷新不进 mermaid 提交）

## 非范围

- demo_agent_host_surface 演示面（DEMO_* 常量 / display 字段消费 / 演示过滤）——**已按 hunk 切出，不在本任务提交内**
- `_tech_graph` 真值行、crosswalk.yaml、build_site.py 数据政策（demo 侧）
- 业务码 app/、SSE、鉴权、单测

## 验收标准

- [x] TC-1 `node --check web/app.js` 通过；`web/app.js` == `dist/app.js`
- [x] TC-2 提交内 `git diff HEAD~2 -- web/app.js` 零 demo 关键词（ENG_DEMO/DEMO_TEXT/demoText/ENG_L0_DEMO/disp./m.display 全 0 命中 · 手术反向校验 64 行差异全属 demo 域）
- [x] TC-3 build_site.py EXIT=0 重建 dist；dist/site-data.json 与 HEAD 一致（纯演示刷新剔除）
- [x] TC-4 hygiene 独立提交（uv.lock=import-linter 合法同步 · pnpm-lock.yaml=spec-wave 3.3.0 锁）；.pnpm-store 已删
- [x] TC-5 已由维护者另窗闭环（api PR #255 / CLOSE PR #256 · demo task 归档 done/）——本窗原 TC-5 表述作废
- [x] TC-6 eng_l0 管线回补（2b34d08）：00 CLOSE 档裁定「_ENG_L0_DEMO_* 只服务 eng_l0 管线 → 判 eng」，首切误归 demo 面切除 → 本 PR 纠正回补（build_site.py +171 · app.js ENG_L0_DEMO_* 过滤改名 · dist eng_l0_mermaid 键 2603ch）

### 自检结论（执行者）

追溯档 CLOSED 回填：TC-1–TC-6 全绿（证据链见上各行与 30 invoke `docs/harness/invokes/by-task/arch_browser_eng_graph_mermaid/invoke_20261016_30_retro.md`）· PR #257 MERGED squash `833f605` ·  lint 机读形态修订仅改勾选符号、验收内容零变更。

## failure_paths

- FP-1 混合 hunk（H3/H5/H7/H12）不可 git apply 子集 → 采「全量文件 − demo 编辑」逆向手术 + 双向 diff 校验（已执行）
- FP-2 dist/site-data.json 重建带来真值衍生刷新（generated_at/graph_generated_at/hitl note）→ mermaid 提交剔除保持纯展示面
- FP-3 手术漏网 demo 编辑 → TC-2 关键词零命中闸 + 64 行差异全分类复核

## 思考轮控制

| 轮 | 内容 | 结论 |
|----|------|------|
| R0 | 脏树侦察（分支==main 无独立提交 · 零档案 · 与 demo 混 14 hunk） | 见 invoke |
| R1 | hunk 分类 + 切分方案 + 手术正确性 | PASS（双向 diff 证据） |
| R2 | rebase 到 master e00b414（demo 面已并）· 冲突解 = mermaid-only + 维护者 demo 编辑集 | PASS |
| R3 | CLOSE 档切分裁定复核：eng_l0 演示政策判 eng → 首切误切除 → 回补 2b34d08 | 纠正闭环 |
| R4–R5 | n/a（追溯） | — |

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSED：PR #257 MERGED（squash `833f605`）· 归档 done/ · CLOSE 档 `../close/close_arch_browser_eng_graph_mermaid_20261017.md` · 批量关账 PR 待开（close/active-batch-20261017）· 分支 `task/arch-browser-eng-graph-mermaid` 移交 00 统一清理（本 CLOSE 不删任何东西） |
