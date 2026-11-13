# invoke_40

- **日期**：2026-11-13
- **task_slug**：p0prime-t2-chat-legacy-cleanup
- **hat**：40
- **来源**：P0' 任务卡 T2（组织人范围裁定拆 T2a/T2b）；维护者 m00177「签收，开始」
- **动作**：grep 零 ChatState/旧 chat 模块引用；test_chat_router.py 全绿（三端点零漂移）；干净环境（无 .env、无在途面）全量 pytest 零新增红；ruff check app tests；./scripts/graph-compile.sh；npx spec-wave task lint
- **已知本地干扰项**：主仓 .env:83 OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo 残留污染 strategy 测试子集（T1 已实证与 diff 无关）；在途面 scripts/ 触碰触发 N3 闸 O2 语义，提交后自清
