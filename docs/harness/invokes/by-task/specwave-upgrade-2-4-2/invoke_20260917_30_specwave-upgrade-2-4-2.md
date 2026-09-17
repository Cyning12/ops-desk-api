# Invoke：30 · specwave-upgrade-2-4-2

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30 |
| task_slug | `specwave-upgrade-2-4-2` |
| task_paths | `docs/tasks/active/task_specwave_upgrade_2_4_2.md` |
| related_review_or_none | `docs/harness/reviews/task_specwave_upgrade_2_4_2_audit_R1_20260917.md`（PASS-WITH-NOTES） |
| git_branch | `task/specwave-2-4-2` |
| created_utc_or_local | 2026-09-17 |
| notes | 维护者授权 00 本窗代签两闸 + 范围 F 裁定收编；00 只委派，30 由子 Agent 执行；过程轨升级，`app/` 仅范围 C-7 授权 1 行 npx 向量包名 + 2 处描述字面 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 维护者授权 00 代签 | Y | Y | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 PASS-WITH-NOTES | Y | Y | Y |
| HG-GRAPH-MODULES | —（graph_change_layer=none） | — | — | N | Y |

reviews：`task_specwave_upgrade_2_4_2_audit_R1_20260917.md` 存在？ **是**（PASS-WITH-NOTES · 零阻塞）

pre-30 invoke：`required_invoke_hats=30` → 无 pre-30 硬闸。

---

## 执行摘要

- 验收 **14/14 PASS**；提交 5 个（9502cdc → dc187e6）；PR #136 CI 全绿后合并 master
- 关键偏差：2.4.2 `SYNC_PROMPT_FILES` 白名单实证不含 prompts README.md，按范围 B-4 意图手合（仓内零本地补丁，不触 F-3），FEEDBACK §1 建议上游
- failure_paths F-1~F-10 无一触发（F-8 graph.json 日期戳接受入库；F-9 assets/pins exit 2 基线留痕不挡）
- 范围 F 收编 5 文件 6 行命令字面；N-2 补锚零命中；N-4 裸名残留未动
- FEEDBACK：`docs/spec/doc-health/feedback/2026-09-17_2.4.2_upgrade-sync-readme-and-new-gates-baseline.md`
