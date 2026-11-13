# invoke_50

- **日期**：2026-11-13
- **task_slug**：p0prime-t2-chat-legacy-cleanup
- **hat**：50（CLOSE）
- **动作**：PR #369 CI 全绿（pytest/import-linter/lint-wiki-delta/check）→ merge a4266f55；registry entry 转 closed 钉 wave_tip=a4266f5；task 档迁 docs/tasks/done/ 状态 closed。
- **如实登记**：① 30 首版漏扫 evals/ 致 test_golden_eval_runner collection ImportError，已内联承接 GRADER 常量补救并扩范围 1 文件；② 主仓 .env（DB 指向 localhost:5432 无服务）致 test_chat_history_api 单件红，baseline 干净 worktree 对照证实与 diff 无关；③ 范围裁定 T2a/T2b 拆分偏差将记 issue #23（web 活依赖 /chat/sessions/latest 前置 T2b）。
