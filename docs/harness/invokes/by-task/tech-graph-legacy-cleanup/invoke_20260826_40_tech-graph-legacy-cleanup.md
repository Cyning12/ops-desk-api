# Invoke · 40-self-check · tech-graph-legacy-cleanup

**task_slug**: `tech-graph-legacy-cleanup`  
**hat**: `40-self-check`  
**timestamp**: 2026-08-26T06:16:00Z  
**actor**: Auto  
**outcome**: success

## 验收勾选

| 项 | 结果 |
|---|---|
| 根 `graph.json` 不存在且 compile 不再生 | PASS |
| `shared/graph.json` 仍为真值 · check 绿 | PASS（9 graphs） |
| `01_struct.md` 已删 · 读序指向 `l1/01_modules` | PASS |
| QUICKREF / backups 已删 · profile/manifest 保留 | PASS |
| `scripts/legacy/` 已清 | PASS |
| `graph-compile.sh` exit 0 | PASS |
| `git diff app/` 空（本意图） | PASS（`app/tools/` 仍 untracked 未纳入） |

## 偏差

① kit compile 会保留/回写 `00_main.md` Sub-graph Links 旧 footer → 30 后手工改指 `l1/01_modules` + `shared/02_version`（已落盘）。  
② 历史 done/SPEC 中 `01_struct` / `scripts/legacy` 字面按非范围保留。
