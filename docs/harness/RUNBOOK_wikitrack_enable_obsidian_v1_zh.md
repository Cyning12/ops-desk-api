# RUNBOOK · WikiTrack 启用 + Obsidian（可复用 · api dogfood）

> **版本**：v1 · 2026-07-28  
> **源仓 dogfood**：`ops-desk-api`（manifest ≥ **2.18.2**）  
> **消费方**：`ops-desk-web`（及同类已接入 Harness 的业务仓）**原样对照执行**  
> **原则**：**单份真值**（不把 `standards` / 部署文 / `_tech_graph` 正文复制进 `coding_wiki`）

---

## 0. 前置

| 项 | 要求 |
|---|---|
| Open Folder | 目标业务仓根 |
| 工作树 | `git status` 干净（或仅本 task 文件） |
| Harness | 先钉 **`@cyning/harness@2.18.2`**（或更新），**再**改 wiki 文档 |
| 非范围 | 不改 cyning-harness 产品仓；不做 Obsidian 插件开发；不力导向 Web UI |

破坏性（自 2.18.0，仍有效）：

- 缺 `wiki_delta` → `task close` **BLOCK**
- `none` / `n/a` 无 `wiki_delta_note` → **BLOCK**
- **勿默认** `--allow-wiki-gap`

---

## 1. 升级到 2.18.2（文档动作前）

在业务仓根：

    git checkout -b task/harness-upgrade-2-18-1   # 或沿用已有 upgrade 分支
    npx --yes @cyning/harness@2.18.2 upgrade --yes --target .
    npx --yes @cyning/harness@2.18.2 check

验收：

- `.cyning-harness/manifest.json` → `"version": "2.18.2"`
- `check` 输出「已是最新」· exit 0
- upgrade 后 **diff AGENTS / FRAGMENT**：恢复本仓 overlay（api 例：pre-30 行、G-L0 / HG-PILOT、FRAGMENT 的 `l1/01_modules`）

若仍停在 2.18.0：先完成 `wiki_delta` 存量补字段（见 USER_GUIDE §6.0b），再升 2.18.2。

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

    npx --yes @cyning/harness@2.18.2 check
    npx --yes @cyning/harness@2.18.2 wiki export --json --target .
    npx --yes @cyning/harness@2.18.2 verify --target . --task docs/tasks/active/task_wikitrack_enable_p0.md
    # 前端仓再加：pnpm lint && pnpm test && pnpm build
    # 后端仓再加：ruff check … && pytest …

`wiki export` 期望：

- `schema` = `harness.wiki_graph.v1`
- `nodes.length` ≥ 4
- `edges.length` > 0（wikilink）
- `warnings` 可空；未解析 `[[...]]` 须修链

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

- [ ] `upgrade` → manifest **2.18.2**
- [ ] 恢复本仓 AGENTS/FRAGMENT overlay（若有）
- [ ] 存量 task 已有 `wiki_delta`（若从 ≤2.17 升上来）
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
| export edges=0 | 补 `[[stable]]` 等互链（见 2.18.2 topics/wikilinks_export） |
| close 缺 wiki_delta | 补字段；**不用** `--allow-wiki-gap` 当绿路径 |
| 误复制正文进 coding_wiki | 删副本，改回相对链 |

---

## 8. api 本波记录（dogfood）

| 项 | 值 |
|---|---|
| manifest | `2.18.2`（from 2.18.1） |
| 分支 | `task/harness-upgrade-2-18-migrate`（含 WikiTrack P0） |
| 单份真值 | 是（coding_wiki 仅指针） |
| export | 见合入前自检（含 topics/） |

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | v1 · api 00 统筹 dogfood · 供 web 复用 |
