# invoke · 30 · execute · api-prompts-sync-3-5-0

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-30 |
| **帽** | 30 |
| **task** | `docs/tasks/active/task_api_prompts_sync_3_5_0.md`（v0.4） |
| **授权** | 双闸 approved（00 代录 · 授权锚 m00500 · R1 审查文 docs/harness/reviews/task_api_prompts_sync_3_5_0_audit_R1_20261030.md 通过零阻塞）· 全程本地严禁 push/PR |
| **retention** | minimal（工具类零业务面 · 承 task_specwave_upgrade_3_5_0 精简形态先例） |

## 闸扫描（GATE_VERIFY 真值 = task 表）

| gate | status | 依据 |
|------|--------|------|
| HG-TASK-DRAFT | approved | task 人工闸表（00 代录 · m00500） |
| HG-AUDIT-R1 | approved | task 人工闸表（00 代录 · m00500） |
| HG-GRAPH-MODULES | n/a | graph_change_layer=none |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |

`npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_api_prompts_sync_3_5_0.md` → VERIFY: PASS · EXIT=0（图谱锚点检查 skipped · graph_path_unreachable · graph_modules_path=l1/01_modules · INFO 不挡 · 照登）

## 执行记录

1. S1 dry-run 复跑：EXIT=0 · skip 4 / add 1（FRAGMENT_graph_first_read_v1_zh.md）/ conflict 8 —— 与起草基线逐字一致零漂移
2. S2 conflict 8 逐枚 diff：全部为上游实质新增被本地旧版遮蔽（仓内零 cyning-harness-local 块 · 与 R1 实证一致）——7 枚「图谱先读」条件条款 + 1 枚（TASK_TEMPLATE）闸表 4 列/粗体格式说明；全部走人工合并（保留本地 + 吸收上游 · 零 --force）
3. 合并校验：7 枚合并后与包内资产零 diff；30-execute-code 保留本地 `_tech_graph/` 硬编码读序项（本仓图谱实体目录 · 上游 3.5.0 将其条件化 · 合并 = 本地项 + 上游条件条款并存）· 其余上游行全吸收
4. S3 apply：`sync prompts --target . --yes`（零 --force）→ EXIT=1（conflict 1 未覆盖提示 · cli-sync-prompts.js:156-157 预期语义照登）· written 1 = FRAGMENT_graph_first_read_v1_zh.md · skip 11
5. V3 sha256：3739570a…f565 与包内同名件一致；V4：apply 前后 conflict 8 枚 sha256 逐枚不变（apply 零越写 · post-merge == post-apply）
6. S4 回归：graph-compile EXIT=0 图谱零 diff；task lint PASS EXIT=0；verify --task task_lg_rag_gate_produces_unfulfilled.md 同步前后输出逐字一致（VERIFY: BLOCKED · HG-AUDIT-R1 pending · EXIT=2 · 零行为变化）
7. 复跑 dry-run 收敛：skip 12 / add 0 / conflict 1（30-execute-code · 明示保留项照登）· EXIT=0
8. 维护者脏文件 docs/arch-browser/dist/site-data.json 全程未动；白名单外零写入

## commit 链

（实现 commit）prompts 同步面 →（docs commit）task 自检回填 + 本 invoke —— 哈希见 task 自检结论

## 结论

**S1–S5 / V1–V7 全绿 · sync 执行完成**；FRAGMENT_graph_first_read 物化 ≠ 接入（生效前提 = profile graph_modules_path 可达目录 · 即 task_api_graph_anchor_profile_fix 修正面 · 本仓当前 skipped=graph_path_unreachable · 如实照登禁拔高）。
