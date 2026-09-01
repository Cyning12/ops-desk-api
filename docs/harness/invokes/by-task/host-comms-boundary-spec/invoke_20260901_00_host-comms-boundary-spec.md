# Invoke：00 · host-comms-boundary-spec（C0）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | `host-comms-boundary-spec` |
| task_paths | `docs/tasks/active/task_host_comms_boundary_spec.md` |
| git_branch | `task/host-comms-boundary-spec` |
| created_utc_or_local | 2026-09-01 |
| notes | 维护者 Prompt 授权开 C 轨（串行波次 3）；docs-only SPEC 波 · **无 30**；00 不实现 |

---

## 阶段 A 卫生（摘要）

| 项 | 结果 |
|---|---|
| T6 done | `docs/tasks/done/task_lg_rag_deprecate_chat_stream.md` · related_pr=#108 · 关账 #110 MERGED |
| active 残留 | 开工前 active 仅 README |
| master | `d03708b`（#110）· 分支从最新 master 切出 |
| C0 前置 | 草稿「暂缓」前提达成：T6 #108（`/chat/stream` 410）· web T5 CLOSE（#109 · WAVE_READINESS §2 回填） |
| 上游草稿 | 自 `docs/hat-identity-feedback-host-plan` 取出随本 PR 入 master |

---

## GATE_VERIFY（00 扫描 · 本波无 30）

| human_gate_id | task表status | 说明 |
|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 · 维护者 Prompt 授权 |
| HG-SPEC-SIGNOFF | pending | 待 20-spec-audit 落盘后 00 代签（docs-only 代签授权） |
| HG-AUDIT-R1 | n/a | 无 30 |
| HG-GRAPH-MODULES | n/a | 无图谱变更 |

结论：**派 10-spec 起草 SPEC → 20-spec-audit；00 不改 `app/` / `tests/`**。

## 签收栏

00 代签 · 维护者 Prompt 授权（`PROMPT_00_t4_close_through_c4_serial` · 串行波次 3）· 2026-09-01
