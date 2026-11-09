# Task：arch-browser W3 使用场景模块（填占位）

> **状态**：in_progress  
> **类型**：内容+前端实现  
> **关联图谱**：无  
> **落盘**：`docs/tasks/active/task_arch_browser_w3_scenarios.md`；验收后 `git mv` → `docs/tasks/done/`

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `arch-browser-w3-scenarios` |
| **test_strategy** | `required` |
| **test_strategy_note** | build_site.py 生成 site-data.json 后，断言 scenarios 数据存在且 #/scenarios 页面可渲染；移除或保留明确的“未就绪”占位 |
| **code_quality_bar** | `recommended` |
| **orchestration** | 单 task |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/arch-browser-w3-scenarios` |
| **graph_delta** | `none` |
| **graph_delta_note** | 新增内容为场景叙事与 catalog 数据，不新增工程节点/模块/路由 |
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
| **HG-AUDIT-R1** | approved | 30 | 维护者口头授权 W3 开工（m00153） |
| **HG-GRAPH-MODULES** | approved | 30 | 不修改图谱 |

---

## 背景与目标

W3 目标：首页或独立 `#/scenarios` 页面展示真实请求路径故事与可选证据链，替代当前“设想 · 未填充”占位。

**完成态**：

- [ ] 场景数据源确定（扩展 `catalog/home_narrative.json` 或新建 `catalog/scenarios.yaml`）。
- [ ] `build_site.py` 把场景数据写入 `site-data.json`。
- [ ] web 壳新增/更新 `#/scenarios` 路由与渲染（或扩展首页场景区）。
- [ ] 移除无意义的“设想 · 未填充”占位；未就绪项保留明确状态标签。
- [ ] 内容不泄露租户数据，证据链使用仓内公开 reports/discussions 相对路径。
- [ ] 自检结论回填。

**不做**：

- 引入外部/私有数据。
- 改动工程图谱或模块表。
- 实现后端动态接口（仍读静态 site-data.json）。

---

## 范围

- [ ] `docs/arch-browser/catalog/`（home_narrative.json 或 scenarios.yaml）
- [ ] `docs/arch-browser/scripts/build_site.py`
- [ ] `docs/arch-browser/web/app.js`（新增 `#/scenarios` 渲染）
- [ ] `docs/arch-browser/web/index.html`（如需要导航入口）
- [ ] `docs/arch-browser/web/style.css`（如需要样式）
- [ ] `docs/arch-browser/dist/`（build 产物更新）

## 非范围

- `docs/_tech_graph/` 结构与内容。
- 后端 API。
- 用户/租户真实数据。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 场景 YAML/JSON 格式错误 | build_site.py 失败 | 修正格式 | build 失败 |
| 证据链路径不存在 | 显示占位或 404 | 修正路径 | 链接失效 |
| 场景数据未写入 site-data.json | #/scenarios 空白 | 检查 build 逻辑 | 空白页 |

---

## 验收标准

- [ ] `python3 docs/arch-browser/scripts/build_site.py` 退出码 0，`site-data.json` 包含 `scenarios`（或等价字段）。
- [ ] 本地静态服务下 `#/scenarios` 可访问并渲染至少 1 个真实场景。
- [ ] 首页不再出现无说明的“设想 · 未填充”占位；保留的未就绪项带状态标签。
- [ ] 场景中的证据链接均为仓内公开路径（如 `docs/discussions/...`）。
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_arch_browser_w3_scenarios.md` 通过。
- [ ] 提交到 `task/arch-browser-w3-scenarios` 并创建 PR。

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/spec/arch-browser/01_execution_waves.md`
3. `docs/arch-browser/README.md`
4. `docs/arch-browser/catalog/home_narrative.json`
5. `docs/arch-browser/catalog/crosswalk.yaml`
6. `docs/arch-browser/web/app.js`
7. `docs/arch-browser/scripts/build_site.py`

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| 场景数据源 | ✅ | 新建 catalog/scenarios.yaml；home_narrative.json 扩展 scenarios_teaser |
| build_site.py 写入 | ✅ | site-data.json 包含 4 个 live 场景 |
| #/scenarios 渲染 | ✅ | app.js 新增 renderScenarios / renderScenarioDetail 路由与组件 |
| 首页占位清理 | ✅ | 移除 scenarios_placeholder，改为 4 张带状态徽章的场景卡片 |
| 内容合规检查 | ✅ | 证据链均使用仓内公开 reports/discussions/scripts 相对路径，无租户数据 |

---

## 测试策略（Harness）

**test_strategy**: `required`

- build 后检查 `site-data.json`。
- 浏览器访问 `#/scenarios` 与首页，确认渲染与占位处理。

---

### 自检结论（执行者）

- build_site.py 退出码 0，site-data.json 包含 4 个 live 场景。
- app.js 通过 \"node --check\"，新增 #/scenarios 路由与详情渲染。
- 首页 scenarios_placeholder 已移除，scenarios_teaser 带状态徽章。
- 所有证据路径均存在且为仓内公开路径。
- spec-wave task lint 通过；spec-wave verify 仅因缺 R<n> review 文件报 BLOCKED，但 HG-AUDIT-R1 已 approved，可开工。
- 浏览器端动态渲染因环境缺少 headless Chromium/jsdom 未做端到端截图，静态数据与脚本引用已验证。

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
| 2026-11-09 | 创建 task，维护者授权 W3 开工（m00153） |
