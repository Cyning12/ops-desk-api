# FEEDBACK · harness 2.20.0 · from ops-desk-api

> **日期**：2026-07-28  
> **业务仓**：`ops-desk-api`（FastAPI · preset `fullstack-node-py` · WikiTrack **已启用**）  
> **起点**：manifest `2.19.0` → 目标钉 `@cyning/harness@2.20.0`  
> **真值对照**：产品 `docs/RUNBOOK_upgrade_wiki_delta_v1_zh.md` · USER_GUIDE §6.0b · `ci/samples/lint-wiki-delta.yml.example`  
> **本波 PR**：https://github.com/Cyning12/ops-desk-api/pull/23

---

## 1. 升级摩擦

| # | 现象 | severity | 说明 |
|---|------|----------|------|
| U1 | Open Folder 指令路径 `/Users/cyning/Desktop/Projects/Ops-desk/ops-desk-api` **不存在**；真根为 `/Users/cyning/Desktop/Ops-desk/ops-desk-api` | **P2** | 产品/调度 Prompt 与本机布局不一致；Agent 须自行定位 git root。建议 RUNBOOK/调度模板写「定位 git root」而非写死 Projects。 |
| U2 | `upgrade --yes` **冲掉** `AGENTS.md` harness 片段定制（丢 `pre-30 invoke` 拒改码句 · 丢 `HG-PILOT-OPSDESK-GLAYER`/`G-L0` 关键词）；`FRAGMENT_30` 把 `HG-GRAPH-MODULES` 占位从本仓 `l1/01_modules` **回退**为产品默认 `01_struct` | **P2** | merge(replace marker) / prompts 全量覆盖。本仓已从 backup 恢复 AGENTS，并手改回 FRAGMENT 的 `l1/01_modules`。RUNBOOK §1 宜显式写「upgrade 后必 diff AGENTS/CLAUDE/cursor/FRAGMENT overlay」。 |
| U3 | `.cyning-harness/local.json` 写入本机 npx 缓存绝对路径 | **P3** | 多机/CI 无意义；本仓未 ignore。建议产品：推荐 gitignore，或 upgrade 不改写已存在的 local 路径。 |
| U4 | 无 `package.json` 时每次 `npx @cyning/harness` 均 `npm warn exec … will be installed` | **P3** | Python 仓常态；CI 样例钉 `@2.20` + `--yes` 正确。本地可接受。 |
| U5 | 环境出现 `npm warn Unknown env config "devdir"` | **P3** | 与 harness 包无关（本机 npmrc）；易误读为 upgrade 失败噪音。 |
| U6 | 起点已是 **2.19.0** 且字段已齐 → 本波升级几乎零字段工作 | **info** | RUNBOOK 对「从低于 2.18 升」叙述充分；对「已 2.19 + WikiTrack」可加一行「仅钉版本 + 可选 CI/--strict dogfood」。 |

---

## 2. lint / strict 摘要

```text
npx @cyning/harness task lint-wiki-delta --target .
→ scope: all · scanned: 25 · strict: false · missing: 0 · issues: 0
→ LINT-WIKI-DELTA: PASS · exit 0

npx @cyning/harness task lint-wiki-delta --target . --strict
→ scope: all · scanned: 25 · strict: true · missing: 0 · issues: 0
→ LINT-WIKI-DELTA: PASS · exit 0 · **strict PASS**

--json --strict → {"ok":true,"missing":[],"issues":[],"scanned":25,"scope":"all","strict":true}
```

| 项 | 结果 |
|----|------|
| 缺字段扫迁 | **无需补字段**（2.18→2.19 波已齐） |
| 决策树选用 | 本仓 `wiki: true` + 已有 `docs/coding_wiki/` → 新 task 用 `none`+note（非 `n/a`） |
| `--strict` | **PASS**（none/n/a 均有 note；path 存在） |
| 剩余缺口 | **无** |

---

## 3. RUNBOOK 缺口

| # | 缺口 | severity | 建议回填 |
|---|------|----------|----------|
| R1 | §1 未强调 overlay 必 diff/恢复（本仓已踩） | **P2** | 增一步：「upgrade 后 `diff AGENTS.md CLAUDE.md .cursor/rules/05-harness-starter.mdc`」 |
| R2 | §5 `cp path/to/@cyning/harness/ci/samples/...` 对消费者不具体 | **P3** | 给可复制：`$(npm root -g)` 不可靠；推荐 `npx` 找到包内路径，或文档写「从 GitHub raw / 发布 tarball 复制」 |
| R3 | 未区分 **Python 无 package.json** vs Node 仓挂 CI 的差异 | **P2** | §5 或 ci/samples README 已有 pnpm 坑；RUNBOOK 正文可交叉链一句「FastAPI/npx-only → `package-manager-cache: false`」 |
| R4 | `wiki export` 文档混用 `--root` / `--target`（本仓 coding_wiki 钉 `--target`，CLI 接受 `--root`） | **P3** | USER_GUIDE / RUNBOOK 统一旗标名 |
| R5 | 未说明「已迁完仓」最短路径（check → lint → strict → 挂 CI） | **P3** | 加「快速路径」小节，避免重复读完整决策树 |

---

## 4. CI 可复制性

| 项 | 评估 |
|----|------|
| 样例可用性 | **高**：直接可挂；本仓已复制为 `.github/workflows/lint-wiki-delta.yml` |
| Python/FastAPI | **必须** `package-manager-cache: false`（与 `tech-graph.yml` 一致）；本仓无 `package.json`，无 pnpm 风险但仍按样例关闭缓存 |
| 钉版本 | 样例 `@cyning/harness@2.20` 正确；避免漂到 next |
| 失败策略 | 本仓字段已齐 → **硬失败**默认 lint；`--strict` 留注释（本地关账预检），符合 RUNBOOK §0「迁完再硬失败 / 半迁勿开 strict」 |
| 与既有 workflow | 独立 job；不改 `pytest.yml` |

**复制命令（本仓实际）**：

```bash
# 对照产品样例手写/粘贴（本机无全局包路径时）
# → .github/workflows/lint-wiki-delta.yml
# 关键：branches: master；注释说明 Python npx-only
```

---

## 5. severity 汇总表

| ID | 主题 | severity | 阻塞升级？ | 建议归属 |
|----|------|----------|------------|----------|
| U1 | Open Folder 路径假 | P2 | 否 | 调度 Prompt / 多仓导航 |
| U2 | overlay 被冲 | P2 | 否（可恢复） | RUNBOOK §1 + ONBOARDING |
| U3 | local.json 本机路径 | P3 | 否 | upgrade 行为 / gitignore 建议 |
| U4 | npx 重复安装 | P3 | 否 | 文档说明即可 |
| U5 | npm `devdir` 噪音 | P3 | 否 | 环境；非包 bug |
| R1 | overlay 步骤缺失 | P2 | 否 | RUNBOOK 回填 |
| R2 | cp 样例路径模糊 | P3 | 否 | RUNBOOK §5 / ci README |
| R3 | Python CI 交叉链不足 | P2 | 否 | RUNBOOK ↔ ci/samples |
| R4 | export 旗标名 | P3 | 否 | USER_GUIDE |
| R5 | 已迁完最短路径 | P3 | 否 | RUNBOOK |
| — | **strict PASS** | info | — | dogfood 成功 |

---

## 6. 环境与命令实录（摘要）

| 步骤 | 命令 / 结果 |
|------|-------------|
| 分支 | `task/upgrade-harness-2-20-runbook-feedback` ← `origin/master` |
| upgrade | `npx @cyning/harness upgrade --yes` → exit 0 · manifest `2.20.0` · from `2.19.0` |
| check | `状态: 已是最新` · 包版本 `2.20.0` |
| overlay | 恢复 `AGENTS.md` 定制 |
| lint | PASS · scanned=25 |
| strict | **PASS** · scanned=25 |
| CI | 已挂 workflow |
| 非范围遵守 | 未改产品仓源码 · 未 publish · 未改 ops-desk-web · 未直推 master |

---

## 7. 可选 BACKFILL 指针

见同目录：`BACKFILL_DRAFT_harness_2_20_0_ops_desk_api_20260728.md`（产品维护者可选用，**非**本仓合入条件）。
