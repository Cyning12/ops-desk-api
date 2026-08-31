# FEEDBACK · close_pr_merged · gh TLS timeout

> **试点仓**：ops-desk-api  
> **日期**：2026-08-31  
> **kit 版本**：1.10.0  
> **操作者**：00 / CLOSE  
> **关联**：`task_lg_rag_sse_stream_updates` · `task_dsh_coding_kit_upgrade_1_10_0`

---

## 1. 场景

对已合入 master 的 task 跑 `task close`。`related_pr` 已填 `#97` / `#98`；`git log` 可见 merge commit。本窗 `gh pr view` / kit 内 GraphQL 均报 `error connecting to api.github.com` / `TLS handshake timeout`。

## 2. 命令与输出摘要

    CLOSE: BLOCKED · close_pr_merged: 无法解析关联 PR（gh 失败或无 PR）: Post "https://api.github.com/graphql": net/http: TLS handshake timeout

加 `--allow-no-pr-merge` 后 dry-run `CLOSE: READY`；`--yes` → `CLOSE: PASS`。

## 3. 期望 vs 实际

| 期望 | 实际 |
|------|------|
| `related_pr=#97` 且 master 含 Merge #97 即过闸 | 仍强制实时 gh GraphQL；网络超时即 BLOCK |

## 4. 影响

- [x] Hub / PR 闸误伤（网络瞬断挡关账）
- [ ] 仅文案困惑

## 5. 建议（给 kit）

`related_pr` 已填 + 本地 `git log --grep='#N'` / merge commit 可作 fallback，不必唯一依赖 GraphQL。

## 6. 本仓临时对策

`--allow-no-pr-merge` + CLOSE invoke 写明 MERGED 证据（commit SHA）+ 本 FEEDBACK。
