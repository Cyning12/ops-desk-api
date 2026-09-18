# Invoke：30 · specwave-upgrade-3-0-0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30 |
| task_slug | `specwave-upgrade-3-0-0` |
| task_paths | `docs/tasks/active/task_specwave_upgrade_3_0_0.md` |
| related_review_or_none | `docs/harness/reviews/task_specwave_upgrade_3_0_0_audit_R1_20260918.md`（PASS-WITH-NOTES） |
| git_branch | `task/specwave-3-0-0` |
| worktree | `/Users/cyning/Desktop/Ops-desk/ops-desk-api-specwave-3-0-0` |
| created_utc_or_local | 2026-09-18 |
| notes | 维护者授权 00 代签 HG-TASK-DRAFT / HG-AUDIT-R1；过程轨 major；**不改 app/**；未 commit / push / merge |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 代签 | Y | Y | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 PASS-WITH-NOTES | Y | Y | Y |

reviews：`task_specwave_upgrade_3_0_0_audit_R1_20260918.md` 存在？ **是**（PASS-WITH-NOTES）

pre-30 invoke：`required_invoke_hats=30` → 无 pre-30 硬闸；00 open / gates_sign + 20 audit 已落盘。

结论：**可进入执行**

---

## 执行摘要（A→B→C→D→E）

| 范围 | 动作 | 结果 |
|------|------|------|
| A | package exact 3.0.0 + `npm install spec-wave@3.0.0 --save-exact` + `upgrade --yes` | manifest 3.0.0 / from_version=2.4.2；`.cyning-harness/` KEEP |
| B | refresh dry-run→stash→`--yes`→pop；`sync prompts --yes`；`skills install` | rewrites=0；local 块零变；HG-GRAPH-MODULES 保留；skills copied=8 |
| C | CI 三处 `@3.0.0`；tests 16 处字面 → 3.0.0；确认 harness_cli / GRAPH_CLI | app/ 零 diff |
| D | version/check/pytest/compile/verify | 全 exit 0 |
| E | assets verify / pins check | 均 exit 2（F-8 留痕不挡） |

验收标准：**13/13 PASS**（E 基线留痕计入 FEEDBACK）

### 退出码

| 命令 | exit |
|------|------|
| `--version` | 0（3.0.0） |
| `check --target .` | 0 · 已是最新 · 零 WARN |
| `pytest tests/test_capability_harness_cli.py` | 0（32 passed） |
| `./scripts/graph-compile.sh` | 0 |
| `verify --task …task_specwave_upgrade_3_0_0.md` | 0 · VERIFY: PASS |
| `assets verify` | 2（F-8） |
| `pins check` | 2（F-8） |

### failure_paths

F-1~F-6 / F-9 / F-10 未触发；F-7 graph.json 日期戳接受；F-8 assets/pins 留痕。

### FEEDBACK

`docs/spec/doc-health/feedback/2026-09-18_3.0.0_upgrade-assets-pins-baseline.md`

### 未做

未 commit / push / merge（等待维护者另令）。
