# invoke_40 · acceptance（p3-t5-admin-memory-api）

## 内容

- feat PR：Cyning12/ops-desk-api#422（`feat(p3-t5-admin-memory-api): admin memory 浏览/撤销端点（issue #23）` · --body-file 中文 · base master）。
- CI 四 job 全绿：check 16s · import-linter 10s · lint-wiki-delta 11s · pytest 2m30s（全量套件含本波 23 用例）。
- squash merge：merge commit `0ab54c7b`。

## 验收台账（task 档 10 条逐条）

| 验收 | 锚 | 结果 |
|---|---|---|
| facts 分页浏览 跨页不重不漏 + 默认 active + status/kind 过滤 | test_facts_pagination_keyset / test_facts_default_status_active / test_facts_filter_status_kind | 真 PG 绿 |
| facts 参数校验 limit=201/0 · 词表外 · 坏 cursor · 缺 tenant → 422 | test_facts_limit_422 / test_facts_vocab_422 / test_facts_bad_cursor_422 / test_facts_missing_tenant_422 | 绿 |
| 投影无 embedding（键集合断言） | test_facts_projection_excludes_embedding | 绿 |
| revoke 幂等 首撤 N · 重放 0 · 无匹配 0 | test_revoke_first_affected_n / test_revoke_replay_affected_0 / test_revoke_no_match_affected_0 | 绿 |
| revoke 缺 user_id tenant 范围全撤 | test_revoke_tenant_wide_without_user（affected=2 · 异 tenant/异 key 零影响） | 绿 |
| 审计留痕 key/tenant/affected 不记 value | test_revoke_audit_log（caplog 断言） | 绿 |
| 鉴权矩阵 401/403/零写 | test_facts_unauthorized_401 / test_revoke_unauthorized_401_zero_write / test_episodes_unauthorized_401 / test_facts_viewer_403 / test_revoke_viewer_403_zero_write / test_episodes_viewer_403 | 绿 |
| episodes 只读 GET 200 过滤 + 写动词 405/404 | test_episodes_list_and_filters / test_episodes_write_verbs_rejected | 绿 |
| pytest 目标文件全绿 + ruff + lint-imports 零新 forbidden | 23 passed · ruff PASS · 12 kept 0 broken | 绿 |
| CI 四绿 + squash merge | PR #422 · merge 0ab54c7b | 绿 |

## 偏差

- 无。并行波次无 CONFLICTING（rebase 未触发）。

## 结果

40 acceptance 完成，进 50 close。
