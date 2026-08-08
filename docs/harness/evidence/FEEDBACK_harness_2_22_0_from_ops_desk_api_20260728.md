# FEEDBACK · harness 2.22.0 · from ops-desk-api（overlay 部分根治 · U2）

> **日期**：2026-07-28  
> **业务仓**：`ops-desk-api`（FastAPI · WikiTrack 已启用 · G-L 试点）  
> **git root**：`/Users/cyning/Desktop/Ops-desk/ops-desk-api`  
> **起点**：manifest `2.21.0` → 目标钉 `@cyning/harness@2.22.0`  
> **对照**：产品 RUNBOOK §1.2 · ide/adapters README · CHANGELOG 2.22.0  
> **上波**：FEEDBACK 2.20 U2 · 2.21 复检（仍冲 · 文档吸收）  
> **PR**：https://github.com/Cyning12/ops-desk-api/pull/23

---

## 1. 结论（验收）

| 项 | 结果 |
|----|------|
| manifest | **2.22.0**（from 2.21.0） |
| pin | 无 · N/A |
| `graph_modules_path` | **`l1/01_modules`** |
| AGENTS local 块 | 关键词在（pre-30 / HG-PILOT / G-L0） |
| **合规路径：upgrade 后零手恢复** | **PASS**（第一次 / 第二次均未从 backup 手贴） |
| lint / `--strict` | scanned=25 · missing=0 · issues=0 · PASS |
| severity=block | **无** |

**U2 判定**：在合规定制（local 块 + profile）下，**部分根治成立** — 不再需要每次 upgrade 后从 backup 手恢复 AGENTS/FRAGMENT。

---

## 2. overlay 迁法（本仓）

1. `.cyning-harness/profile.json` 顶层增加 `"graph_modules_path": "l1/01_modules"`。  
2. `AGENTS.md`：产品 `cyning-harness:begin/end` 内改为产品片段（无仓特异词）；仓特异句移入紧随其后的 `cyning-harness-local:begin/end`。  
3. 先 commit 契约，再 `upgrade`（脏树会撞 S5；本波曾复现，属操作序摩擦）。

---

## 3. upgrade 实录

### 3.1 第一次（契约已提交 · 干净树）

```text
npx --yes @cyning/harness@2.22.0 upgrade --yes
→ overlay · FRAGMENT graph_modules_path → l1/01_modules
→ hint · overlay（v2.22+）… 打印 diff --stat
→ 升级完成 · manifest 2.22.0
```

| 文件 | 手恢复？ | 说明 |
|------|----------|------|
| AGENTS.md | **否** | local 块保留；未进 diff --stat（产品块替换后与 fragment 对齐） |
| FRAGMENT_30 | **否** | 占位展开为 `{l1/01_modules或—}`（非裸 01_struct） |
| CLAUDE.md / cursor mdc | **否** | 仅产品合法小 diff（v2.22 文案），保留 |

### 3.2 第二次（已钉 2.22 后再 upgrade）

```text
hint · overlay … 本波 diff --stat:（空）
local.json 未变（跳过写入）
```

| 检查 | 结果 |
|------|------|
| local 关键词 | 仍在 |
| FRAGMENT `l1/01_modules` | 仍在 |
| 相对 HEAD overlay diff | **空**（零手恢复） |

### 3.3 负面对照（产品 marker 内裸写）

注入 `NEGTEST_TOKEN_SHOULD_BE_WIPED` 于产品 begin/end **内** → `upgrade --force` 后：

| 结果 | |
|------|--|
| NEGTEST | **被冲掉**（边界仍在） |
| local 块 | **仍保留** |

---

## 4. lint / strict

```text
lint-wiki-delta            → PASS · scanned=25 · missing=0
lint-wiki-delta --strict   → PASS · issues=[]
```

未改 close / wiki_delta / pre-30 / HG-* 闸语义。

---

## 5. 剩余缺口与 severity

| ID | 现象 | severity | 说明 |
|----|------|----------|------|
| U2-ok | 合规路径零手恢复 | info | 2.22 目标达成 |
| S5-order | 未提交契约时 upgrade 被 S5 中止 | **P3** | 须先 commit/stash 或 `--force`；RUNBOOK 可加「先迁并提交 overlay 契约再 upgrade」一句 |
| prompts-cp | prompts 仍全量 cp | info | 预期；FRAGMENT 靠 profile 展开，勿再手改 FRAGMENT 长久定制 |
| U2-boundary | 产品块内裸定制仍冲 | info | 负面对照确认；纪律：勿写回产品 marker |

---

## 6. 对本仓 / 产品建议

| 侧 | 建议 |
|----|------|
| 本仓 | 合入 PR #23；关账遵守 wiki_delta；CI 钉 `@2.22.0` |
| 产品 | 可选：RUNBOOK §1.2 补「脏树 S5 → 先提交 local/profile 再 upgrade」；其余 U2 可关 |

---

## 7. 验收清单

- [x] manifest = 2.22.0  
- [x] profile `graph_modules_path=l1/01_modules`  
- [x] AGENTS 产品块外有 local 块且关键词在  
- [x] upgrade 后无需 backup 手恢复（合规路径 · ×2）  
- [x] FEEDBACK 已落盘  
