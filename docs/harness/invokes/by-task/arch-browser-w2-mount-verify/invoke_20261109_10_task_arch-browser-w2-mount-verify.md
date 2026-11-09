# Invoke: 10 · arch-browser-w2-mount-verify (task draft placement)

## Meta

| field | value |
|------|-----|
| hat_id | 10 |
| task_slug | `arch-browser-w2-mount-verify` |
| task_paths | `docs/tasks/active/task_arch_browser_w2_mount_verify.md` |
| related_review_or_none | `docs/harness/reviews/task_arch_browser_w2_mount_verify_audit_R1_20261109.md` |
| git_branch | `task/arch-browser-w2-mount-verify` |
| created_utc_or_local | 2026-11-09 |
| notes | task drafted in upstream branch `task/arch-browser-next-waves`; maintainer verbally authorized W2 start (m00153) |

## This round (10)

1. Acceptance criteria finalized: build_site.py -> uvicorn start -> curl assertions 200/404.
2. Out-of-scope finalized: no Nginx, no Vue login guard, no TLS/SSL.
3. graph_delta=none (no new modules/routes/tables).
4. Human gates: HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES all approved.

Forbidden this round: modify `app/**` business implementation.
