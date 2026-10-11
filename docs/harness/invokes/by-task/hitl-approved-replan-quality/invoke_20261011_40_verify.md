---
hat: 40
task_slug: hitl-approved-replan-quality
date: 2026-10-11
---

# invoke · 40-verify · hitl-approved-replan-quality（复核 + TC3 live 实证 + TC4 终验）

> 复核对象：HEAD 403a0e9（base master cae745e · worktree 专用分支）。30 已收口 D1=C 混合案；序2（logging 初始化）已 merge master，live 依赖解锁。

## 逐项 verdict

### 1. diff/契约复核 ✅ PASS

`git diff master...HEAD`：12 文件 861+/11-；生产面仅 `app/ops/lg_rag/multi/nodes.py`（163 行增量 · 三处）+ 模板 `lg_rag.supervisor.suffix.system.md` v1→v2 + assets README + `tests/test_prompt_assets.py` + 新测 341 行 + 文档。`app/ops/hitl/`（resume.py/router.py）**零 diff 实证**。

钉死契约五逐条独立核：

| # | 契约 | 40 独立核结论 |
|---|---|---|
| 1 | 已终态 write 步零重发（结构性） | ✅ 实码复核：`_guard_write_key`（tool+sort_keys canonical · 仅 WRITE_SIDE_EFFECTS 注册能力 · 未注册/序列化失败返 None 不护栏）+ `_join_subtasks` 分发层**先于签发检查** guard-skip（不派发/不消费/output deepcopy 照抄/`write_replay_guard_skip`+`replay_of` 台账/span metadata）；同批双胞胎首发照派次发挂起下轮 skip。非提示词约束，机断成立。**live 实证命中**（见 §3 run1） |
| 2 | 保号机制零回归 | ✅ TB 组 48 枚+新测 8 枚+prompt_assets 共 93 枚全绿；台账键（delegation_approval_consumed/hitl_persist_guard_skip）live 字面如旧；TC1-b 断言保号落位 [locked→preserved→新后缀] 存续 |
| 3 | 手动/auto resume 双路径同口径 | ✅ resume.py:131 未触（hitl/ 目录零 diff）；live 手动路径实证 ok |
| 4 | reject 路径零 diff | ✅ rejected 集合语义未触（diff 面控无涉） |
| 5 | pytest 全量零新增红 | ✅ 见 §2 TC4——7 红与 master 基线**逐枚同名同因** |

锚点复核：`obs["verdict"] = "replan" if approved else "settle"` 现位于 nodes.py:1910（base 时 :1759 · 行号因增量漂移 · 字面逐字一致）。

### 2. TC4 终验 ✅ PASS

- **全量 pytest**（.venv/.env 软链主仓先例 · postgres checkpointer ON 口径）：`7 failed, 1769 passed, 1 skipped`（55.6s）。7 红=test_capability_lookups×3 + test_hitl.py::test_db_store_alist_really_executes_on_asyncpg + test_lg_rag_multi.py::test_unknown_tool_at_invoke_recorded_and_continues + test_multi_replica_dualproc×2。
- **基线对拍**：同 7 枚在 master 码面（checkout master -- app tests）复跑 `7 failed` 逐枚一致 → 环境性（asyncpg event-loop 噪音/dualproc 跨实例 DB），**零新增红**。
- **ruff 对拍**：全仓 HEAD 55 = master 55；涉改文件（nodes.py+test_prompt_assets.py+新测）HEAD 6 = master 6 → 新码零新增。
- **TB 组定点**：test_hitl_approval_consumption + test_hitl_approved_replan_quality + test_prompt_assets 共 **93 passed**。
- **capability_acceptance 门禁**（SKIP_SMOKE=1）：本分支 失败2·跳过1；master 主仓（cae745e 本分支 base · 工作树净）同口径复跑 **失败2·跳过1 完全同形**（单测层系上述环境性红 · 编排层同因）→ 基线环境性，零新增。

### 3. TC3 live 实证 ✅ PASS（双 run 对照 · 核心证据）

环境：docker db/qdrant 复用主仓 healthy 容器（worktree compose 项目端口冲突 · 已 down 清理）；uvicorn :8080（/tmp/verify40_serve.py 启动器 · sys.path 钉本 worktree · CODE_UNDER_TEST 日志自证 · logging.basicConfig(INFO)）；六 env 组承验收口径；登录 create_initial_user.py（PYTHONPATH=$PWD）→ admin cookie。**坑位命中**：NO_PROXY 含 `[::1]` 致 httpx InvalidURL（首轮 run e35269f6 error 帧）→ 剥 no_proxy/NO_PROXY 重启后通（验收文档坑位 1 复发 · 已按先例处置）。

#### run1 · run=`6d46735942af47f6bf4e9c075ff2ca4d`（单写步 · 护栏 live 命中）

query=调用 testing.write.echo 回显 note=verify40-tc3-002 → 挂起 `hitl_a9bdf7f2478f48a8a63c`（:1）→ decide approved → resume：
- approved :1 正常重跑：`delegation_approval_consumed`（request 命中原单 · sid=:1）→ `token_issued dt-1-9d10ad7bc8bb` → `token_verified` → echo 执行成功。**FP-3 对照实证：approved unlocked 步自身无终态不命中自身护栏，正常消费派发** ✅
- replan 轮 LLM **仍规划同参孪生 :2**（locked 空 → 走基础 prompt · 注入未激活路径，见偏差 N1）→ 下一 join pass **`write_replay_guard_skip {"subtask_id":":2","replay_of":":1","capability_id":"testing.write.echo"}`** 台账命中 ✅
- :2 零 token 事件 · 零 delegation_approval_consumed · pending **零孤儿单**（旧盲循环签名=approve 后孪生产新 pending 单，本 run 无）· write 执行次数=**1**（token_issued 计数）· 终态 answer 自陈述 :2 带 write_replay_guard_skip+replay_of :1 ✅
- replay 持久化：events_persisted=10 · failed=0 · `HITL 恢复完成` 台账收尾 ✅

#### run2 · run=`3f2c58bfef0542a78ae89fc6a332cf77`（rag+write 双步 · 注入路径 live 激活）

query=先查知识库 HITL 审批流 + 再 echo note=verify40-tc3-003 → :1 rag 完成 · :2 write 挂起 `hitl_69176ccf5d9447d0b057` → decide approved → resume：
- replan 观测 `prefix_len=1`（locked=[:1] 非空 → **suffix 模板 v2 路径激活 · preserved_block 注入执行** · 渲染无 KeyError）→ LLM **未规划孪生**：planned=2 保号落位 [:1 locked · :2 preserved] · 零新后缀步 · verdict=settle ✅（与 run1 构成注入 off/on 活体对照）
- :2 重跑 exactly once：`delegation_approval_consumed` 命中原单原 sid → `token_issued dt-2-d74362139f2e`（全 run 仅此 1 枚）→ `token_verified` ✅
- :1 rag **零重跑**（DB 事件面：resume 后 subtask.progress 仅 +1 = :2 tool done；rag 管线 ~28 事件未重演）✅
- pending 零孤儿 · events_persisted=10 failed=0 ✅

#### TC3 验收口径核对

| 断言 | 结论 |
|---|---|
| 无孪生 subtask | ⚠️ 分层：run2 注入激活路径**无孪生** ✅；run1 locked 空路径 LLM 仍产孪生（注入未激活 · 偏差 N1），但**结构护栏中性化**（零重发零孤儿单） |
| write 步执行次数=1 | ✅ 双 run 均 1（token_issued 计数机断） |
| delegation_approval_consumed 命中原 sid | ✅ 双 run 台账逐字命中 |

#### TC5 台账链 ✅

live 全程台账键 grep 可断：`token_issue_hitl_required` → `hitl_persist_guard_skip` → `delegation_approval_consumed` → `token_issued` → `token_verified` →（run1 追加 `write_replay_guard_skip`+replay_of）→ `HITL 恢复完成`。新键仅 `write_replay_guard_skip`/`replay_of`（契约一新增台账 · 设计内），既存键零字面改动。

### 4. 偏差登记（照实 · 不硬编）

- **N1（新发现 · 建议后续 task）**：locked 空时 supervisor 走 `_build_supervisor_system` 基础 prompt（nodes.py :1172-1173 else 分支），**preserved_block 不注入**——「approved 写步是首步/全部前置步无终态」场景 LLM 对保号行仍盲，孪生规划纯靠结构护栏兜底（run1 活体实证）。契约一红线（write 零重发）不受影响（护栏结构性兜住），但注入去盲面存在路径缺口。建议：基础 prompt 路径亦注入保号行名单（或 locked 空+preserved 非空时走 suffix 模板），另立 task 裁定。
- **N2**：replan prompt 的 preserved_block **内容级**直证不可观测（app INFO 日志不dump prompt · langfuse 仅 SPAN 无 GENERATION input）；内容断言由 TC1-b 单测钉死（绿），live 面以「suffix 路径激活+渲染成功+行为对照（run1 孪生 vs run2 无孪生）」为间接实证。已尽力，照实登记。
- **N3**：worktree compose db/qdrant 端口 5432/6333 被主仓容器占用 → 复用主仓 healthy 容器（DATABASE_URL 本即指 localhost:5432），worktree compose 项目已 down 清理，零残留。
- 环境：.venv/.env 软链主仓先例承 30；7 红环境性对拍一致（§2）。

### 5. 不做 PR

00 统一编排 · 本分支 CI 待并 master 钉版——本棒零 PR 动作。

## 结论

**PASS-WITH-NITS**——钉死契约五条全过 · TC3/TC4/TC5 全勾 · write 零重发核心红线 live 双 run 实证（guard-skip 命中 + 注入路径行为对照）；N1（locked 空路径注入缺口）为质量改进点不阻塞本 task 目标（目标机断面=孪生零重发已达成），建议另立 task。

## 验收勾选回填

- TC3 ✅（双 run live · 上表口径）· TC4 ✅（全量对拍+ruff+TB 组+门禁基线同形）· TC5 ✅（台账链 grep 可断）。

## 证据指针

- api 日志：/tmp/verify40_api.log（run1/run2 台账链逐行在案）
- SSE/响应：/tmp/verify40_sse2.log（run1 挂起）· /tmp/verify40_resume.log（run1 resume 全状态）· /tmp/verify40_sse3.log（run2 挂起）· /tmp/verify40_resume2.json（run2 resume 全状态）
- 门禁报告：.acceptance-reports/capability-acceptance-20261011-100006.md（本分支）· 主仓 capability-acceptance-20261011-100054.md（master 基线同形）
