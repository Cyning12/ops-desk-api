# Task：arch-browser W4 简历包装与韧性（vendor + 60秒读法 + 打印/动效）

> **状态**：in_progress  
> **类型**：增强/包装  
> **关联图谱**：无  
> **落盘**：`docs/tasks/active/task_arch_browser_w4_resume_harden.md`；验收后 `git mv` → `docs/tasks/done/`

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `arch-browser-w4-resume-harden` |
| **test_strategy** | `required` |
| **test_strategy_note** | build 后断言 dist/vendor/ 存在且 index.html 引用本地 vendor；断网/弱网环境页面仍可用 |
| **code_quality_bar** | `recommended` |
| **orchestration** | 单 task |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/arch-browser-w4-resume-harden` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅改 arch-browser 静态资源，不新增模块/路由/表 |
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
| **HG-TASK-DRAFT** | approved | 22-R1, 30 | 维护者授权直接开工（W4 延续 W1-W3 授权链） |
| **HG-AUDIT-R1** | approved | 30 | 维护者口头授权（m02493「开始W4」） |
| **HG-GRAPH-MODULES** | approved | 30 | 不修改图谱 |

---

## 背景与目标

arch-browser W1-W3 已交付（doc viewer + nginx 入口 + scenarios），当前页面依赖 jsDelivr CDN 加载 mermaid 和 marked。W4 目标：弱网/无 CDN 环境仍可用；增加简历包装（60 秒读法）；可选打印样式。

**完成态**：

- [ ] mermaid/marked vendor 进 `dist/vendor/`，index.html 引用本地文件。
- [ ] `home_narrative.json` 新增「给招聘官的 60 秒读法」区块。
- [ ] 可选：`prefers-reduced-motion` 支持。
- [ ] 可选：打印样式（@media print）。
- [ ] `build_site.py` 通过，`dist/` 产物完整。

**不做**：

- 改源 MD 真值内容。
- 新增工程节点或模块。
- 改 CDN 版本（除非 vendor 必须）。

---

## 范围

- [ ] `docs/arch-browser/scripts/build_site.py`（vendor 下载/复制逻辑）
- [ ] `docs/arch-browser/web/index.html`（改本地引用）
- [ ] `docs/arch-browser/catalog/home_narrative.json`（60 秒读法）
- [ ] `docs/arch-browser/web/style.css`（可选打印样式/动效）
- [ ] `docs/arch-browser/dist/`（build 产物更新）

## 非范围

- `docs/_tech_graph/`、`docs/discussions/` 真值 MD 内容。
- 后端 API。
- 其它页面功能变更。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| vendor 下载失败（无外网） | build 报错，提示手动下载 | 是 | 构建失败信息 |
| vendor 文件缺失 | 页面显示降级提示（chip 列表仍可用） | 重新 build | 降级提示 |
| home_narrative.json 格式错误 | build 报错 | 修复 JSON | 构建失败信息 |

---

## 验收标准

- [ ] `python3 docs/arch-browser/scripts/build_site.py` 退出码 0。
- [ ] `dist/vendor/` 存在且包含 mermaid.min.js 和 marked.min.js。
- [ ] `dist/index.html` 引用 `./vendor/mermaid.min.js` 和 `./vendor/marked.min.js`（非 CDN）。
- [ ] 断网环境（或 CDN 被墙）页面 Mermaid 和 Markdown 仍渲染。
- [ ] 首页显示「给招聘官的 60 秒读法」区块。
- [ ] （可选）`prefers-reduced-motion` 生效。
- [ ] （可选）打印样式生效。
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_arch_browser_w4_resume_harden.md` 通过。
- [ ] 提交到 `task/arch-browser-w4-resume-harden` 并创建 PR。

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/arch-browser/README.md`
3. `docs/spec/arch-browser/SPEC-arch-browser_v0.md`
4. `docs/spec/arch-browser/01_execution_waves.md`
5. `docs/arch-browser/web/index.html`
6. `docs/arch-browser/scripts/build_site.py`

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| vendor 逻辑 | ⏳ | |
| index.html 本地引用 | ⏳ | |
| 60 秒读法 | ⏳ | |
| prefers-reduced-motion | ⏳ | |
| 打印样式 | ⏳ | |
| build_site.py 通过 | ⏳ | |
| 断网验证 | ⏳ | |

---

## 测试策略（Harness）

**test_strategy**: `required`

- build 后断言 vendor 文件存在且 index.html 引用本地路径。
- 断网/CDN 被墙环境冒烟（可用 hosts 屏蔽或离线环境）。
- 首页 60 秒读法渲染验证。

---

### 自检结论（执行者）

（30/40 回填）

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
| 2026-11-09 | 创建 task，维护者授权开工（m02493） |
