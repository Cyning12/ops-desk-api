# Invoke · 40 验收/CLOSE · host-v1-delegation-token-observe（D2 第一闸 · 本地观察准备）

> **日期**：2026-09-24 · **帽**：40（验收 · 00 代录留痕）  
> **维护者令（原话留痕）**：「仓内改动也可以吧，LG_RAG_DELEGATION_TOKEN_SECRET本地如何生成？落盘一份完成的本地checklist」（2026-09-24 · D2 推进窗口）· 承「签收，生成00 Prompt，在新窗口开始D1统筹」（2026-09-24）与 2026-09-23 长程令  
> **PR**：[#198](https://github.com/Cyning12/ops-desk-api/pull/198) **MERGED**（95c0c91 · CI 四绿：check / import-linter / lint-wiki-delta / pytest）  
> **task**：`docs/tasks/done/task_host_v1_delegation_token_observe.md`（已归档）

## 验收（6/6 · 对照 task 验收标准逐条机断）

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | D1 RUNBOOK 落盘 | **PASS** | §0-§10 齐：SECRET 生成双法（openssl/python）· 冒烟断言（logs grep `delegation token_`）· 报告模板节 · 复位节 · 故障排查 |
| 2 | D2 compose 三键透传 | **PASS** | 默认值 `off`/空/600 · 注释指 RUNBOOK · `docker compose config` 渲染实证（默认关零 diff） |
| 3 | D3 env 样例 | **PASS** | `.env.example` LG_RAG 区块三键注释 · 全仓 grep 无真实密钥值 |
| 4 | D4 报告模板 | **PASS** | `_TEMPLATE_delegation_token.yaml` 字段族与 SPEC §2 D2 钉死格式逐项一致 |
| 5 | diff 白名单 + 密钥扫描 | **PASS** | `git diff origin/master --stat -- app/` 为空 · 新增行 grep 无 SECRET 值 |
| 6 | 机械闸 + PR | **PASS** | `spec-wave verify --task` PASS · `task lint` PASS · #198 MERGED（95c0c91）CI 四绿 |

## CLOSE 清单（承 agent_close_discipline）

- [x] 复检绿（验收 6/6 + R1 PASS）· PR #198 MERGED
- [x] Hub 域表行 + 修订记录行已追加
- [x] `task close` dry-run → CLOSE: READY → `--yes` → CLOSE: PASS
- [x] task 已离 active/ 入 done/

## 下一棒（钉死交接）

观察期执行 + 首份报告：维护者本地按 RUNBOOK §0-§8 跑（开 observe → 冒烟 → 观察期/合成演练 → 聚合）→ `reports/gate_observe/delegation_token_<period>.yaml` 落盘另行登记；enforce 前置 = 零误判报告 + SECRET 已配（SPEC 锁死 · 宁停勿闯）。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 40 验收 6/6 PASS + CLOSE 归档（00 代录 · 维护者令原话留痕见头部） |
