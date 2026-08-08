# FEEDBACK 复检 · harness 2.21.0 · from ops-desk-api

> **日期**：2026-07-28  
> **业务仓**：`ops-desk-api`（FastAPI · WikiTrack 已启用 · 字段已迁完）  
> **路径**：RUNBOOK §0b 快速路径 · `2.20.0` → **`2.21.0`**  
> **对照**：产品 CHANGELOG 2.21.0 · 两仓 FEEDBACK（ops U\* · web F-220-\*）  
> **PR**：https://github.com/Cyning12/ops-desk-api/pull/23

---

## 1. 命令实录

```text
npx @cyning/harness@2.21.0 upgrade --yes  → exit 0 · manifest 2.20.0→2.21.0
npx @cyning/harness@2.21.0 check          → 已是最新 · 包版本 2.21.0
git diff overlay（§1.2）                  → AGENTS / FRAGMENT 被冲 · 已从 backup 恢复
npx … task lint-wiki-delta --target .     → scanned=25 · missing=0 · PASS
npx … task lint-wiki-delta --strict --json→ ok:true · issues:[] · strict PASS
npx … wiki export --json --target . --root docs/coding_wiki
  → schema harness.wiki_graph.v1 · nodes=7 · edges=33 · warnings=[]
```

本仓无 `harness.pin.json` → §1.1 pin bump **跳过**（web F-220-01 不适用）。

---

## 2. 两仓 FEEDBACK × 2.21 吸收矩阵

| 来源 | ID | 产品 2.21 声称 | 本仓复检 | 结论 |
|------|-----|----------------|----------|------|
| ops | U1 Open Folder 假路径 | RUNBOOK 抬头「对准 git root」 | 文案已改 | **吸收** |
| ops | U2 overlay 被冲 | §1.2 overlay 自检必做 | 升 2.21 **仍冲** AGENTS/FRAGMENT；按 §1.2 恢复后绿 | **文档吸收 · 行为未消**（预期；须人工 diff） |
| ops | U3 local.json | §1.3 建议 gitignore | 已加 `.gitignore` + `git rm --cached` | **吸收（消费者落地）** |
| ops | U6 已迁完快速路径 | §0b | 本波只跑 §0b · 跳过决策树 | **吸收** |
| ops | R3 Python cache | §5.2 + ci/samples README | workflow 保持 `package-manager-cache: false` · pin `@2.21.0` | **吸收** |
| ops | R2/F-220-03 cp 路径 | §5.1 三法 clone/pack/raw | 文档可读；本仓未重 cp（已有 workflow） | **吸收** |
| ops | R4 export 旗标 | `--target` + `--root` 并列 | 命令可跑 · schema 正确 | **吸收** |
| web | F-220-01 pin bump | §1.1 POINTER | 无 pin · 跳过 | **N/A（本仓）** |
| web | F-220-02 pin CI 样例 | `lint-wiki-delta.pin.yml.example` | 本仓无 pin · 继续钉版本 yml | **N/A（本仓）** |
| web | F-220-04 钉目标版 | RUNBOOK 命令钉 `@2.21.0` | 本波全程钉版 | **吸收** |
| web | F-218-07 伪链降噪 | export `skipped_illustrative` | 本仓 export `warnings=[]`；字段未出现（无伪链样本） | **能力在包内 · 本仓无触发** |

**severity=block：无。** 新摩擦：**U2 在 2.21 仍复现**（RUNBOOK 已写自检，属接受态）。

---

## 3. 本仓落地变更（相对 2.20 PR）

| 项 | 动作 |
|----|------|
| manifest | `2.21.0`（from `2.20.0`） |
| CI | `@cyning/harness@2.21.0`（显式 patch 钉） |
| `.gitignore` | 忽略 `.cyning-harness/local.json` |
| git | 停止跟踪 `local.json` |
| overlay | 恢复 `AGENTS.md` · `FRAGMENT`（`l1/01_modules`） |

---

## 4. 结论

| 项 | 结果 |
|----|------|
| 钉版本 | **2.21.0** |
| 默认 lint | **PASS** |
| `--strict` | **PASS** |
| FEEDBACK 吸收 | 文档/CI/gitignore **到位**；overlay 冲刷 **仍须 §1.2** |
| 剩余缺口 | 无字段缺口；产品侧若要消 U2 需改 merge 策略（非本仓范围） |
