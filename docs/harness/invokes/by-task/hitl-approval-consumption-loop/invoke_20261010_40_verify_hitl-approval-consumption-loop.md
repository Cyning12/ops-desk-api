# 40 invoke · hitl-approval-consumption-loop（T1 核验帽）

> **帽**：40-verify · **task**：docs/tasks/active/task_hitl_approval_consumption_loop.md
> **核验对象**：T1 30 交付 4 commits（f7177bf / b281d7c / 8503456 / c70a9d4 · 分支 task/hitl-approval-consumption-loop · 基 master 7853334）
> **日期**：2026-10-10 · **结论**：**PASS（带偏差登记 · 可进 PR 队列）**——核验对象扩为 6 commits（+80eb872 增强 +b78d814 回填 · 00 接管段 +lint 修复 commit 见下）
> **纪律**：独立复跑 · 不采信 30 自报 · 不因落地者身份放松

---

## 核验总表（七项 · 逐项回填）

| # | 核验项 | 结论 | 实证 |
|---|--------|------|------|
| 1 | diff 面对拍 + 五文件空 diff | **PASS** | diff master --stat：nodes.py+148 / 5 随改文件 / 新测试 508 行 / 图谱+文档 · 面外零改动；registry/policy/delegation/store/router 五文件 diff 行数全 0（亲跑） |
| 2 | 新测试抽跑 + 断言强度亲读 | **PASS** | 34 枚（30 收尾棒增强后）全绿两轮；亲读 TA2 变异组 mutate 真实造成不匹配（非假绿）；Db 组真 DbHitlStore alist/aget 路径（DB_AVAILABLE=True 非 skip） |
| 3 | 全量 pytest / ruff / graph-compile | **PASS（口径注记）** | 全量 1713 passed · 1 skipped · 0 failed（353s · 30 棒净态口径 mode 中性）；ruff 触及七文件与 base 7853334 逐枚同构零新增（新测试文件 2 枚已修：F841/F821 · 00 收尾 commit）；graph-compile EXIT=0（graph.json 日期噪音还原）· ⚠️ 并发窗 .env 被翻 enforce 致窗口性红 4 枚（capability_lookups×3+lg_rag_multi×1 · delegation no_token）——env 覆盖/复原后复绿 · 非代码归因（T3 先例口径）· **master 基线对拍钉死（2026-10-10 09:58）**：主仓 master eb8e93d 同款 4 测本地同红（CI 绿）→ 本地环境性红 · 与 T1 零关系 |
| 4 | B1 十四处 + 门禁 | **PASS** | 三测试文件 62 passed（30 棒亲跑）+ capability_acceptance.sh 失败 0 跳过 1（联调桩目录缺 · 环境性）· CAP_EXIT=0 |
| 5 | TA3 live 段 | **PASS 带偏差（末段见「重要发现」）** | 六 env 组（三 env + T3 候选口 + OPS_HITL_PERSISTENCE=db + OPS_CAPABILITY_ALLOW_WRITE=1）· uvicorn :8020 · docker PG · run 7b3178041bf44edba8a81d40b18be22e：① hitl.waiting（unlock_subtask_id=sid **回填 live 实证**）② pending 200 可见 ③ decide(approved) 200 persisted ④ **resume 200**（D2 时代 409 已消 · 逐字目标达成）⑤ 见重要发现 |
| 6 | 闸面终态 | **PASS** | verify EXIT=0 · task lint PASS · 01_modules.md lg_rag/hitl 行备注 + 在册行（00 代录 2026-10-10）实证在案 |
| 7 | task 自检段回填 | **PASS** | 已回填（本帽/00 协同 · 见 task 修订行） |

---

## 过程留痕

- 2026-10-10 40 骨架先行落盘（本文件）。
- **工作区状态注记**：开工即发现 `tests/test_hitl_approval_consumption.py` 存在**未提交修改**（工作区版较 HEAD 多 `test_ta2_ttl_db_store_real_read_path_iso_str` 等增强 · 详见核验项 2 实证）。40 纪律「commit 只 add 自产文件」→ 该文件不入 40 commit；按「committed 态 / 工作区态」双面如实核验登记。

---

## 重要发现（live 实证 · 上抛 SPEC v2 / T2 裁定）

**replan 重盖章使消费键失配**：live 中每次 resume 后 supervisor 走 LLM 正常重规划 →
`_stamp_host_plan` 重盖 sid（:1→:2→…→:11 逐轮递增实证），消费键
(run_id, subtask_id, capability_id) 永不命中 → FP-3 再拦循环（每轮 decide+resume
均 200 但末段 done{completed} 不可达）。SPEC FP-3 假设「_carry_plan 沿用 id 可命中」，
实读 nodes.py:1017-1054 证实 carry 只在 LLM 重规划**失败/非法**时触发；正常 replan
必重盖章。机制段（TA3③ pytest · sid 保留形态）消费成环已证；live 收敛需裁定：
resume 后对 approved 步骤走 carry 保号 / 或消费键放宽（(run_id, capability_id) 粒度）。
**登记：非本 task 回归 · T1 范围（手动模式 resume 200 成环机制）达成 · 留 T2/SPEC v2。**

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 40 骨架先行落盘（七项核验占位 + 工作区未提交修改注记） |
