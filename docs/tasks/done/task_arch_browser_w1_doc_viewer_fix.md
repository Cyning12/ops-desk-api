# Task：修复 arch-browser W1 源文档查看器 Mermaid/表格渲染（3.3 项 14）

> **状态**：completed  
> **类型**：缺陷修复  
> **关联图谱**：无  
> **落盘**：`docs/tasks/active/task_arch_browser_w1_doc_viewer_fix.md`；验收后 `git mv` → `docs/tasks/done/`

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `arch-browser-w1-doc-viewer-fix` |
| **test_strategy** | `required` |
| **test_strategy_note** | build_site.py 出 dist 后，用浏览器/静态服务断言含 Mermaid 与表格的 MD 在直接 hash 跳转时正确渲染 |
| **code_quality_bar** | `recommended` |
| **orchestration** | 单 task |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `fix/arch-browser-w1-doc-viewer-fix` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅修复 web/app.js 渲染逻辑，不新增模块/路由/表 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **wiki_promotion** | `none` |
| **close_pr_policy** | `required` |
| **experience_capture** | `recommended` |
| **kpi_rubric** | `KPI_RUBRIC_v1_2` |
| **kpi_aggregator** | `CLOSE` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| **HG-TASK-DRAFT** | approved | 22-R1, 30 | 维护者授权直接开工 |
| **HG-AUDIT-R1** | approved | 30 | 维护者口头授权修复 14 项（m00153） |
| **HG-GRAPH-MODULES** | approved | 30 | 不修改图谱 |

---

## 背景与目标

arch-browser W1 源文档查看器在人工验收中出现 3.3 项 14 缺陷：从源文档索引或 Host 详页点击 MD 链接直接跳转到 `#/doc?path=...` 后，Mermaid 图表与 Markdown 表格不渲染；把同一 URL 复制到新标签页打开则正常。

本任务修复该渲染失败，使 SPA hash 路由内的直接跳转与刷新/新标签页行为一致。

**完成态**：

- [x] 根因修复：doc viewer 的 Mermaid 代码块在 `renderDoc` 后能被 `mountMermaid` 正确渲染。
- [x] 表格正确渲染（GFM table 输出 `<table>` 而非原始管道文本）。
- [x] 直接 hash 跳转、刷新、新标签页三种打开方式结果一致。
- [x] `build_site.py` 通过，`dist/` 产物无异常。
- [x] 自检结论回填。

**不做**：

- 变更白名单或源 MD 文件内容。
- 新增工程节点或模块。
- 改动 Mermaid/marked CDN 版本（除非必要且经评估）。

---

## 范围

- [x] `docs/arch-browser/web/app.js`（核心修复）
- [x] `docs/arch-browser/web/style.css`（表格/Mermaid 样式微调）
- [x] `docs/arch-browser/dist/`（build 产物更新）

## 非范围

- `docs/_tech_graph/`、`docs/discussions/` 真值 MD 内容。
- 后端 API。
- 首页/Host 目录/工程图谱/规划波次等其它页面。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| Mermaid CDN 未加载 | 显示“mermaid CDN 未加载，备用列表仍可用” | 刷新页面 | 错误提示 |
| marked 解析失败 | 退化为 `<pre>` 原始文本 | 否 | 原始 MD 文本 |
| 目标 MD 不在白名单 | 已存在的拒绝页 | 否 | “该路径不在 W1 白名单内，不进入 dist、不提供查看。” |
| 静态文件 404 | 显示“加载失败：HTTP 404” | 检查 build | 错误提示 |

---

## 验收标准

- [x] `python3 docs/arch-browser/scripts/build_site.py` 退出码 0，`dist/` 生成。
- [x] 本地静态服务下，直接访问含 Mermaid 的 MD hash URL 后，Mermaid 图表渲染为 SVG。
- [x] 直接访问含表格的 MD hash URL 后，表格以 `<table>` 形式渲染，非原始管道文本。
- [x] 同一 URL 在新标签页打开与直接跳转结果一致。
- [x] 拒绝页（非白名单路径）文案保持明确，15/16 项语义可区分。
- [x] `npx spec-wave task lint --file docs/tasks/active/task_arch_browser_w1_doc_viewer_fix.md` 通过。
- [x] 提交到 `fix/arch-browser-w1-doc-viewer-fix` 并创建 PR：#364。

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/arch-browser/README.md`
3. `docs/spec/arch-browser/SPEC-arch-browser_v0.md`
4. `docs/spec/arch-browser/01_execution_waves.md`
5. `docs/arch-browser/web/app.js`（重点看 `renderDoc`、`mountMermaid`）
6. `docs/arch-browser/web/index.html`

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| 根因定位 | ✅ | `renderDoc` 把 `<pre><code class="language-mermaid">` 替换成裸 `<div class="mermaid">`，但 `mountMermaid` 只处理 `.mermaid-viewer` / `.clickable-mermaid` 容器 |
| Mermaid 修复 | ✅ | `renderDoc` 将代码块包进 `.mermaid-viewer.clickable-mermaid.doc-inline-mermaid`，内部用 `.mermaid-stage > div.mermaid`；`mountMermaid` 选择器改为 `.mermaid-stage .mermaid` 以兼容首页 `<pre>` 与文档内联 `<div>` |
| 表格修复 | ✅ | `marked.use({ gfm: true })` 启用 GFM，`style.css` 新增 `.md table/th/td` 样式 |
| 15/16 文案区分 | ✅ | 非白名单路径分两类：未被任何 Host module sources 引用显示“该路径不在 W1 白名单内…”；被引用但未进 dist 显示“该路径被源链引用，但未进入 W1 dist 白名单…” |
| build_site.py 通过 | ✅ | 退出码 0，dist 产物已更新 |
| 浏览器验证 | ✅ | Playwright 断言：Mermaid 渲染为 SVG、原 `pre.mermaid` 不可见、表格渲染为 `<table>`、刷新后稳定 |

---

## 测试策略（Harness）

**test_strategy**: `required`

- 先改实现再运行 `build_site.py` 与本地静态服务冒烟。
- 关键样本：`M01_capability-registry.md`（Mermaid）、`01_modules.md`（表格）。
- 验证三种打开方式：直接 hash 跳转、刷新、新标签页。

---

### 自检结论（执行者）

- `docs/arch-browser/web/app.js`：
  - `renderDoc` 启用 marked GFM；Mermaid 代码块替换为 `.mermaid-viewer` 容器；拒绝页按是否被源链引用区分文案。
  - `mountMermaid` 选择器从 `pre.mermaid` 改为 `.mermaid-stage .mermaid`，同时兼容首页与文档内联两种结构。
- `docs/arch-browser/web/style.css`：新增 `.md table/th/td` 与 `.doc-inline-mermaid` 样式。
- `docs/arch-browser/dist/`：已重新 build。
- 浏览器验证（Playwright）：直接 hash 跳转、刷新后 Mermaid SVG 与表格均正常渲染；原 `pre.mermaid` 不可见。
- `npx spec-wave task lint`：PASS。

---

### KPI（00）

（关账回溯填写）

---

### 经验总结

（关账必填）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-11-09 | 创建 task，维护者授权开工（m00153） |
| 2026-11-09 | 实现修复、浏览器验证、spec-wave lint PASS、推送 PR #364 |
