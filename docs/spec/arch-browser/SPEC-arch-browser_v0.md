# SPEC：架构浏览器（Arch Browser · Agent Host 概念图可点击静态站）（v0）

> **层级**：L1 文档/观测衍生轨（**非**业务 API 功能波 · 服务简历交付与仓内架构导览）  
> **状态**：`draft`（初版实现随本 PR 落盘 · **HG-SPEC-SIGNOFF=pending** · 升级波次待人签后再拆 30 task）  
> **立项令（原话留痕）**：维护者 2026-10-14「初版通过，补充并新增对应的系列spec文档 … 然后PR到主分支，后续交由api agent根据specwave流程来升级优化」  
> **上游**：`docs/discussions/2026-09-24_agent-host_current_architecture_v1_zh.md` · `docs/discussions/agent-host-current-architecture/modules/M01–M34` · `docs/_tech_graph/` · Host v1 出口对照  
> **下游**：人签 → 按 [`01_execution_waves.md`](./01_execution_waves.md) 拆 task（W1+）  
> **Open Folder（实现）**：`ops-desk-api/`  
> **格式基准**：`docs/spec/inform-graph-backfill/SPEC-inform-graph-backfill_v1.md`（docs 衍生轨分波）· `docs/spec/gha-deploy-api/SPEC-gha-deploy-api_v1.md`（Harness 元信息块）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `arch-browser` |
| **invoke_slug** | `arch-browser`（task 阶段按 wave 可加后缀，如 `arch-browser-w1-doc-viewer`） |
| **test_strategy** | `recommended`（W0：本地 `build_site.py` + 静态服冒烟；W1+：按波次补断言；**不**强制全量 pytest） |
| **默认分支** | `docs/arch-browser`（本轨初版）· 升级 `task/arch-browser-wN-*`（**禁止 master 直改**） |
| **graph_change_layer** | `none` 预期（衍生视图 · 不改 graph 真值）；若某波改 `_tech_graph` 源 YAML → 回本 SPEC 修订并判 G-L* |
| **freeze_id** | 无（零 SSE / 零 REST 契约变更 · 仅可选 StaticFiles 挂载） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 初版实现可合入作基线；升级波次（W1+）须人签后再出 00 task / 30 改码 |

---

## 1. 背景与目标

Agent Host 大纲（五层 · M01–M34）与工程 `_tech_graph` 长期以 MD/YAML 存在，对外（含简历用人单位）难浏览。需要一个**只读、可点击、可静态托管**的衍生 HTML，把概念图、落地状态、工程钻取对齐展示，且**不删除、不篡改**原真值文档。

### 一句话目标

交付仓内 `docs/arch-browser/`：构建脚本聚合真值 → `dist/` 静态站；首页含架构理念 + 状态色可点 Mermaid + 场景占位；API 可选挂载 `/docs/arch-browser/`；用 SPEC 系列钉死升级波次供 SpecWave 接力。

### 设计纪律（签收时锁死）

1. **HTML 非真值**：架构结论只改 `discussions` / `crosswalk` / `home_narrative` / `_tech_graph` 源，再跑 `build_site.py`；禁止在 `app.js` 手写模块结论。
2. **零业务契约**：不改 lg-rag / HITL / capability 执行语义；不增鉴权必过的业务 API。
3. **名实分离**：叙事=Agent Host；对外演示面（首页 / 入口层 / 概念图 / 工程图演示标签 / Host 对照展示）统一 Agent Host 口径，不出现 lg-rag / LG RAG / LC Evidence / legacy Chat 等旧栈名（2026-10-16 三方演示裁定；HTTP 路径 / freeze / 包名 / 表名 / 模块 id 等业务契约不变，工程钻取真值层 docs/_tech_graph 除外——见修订记录）。
4. **状态标签对外**：展示「暂未排期」对应 crosswalk「不适用」；可保留 `status_raw`。
5. **公开面谨慎**：生产 Nginx 暴露（W2）前须维护者确认「未登录可读」范围（仅 arch-browser dist，非整棵 `docs/`）。

---

## 2. 范围

### W0 · 初版基线（本 PR 交付 · 已实现）

| # | 件 | 验收 |
|---|---|---|
| W0-1 | 目录骨架 | `docs/arch-browser/{catalog,web,scripts,dist,README.md}` 齐 |
| W0-2 | 构建 | `python3 docs/arch-browser/scripts/build_site.py`（或 `scripts/arch-browser-build.sh`）写出 `dist/site-data.json` + 复制 web 壳 |
| W0-3 | 首页 | 理念文案（`home_narrative.json`）+ 状态图例 + 可点 Mermaid（click→`#/host/{n}` · 色=落地状态）+ chip 备用 + 场景占位卡 |
| W0-4 | 路由 | `#/` · `#/host` · `#/host/{n}` · `#/eng/*` · `#/wave*`（见实现 README） |
| W0-5 | API 挂载 | `app/main.py`：若 `dist/index.html` 存在则 `StaticFiles` → `/docs/arch-browser` |
| W0-6 | 指针 | discussions / `_tech_graph` README 链到 arch-browser；本 SPEC 系列落盘 |

### W1+ · 升级波次（未实现 · 见 `01_execution_waves.md`）

| 波 | 主题 | 摘要 |
|---|---|---|
| W1 | 源文档真 URL + MD/Mermaid 查看器 | dist 内可打开源 MD；页内渲染 + mermaid |
| W2 | 生产公开入口 | Nginx `location /docs/arch-browser/`；登录/未登录均可看（workspace/deploy 协同） |
| W3 | 使用场景模块 | 填满 `scenarios_placeholder` → 真场景卡（可挂证据路径） |
| W4 | 简历包装 / 可访问性 | 外链摘要页、打印样式、无 CDN 降级说明等 |

---

## 3. 非范围

- ❌ 在线编辑架构结论 / 写回 MD
- ❌ 替代 `graph-compile` 或 inform-graph-backfill
- ❌ 把整棵 `docs/` 匿名公开（仅 arch-browser dist；W1 复制的 MD 须白名单）
- ❌ Vue SPA（ops-desk-web）内嵌为本波必做（可选后续另 SPEC）
- ❌ 改 Host 模块业务代码以「配合展示」

---

## 4. 开放裁定

| ID | 问题 | 建议默认 | 状态 |
|---|---|---|---|
| Q1 | 生产是否未登录可读？ | 是（仅 `/docs/arch-browser/`）· W2 实施前须人确认 | **待裁定** |
| Q2 | 源 MD 查看器内嵌全文还是摘要？ | W1 默认：白名单路径全文进 dist + `#/doc` 查看器 | **待裁定** |
| Q3 | 场景卡证据形态？ | W3：链接到仓内 reports/discussions 路径；不做视频托管 | **待裁定** |
| Q4 | Mermaid 依赖 CDN？ | W0 用 jsDelivr；W4 可 vendor 进 dist 作离线 | **待裁定** |

---

## 5. 验收（W0）

- [ ] 仓根执行 `python3 docs/arch-browser/scripts/build_site.py` 退出 0；打印含 `concept_mermaid_chars>0`
- [ ] `cd docs/arch-browser/dist && python3 -m http.server 8765` → 首页可见理念 + 着色 Mermaid；点击节点进 `#/host/{n}`
- [ ] 状态标签无「不适用」字面，为「暂未排期」（或与 badge 图例一致）
- [ ] 场景区三张占位卡可见且标注「设想 · 未填充」
- [ ] `GET /docs/arch-browser/`（本地起 api 且 dist 存在）返回 index（或 200 静态）
- [ ] 本目录 SPEC README + 主 SPEC + waves 可读

---

## 6. 风险与回滚

| 风险 | 缓解 |
|---|---|
| dist/`site-data.json` 体积膨胀 | 构建已截断 L2 index；禁把全仓 MD 无白名单拷进 dist |
| CDN 不可达 | chip 备用列表仍可导航；W4 vendor |
| 误把私密 docs 公开 | W2 只反代 arch-browser；W1 白名单路径表进 SPEC/waves |
| 与真值漂移 | README 纪律 + CI 可选「build 后 git diff dist」门禁（另 task） |

回滚：撤 `app/main.py` mount；删或停用 `docs/arch-browser/dist` 不影响业务 API。

---

## 7. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-14 | v0 draft 落盘：对齐初版实现 + W1–W4 升级轨道；HG-SPEC-SIGNOFF=pending |
| 2026-10-16 | §1 纪律 3 修订（task demo_agent_host_surface）：三方演示裁定——演示面统一 Agent Host 口径，废止原「传输壳可仍叫 lg-rag（首页文案须保持）」；隐藏只发生在演示视图（catalog 文案 / build 展示层过滤 / app.js 视图过滤），docs/_tech_graph、crosswalk.yaml、路由、freeze、包名、表名等真值不改不删 |
