# Invoke：demo_agent_host_surface · 50-CLOSE 全链关账复核

- **task_slug**：demo_agent_host_surface
- **日期**：2026-10-16
- **触发**：维护者回报「web已完成」；本窗只读复核 web 仓并同步 api 仓 task 关账记录，未改 web 仓。
- **互链**：`invoke_20261016_00_task_shell.md`、`invoke_20261016_30_impl.md`、`docs/tasks/active/task_demo_agent_host_surface.md`。

## web 合并链（均已并 main）

| PR | 用途 | merge commit | 复核结论 |
|---|---|---|---|
| [#70](https://github.com/Cyning12/ops-desk-web/pull/70) | B1–B3 初版：菜单隐藏、Agent 工作台、默认落地 | `44a77db` | task 已记录 CI 双绿 |
| [#71](https://github.com/Cyning12/ops-desk-web/pull/71) | D4 修正：Agent 工作台改指 `/chat` 直接对话页 | `46c8c54` | task 已记录 CI 双绿 |
| [#72](https://github.com/Cyning12/ops-desk-web/pull/72) | 登录落地残留收口 `/chat` | `d039853` | MERGED 2026-10-16T08:13:15Z；CI `frontend` / `check` 均 SUCCESS |

## 最终代码证据（ops-desk-web main `d039853`）

- `src/layouts/AppLayout.vue:47`：菜单「Agent 工作台」→ `/chat`；`/lg-rag` 与 `/lc-evidence` 不出现在菜单。
- `src/router/index.ts:24`：根路径 redirect `/chat`。
- `src/router/index.ts:57-75`：`/chat` meta.title = `Agent 工作台`；`/lc-evidence`、`/lg-rag` 路由与组件保留，深链不拦截（D2）。
- `src/router/index.ts:104`：已登录访问 `/login` → `/chat`。
- `src/views/LoginView.vue:30`：登录成功无有效 redirect 时 fallback `/chat`。
- PR #72 diff：3 文件 +5/-5；`tests/router-guard.spec.ts` 断言随该残留决策点最小同步，非 api 面新增改动。
- web 工作树复核：HEAD `d039853` 与 `origin/main` 完全同点（当前检出分支后被维护者切至 `task/close-completed-active-tasks`，内容与 `main` 零 diff）；仅既有未跟踪 `.codex/`，本窗未触碰。

## 关账结论

- TC-1–TC-8 全 PASS；web 面无未闭环残留。
- api 仓 task 状态、D4、TC-5、TC-8、R4/R5、CLOSE 补记与经验总结已同步 PR #72。
- 仍归 maintainer：api 仓提交切分（与 eng-graph-mermaid 脏树隔离）及 task 文件 active→done 归档移位；本窗未 commit、未移动 task。
