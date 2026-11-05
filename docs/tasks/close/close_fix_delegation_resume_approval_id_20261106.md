# CLOSE：fix-delegation-resume-approval-id（delegation resume 双消费合一 · 写闸查命中不重复记台账）

> 关账日期：2026-11-06 · 关账人：bot 全棒链执行（10 → 20 → 30 → 40 → 50 CLOSE · 两日闭环）· 维护者令 issue #334 comment `6666638933`（40 复跑销项 · #339 偏差口径）+ 裁定 comment `6665660681`（锚点作废 · 真实缺陷=双消费 · 第七条留痕）
> 体例承 [close_fix_worker_state_send_run_id_20261105.md](close_fix_worker_state_send_run_id_20261105.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [`task_fix_delegation_resume_approval_id.md`](../done/task_fix_delegation_resume_approval_id.md)（已归档 done/） |
| 性质 | fix / 缺陷修复（delegation resume 同一 approval_id 双消费 · 与主路径单消费语义不齐 · issue #334 backlog） |
| 由来 | issue #334（来源 #323 stage-w 40 invoke 证据链）· 30 调查红测探针实证**签认锚点 `:2162+:2177` 为干净面作废**，真实缺陷 = 签发门 + 写闸独立触达同一单据（维护者裁定 `6665660681` 确认 · lead 亲核 :420-504） |
| PR | [#341](https://github.com/Cyning12/ops-desk-api/pull/341)（10 起草 · squash `c162d1d` · CI 4/4 绿 · lead review APPROVED 签认四闸+案 A 裁决）· [#343](https://github.com/Cyning12/ops-desk-api/pull/343)（30 实现 · squash `afc8c17` · CI 4/4 绿 · lead 验收七条件全过含锚点留痕）· #342 误开已关闭（分支改名绑定留痕） |
| 闸 | HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN（裁决=案 A · 锚点经实证修正为消费层双消费合一 · 维护者签）· HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（lead 签认 · 依据 PR #341 review `5789202776` + issue #334 `6662721599`/`6664735511`/`6665660681`） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/lg_rag/multi/nodes.py::_write_execution_approval` | delegation 类命中 = **查命中不重复消费**（+18/-3 · 改码面唯一）：同一 fail-closed 匹配 + W2 租户守卫 + 返回行（approval_id 注入与三照串链不变），提前返回不再重复记 `capability_write_approval_consumed` 台账；delegation 类消费归签发门 `_approval_consumed` 单点（`delegation_approval_consumed` 即唯一消费记录）；capability_write 类形态与主路径逐字节一致 |
| `tests/test_fix_delegation_resume_approval_id.py` | 2 枚红测先行（先红后绿）：负样本 = delegation on 全链 resume 端到端断言单消费（签发门唯一台账 + 写闸零第二笔 + 真落笔三照串链）；对称对拍 = 主路径（delegation off · capability_write 闸）单消费形态零漂移 |
| 旧测适配 | **零适配**（实扫 190 枚关联断言对象均不锚写闸 delegation 类台账 · 如实列出） |
| 过程文档 | task 档（四闸签认 + 锚点修正留痕 + 全棒自检）· 20-R1 审查文（lead 人审转录）· 10/20/30/40/50 invoke 全落盘 |

## 三、验收核验（全 PASS · 维护者 item 3 口径机制面关账）

| 验收 | 结果 |
|---|---|
| 红测负样本（维护者红线） | ✅ 2 枚先红后绿（修复前双消费两笔并存实证 RED → 修复后单消费绿） |
| **live 单消费实证（修复核心）** | ✅ run `eedd75f3…`：签发拦下 → decide 200/重复 409 → resume 受理 → 重放守卫 → 解锁 → replan 保号 → **`delegation_approval_consumed{request_id=hitl_78f72333…}` 唯一消费台账** → token issued/verified → 写闸放行执行 · **同 id `capability_write_approval_consumed` 全程 0 笔**（grep 实证） |
| 对称性对拍 | ✅ 主路径（capability_write 类）写闸单消费形态与修复前零漂移（单测对拍 + 全量回归双证） |
| 消费门 fail-closed 零变化 | ✅ 未命中/读失败/过期/类型/租户负样本全绿（TA2/W2 全组 190 枚）· live 重放守卫（`hitl_persist_guard_skip`）原样 |
| 红线对拍 | ✅ resume 单路径 / SSE 事件表 / `hitl/**` / `registry.py` / `policy.py` / web freeze 全零 diff（30 自检 + 40 独立双证 · delta 恰 7 文件） |
| 工程面 | ✅ 40 独立复跑：全量 2065 passed · 4 failed = 既有基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1 · worktree 对照）· ruff 零新增 · graph-compile EXIT=0 · verify PASS |
| 40 复跑销项 | ✅ 机制面 PASS——live 单消费达成；偏差②真落笔（planner string-args）按 item 3 口径另波 #339 |

## 四、偏差与裁定留痕

- **签认锚点修正（第七条交付条件 · 全档留痕）**：签认锚点 `nodes.py :2162+:2177`（`_approved_fresh_for_subtask`/`_persist_hitl` 建单守卫区）经 30 红测探针端到端实证为**干净面**（graph state / 工人 Send 载荷 / replan 保号行 / checkpoint 双路径全净）→ 锚点作废；真实缺陷 = 双消费（维护者裁定 `6665660681` · lead 亲核 :420-504「签发门读台账+写闸查命中均独立触达同一单据，双消费成立」）。留痕位：task 档闸表行（删除线+引注）· 背景缺陷段 · D-fix-1 · 30/40 invoke。
- **偏差①（环境噪点 · 模型层）**：默认 supervisor 模型 `Qwen/Qwen3.6-27B` 对 resume replan 持续返回空 `{"subtasks": []}`（8/8 轮）→ fail-closed 停图；切 `deepseek-ai/DeepSeek-V4-Pro` + 两步任务引导后首轮成功——模型层环境性，非仓码语义。
- **偏差②（真落笔未达成 · 另波 #339）**：live 消费放行后真落笔被 `args_schema_invalid` 拦（planner string-args）——issue #339 同源（stage-w 40 观察③）· 预存在 · 非本链缺陷 · 非 #343 引入。维护者 item 3 预期口径：机制面 PASS 关账 + 偏差如实登记。
- **#342 误开留痕**：首版 30 PR 因分支末段不满足工单绑定规则被系统拒绑，改名 `fix/approval-id-fix-task-be209a5f60c8` 重出 #343（#342 关闭注明承接 · task 档 git_branch 字段 + 30 invoke 如实记录）。

## 五、关账动作

- 档迁：`docs/tasks/active/` → `docs/tasks/done/`（本 CLOSE 档 + done/README + active/README 同步 + 50 invoke）；
- issue #334：维护者执行关 issue（bot 不 close issue · 已声明）；
- 后续跟踪：supervisor planner args 文档化 → issue #339（另波立项 · 同源 stage-w 40 观察③）；
- 评审署名：PR #343 lead（Cyning12）approval review `5790425462` 因 merge 先于署名改写，**未署名记录**（按规不 rewrite 已合并 PR · 此处登记）。

## 六、棒链留痕

| 棒 | 交付 | PR / 落点 |
|----|------|-----------|
| 10 | task 档起草（四闸 pending · NO-GO 20/30） | #341 squash `c162d1d` · CI 4/4 绿 |
| 20 | 四闸签认代录 + R1 审查文（lead 转录 · 案 A 裁决） | PR #341 review `5789202776` → 30 分支闸据档 `8f2d23f` |
| 30 | 双消费合一（nodes.py +18/-3 · 改码面唯一）+ 红测 2 枚先红后绿 | #343 squash `afc8c17` · CI 4/4 绿 · lead 验收七条件全过 |
| 40 | 独立复跑全绿 + live 单消费实证 + 偏差①②登记 | `invoke_20261106_40_verify.md` · worktree `/tmp/verify40` @ `afc8c17` |
| 50 | 本 CLOSE 收口 | 本档 + done/README + active/README + `invoke_20261106_50_close.md` |
