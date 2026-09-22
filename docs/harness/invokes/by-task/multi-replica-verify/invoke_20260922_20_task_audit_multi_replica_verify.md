# invoke · 20 · multi-replica-verify · task audit R1

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 20-task-audit（task R1 书面审查 · HG-AUDIT-R1 人签之前） |
| **文件** | `docs/tasks/active/task_multi_replica_verify.md`（R1 · 68550cc） |
| **上游** | `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 8236747） |
| **审查文** | `docs/harness/reviews/task_multi_replica_verify_audit_R1_20260922.md` |
| **required_invoke_hats** | `10,20,30,40`（含 20 · 本快照为强制落盘项） |

## 结论

**内容 PASS · 零内容阻塞**：范围 D1–D5 / 非范围 9 条 / failure_paths 14 条（SPEC 十条 + 双进程基建起停不稳 + 过程三）/ 验收 26 条 / 钉死契约 / R0–R5 逐块映射 SPEC 核对一致，实质差异为零。流程闸：HG-TASK-DRAFT / HG-AUDIT-R1 均 pending（blocks 30 · 本帽如实记录 · 签闸权属维护者）；HG-GRAPH-MODULES approved（本帽亲读复核成立 · 预期无新签义务按实判 + 偏离回炉条款）。审查文附维护者签闸清单；pending 期间不附 30 Prompt。

## 真跑留痕（本帽复核）

- `git branch --show-current` = `task/multi-replica-verify` ✓
- `npx spec-wave task lint --file docs/tasks/active/task_multi_replica_verify.md` = **LINT: PASS**（exit 0 复跑）
- pytest 基线：`python -m pytest tests --collect-only -q` = **1349 collected**（复跑一致）
- 双进程零先例：`grep -rnE 'uvicorn' tests/ --include='*.py'` = **零命中**；subprocess 仅 `test_capability_harness_cli.py`（复核一致）
- B1 抽 5 组：用例计数 11 文件全吻合 · conftest budget fixture :202-220 在案 · runbook 先例 4 文件在案（目录总数 16 vs 文写 15 · 非阻塞观察 1）· checkpointer 关联 15 文件口径复现 · ls tests 扫描口径 31 吻合
- HG-GRAPH-MODULES 亲读 `01_modules.md`：api :20 / capability :26（进程内注册表 · 非跨进程注册中心）/ lg_rag :27 / hitl :31 / db :33（checkpoint 表在案）· bootstrap 签 :55（2026-07-16）· 签录链至 :93（memory-compliance-delete）——**全部属实**
- 命名冲突扫 `multi_replica`：app/ tests/ scripts/ docs/_tech_graph/ **零命中**
- 否定性断言可测性：归属 FAIL 非 skip（变异检验①兜底）✓ · 图真的续跑（断言链三要素 + 只断 200=不合格 + 409/503 负路径先例在案）✓
- 变异检验三条 × 零生产码相容性：**成立**（变异对象落测试形态/进程 env/实证拓扑三面 · 变异②括号内 env 面合规路径 · 过程态变异与交付态 diff 白名单时态分离）

## 闸态

- `HG-TASK-DRAFT` = pending（本帽不签）
- `HG-AUDIT-R1` = pending（blocks 30 · 本帽不签 → **30 拒开工**）
- `HG-GRAPH-MODULES` = approved（模块表已建置 · 预期无新签义务按实判 + 偏离回炉条款 · 本帽亲读复核认可）
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## 下一棒

维护者：读审查文 → 签 HG-TASK-DRAFT 与 HG-AUDIT-R1 = approved → commit → 下发 30 Prompt。
