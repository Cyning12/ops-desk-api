# invoke：delegation-naming-boundary · 30_implement · 2026-10-20

- **hat**：30（实施 · 红测先行）
- **分支**：`task/delegation-naming-boundary`（自 docs/task-delegation-naming-boundary HEAD `d337486` 切出 · PR 含文档+代码全链）
- **契约锚**：task v0.2（194 行 · HG-SPEC-SIGNOFF/HG-AUDIT-R1/HG-GRAPH-MODULES 全 approved）+ SPEC v0.1 + R2 审查文（pass）
- **写入面**：app/ops/capability/delegation.py · app/ops/lg_rag/multi/nodes.py · tests/test_capability_delegation.py · tests/test_capability_testing_write.py（仅注释）· tests/test_lg_rag_write_replay_guard.py（新增）· tests/test_hitl_approved_replan_quality.py（00 裁定扩充 · 限定语内一行 setenv）· tests/test_strategy_scenario.py（00 裁定扩充 · #3 闸跨波次碰撞修正）· docs/_tech_graph/l1/01_modules.md（行内回写+闸登记行）· docs/guides/GUIDE_env_inventory_v1.md（83→84 键）· 本 invoke。scripts//alembic/ 零触达 · 零新 event_type/路由/表。

## 〇、GATE_VERIFY 机读误报（第四次先例）

`npx spec-wave verify` 报「HG-AUDIT-R1 pending 拒 30」（EXIT=2），但同表 status 栏明写 approved，且 commit `d337486`「HG-AUDIT-R1 落签 approved（00 代签 · R2 pass · M1-M3 闭合）」实证——系机读误报（本 task 第四次），闸表真值为准开工，特此落档。

## 一、D1 正名（auto_approve_ok → issuance_policy_allows · 直改不留别名）

| 面 | 实测坐标 | 内容 |
|---|---|---|
| def | app/ops/capability/delegation.py:479 | `def issuance_policy_allows(specs, *, effective_scope)`（判定体 :479-505 逐字节不动） |
| 调用 | app/ops/lg_rag/multi/nodes.py:445 | `dl.issuance_policy_allows(...)` |
| docstring | nodes.py:433 | `issuance_policy_allows` 字样 |
| 测试 def ×3 | tests/test_capability_delegation.py:339/:353/:359（R2 校正命中） | test_issuance_policy_allows_readonly_in_scope / _denies_write_and_sandbox_cli / _denies_out_of_scope + 三调用点 |
| 注释级 ×3 | tests/test_capability_testing_write.py:185/:412/:468 | 注释内旧名换新（逻辑零改） |
| 图谱 | docs/_tech_graph/l1/01_modules.md:35 | lg_rag 行 T1 备注换新名（去字面化：新段以「旧名直改不留别名 · 映射见 task/invoke」表述，防 TC1 自咬） |

TC1 grep（`grep -rnI --exclude-dir=__pycache__ 'auto_approve_ok' app/ tests/ docs/_tech_graph/ docs/guides/`）：唯一命中 01_modules.md:116 闸登记表历史回写行（豁免②）→ 通过。app/ 零残留。

## 二、D2 护栏解耦（FP-2 唯一 intentional behavior change）

- 新开关：nodes.py `ENV_WRITE_REPLAY_GUARD_ENABLED="LG_RAG_WRITE_REPLAY_GUARD_ENABLED"` + `_write_replay_guard_enabled()`（:266-289 · 布尔默认开 · 非法值 `logger.warning` 留痕回退开 · 解析承 SESSION_SUMMARY_ENABLED 先例 continuity.py:155-170 但方向相反 · R1 N-d 防误抄已避）。
- **真门控仅两处**切换：write_done_keys 条件建索引 + guard-skip 块头（原 :903/:931 · 行号因插入前移）。`:987-988` batch_write_keys 惰性跟随在门控块外，解耦后不破。
- **不动实证**：签发审批门（现 :999）与 scope 门（现 :1300）保持 `_delegation_active()` 耦合——grep 实证两处未被触碰；R1 N3 误并澄清落地（照 R1 字面误并会错误启用签发审批）。
- FP-2 声明：delegation off 下护栏由从不生效变默认生效（唯一行为变更 · 已同步图谱 :35 段与本 invoke）。

## 三、00 裁定链（枚举外冲突 2 起 · STOP 呈裁 → 裁准执行）

**呈裁**：park 全量 2 failed——① 遗留钉 test_tc2_guard_zero_touch_when_delegation_off 系 FP-2 正面翻转对象（task/SPEC/R2 全文未枚举其改造 · 文件不在 TC8 白名单）；② #3 闸 test_diff_whitelist_scenario_stage_rewire 前置 banned 断言误咬本波次白名单内 app/ops/capability/delegation.py（base worktree 实证该闸于 d337486 干净树 1 skipped · 系跨波次碰撞非越界）。

**裁定 A（裁准建议）**：旧钉语义=「delegation off 零介入」，FP-2 后忠实译法=两开关同关——tests/test_hitl_approved_replan_quality.py :357 后增补一行 `monkeypatch.setenv("LG_RAG_WRITE_REPLAY_GUARD_ENABLED","false")`（夹具级 · 断言/场景零改）；扩充 #4 TC8 白名单纳入该文件（带限定语）。已执行 ✓。

**裁定 B（修订 #3 闸 · 先例 9dd5c79/c61a2d5 均由 00 裁定修订前波次闸）**：O2 本意=禁区（scripts//alembic/）不被 skip 掩盖，但现行实现把 app/ 白名单越界也前置 fail。修法=前置硬 fail 仅限 `_BANNED_PREFIXES`；app/ 及其余越界一律走波次分类（foreign → 态③可审计 skip · 波内 → 态② fail 保牙）。已执行 ✓（tests/test_strategy_scenario.py `_banned` 收窄 + 注释注明裁定）。

## 四、#3 闸三态验证（裁定 B 要求）

| 态 | 方法 | 结果 |
|---|---|---|
| #4 分支上 skip | 直接跑 | ✓ SKIPPED · reason 列 `['app/ops/capability/delegation.py', …]` 全为 foreign（可审计） |
| 波内文件被改仍 fail | 临时摘除 `tests/test_memory_injection_consumer.py` 出 #3 白名单 + 触碰该文件（波次窗内） | ✓ fail `diff 越白名单且属 #3 波次窗内文件（回归牙）`（验毕 git checkout 还原 · 闸文件误还原事故已发现并即修复重验） |
| banned 越界仍 fail | 临时落 `scripts/__tmp_gate_probe_30.py`（untracked） | ✓ fail `禁改面（scripts/ alembic/）出现改动`（验毕删除 · 树净） |

#4 自身 TC8 四态（tests/test_lg_rag_write_replay_guard.py）：态①钉锚 d337486 在库全量判定（本机）· 态②波内 fail 保牙 · 态③ foreign 可审计 skip · 态④锚缺失 banned 以 vs HEAD+untracked 兜底；banned 前置于全部 skip 出口；白名单已含两裁定扩充文件（各带限定语注释）。

## 五、TC 逐项状态

| TC | 内容 | 状态 |
|---|---|---|
| TC1 | 三面 grep 零残留（豁免两类） | ✔（唯一命中 01_modules.md:116 豁免行） |
| TC2 | 正名后 delegation 测试矩阵绿 | ✔ |
| TC3 | 默认开 · delegation off 拦重放（金样钩子 write_replay_guard_skip/replay_of） | ✔（红→绿） |
| TC4 | 关恢复与 master 基线逐字节一致（逆牙 · 前后皆绿） | ✔ |
| TC5 | delegation on 矩阵零 diff（on×on 照拦 · on×off 签发门照常拦 delegation_issue_hitl_required） | ✔（TC5-b 红→绿） |
| TC6 | （task 定义面 · 图谱/env 台账同步） | ✔ 见 TC10 |
| TC7 | 非法值回退开 + warning（行为面 2 例 + 解析矩阵 13 例） | ✔（红→绿） |
| TC8 | 四态 diff 闸（白名单 ⊆ 裁定后面 · banned 前置 · 态④兜底） | ✔ |
| TC9 | 冻结面零变化（SSE lg-rag-sse-v1/HTTP lg-rag-http-v1/审计五动作/拒绝码/TTL） | ✔（diff 自查零触达） |
| TC10 | 图谱回写+GUIDE 84 键+invoke 齐+graph-compile | ✔（graph-compile EXIT=0） |

## 六、红测先行记录

红测（tests/test_lg_rag_write_replay_guard.py 全套 + 三正名 def 改名）于实施前落地：**RED 实证 23 failed / 32 passed**（TC3、TC5-b、TC7 全组、三正名测试 RED；TC4/TC5-a/TC8 按设计绿）→ 实施 D1/D2 后逐项转绿。

## 七、验证面

- **park .env 全量**：1762 passed / 184 skipped / **0 failed**（全绿）。
- **.env 在场对拍**：branch FAILED 清单（37 项）与 base `d337486` worktree 同条件逐项 **IDENTICAL**（diff 零输出）——全部为既有 .env 噪声（delegation enforce/manifest 预注册/write-tags/strategy 候选等泄漏族），本波次零新增。
- **ruff check app tests**：全绿。**lint-imports**：12 kept 0 broken。**graph-compile**：EXIT=0。
- 调查插曲：对拍初差 1 项（fp5 env_write_id_stripped 在 branch 翻 fail）——实证定位为跨文件注册表泄漏：`tests/test_lg_rag_delegation_wiring.py:56` `get_registry().clear()` 后，本波次新文件的共享 `cap_env` 夹具重注册 `testing.write.echo` 无卸载，翻转下游 ∩visible 断言。修复=新文件内 autouse 快照恢复夹具（用例前未注册则用后 `unregister` · 不动共享夹具与任何他文件）→ 复跑 IDENTICAL 达成。

## 八、冻结面与铁律自查

- SSE 帧/HTTP 契约/审计五动作词表/拒绝码 R-a~R-f/TTL 600s/HITL TTL 3600s/三档默认值：零触达（diff 自查 + TC9）。
- app/ 改动限白名单两文件；scripts//alembic/ 零触达；零新 event_type/路由/表；图谱仅 capability/lg_rag 行内备注回写+闸登记一行（不增行外结构）。

## 九、遗留挂账

- GATE_VERIFY 机读误报（第四次）——建议 spec-wave 侧修闸表 status 栏解析，另案。
- .env 在场 37 项既有噪声族（与 base IDENTICAL）——非本波次引入，清理另案。
- 共享 `cap_env` 夹具（tests/test_hitl_approval_consumption.py:77-87）注册表无卸载的先例泄漏面仍在（本波次以新文件内快照夹具隔离 · 未动共享件）；如需根治另案裁定。
- untracked `backups/` 与 `docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md` 系外波次遗留 · 非本波次产物 · 不动。
