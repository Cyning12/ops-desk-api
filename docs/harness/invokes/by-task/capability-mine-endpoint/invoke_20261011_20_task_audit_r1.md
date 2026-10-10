# Invoke · 20 · capability-mine-endpoint（R1 task-audit）

- **hat**：20-task-audit
- **task_slug**：`capability-mine-endpoint`
- **日期**：2026-10-11
- **对象**：`docs/tasks/active/task_capability_mine_endpoint.md`（fc9885e 链）· 上游 SPEC v0（HG-SPEC-SIGNOFF approved）+ R1 审 PASS-WITH-NITS（N1–N3 回填核）
- **结论**：**BLOCKER · 退回 10 修订** —— 内容面 C1–C12 全通过（锚点 13 行全核真：deps.py:18-115/:114 · models.py:40 · visibility.py:112-135 · admin/capability.py:163-214 N1 修正锚点 · hitl/router.py:94/:172 {items,count} · gateway.py:133-143 · 包内 APIRouter 禁令 docstring :1-6 · grep capability/mine 码面零命中；N1/N2/N3 回填到位，N3 `roles=frozenset({user.role})` + TC3 ⊆ 对拍钉死；钉死契约八条对齐 SPEC 纪律；TC1–TC7 可机断；落点 capability_mine.py / baseline 默认不叠加两候选倾向合理且不锁死），唯机械闸 `npx spec-wave task lint --file` **FAIL · [E5] 缺 ### 自检结论 节**（兄弟 task 同命令 PASS · 节在其 :190）→ 退 10 补节后复核。
- **nits 照登**：n-1 钉死契约 1/FP-1 漏引第三 401 分支 deps.py:49-51 · n-2 R1 思考轮「12 行」与锚点表实 13 行计数差。
- **闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending · 本帽不代签 · 30 拒开工。
- **产物**：`docs/audits/task-review/20261011_capability-mine-endpoint_r1.md`（骨架 e87d85f 先行 → 填肉续 commit）；本帽未改 task 正文/闸表/app/tests。

| 2026-10-11 | 20 |
