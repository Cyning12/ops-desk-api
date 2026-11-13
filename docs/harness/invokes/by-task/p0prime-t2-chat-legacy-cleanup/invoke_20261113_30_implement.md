# invoke_30

- **日期**：2026-11-13
- **task_slug**：p0prime-t2-chat-legacy-cleanup
- **hat**：30
- **来源**：P0' 任务卡 T2（组织人范围裁定拆 T2a/T2b）；维护者 m00177「签收，开始」
- **动作**：删 chat 计算栈 7 件（graph/service/nodes/rag_nodes/state/streaming/sse）+ __init__.py 墓碑注记；死测试 3 整件删除 + 5 件手术（test_llm_retry.py 改写 1 用例承接 lg-rag complete_answer_streaming）；删 scripts/rag_smoke.py、trace_smoke.py；docstring 两处（lg_rag/__init__.py、llm/usage.py）；图谱 01_modules.md 备注+签收行、10_flow_chat.md/11_flow_sync_to_chat.md 退役注记；registry.yaml N3 自注册
- **非范围**：chat/router.py、chat/schema.py、models.py 三表类、alembic/ 零 diff；web/ios/workspace 仓零改动
