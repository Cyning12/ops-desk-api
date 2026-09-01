# Invoke：00 · lg-rag-deprecate-chat-stream（T6）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | `lg-rag-deprecate-chat-stream` |
| task_paths | `docs/tasks/active/task_lg_rag_deprecate_chat_stream.md` |
| git_branch | `task/lg-rag-deprecate-chat-stream` |
| created_utc_or_local | 2026-08-31 |
| notes | 维护者 Prompt 授权开工 T6（串行波次 2 · 含下线窗口授权）；阶段 A 卫生已过；**00 不实现** |

---

## 阶段 A 卫生（摘要）

| 项 | 结果 |
|---|---|
| T5 done | `docs/tasks/done/task_lg_rag_sse_token_stream.md` · related_pr=#105 · 关账 #106 MERGED |
| active 残留 | 开工前 active 仅 README |
| master | `11732cd`（#106）· 与 origin/master 一致 · 分支从最新 master 切出 |
| 生产 | deploy-api `27cf7af`/`11732cd` success |
| 下线窗口 | 维护者 Prompt 授权（本 invoke notes 即凭据）；410 vs 删路由 已在 00 定夺钉死=**410** |

---

## GATE_VERIFY（00 扫描 · 非 30 改码）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 · 维护者 Prompt 授权 | Y | N | 待 20 |
| HG-AUDIT-R1 | pending | 尚未 20 | Y | Y | **否** |
| HG-GRAPH-MODULES | approved | 不新增/不删一级模块（仅 chat 行/flow 备注） | Y | N | 待 R1 |

reviews：尚无 R1 → 30 不可开工。

pre-30 invoke：本文件（00）+ 下一棒 10。

结论：**派 10 → 20；00 不改 `app/` / `tests/`**。

## 签收栏

00 代签 · 维护者 Prompt 授权（`PROMPT_00_t4_close_through_c4_serial` · 串行波次 2）· 2026-08-31
