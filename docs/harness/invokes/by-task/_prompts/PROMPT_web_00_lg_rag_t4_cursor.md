# 可复制 Prompt · web 00 · T4 断网恢复 / 存 cursor（完成后查 T5 就绪）

> **给谁**：ops-desk-web **00**（新窗）。  
> **Open Folder**：`ops-desk-web/`  
> **api 真值**：`ops-desk-api` · T4 `lg-rag-sse-resume` · freeze `lg-rag-sse-v1` · `POST /lg-rag/replay`  
> **下一波入口（书签 · 强制）**：[`ops-desk-api/docs/spec/agent-infra/WAVE_READINESS_lg_rag_sse_v0.md`](../../../ops-desk-api/docs/spec/agent-infra/WAVE_READINESS_lg_rag_sse_v0.md)  
> **api 00 本窗不改 Vue**。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-web 的 00 统筹。默认只编排，不亲自改 Vue（派 10/30）。

Open Folder
  ops-desk-web 仓根

════════════════════════════════════
约定 · 波次就绪入口（全窗记住）
════════════════════════════════════

唯一查看文档（下一波能否开）：
  ../ops-desk-api/docs/spec/agent-infra/WAVE_READINESS_lg_rag_sse_v0.md

契约详规（只读）：
  ../ops-desk-api/docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md
  · T4 = §10.3 · T5 = §10.4 · T6 = §10.5

联调勾选副本：
  docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md §3（T4）· §4（T5）

规则：web T4 CLOSE 完成后，必须打开 WAVE_READINESS §1 勾选并回填「结论」行；
禁止跳过该闸直接开 T5 打字机实现。

事实
  - 主 Chat 已走 POST /api/ops/lg-rag/stream（T2 · web #23）
  - web T3 thread_id：建议先稳；未稳也可先做「单 run」cursor/replay（写进 task）
  - api T4：slug lg-rag-sse-resume（以 api done/ 或 MERGED PR 为准）
      · live SSE data 顶层可选 cursor = "{run_id}:{seq}"
      · POST /api/ops/lg-rag/replay · body {run_id, after_seq} 或 {cursor}
      · 重放 seq > after_seq；同 run_id+seq 客户端去重不重复渲染
      · 断连服务端仍尽量跑完；未知/跨用户 run_id → 404
  - 本波禁止：C0–C4 · T5 token 打字机实现 · 再切回 chat/stream · 改 api 仓

════════════════════════════════════
阶段 A · 交付 web T4
════════════════════════════════════

任务（建议 slug web-lg-rag-sse-t4 或 web-lg-rag-sse-resume）
  - 存最近 run_id / seq / cursor（会话或 local）
  - 断网/刷新后：从 cursor 调 /lg-rag/replay 续看
  - 重复 seq 不重复 append（尤其 answer）
  - 联调：DevTools offline → 恢复后帧不丢、不重复
  - 非范围：api 实现、token delta（T5）、删 chat 死代码（T6）

动作
  1. 确认 api T4 契约可读（05 §10.3 · api task done 或 MERGED）
  2. 起草 web T4 task · 闸 · 派 30
  3. PR 勿 auto-merge → CI 绿 → merge → CLOSE → Hub/done

════════════════════════════════════
阶段 B · T4 CLOSE 后强制 · 查能否开 T5（勿跳过）
════════════════════════════════════

1. 打开入口文件 WAVE_READINESS_lg_rag_sse_v0.md §1
2. 按表勾选（读两仓 done/、gh、05 §10.4；禁止臆造）
3. 回填该文件「结论」行：日期 · web-00 · 可开工 T5 / 阻塞—原因
4. 同步勾 checklist §3 T4 项；若判定可开 T5，预勾或注明 §4 待开工
5. 分支：
   - 可开工 T5 → 产出/落盘 web T5 Prompt（打字机 · 兼容 T2 整段 answer）或起草 web T5 task；并短报通知 api 00（若 api T5 未合）
   - 阻塞 → 只输出阻塞清单 + 下一棒「等 api T5 契约/合入」或「补 web T3 thread_id」；本波停止扩 scope

输出形状（对人类）
  阶段：{A-T4|B-就绪闸|T5起草} · {pass|blocked}
  就绪入口：WAVE_READINESS §1 结论 = {可开工 T5|阻塞—…}
  交付：路径列表
  下一棒：{web T5 | 停—原因}
  本窗未改 Vue 实现码 · 已派/待派：{帽}

停止条件
  - web T4 done 且 WAVE_READINESS §1 结论已回填
  - 若可开工：已有 web T5 Prompt 或 active task；若阻塞：清单已写清
`````

---

## 维护者备注（勿粘贴）

- **书签入口**固定为 api 仓 `WAVE_READINESS_lg_rag_sse_v0.md`，勿再发明第二套「能不能开 T5」文档。  
- api 串行开 T5 不解除 web 00 的 §1 勾选义务（前端跟进仍要闸）。  
- web T3 未稳：WAVE_READINESS 允许「单 run」豁免，须写入 T5 task 非范围。
