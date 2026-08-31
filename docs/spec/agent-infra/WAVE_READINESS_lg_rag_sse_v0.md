# 波次就绪闸 · lg-rag SSE（跨仓 · web/api 00 共用入口）

> **角色**：唯一入口——完成当前波（尤其 **web T4 CLOSE**）后，**主动打开本文件**判断下一波（T5 / T6）能否开工。  
> **Open Folder**：api 或 web 均可；路径相对 api 仓根如下。  
> **契约详规**：仍以 [`05_lg_rag_transport_and_session_plan_v0.md`](./05_lg_rag_transport_and_session_plan_v0.md) §10–§11 为准；本文件只做 **就绪勾选 + 下一棒结论**。  
> **联调勾选副本**：[`ops-desk-web/docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md`](../../../ops-desk-web/docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md) §3–§4  
> **状态**：active · 2026-08-31

---

## 0. 怎么用（00 纪律）

1. **关账当前波之前或紧接 CLOSE 后**：打开本文件对应「从本波 → 下一波」节。  
2. 按表勾选（读 task `done/`、`gh pr view`、05 §10.x，**禁止臆造**）。  
3. 文末写一行结论：`下一棒：可开工 T5 | 阻塞—原因`。  
4. **可开工** → 产出/刷新下一波 Prompt 或起草 web/api task；**阻塞** → 只列清单，不擅自开 T5 实现。  
5. api 串行轨（T5→T6→C0…）见 [`PROMPT_00_t4_close_through_c4_serial.md`](../../harness/invokes/by-task/_prompts/PROMPT_00_t4_close_through_c4_serial.md)；web 不代替 api 串行，但 **web T4 后必须跑本闸看 T5**。

---

## 1. 从 web T4 → 能否开 web/api T5

> **T5 含义**：终答 `answer` **多帧 delta**（打字机）；见 05 **§10.4**。  
> **本闸触发者**：web 00 在 **web T4 CLOSE 完成后必须执行**（即使 api T5 已由 api 00 串行推进，web 仍须核「前端能否跟」）。

| # | 条件 | 查哪里 | 勾选 |
|---|---|---|---|
| 1 | api T4 已合入 master（cursor + `POST /lg-rag/replay`） | api `docs/tasks/done/task_lg_rag_sse_resume.md` · `gh pr` MERGED | [ ] |
| 2 | web T4 已 CLOSE（存 cursor · replay · 同 seq 不重复渲染） | web `docs/tasks/done/task_web_lg_rag_sse_*`（实际 slug） | [ ] |
| 3 | web T3 稳定 `thread_id` 已可用，或 T5 明示「可单 run 打字机、不依赖多轮」 | web T3 done/ 或本行写豁免 | [ ] |
| 4 | 05 §10.4 可读；api 侧 T5 契约已有草案或 active/done task（freeze / delta 语义） | 05 §10.4 · api `task_*token*` / `*delta*` 或 00 串行 Prompt 中 T5 节 | [ ] |
| 5 | 联调环境：api 部署含 T4（及若已合则含 T5）；cookie 同域 | 现网/本地 Network | [ ] |

**T5 可开工判定**

- **web T5（打字机）**：上表 **1+2** 必勾；**3** 未勾则仅允许「单 run delta」范围并写进 task 非范围；**4** 未勾 → **阻塞**（等 api 00 钉契约，可出「待 api T5」短报，不派 web 30）。  
- **仅通知 api**：若 1+2 勾且 4 未勾 → 结论写「web T4 已就绪 · 催 api 开/合 T5」。

**结论（每次 CLOSE 后回填）**

| 日期 | 操作者 | 下一棒 | 备注 |
|---|---|---|---|
| YYYY-MM-DD | web-00 / api-00 | 可开工 T5 / 阻塞—… | |

---

## 2. 从 T5 → 能否开 T6（参考 · 同入口）

| # | 条件 | 查哪里 | 勾选 |
|---|---|---|---|
| 1 | api+web T5 CLOSE（或维护者豁免「无打字机也清 chat」） | 两仓 done/ | [ ] |
| 2 | 05 §10.5 · 维护者下线窗口 | 05 / 本表结论行 | [ ] |

结论行：同上表格式，波次改为 T6。

---

## 3. 路径速查（跨仓）

| 用途 | 路径 |
|---|---|
| **本入口（书签）** | `ops-desk-api/docs/spec/agent-infra/WAVE_READINESS_lg_rag_sse_v0.md` |
| 契约 §10.3 T4 | `…/05_lg_rag_transport_and_session_plan_v0.md` §10.3 |
| 契约 §10.4 T5 | 同上 §10.4 |
| 契约 §10.5 T6 | 同上 §10.5 |
| web 联调勾选 | `ops-desk-web/docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md` |
| web T4 Prompt | `ops-desk-api/docs/harness/invokes/by-task/_prompts/PROMPT_web_00_lg_rag_t4_cursor.md` |
| api 串行 00 | `…/_prompts/PROMPT_00_t4_close_through_c4_serial.md` |

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | 初版：约定 web T4 后查 T5 的唯一入口 |
