# invoke_20261115_10_task_draft

## 内容

10 帽起草：task 档按设计真源 07 §5 T2 行落盘；范围=goals router+注册+REST 测试；非范围=入口接线/uq 迁移/注入/SSE；红线=跨租户 404 防探测、词表外 422 前置。

## 结果

- 勘察锚点：goal_store 接口（T1 #387 已交付 · patch 显式抛 404/409）· tenant 解析先例 lg_rag/router.py:376-384 + hitl/router.py:59-62,755 · resolve_header_against_session tenant_context.py:57 · override_auth fixture 体例 test_chat_router.py。
- lint 待跑。

## 偏差记录

无。
