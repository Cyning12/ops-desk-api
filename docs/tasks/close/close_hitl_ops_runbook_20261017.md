# CLOSE：hitl-ops-runbook（HITL 生产使用流程手册 + 现行 master compose 阶段 5 复走收口）（2026-10-17）

> **task**：[../done/task_hitl_ops_runbook.md](../done/task_hitl_ops_runbook.md)（已归档 done/）
> **类型**：文档 / 验收复走（纯文档零改码 · `graph_change_layer=none` · freeze lg-rag-sse-v1 只读引用）
> **关账日期**：2026-10-17 · 帽位：CLOSE（50 · 批量关账棒 · 分支 close/active-batch-20261017-pm · 闸态维护者授权 00 代录签收 m00238）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `hitl_ops_runbook` |
| 依据 | SPEC chat-history-hitl-ux（B1/B2 done · F1/F2 Q4 裁定移交 ops-desk-web）· 三连架构合并后运维面变化（PR #250 RunWorker squash 56e4a9f · PR #248 replay 409+latency_ms squash acac5e6 · PR #252 resume 异步化 squash 0e5f6b1）· 20261009/20261010 两份验收档坑位与偏差 |
| 背景 | 四处残留收口：①HITL 运维知识散落 4+ 份文档无单一入口；②阶段 5 复走遗留（旧实证 1117286 不覆盖异步 resume+409 契约新链路，现行 master 579d283 compose 形态全链未复走）；③FP-1「resume 终帧 done 无 model 键不补」裁定未入操作面；④F1/F2 前端移交缺契约指针锚点 |
| 目标 | 产出 `docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 单一入口（五必备节 + FP-1 钉案节 + F1/F2 锚点节）+ 现行 master compose 形态阶段 5 全链复走证据落盘 |
| 分支 | `task/hitl-ops-runbook` |
| 帽链 | 10-task 落稿 → 20-task-audit **R1 退回**（B-1 思考轮 R0–R5 全占位 · 全仓零先例）→ 10 回填（R0–R5 控制表+正文六节实填闭合 · HG-TASK-DRAFT 行补 · event_store.py:132 谓词锚点补）→ **R2 PASS-WITH-NITS**（残留 N-1 行号漂移一条）→ 闸 approved（2026-10-17 00 代录 · m00238 · R1 书面审豁免口径照登）→ 40 执行（runbook 落稿 + compose 复走 · TC-1..9 全 PASS）→ PR #264 → **CLOSE（本档）**；orchestration 无 30 棒 |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#264](https://github.com/Cyning12/ops-desk-api/pull/264) · **MERGED 2026-10-17T05:50:24Z · squash commit `dd6e02d`** |
| F1 runbook | `docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 五必备节全在：§1 全链菜谱（六 env 组 + 挂起 query 诀窍 → decide/resume 两步钉死 → replay 追帧终帧）· §2 409+Retry-After 退避纪律（`app/ops/lg_rag/router.py:384-420` · 谓词本体 `event_store.py:132`）· §3 OPS_HITL_PERSISTENCE=db 重启恢复（`docker-compose.yml:68` 插值透传 · runtime 三键机断）· §4 常见 failure 排查表 · §5 FP-1 钉案+F1/F2 锚点；TC-1 grep 节名命中 20 处 ≥5 |
| F2 复走证据 | `docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md`（环境形态 / S1–S7 命令输出摘录 / 偏差两条登记 / 台账链摘录） |
| F3 FP-1 钉案节 | 裁定溯源 close_hitl_resume_replay_contract_20261017 + 「禁伪造 model 键」钉文 + 前端兜底 0/'' 存续说明三要素 grep 全命中（TC-6） |
| F4 交接锚点节 | ops-desk-web 专项 SPEC 指针 + SPEC Q4 裁定移交记录 + freeze lg-rag-sse-v1 声明三要素 grep 全命中（TC-7） |
| 图谱/码面 | 零 app/ 改动（TC-9 diff 面仅 docs/）· 零 docker-compose.yml/.env.example 改动 · 图谱/standards/wiki 零触 |
| invokes | `docs/harness/invokes/by-task/hitl-ops-runbook/`（10_task_draft / 20_task_audit_r1 / 20_task_audit_r2 / 40_runbook_acceptance） |
| 审查文 | 址A `docs/harness/reviews/task_hitl_ops_runbook_audit_R1_20261017.md`（退回）· `task_hitl_ops_runbook_audit_R2_20261017.md`（PASS-WITH-NITS） |
| **CLOSE 增量** | 本档落盘（50 帽 · 零 git 操作 · 零其他文件改动） |

## 三 · 核验结论（验收终态摘要 · TC-1..9 全 PASS）

### 40 执行自检（task 档自检结论节在案）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC-1 runbook 五节 | ✅ | grep 节名命中 20 处 ≥5 |
| TC-2 runtime 机断 | ✅ | `{"mode":"db","store":"DbHitlStore","persists":true}` 双键 grep 命中（验收档 S1） |
| TC-3 重启持久化 | ✅ | `docker restart hitl-rewalk-api` 后 pending grep 命中复走建单 `hitl_a1cef212bf354860a3bc`（S3 · api ready after restart: 2s） |
| TC-4 终帧三断言 | ✅ | decide(approved) 200 → resume 200 `status:accepted` 携 replay.cursor `:7` → 追帧 seq8 hitl.resumed → **终帧 seq18 `done{status:resumed, latency_ms:435584 整数, payload 无 model 键}`**（S4/S6 · jq 三断言全过 · FP-1 钉案实证复核与 close_hitl_resume_replay_contract_20261017 TC5 形态一致） |
| TC-5 证据落盘 | ✅ | `docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md` 环境形态（master 579d283 · compose ps）/命令摘录/偏差登记齐 |
| TC-6 FP-1 钉案节 | ✅ | 三要素 grep 全命中 |
| TC-7 F1/F2 锚点节 | ✅ | 三要素 grep 全命中 |
| TC-8 task lint | ✅ | `LINT: PASS`（回填后 W3 亦消） |
| TC-9 零 app/ diff | ✅ | diff 面仅 docs/（runbook + 验收档 + task + invokes + R1/R2 审查文） |

### 附：FP live 实证与回填

- **FP-4 live 实证**（验收档 S7）：另起 run `b7d9e4fc…` 在 run.start 后 done 前探测 replay → **HTTP 409 · retry-after: 2 · detail "Run is still in flight; retry after it settles."**，与 runbook §2.1 钉文一致；探针残留两笔挂起申请已 decide rejected 清理。
- **FP-5 live 实证**（S5）：resume 在飞重复提交 → **409 {"detail":"该申请的恢复正在执行中，待沉降后再试"}**，并发守卫 `app/ops/hitl/router.py:561-566` `_RESUME_IN_FLIGHT` 与 §2.2 钉文一致。
- **追帧 nuance 实测回填 runbook §1.5**：resume 段执行期间 replay **返 200 携部分帧**（非 409）——挂起 run 已由 done{waiting_approval} 收尾，`run_stream_closed` 判已收尾，恢复段追帧走「200+推进 cursor」而非「409 退避」（与 close_hitl_resume_async TC8-3a 裁定 (a) 语义同构）。
- **R2 N-1 顺手修已落**：auto_resume fail-closed 引用行号 `:39` → `app/ops/hitl/auto_resume.py:6-7` 真址。
- **FP-7 未触发**：三连架构合并后现行 master compose 形态复走零回归缺口暴露。

**CLOSE 质量钉复跑（本帽 · 归档后仓态 · 重定向取真码）**：

- `npx --yes spec-wave verify --target . --task docs/tasks/done/task_hitl_ops_runbook.md` > /tmp/verify_close_runbook.log → **EXIT=0 · VERIFY: PASS**。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_hitl_ops_runbook.md` → **EXIT=0 · LINT: PASS**。

## 四 · 偏差与 nit（如实照登）

1. **宿主机 8000 被占 → 18000 实映射（偏差#1 · 环境形态非仓面缺陷）**：复走 api 以 `--publish 18000:8000` 起栈全程用 18000；runbook 已钉「端口以 compose ps 实映射为准」兜底坑位时效性。
2. **db/qdrant 复用运行中容器未重建（偏差#2）**：主仓 .env 形态复用 —— 复走目标是 api 面重启持久化全链，db 数据存续恰为验证前提；共享开发库内 2026-10-14 存量 admin 申请如实照登（pending 列表含存量非本复走产物 · 非异常）。
3. **R1 退回 → 回填 → R2 PASS-WITH-NITS 史照登**：20 R1 退回（B-1 思考轮 R0–R5 全占位 · 全仓零先例）→ 10 回填六节实填闭合 + HG-TASK-DRAFT 行补 + 谓词锚点补（验收/failure_paths/范围实质零迁就）→ R2 裁定 PASS-WITH-NITS（diff 越界扫描零越界 · 残留 N-1 行号漂移已由 40 顺手修落）。完整 R 轮史留存址A 两件审查文，本 CLOSE 不复述细节。
4. **六 env 组 + checkpointer 注入形态（照登）**：六 env 组经 `docker-compose.yml:68` 插值透传；`LG_RAG_HTTP_CHECKPOINTER=postgres` 不在 compose 白名单，须 `run -e` 显式注入（验收档环境形态节在案 · 复走容器 `--rm` 已拆除，主仓 db/qdrant 未动）。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-17 维护者授权 00 代录（m00238 · blocks 20,40 · 补行对齐同批兄弟档口径 · 本 task 无 30 棒） |
| HG-AUDIT-R1 | **approved** | 2026-10-17 维护者授权 00 代录（m00238 · 20 R1 书面审豁免口径照登 · R1/R2 审查文实存在址A） |
| HG-GRAPH-MODULES | n/a | `graph_change_layer=none` · 不触图谱闸（承 task_compose_hitl_persistence_env 先例） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 非物理分层试点改码 |
| 20 R1/R2 审查 | **R1 退回 → R2 PASS-WITH-NITS** | 址A `docs/harness/reviews/task_hitl_ops_runbook_audit_R1_20261017.md` / `_R2_20261017.md` |
| invokes | — | `by-task/hitl-ops-runbook/`（10/20_r1/20_r2/40 四件） |
| 合并 | **MERGED** | PR [#264](https://github.com/Cyning12/ops-desk-api/pull/264) · squash `dd6e02d` · 2026-10-17T05:50:24Z |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**：分支 `task/hitl-ops-runbook`（本地/远端）**移交 00/维护者统一清理**——task 分支已 squash 合入 master `dd6e02d`，删除安全，远端一并清。
- 复走容器 `hitl-rewalk-api`（`--rm`）复走收尾已 `docker stop` 拆除自动清；主仓 db/qdrant 容器未动；探针残留挂起申请已 decide rejected 清理。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（需人验收项）

- [ ] **runbook 抽验**：`docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 五必备节 + §1.5 追帧 nuance + FP-1 钉案节 + F1/F2 锚点节通读；全文无本机绝对路径（端口一律「以 compose ps 实映射为准」）。
- [ ] **复走证据抽验**：`docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md` S1–S7 命令输出摘录与偏差两条登记抽查一致。
- [ ] **终帧契约抽验**：终帧 `done{status:resumed, latency_ms:int≥0, 无 model 键}` 逐键 · hitl.resumed 恰 1 枚（seq8）。
- [ ] **R 轮史抽验**：址A R1（退回）/ R2（PASS-WITH-NITS）两件审查文在案。

### 后续建议

1. **HMAC 对接面运维手册化另立 task**（非范围在册）：GET /requests · POST /callback · POST /requests 手工补录——受众为外部系统对接方，契约形态与运维菜谱不同构。
2. **OPS_HITL_AUTO_RESUME=auto 运维化另立 task**（非范围在册）：生产默认 manual（fail-closed 回退 `app/ops/hitl/auto_resume.py:6-7`）· 认领竞态已由 PR #224 收口 · 本 runbook 菜谱以 manual 为准 auto 仅附录提示。
3. **便签坑位时效性**：20261010 操作便签坑位（临时启动器/当时端口形态）只溯源不照抄；runbook 后续维护以 compose ps 实映射为准持续兜底。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（50 close 棒 · 批量分支 `close/active-batch-20261017-pm`）：九节沿仓内先例（close_hitl_resume_async_20261015）· 验收终态承 40 自检 TC-1..9 全 PASS + 验收档 S1–S7 实证全录 · R1 退回→回填→R2 PASS-WITH-NITS 史照登 · 偏差两条（18000 实映射 / 复用容器）如实照登 · §1.5 追帧 nuance / FP-4/FP-5 live 实证照登 · 质量钉复跑（verify EXIT=0 PASS · task lint EXIT=0 PASS · 重定向取真码）· 零 git 操作 · 零其他文件改动 |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| task（已归档） | `docs/tasks/done/task_hitl_ops_runbook.md` |
| CLOSE 档 | `docs/tasks/close/close_hitl_ops_runbook_20261017.md`（本档） |
| 交付文档 | `docs/guides/RUNBOOK_hitl_ops_v1_zh.md` · `docs/acceptance/20261017_hitl_ops_runbook_compose_rewalk.md` |
| 审查文（址A） | `docs/harness/reviews/task_hitl_ops_runbook_audit_R1_20261017.md` · `task_hitl_ops_runbook_audit_R2_20261017.md` |
| invokes | `docs/harness/invokes/by-task/hitl-ops-runbook/`（10/20_r1/20_r2/40） |
| 码面锚点（只读引用） | `app/ops/hitl/router.py`（端点族 · :561-566 `_RESUME_IN_FLIGHT`）· `app/ops/hitl/persistence.py:22,40,54-57` · `app/ops/lg_rag/router.py:384-420` · `app/ops/lg_rag/event_store.py:132`（run_stream_closed）· `docker-compose.yml:68` · `app/ops/hitl/auto_resume.py:6-7` |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave verify --target . --task docs/tasks/done/task_hitl_ops_runbook.md > /tmp/verify_close_runbook.log 2>&1; echo "EXIT=$?"   # EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_hitl_ops_runbook.md                    # EXIT=0 · LINT: PASS
```
