---
hat: 40
task_slug: hitl_ops_runbook
date: 2026-10-17
---

# invoke · 40-runbook-acceptance · hitl_ops_runbook（执行 + 验收复走）

## 执行摘要

- **F1 runbook 落稿**：`docs/guides/RUNBOOK_hitl_ops_v1_zh.md` —— §0 速览 / §1 全链菜谱（六 env 组+checkpointer 前置 → 挂起诀窍 query → pending → decide 两步钉死 → resume 异步受理携 replay.cursor → replay 追帧终帧契约 → 重启恢复四步）/ §2 409+Retry-After 重试纪律（replay 在飞退避 · resume 在飞 409 中文 detail）/ §3 OPS_HITL_PERSISTENCE=db 重启恢复（三模式表 · docker-compose.yml:68 透传 · runtime 三键机断 · FP-6 不可重试）/ §4 排查表 12 行 / §5 FP-1 钉案（禁伪造 model 键 · 前端兜底 0/''）/ §6 F1/F2 交接锚点（SPEC Q4 移交 · B2 端点族 · freeze lg-rag-sse-v1）/ §7 auto 附录。
- **F2 复走**：现行 master（579d283）compose 形态阶段 5 全链一次通过，证据落盘 `docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md`；TC-2/3/4 PASS + FP-4/FP-5 live 实证；偏差两条如实登记（宿主 8000 占用 → 18000 实映射 · db/qdrant 复用运行中容器）。
- **F3/F4**：FP-1 钉案节 + F1/F2 锚点节均入 runbook，TC-6/TC-7 三要素 grep 全命中。
- **R2 N-1 顺手修**：task 档 `auto_resume.py:39` → `app/ops/hitl/auto_resume.py:6-7`（docstring 真址）。
- **铁律核验**：零 app/ 改动 · 零 docker-compose.yml/.env.example 改动（TC-9 diff 面仅 docs/）；复走零回归缺口暴露，FP-7 未触发。
- **实测反哺**：resume 段追帧 replay 返 200 携部分帧（非 409 —— done{waiting_approval} 已收尾 stream）· 已回填 runbook §1.5。

## 过程

1. GATE_VERIFY：HG-TASK-DRAFT/HG-AUDIT-R1 approved（2026-10-17 维护者授权 00 代录 · task 人工闸表真值）· HG-GRAPH-MODULES/HG-PILOT-OPSDESK-GLAYER n/a · R2 PASS-WITH-NITS 签收 → 开工。
2. 亲读码面锚点（hitl router :76/:161/:185/:530/:561-566 · persistence.py:22,40,54-57 · lg_rag/router.py:384-420 · event_store.py:132 · auto_resume.py:6-7 · resume.py:317 · docker-compose.yml:49-80）与依赖档（20261010 验收 · close_hitl_resume_replay_contract · close_lg_rag_sse_run_worker_co_disconnect · SPEC Q4 · RUNBOOK_delegation_token_observe 先例）。
3. runbook 落稿（禁绝对本机路径 · 端口以 compose ps 实映射为准 · 五必备节 + 钉案/锚点节）。
4. F2 复走：docker compose build api（exit 0）→ `docker compose run -d --rm --publish 18000:8000 -e <六 env 组> -e LG_RAG_HTTP_CHECKPOINTER=postgres api` → 建用户登录 → TC-2 runtime 机断 → 诀窍 query 挂起建单（hitl_a1cef212bf354860a3bc）→ docker restart → TC-3 pending 命中 → decide approved → resume 200 携 replay.cursor=:7（FP-5 重复提交 409 实证）→ replay 追帧 seq8 hitl.resumed → seq18 done{resumed, latency_ms:435584, 无 model 键}（TC-4）→ 另起在飞 run 实证 FP-4 409+retry-after:2 → 探针残留申请 decide rejected 清理 → 容器 stop（--rm）主仓 db/qdrant 未动。
5. 验收档落盘 → TC-1/6/7/8/9 机断全 PASS → task 档自检结论/修订记录回填 → commit/push/PR。

## TC 结论速览

TC-1..9 全 PASS（明细见 task 档「自检结论」表与验收档）。
