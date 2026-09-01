# Invoke：00 · lg-rag-sse-delta-realtime-spec（T5.1 docs-only）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | `lg-rag-sse-delta-realtime-spec` |
| task_paths | `docs/tasks/active/task_lg_rag_sse_delta_realtime_spec.md` |
| git_branch | `task/lg-rag-sse-delta-realtime-spec` |
| created_utc_or_local | 2026-09-01 |
| notes | 维护者 Prompt 授权起草 SPEC 增量（api 00/10-spec · T5.1）；docs-only · **无 30**；00 不实现 |

---

## 阶段 A 卫生（摘要）

| 项 | 结果 |
|---|---|
| T5 done | `docs/tasks/done/task_lg_rag_sse_token_stream.md` · related_pr=#105 |
| active 残留 | 开工前 active 仅 README；本波新建本 task |
| 分支 | 从 master 切出 `task/lg-rag-sse-delta-realtime-spec` |
| 触发 | web 联调 2026-09-01：EventStream 多帧 `answer`+`delta` 仍「一次性出全文」 |
| 产品裁定 | 传输层真流式；禁止前端假打字机入契约 SoT |

---

## GATE_VERIFY（00 扫描 · 本波无 30）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 维护者 Prompt 授权落盘 | Y | N | — |
| HG-SPEC-SIGNOFF | **approved** | 维护者令「签收」 | Y | N | — |
| HG-AUDIT-R1 | n/a | 无 30 | Y | Y（若有人改码） | **否** |
| HG-GRAPH-MODULES | n/a | 无图谱变更 | Y | N | — |

pre-30 invoke：本波 **无 30**；required ∩ {10,00} 落盘本目录。

**用户口头「开工实现」≠ 闸** — 本波拒改 `app/**`。

结论：**SPEC 已签收**；**仍拒 30 改码**（实现另 task · 须维护者令「开工」）。

## 签收栏

00 代签 HG-TASK-DRAFT · 维护者 Prompt 授权 · 2026-09-01  
**HG-SPEC-SIGNOFF=approved** · 00 代签 · 维护者令「签收」· 2026-09-01 · 凭据：`docs/harness/reviews/task_lg_rag_sse_delta_realtime_spec_audit_R1_20260901.md`（pass）
