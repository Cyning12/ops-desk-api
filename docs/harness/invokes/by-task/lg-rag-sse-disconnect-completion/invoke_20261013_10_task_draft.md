# invoke：10-task 起草（lg_rag_sse_disconnect_completion · 2026-10-13）

> **帽位**：10-task（任务需求分析 · 只起草文档 · 零实现码改动）  
> **分支**：`task/lg-rag-sse-disconnect-completion`（base master `9ee928c`）  
> **产物**：`docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` + active README 一行 + 本 invoke

---

## 输入

| 来源 | 内容 |
|------|------|
| 维护者对话实勘（2026-10-13） | SSE/History/replay 语义澄清后，认定「断连 → 无 done → replay 补不全 → 对话无效」为产品缺口 |
| T4 遗留 | web `task_web_lg_rag_sse_t4`：客户端断开即取消 generator · done 不落盘 |
| F-OBS-2 40 | 孤儿在飞 run `22b65ce2` 永久 409 活样本 |
| 契约 | `05` §10.3「断连尽量跑完」 |

## 锚点亲读（摘要）

| 锚点 | 结论 |
|------|------|
| `sse_stream.py` 头注释 | 契约：尽量跑完 · 无 cancel |
| `sse_stream.py` 主循环 finally cancel anext | 断连实然停跑 |
| `event_store.run_stream_closed` | 无 done/error → replay 409 |
| HITL resume | 非通用续跑 · 不得与 replay 混用 |

## 交付

1. task 草稿：背景 F-OBS-DISCONNECT · Wave A/B · D1–D3 裁定口 · 范围/非范围/FP/TC1–TC7 · R0–R5。
2. 三闸 **pending**（不代签）。
3. **默认建议 D1=A-only**（先收尾帧消孤儿；解耦另波/另 task）。
4. 零 `app/` 改动；未提交 `uv.lock` 脏文件。

## 交给 20

请对 `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` 做 **20-task-audit R1**：

- 内容阻塞项（范围过大 / 验收不可测 / 与 HITL·409 冲突）
- D1 建议是否同意 A-only
- D2 收尾帧形状与 History `terminal_status` 兼容性
- 锚点行号是否需校正
- **不代签**人工闸；输出审查文路径建议与维护者签闸清单

## 自检

- [x] task 落 `docs/tasks/active/`
- [x] README 索引一行
- [x] 分支名与 git_branch 字段一致
- [x] 禁 30 字样明确
- [x] freeze 不升 · 禁 silent 新 event_type
