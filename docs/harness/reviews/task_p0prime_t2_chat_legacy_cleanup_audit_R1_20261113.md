# R1 审查文：P0' T2a 旧 chat 计算栈清除（开工前审查）

- **日期**：2026-11-13
- **task_slug**：p0prime-t2-chat-legacy-cleanup
- **分支**：task/p0prime-t2-chat-legacy-cleanup（base 77a1102 = master T1 CLOSE 合并点）
- **审查帽**：20 · **结论**：approved（维护者 m00177「签收，开始」，覆盖 P0' T1–T7）

## 审查范围

- task 单 docs/tasks/active/task_p0prime_t2_chat_legacy_cleanup.md（范围 23 文件 / 非范围六条 / 验收 8 条 / R0–R5）
- N3 自注册 registry.yaml entry（base=77a1102 · allowed 面与签认面一致）

## 审查结论

1. **死码判定证据充分**：app/ops/chat/ 计算栈 7 件零运行时消费者——app/ops/router.py 仅挂 chat/router.py（410 墓碑 + models + sessions/latest），全仓 import 闭包自查仅 chat 包内部互引 + 死测试 + 2 冒烟脚本。
2. **范围拆分裁定成立**：卡 T2 原文 bundle 的 alembic drop 三表被 web 活依赖 /ops/chat/sessions/latest 阻塞（ops-desk-web/src/api/chat.ts:22 fetchLatestSession + src/stores/chat.ts:552 调用 + :872/:903 发送/续答硬门）。单仓纪律禁跨仓同波次改码 → 拆 T2a（本卡纯代码面）+ T2b（端点 410 化 + 归档导出 + drop 三表，web 前置另落卡）。卡验收「零 ChatState 引用」归 T2a、「迁移 up/down」归 T2b；偏差将记 issue #23。
3. **测试手术有承接**：test_llm_retry.py 的 stream 纪律用例改写至 lg-rag app/ops/lg_rag/answer_stream.py:58-90 complete_answer_streaming（中途异常→已发 delta 保留 + 降级 provider.complete 整段，complete_stream 零重试），纪律不丢；接线用例随被测模块死亡，单元逻辑由文件内其余用例与 lg-rag 面既有用例承继。
4. **保留面钉死**：chat/router.py 三端点零 diff（test_chat_router.py 全绿为机断钉）；models.py 三表类与 alembic 归 T2b 不动；test_chat_history_api.py（lg-rag 历史 API）不动；图谱 yaml 不动仅 .md 注记（R4 warn-only 不炸）。
5. **风险登记**：残留 import（ImportError）与测试手术误伤为最锋利边界——全仓 grep 零残留 + 干净环境全量 pytest 兜底（T1 实证工作流：提交先行 + 无 .env worktree）。

## 遗留项（非本卡范围）

- T2b：/chat/models + /chat/sessions/latest 410 化 + 归档导出 + drop ops_runs/ops_run_events/ops_sessions_chat（前置 = web 仓摘除 session 硬门 + prod 归档导出 runbook）。
- T2a 合并后 ops_runs/ops_run_events 即零写入方（T2b drop 前仅剩表定义）。
