# Harness 30 Prompt · post-merge-hygiene（api）

> 用法：Open Folder = `ops-desk-api` 根；新会话整段粘贴下方复制区。

---

`````text
你是 Harness 30（含 40 自检）。Open Folder = ops-desk-api 仓根。

读：
- docs/tasks/active/task_post_merge_hygiene.md
- docs/harness/reviews/task_post_merge_hygiene_audit_R1_20260728.md
- docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
- 00 统筹：../ops-desk-workspace/docs/05-plan/03-post-go-live-hygiene-orchestration.md（棒 A）

纪律：
1. 首输出 GATE_VERIFY；闸已 approved 才改文件。
2. 禁止在 master 直推。从最新 origin/master 建 task/post-merge-hygiene。
3. 若工作区已有 active→done 的 task_api_tech_graph_ci 搬家，纳入本分支提交；否则完成搬家。
4. 可把本 task 与 PROMPT/R1 一并提交；合入后将本 task 标 completed 并移入 done/（可同 PR 或 follow-up）。
5. invoke_retention_profile=minimal：落盘 30 invoke。
6. 跑 npx @cyning/harness verify --target . --task docs/tasks/active/task_post_merge_hygiene.md（或合入前等价检查）。
7. commit → push -u → gh pr create。不 force push。不改 app/、CI、图谱正文。

完成后：回填自检表；汇报 PR URL。
`````
