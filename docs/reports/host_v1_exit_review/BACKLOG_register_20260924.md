# BACKLOG 登记 · host-v1-wrap-up D4（2026-09-24）

> **性质**：背景债**只登记不消化**（SPEC `docs/spec/host-v1-wrap-up/SPEC-host-v1-wrap-up_v0.md` §2 D4 · Q3 裁定「登记不消化」）  
> **00 代录**：维护者令原话「签收，生成00 Prompt，在新窗口开始D1统筹」（2026-09-24）· 承长程令「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」（2026-09-23）  
> **来源**：三方验收 `ACCEPTANCE_three_party_20260924_00.md`（存量背景节）+ 出口复核 `REPORT_host_v1_exit_review_20260924_v1_zh.md`

| # | 条目 | 真态（证据在案） | 处置口径 | 归属 |
|---|---|---|---|---|
| B1 | 仓级 reviews 裸扫描 **92 缺口** | 全部为 legacy 历史任务（**host_v1 面零缺口** · `verify --json` 过滤实证 · 三方验收在案） | 指豁免机制：spec-wave 2.3.0+ 支持 `docs/harness/legacy-gate-exempt.yaml` 过渡豁免（本仓**暂未建**该文件 · 非必须）；批量补审消化是独立工程，**另案**，不混入 v1.0 收尾轨 | 后续独立工程（维护者裁决是否开轨） |
| B2 | 代跑 agent WIP：`docs/agent-host-current-architecture-20260924` 分支 + 2026-09-24 讨论稿（未跟踪） | 在制品 · 本轨**未触碰**（三方验收 §残余与建议 3 在案 · 本棒开工 `git status` 快照留痕：该分支 1 修改 + 3 未跟踪讨论稿） | **归原线负责人**收口；任何窗口不得跨轨触碰 | 原线（代跑 agent 轨） |
| B3 | 本地 `pytest tests` · `test_import_from_supabase` **3 ERROR** | 本地 PG create-database 权限 · **环境性**；CI pytest pass（三方验收对照在案：全量 1599 passed / 1 skipped / 3 errors） | **非缺陷** · 不修；若未来 CI 复现再开 fix task | 无（登记即闭合） |

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 初版：三条目登记（B1 legacy 92 缺口指豁免机制 · B2 代跑 WIP 归原线 · B3 环境性 3 ERROR 非缺陷）· Q3 裁定只登记不消化 · 00 代录（维护者令原话留痕见头部） |
