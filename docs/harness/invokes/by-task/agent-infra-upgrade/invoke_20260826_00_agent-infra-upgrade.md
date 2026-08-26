# Invoke：00 · agent-infra-upgrade（总轨收官）

| 字段 | 值 |
|------|-----|
| hat_id | 00 |
| 总轨 slug | `agent-infra-upgrade` |
| 方案 | A · docs 先行 → 实现波次 1→2→3；波次 4 跳过 |
| 授权 | 维护者 2026-08-26：PR 权限一次授权 + CI 过自动 merge + 自动下一波 |

---

## 终态表

| 序 | 波次 | PR | 状态 |
|---|---|---|---|
| 0 | docs-hierarchy | [#65](https://github.com/Cyning12/ops-desk-api/pull/65) | CLOSE PASS |
| 1 | cap-portable-core | [#66](https://github.com/Cyning12/ops-desk-api/pull/66) | CLOSE PASS |
| 2 | so-schema-hygiene | [#67](https://github.com/Cyning12/ops-desk-api/pull/67) | CLOSE PASS |
| 3 | cap-mcp-real | [#68](https://github.com/Cyning12/ops-desk-api/pull/68) | CLOSE PASS |
| 4 | so-complete-adopt | — | **SKIPPED**（默认） |
| 收官+ | repo-branch-task-hygiene | — | 仍挂 DEF-002（另开） |

---

## 收官动作

1. 回写 `01_upgrade_roadmap` / 域 ROADMAP / L0 README 落地状态 → `stable`
2. task 全部迁 `docs/tasks/done/`
3. 过程闸与 invoke 齐备；**不**伪造测试

## 下一棒（非本轨）

- DEF-002：本地/远程无效分支与陈旧 task 卫生（维护者另令）
- 波次 4：须维护者再授权才开

| 2026-08-26 | 总轨收官 · 波次 1–3 DONE · 4 SKIP |
