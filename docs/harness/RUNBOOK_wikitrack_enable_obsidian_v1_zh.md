# RUNBOOK · WikiTrack 启用 + Obsidian（可复用 · api dogfood）

> **版本**：v1.2 · 2026-07-28  
> **源仓 dogfood**：`ops-desk-api`（manifest ≥ **2.19.0**）  
> **消费方**：`ops-desk-web`（当前常见起点 **2.18.0** · preset 可为 `harness-only`）**原样对照执行**  
> **原则**：**单份真值**（不把 `standards` / 部署文 / `_tech_graph` 正文复制进 `coding_wiki`）

---

## 0. 前置

| 项 | 要求 |
|---|---|
| Open Folder | 目标业务仓根 |
| 工作树 | `git status` 干净（或仅本 task 文件） |
| Harness | 先钉 **`@cyning/harness@2.19.0`**（或更新），**再**改 wiki 文档 |
| 非范围 | 不改 cyning-harness 产品仓；不做 Obsidian 插件开发；不力导向 Web UI |

破坏性（自 2.18.0，仍有效）：

- 缺 `wiki_delta` → `task close` **BLOCK**
- `none` / `n/a` 无 `wiki_delta_note` → **BLOCK**
- **勿默认** `--allow-wiki-gap`

---

## 0.5 从 2.18.0 起步（web 对照 · api dogfood）

api 已走完 **2.18.0 → 2.18.1 → 2.18.2 → 2.19.0**。web 若停在 **2.18.0** 且已做 `wiki_delta` 存量（多为 `n/a`），建议**一把升到 2.19.0**（不必逐步停 2.18.1/2.18.2），再决定是否启用 WikiTrack。

### 建议路径（两棒可同 PR）

| 棒 | 做什么 | 验收 |
|---|---|---|
| A · 钉版本 | `npx --yes @cyning/harness@2.19.0 upgrade --yes`（不带 `--ide`） | manifest=`2.19.0` · `check` 已是最新 |
| A · 字段扫描 | `task lint-wiki-delta --scope all` | missing=0 · exit 0；有缺失则补 `path\|none\|n/a`+note |
| A · overlay | diff `AGENTS.md` / `FRAGMENT_30_gate_verify*` | 恢复本仓定制（upgrade 会冲掉） |
| B · WikiTrack（可选） | 按下文 §2–§3 启用入口 | `wiki export` 有边；Obsidian 只开 `coding_wiki/` |
| B · 若暂不启用 | 新 task 可继续 `wiki_delta=n/a`+note，或改为 `none`+note | 勿漏字段 |

### api → web 差异（经验）

| 点 | api dogfood | web 注意 |
|---|---|---|
| preset | `fullstack-node-py` | 现为 `harness-only` 亦可 upgrade；质量门用 `pnpm lint/test/build` |
| 2.18.0 存量 | 曾标 `n/a`「未启用」→ 后启用 WikiTrack | 若已 `n/a` 且空壳/无 wiki：可保持 `n/a` 到启用日；**done 不必回刷** |
| 2.18.2 | 两层目录 `topics/`（recommended） | 启用 WikiTrack 时一并做；未达加深阈值勿建第 3 层 |
| 2.19.0 | `lint-wiki-delta` 替代 `rg -L` | **必跑**；缺字段 exit 2 |
| Obsidian | vault = **`docs/coding_wiki/`** | **不要**开上级 `docs/`（tasks/invokes 会刷孤点） |
| 关账 | `task close --file … --yes` | **勿**加 `--target .`（`--target`=归档目标路径，不是仓根） |
| 单份真值 | coding_wiki 只指针 | 同左；禁复制 standards/图谱正文 |

### 摩擦清单（升级时必查）

1. **overlay 被冲**：每次 `upgrade` 后 diff AGENTS harness 段 / FRAGMENT（api：`l1/01_modules`、pre-30、G-L0 关键词）。  
2. **伪双括号字面**：coding_wiki 叙述里不要写会进 export 的「假链接」字样（F-218-07）；真互链用真实页名。  
3. **`upgrade` 不代写**：不补 task 的 `wiki_delta`，也不自动把已有 wiki 迁成 `topics/`。  
4. **close 前**：状态 `completed` · 有 `### KPI`（或非 CLOSE 的 `kpi_aggregator`）· 勾选齐 · R1 review · invoke hats。

---

## 1. 升级到 2.19.0（文档动作前）

在业务仓根：

    git checkout -b task/harness-upgrade-2-18-1   # 或沿用已有 upgrade 分支
    npx --yes @cyning/harness@2.19.0 upgrade --yes --target .
    npx --yes @cyning/harness@2.19.0 check

验收：

- `.cyning-harness/manifest.json` → `"version": "2.19.0"`
- `check` 输出「已是最新」· exit 0
- upgrade 后 **diff AGENTS / FRAGMENT**：恢复本仓 overlay（api 例：pre-30 行、G-L0 / HG-PILOT、FRAGMENT 的 `l1/01_modules`）

若仍停在 2.18.0：先完成 `wiki_delta` 存量补字段（见 USER_GUIDE §6.0b），再升 2.19.0。

---

## 2. 00 统筹产物（建议落盘）

| 产物 | 路径约定 |
|---|---|
| active task | `docs/tasks/active/task_wikitrack_enable_p0.md` |
| 00 invoke | `docs/harness/invokes/by-task/wikitrack-enable-p0/invoke_*_00_*.md` |
| R1 review | `docs/harness/reviews/task_wikitrack_enable_p0_audit_R1_*.md` |
| 本 RUNBOOK | `docs/harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md`（可从 api 拷贝） |

人工闸（基础设施惯例 · 00 可代签）：

| human_gate_id | status | blocks |
|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 |
| HG-AUDIT-R1 | approved | 30 |
| HG-GRAPH-MODULES | approved | 30（仅入口文档 · 不改模块边界） |

task 元信息要点：

- `graph_change_layer` / `graph_delta` = `none` + note
- `wiki_delta` = `docs/coding_wiki`（或具体改动的 md）
- `wiki_delta_note`：启用入口；真值仍在原路径
- `invoke_retention_profile` = `minimal` 或显式含 `00,30`
- **禁止**再写 `wiki_delta: n/a`（启用后）

---

## 3. 落地 coding_wiki（无双份）

### 3.1 目录角色

| 路径 | 角色 |
|---|---|
| `docs/coding_wiki/` | 入口 + `[[wikilink]]` 互链 + volatile |
| `docs/standards/` 等 | **正文真值**（唯一） |
| `docs/_tech_graph/` | GraphTrack 真值（yaml 编译）；wiki **只链不拷** |

### 3.2 两层目录（v2.18.2 recommended · 非硬闸）

- 根：`README` / 可选 `_index` / `stable`·`context`·`volatile`
- 主题薄页：`topics/*.md`（勿按日期/PR/task_slug 建目录）
- 未达加深阈值（md≥15 等）**不要**提前第 3 层
- 缺两层 **≠** close BLOCK

### 3.3 必改读序文件


对 `README.md` / `stable.md` / `context.md` / `volatile.md`：

1. 层内互链至少含：`[[README]]` · `[[stable]]` · `[[context]]` · `[[volatile]]`（保证 `wiki export` 有边；对齐 2.18.2 两层 + 互链模板）
2. `context.md` 用**相对 md 链**指向真值（示例，按仓裁剪）：

    - `../standards/...`
    - `../_tech_graph/README.md`（前端仓可能无 G-L 分层，改成本仓图谱读序）
    - `../deployment/...` 或前端等价部署说明

3. `volatile.md` 填当前 `docs/tasks/active/` 的 slug 表；关账后清空
4. **不要**把长规范/流程图粘进 coding_wiki

### 3.4 Obsidian

1. Obsidian → Open folder as vault → 业务仓 **`docs/coding_wiki/`**（推荐）
2. **不要**开上级 `docs/`：会把 `tasks/` · `harness/invokes` · `reviews` 等过程轨扫进图谱 → 大量孤点
3. `context` 里指向 `../standards` 等的相对链是**真值指针**（单份、不双写）；出 vault 时用系统打开或 IDE 看正文即可，不必为进图谱而复制进 wiki
4. Mermaid：图谱 md 在 vault 外时按需另开；本 vault 以入口互链为主
5. **勿**把仓根（含 `node_modules` / `.venv`）当 vault

---

## 4. 校验命令（合并前）

    npx --yes @cyning/harness@2.19.0 check
    npx --yes @cyning/harness@2.19.0 task lint-wiki-delta --target . --scope all
    npx --yes @cyning/harness@2.19.0 wiki export --json --target .
    npx --yes @cyning/harness@2.19.0 verify --target . --task docs/tasks/active/task_wikitrack_enable_p0.md
    # 前端仓再加：pnpm lint && pnpm test && pnpm build
    # 后端仓再加：ruff check … && pytest …

`wiki export` 期望：

- `schema` = `harness.wiki_graph.v1`
- `nodes.length` ≥ 4
- `edges.length` > 0（wikilink）
- `warnings` 可空；未解析的双括号链须修链

---

## 5. 启用后 · 日常写文档流程（交 10/30）

    10 起草 task
      → 文档只选一个落点（standards / deployment / graph / …）
      → 预填 wiki_delta：改入口→ docs/coding_wiki/… ；改真值→该文件 path ；无文档→ none+note
    20 审查
    30 只写那一处正文；若影响读序，同步改 coding_wiki 指针（仍不复制正文）
    40 / close
      → path 存在；required∩path 时经验节含 Wiki: 指针
      → 更新或清空 volatile

存量已标 `n/a` 的 done task：**不必回刷**；新 task 禁止默认 `n/a`。

---

## 6. web 仓对照清单（直接勾选）

- [ ] `upgrade` → manifest **2.19.0**
- [ ] 恢复本仓 AGENTS/FRAGMENT overlay（若有）
- [ ] 存量 task 已有 `wiki_delta`（若从 ≤2.17 升上来）
- [ ] `task lint-wiki-delta --scope all` → PASS（missing=0）
- [ ] 改写 `docs/coding_wiki/{README,stable,context,volatile}.md`（互链 + 真值相对链）
- [ ] `wiki export --json` 有边
- [ ] 新 task：`wikitrack-enable-p0` + R1 + invoke
- [ ] Obsidian 打开 `docs/coding_wiki/` 冒烟（图谱应少孤点；勿开上级 `docs/`）
- [ ] 拷贝本 RUNBOOK 到 web：`docs/harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md`
- [ ] PR 写明：已启用 WikiTrack；勿默认 `--allow-wiki-gap`

### web 与 api 差异提示

| 点 | api | web 建议 |
|---|---|---|
| 规范 | `CODING_BACKEND_L2` | `CODING_*_L2` 前端规范路径 |
| 图谱 | `_tech_graph` G-L 分层 | 本仓 `_tech_graph` 读序（若有） |
| 质量门 | ruff + pytest | pnpm lint/test/build |
| vault | `docs/coding_wiki/` | 同左（勿开上级 `docs/`） |

---

## 7. 失败路径

| 触发 | 行为 |
|---|---|
| S5 dirty 挡 upgrade | commit/stash 后再 upgrade |
| upgrade 冲掉 overlay | 恢复后提交；记摩擦 |
| export edges=0 | 补 stable 等互链（见 topics/wikilinks_export） |
| close 缺 wiki_delta | 补字段；**不用** `--allow-wiki-gap` 当绿路径 |
| 误复制正文进 coding_wiki | 删副本，改回相对链 |

---

## 8. api 本波记录（dogfood）

| 项 | 值 |
|---|---|
| manifest | `2.19.0`（from 2.18.2） |
| 分支 | `task/harness-upgrade-2-18-migrate`（含 WikiTrack P0） |
| 单份真值 | 是（coding_wiki 仅指针） |
| export | 见合入前自检（含 topics/） |

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | v1 · api 00 统筹 dogfood · 供 web 复用 |
| 2026-07-28 | v1.1 · 钉 2.19.0 · lint-wiki-delta · vault=coding_wiki/ |
| 2026-07-28 | v1.2 · §0.5 从 2.18.0（web）起步 · api→web 差异与摩擦清单 |
