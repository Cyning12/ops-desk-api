# invoke：50-close · 批量关账第三波（api-embedder-internal-batching / host-v1-sli-dashboard-live-evidence / rag-golden-eval-live-run · 2026-10-19）

> 帽：50-CLOSE · 执行人：00（goal-eb568703 · 承授权链 m00238/m01101 + 用户 m01262「全做」resume 授权 · goal 目标文「CI 绿后承授权链合并」）

## 一、前置核验

| 项 | 证据 |
|---|---|
| PR #278 MERGED | squash `056d874` · CI 4/4 绿 · TC-EB-1~5 全 PASS（红测先行 · F3a 10 批全 200 · 70.9 chunks/s） |
| PR #279 MERGED | squash `72aebad` · CI 4/4 绿 · TC-L1~L6 全绿（capability_ok=0.7129 · p99=562052.0ms · widget 照登） |
| PR #280 MERGED | squash `4ab5f3a` · CI 4/4 绿 · TC-LR-1~6 全 PASS（zh2en MET 19/26=73.08% · 拒答 10/11 · 73/73 partial=false） |
| R1 审查 ×3 | docs/harness/reviews/*_audit_R1_20261019.md 全通过零阻塞（锚点 14/12/14）· 随各 PR 落址A |
| 闸 | 授权链 00 代录：档1 四闸（含 HG-EVAL-LIVE-RUN）· 档2/3 三闸 · 签注=128/fail-fast/F3b 不授权 · VERIFY PASS ×3 |

## 二、关账动作清单

- [x] git mv 三档 active → done/ · 状态行全改 done CLOSED · 修订记录各补 CLOSED 行
- [x] README 登记表插三行「批量关账·第三波」
- [x] CLOSE 档×3（六节体例承 close_hitl_resume_async_20261015.md）：close_api_embedder_internal_batching_20261019.md · close_host_v1_sli_dashboard_live_evidence_20261019.md · close_rag_golden_eval_live_run_20261019.md
- [x] 本 invoke 落盘（批量目录 close_batch_20261019）

## 三、质量钉

- npx spec-wave task lint 三档 done/ 全 LINT: PASS（实跑）
- npx spec-wave verify --target . → EXIT=0 VERIFY: PASS（存量豁免留痕无新增）

## 四、交付移交

- commit `9b65364` · PR #281（https://github.com/Cyning12/ops-desk-api/pull/281）· 合并后 active 清零
- 遗留呈维护者：① 结案报告 §7 签字位（有条件通过定稿）② G63 误答/9 疑似误拒归因复核另 task 候选 ③ widget 缺口（API 404 · 持 UI 会话者重试路径在案）④ terminal_status 埋点缺口（FP-L4 另立 SPEC 面）⑤ 构造非法回退语义裁定口（embedder 档 §四.4）
- goal-eb568703 剩余：C2 生产水位（卡生产 Qdrant 只读凭据）· E backups/ 保留期（默认保留）——均呈报待维护者示下
