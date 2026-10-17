# invoke · 50-close · active 批量关账（第二波 · 五档）

- 日期：2026-10-17（Asia/Shanghai）
- 帽：50-close（00 会话亲自执行 · 承 harness-00-delegate-only「只做 50+CLOSE」条款）
- 分支：close/active-batch-20261017-pm（base master dd6e02d）
- 授权链：维护者 m00238「授权00签收后续文档，开始下面的任务」· m00363 ask_user_question 选定「授权我代合并（squash）」

## 一、前置核验表（五档 · 全 MERGED 实证）

| task | PR | squash | mergedAt | CI |
|---|---|---|---|---|
| ci_specwave_pin_align | #260 | de3c7d7 | 2026-10-17T05:50:10Z | 4/4 绿（run 日志实证 3.3.0 实载） |
| host_v1_sli_dashboard | #261 | 19a32d5 | 2026-10-17T05:50:13Z | 4/4 绿 |
| rag_golden_eval_r4_r5 | #262 | e1697ad | 2026-10-17T05:50:17Z | 4/4 绿 |
| prod_vector_waterline_check | #263 | ea65d3d | 2026-10-17T05:50:21Z | 4/4 绿 |
| hitl_ops_runbook | #264 | dd6e02d | 2026-10-17T05:50:24Z | 4/4 绿 |

## 二、落盘清单

- git mv 五档 docs/tasks/active/task_*.md → docs/tasks/done/；状态行全改 done（CLOSED 2026-10-17 · PR/squash/mergedAt/CLOSE 档路径）；修订记录各补 CLOSED 行
- CLOSE 档 ×5 落 docs/tasks/close/（委派两子代理起草 · 模板承 close_hitl_resume_async_20261015.md 体例 · 诚实纪律「照登：无实证」）
- docs/tasks/active/README.md 登记表表头后插五行归档记录（标「批量关账·第二波」）
- 本 invoke 落盘

## 三、质量钉

- `npx --yes spec-wave verify --target .` → EXIT=0 **VERIFY: PASS**（4 条存量基线豁免命中留痕 · 2026-10-11 授权在案 · 本批五档均有 R1/R2 审查文随各 PR 落址A，无新增豁免）
- `spec-wave task lint` 五档 done/ 全 **LINT: PASS**（父级预检 5/5 + 两 50 帽各自复跑一致）

## 四、善后（本波已执行 · 合并前完成）

- 五 PR squash 合并（gh pr merge --squash）· 远程五分支删除（--delete-branch 因 worktree 占用跳过 → git push origin --delete 补删）
- 五 worktree（t-ci-pin/t-sli-dashboard/t-rag-r4r5/t-prod-waterline/t-hitl-runbook）移除（均干净）· 本地五分支删除
- master 工作树 untracked 副本（task 档×5 + invoke 10/20×5 + 审查文 R1×5/R2×1）删除后 pull --ff-only 至 dd6e02d

## 五、移交维护者事项（不关本 CLOSE）

1. HG-EVAL-LIVE-RUN（rag 档）：签后现集 73 条真跑结案（旧过程稿 71 条≠现集）
2. HG-PROD-READONLY-ACCESS（waterline 档）：签后生产执行 + 报告回填
3. TC-WL-5（waterline 档）：40 轨本地/compose 亲跑
4. TC-D1（sli 档）：Langfuse 权限获后补真实 widget 实证
5. graph.json freeze_id 日期化照登项（ci 档）：可另立案

## 六、交付

- commit/PR：（commit 后回填）
- 合并后 active 清零（README 留守）
