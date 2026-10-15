# invoke：10-task 起草（lg_rag_sse_run_worker · 2026-10-14）

> **帽位**：10-task（任务需求分析 · 只起草文档 · 零实现码改动）  
> **分支**：`task/lg-rag-sse-run-worker`（base master `9ee928c`）  
> **产物**：`docs/tasks/active/task_lg_rag_sse_run_worker.md` + active README 一行更新 + 本 invoke  
> **硬约束**：禁改 `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` 正文

---

## 输入

| 来源 | 内容 |
|------|------|
| 维护者 | E3 + 不改旧 task · 新 task 关联 co-CLOSE · 授权重签 D1 落新 task |
| 方案真值 | `docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_00_e3_wave_b_plan.md` |
| 生成令 | `…/invoke_20261014_00_e3_new_task_spawn.md` |
| 旧 task 史实 | Wave A / TC5 live×3 FAIL / 停派 ASGI 钩（正文冻结） |

## 裁定落录（10 写入新 task）

| ID | 值 |
|----|-----|
| D1 | **A+B**（B 为主；A=worker 死后补偿终帧 · 不赌 ASGI disconnect）· **00 代录已授权** · HG-\* 仍 pending |
| D2 | 建议：成功普通 `done`；失败 `error{stage:lg_rag.worker_failed}`；补偿可 `done{disconnected}` |
| D3 | **须同步开 web task**（CTA） |
| freeze | `lg-rag-sse-v1` · 禁 silent 新 `event_type` |
| co-CLOSE | 与 `task_lg_rag_sse_disconnect_completion` 同批关账 |

## 交付

1. 完整 task：Harness 元信息 · 人工闸 pending · D1–D3 · 范围 F5–F7+补偿 · 非范围 · FP · TC-B1–B10 · R0–R5 · 必读 · 自检占位。
2. 关联句：依赖/背景显式链旧 task 路径。
3. `npx --yes spec-wave@3.3.0 task lint --file docs/tasks/active/task_lg_rag_sse_run_worker.md`（结果见下）。
4. 零 `app/` 改动；**未 commit**；无关 `uv.lock` 不纳入本 task 范围。

## lint 结果

```text
npx --yes spec-wave@3.3.0 task lint --file docs/tasks/active/task_lg_rag_sse_run_worker.md
→ LINT: PASS · task_lg_rag_sse_run_worker.md
```

## 交给 20

请对 `docs/tasks/active/task_lg_rag_sse_run_worker.md` 做 **20-task-audit R1**：

- 范围 F5–F7+补偿是否可测；与旧 task co-CLOSE / 禁改正文是否写清
- D1=A+B / D2 / D3 是否与方案 invoke 一致
- TC-B* 是否覆盖产品口径（部分可见 · 断连跑完 · 失败新 run · 禁 resume/replay≡LLM）
- graph_change_layer=G-L1 新模块 → HG-GRAPH-MODULES
- **不代签**人工闸；输出审查文路径建议

## 自检

- [x] 新 task 落 `docs/tasks/active/task_lg_rag_sse_run_worker.md`
- [x] 旧 task md **未改**
- [x] README 索引行更新
- [x] 分支名与 `git_branch` 一致
- [x] 禁 30 / 闸 pending 明确
- [x] D1 代录授权 + HG 待签写明
- [x] freeze 不升 · 禁 silent 新 event_type
- [x] D3 web task 提示在范围/验收
- [x] 未 commit
