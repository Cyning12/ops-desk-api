# CLOSE：cosign-gate-semantics（human-gate 同签语义裁决 · 案①幂等为主干 · gate 记录层落文）

> 关账日期：2026-11-06 · 关账人：bot 全棒链执行（10 → 20 → 30 → 40 → 50 CLOSE · 同日闭环）· 维护者令 issue #333 comment [`6678465675`](https://github.com/Cyning12/ops-desk-api/issues/333#issuecomment-6678465675)（40 复跑销项 + 全绿关账）
> 体例承 [close_fix_seen_surface_idempotency_20261106.md](close_fix_seen_surface_idempotency_20261106.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [`task_cosign_gate_semantics.md`](../done/task_cosign_gate_semantics.md)（已归档 done/） |
| 性质 | fix / 流程设计（human-gate 同签认定规则缺位 · 设计裁决 + 落文 + 机断回归 · issue #333 backlog：co-sign branch（0c88ac32）缺机器人同签语义——绕过 record 杠杆仍在） |
| 由来 | issue #333 维护者 comment [`6676316476`](https://github.com/Cyning12/ops-desk-api/issues/333#issuecomment-6676316476) 令立项（题面 = 同一维护者对同一工单的签认在跟进消息送达时的认定规则）· 受理依据 = 2026-11-06 08:48 授权（lead 代行签收与验收） |
| PR | [#351](https://github.com/Cyning12/ops-desk-api/pull/351)（10 起草 + 四闸签认代录 · squash `82bf056` · lead review APPROVED `5795679444`）· [#352](https://github.com/Cyning12/ops-desk-api/pull/352)（30 交付 · squash `3cc3e71` · lead 验收合并） |
| 闸 | HG-COSIGN-SEMANTICS-DESIGN（**裁决 = 案①幂等为主干** · 幂等锚五元组 · 覆盖不设默认 append-only · 拒重复不设 · 落点=gate 记录层）· HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（lead 签认 · 依据 PR #351 review `5795679444` + issue #333 `6676780590` + 授权链 08:48 + 12:17『验收333』） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `docs/harness/prompts/FRAGMENT_00_gate_cosign_semantics_v1_zh.md` | **裁决落文**（gate 记录层唯一机断真源）：幂等锚 =（维护者, 工单, 闸集, 签认依据 comment id, 授权窗口）· 同锚重送达 = 同效力不重复记录（可记 replay 附注）· 覆盖不设默认（append-only · 同锚+显式替换意图追加新行 · 旧行保留引注）· 拒重复不设（补发/重送达合法通路）· 落点 = gate 记录层（消费门内 = 仓外运行时面随 residual_risk 登记） |
| `docs/harness/prompts/00-orchestrator.md` | 引用行 + 修订记录（**不改默认表语义**） |
| `tests/test_cosign_gate_semantics.py` | 机断 8 断言（FRAGMENT 存在/frontmatter · 幂等锚五元组 · 同锚重送达 · 覆盖 append-only · 拒重复不设 · 落点 · orchestrator 可达 · 闸表四列契约红线钉）· 先红（`d2d9eaf` 7 failed）后绿（`c25336c` 8 passed） |
| 旧测适配 | **零适配**（prompt-packs 仅锚 delegate_only/reanchor 两档 · 55 passed 不扰动 · 如实列出） |
| 过程文档 | task 档（四闸签认 + R2 裁决回填 + 全棒自检）· 20-R1 审查文（lead 人审转录 · 非自签 · source = PR #351 review `5795679444`）· 10/20/30/40/50 invoke 全落盘 |

## 三、验收核验（全 PASS · 机制面关账）

| 验收 | 结果 |
|---|---|
| 机断判据（维护者条件①） | ✅ 8 断言先红后绿（负样本 = 裁决落文缺失时同锚重送达认定规则空缺 = 存在误读为新签的口子）· spec 锚 grep 15 关键词全命中（幂等锚/同锚重送达/同效力/不重复记录/replay/覆盖不设默认/append-only/显式声明替换意图/追加新行/旧行保留引注/拒重复不设/合法通路/gate 记录层/消费门内/residual_risk） |
| 旧测适配（条件②） | ✅ 零适配 · prompt-packs 55 passed · 全量 2083 passed · 4 failed = 既有红基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1） |
| 改码面收敛（条件③） | ✅ 唯一改码面 = docs/harness prompts（FRAGMENT 新档 + 00-orchestrator 引用行 2 处）+ tests 新档 1 枚；实扫未溢出（无 spec-wave 上游/机检扩展需求） |
| 红线零 diff（条件④） | ✅ `git diff f78a721..3cc3e71`：8 文件全落承载面 · `app/` / `alembic/` 零 diff · SSE 事件面（subtask_message/progress_stream/answer_stream/chat router/event_store）零命中 · 闸表四列契约断言恒绿 · **GATE_VERIFY 仍是唯一闸据**（verify 四闸 approved PASS） |
| 工程面（条件⑤） | ✅ ruff All checks passed（F541 一枚即修即 amend）· 全量 pytest 零新增红 · graph-compile EXIT=0 · task lint / lint-wiki-delta PASS |
| PR 逐条对照（条件⑥） | ✅ 30 PR 六条件对照表 + task 档自检 hat 30 + 30 invoke |
| 40 复跑销项 | ✅ **机制面 PASS**——独立复跑不采信 30 自报：worktree `/tmp/verify40-cosign` @ `3cc3e71` 新测 8 / 关联 prompt-packs 55 / 全量 2083 passed · 4 failed = base `f78a721` 同 4 枚**逐字复证**（同 node id 同签名 · 7.21s 定点复跑实锤）· ruff / graph-compile / lint / wiki-delta / verify 全绿 · 红线对拍零命中 |

## 四、偏差与裁定留痕

- **偏差①（GitHub Actions 零投递 · 维护者告知在查）**：GitHub Actions 自 04:20Z 起零投递（疑似账户分钟额度耗尽）。40 机检证据以**本地 CI 同款**（ruff 0.15.21 / pytest / graph-compile / spec-wave lint+verify）为准，基线对拍 = 干净 worktree @ `3cc3e71` vs base `f78a721` 定点复跑。后续 CI 恢复后如需补跑，按本档证据链对照即可，不构成语义缺口（本波零 app/ 码）。
- **偏差②（环境性 · 承先例）**：40 worktree 无 `.env`，全量套件墙钟 ~90s（网络型用例走真实超时路径）——环境性非仓码语义，与基线判定无关。
- **residual_risk 登记（承 task 档 R0/R4）**：0c88ac32 承载面在**仓外运行时**（本仓 git 无此对象 · 10 档实扫如实登记）——本 task 落点裁决 = gate 记录层（本仓过程资产机断可 grep），消费门内判定属仓外运行时面，**不在本 task 语义内**；后续若仓外运行时需消费同签语义，以 FRAGMENT 落文为唯一真源转译，不另立口径。

## 五、关账动作

- 档迁：`docs/tasks/active/` → `docs/tasks/done/`（本 CLOSE 档 + done/README + active/README 同步 + 40/50 invoke）；
- issue #333：维护者执行关 issue（bot 不 close issue · 已声明）；
- 后续跟踪：无另波（仓外运行时消费面转译如立项另走 Harness 流程）；
- 分支移交：`agent/cosign-semantics-task-022a61b26cba` / `fix/cosign-gate-semantics` / `close/cosign-gate-semantics` 移交 00 统一清理（本 CLOSE 不删任何东西）。

## 六、棒链留痕

| 棒 | 交付 | PR / 落点 |
|----|------|-----------|
| 10 | task 档起草（四闸 pending · NO-GO 20/30 · 三案对比 + 滑点 + 审计链影响面 · R0–R5 全轮 · 0c88ac32 仓外承载面如实登记） | #351 `70cb1a0` → squash `82bf056` |
| 20 | 四闸签认代录（lead · 依据 review `5795679444` + #6676780590 + 授权链）+ R2 裁决回填 · 20-R1 审查文随 30 落盘 | PR #351 review `5795679444` → 签认档 `f72ab1d` |
| 30 | 裁决落文 FRAGMENT + 00-orchestrator 引用行 + 机断 8 断言先红后绿 + 旧测零适配 | #352 squash `3cc3e71`（`d2d9eaf` 红 → `c25336c` 绿 → `8fc4229` 出货）· 六条件全过 |
| 40 | 独立复跑机制面 PASS（worktree `/tmp/verify40-cosign` @ `3cc3e71` · 基线 `f78a721` 同 4 红逐字复证零新增）· 偏差①②登记 | `invoke_20261106_40_verify.md` |
| 50 | 本 CLOSE 收口 | 本档 + done/README + active/README + `invoke_20261106_50_close.md` |
