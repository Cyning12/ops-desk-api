# SPEC 书面审查：hitl-approval-consumption · R1（20-spec-audit）

## 元信息

| 字段 | 值 |
|---|---|
| **帽** | 20-spec-audit（SPEC 书面审 · 不实现代码 · 不改 SPEC 实质内容） |
| **日期** | 2026-10-09 |
| **对象 SPEC** | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v0.md`（v0 · draft · commit 2fd69c8 · HG-SPEC-SIGNOFF=pending） |
| **起草 invoke** | `docs/harness/invokes/by-task/hitl-approval-consumption/invoke_20261009_10_spec_hitl-approval-consumption.md`（含留转本帽六条） |
| **轮次** | R1（轻量路径：10-spec 思考轮 R0–R5 已回填充分，单轮书面审） |
| **实证复核范围**（本帽于 worktree spec/hitl-approval-consumption = master ca4148f + SPEC commit 逐一实读） | `delegation.py:488-514` · `nodes.py:277-295,147-157,660-738,1397-1471` · `router.py:255-274,287-316,403-411,486` · `strategy/config.py:1-45` · `builder.py:170-189` · `registry.py:112-140` · `policy.py:90-114` · `store.py:60-163` · `models.py:449-487` · `step_contract.py:33-64,195-231` · 30/40 invoke 源证据节 |

---

## 一、起草者留转六条 · 逐条裁定

| # | 留转审查要点 | 裁定 | 实证依据 |
|---|---|---|---|
| 1 | **payload 增记 capability_id 是否越「挂起/decide 落库不动」非范围边界** | **PASS（不越界）** | `payload` 为 jsonb 列（models.py:480），DbHitlStore `_INSERT` 已含 `CAST(:payload AS jsonb)`（store.py:130-138）——增键零迁移、零 SQL 改动、既有读取兼容；增键点在 `_persist_hitl` 申请**创建**路径（nodes.py:1446-1457），不触 decide 状态机 / `adecide` 只受理 pending 守卫（store.py:89-94 · `_DECIDE` WHERE status='pending' :159-163）/ 重复 decide 409（router.py:265-274）。SPEC §3 第一条已显式立字据澄清此边界，且以「旧单据缺键 → 不消费（fail-closed）」+ A2 断言兜底；A7 再以 `store.py` git diff 为空钉死。裁定：属接线修补，非范围声明与边界澄清相容。 |
| 2 | **TTL 默认 3600s 与读时过期不写状态语义** | **PASS** | 「读时判过期、不写 expired 状态」恰好守住「decide 落库不动」非范围（写状态即越界，Q5 S3 弃选理由成立）；models.py:481 注释 `pending \| approved \| rejected \| expired` 已预留语义位，未来 sweep 另议不冲突；env 非法/越界回退默认承 `_env_int` 既有纪律（step_contract.py:33-42 · delegation.py:85-86,107 low=1 high=86400 先例在仓）；台账记 TTL 余量（§1 纪律 5 / D4）使「为何这次不消费」可审计。3600s 默认值可配、方向正确（防囤批），不过宽不过窄。 |
| 3 | **_delegation_issue_block_reason 消费点 async 化冲击面** | **PASS（附 nit N2）** | 调用面实证仅两处：nodes.py:711（`_join_subtasks` 派发循环内 :684-738，宿主为图节点、LangGraph 节点天然 async，await 化可行）+ tests/test_capability_testing_write.py:492（sync 直调，须随改）。SPEC Q2 已裁定编排层消费并承认「nodes 调用面 async 化小改」；`auto_approve_ok` 保纯函数零 IO（delegation.py:488-514 docstring 实证）纪律守住。冲击面有界，但 SPEC 未点名这两处——留 task 阶段点名（见 N2）。 |
| 4 | **unlock=被拦 sid 自身形态守卫完备性（其他 blocked_by 是否也产空 unlock）** | **PASS（完备）** | blocked_by 全词表实证：`step_contract.gate` 仅产出 `predecessor_failed` / `contract_missing_field` / `prefix_touch_required`（step_contract.py:56-64,195-231），其中 HITL 类仅 `prefix_touch_required`（:67 `HITL_REASONS` 单元素集），且按构造 `dep ∈ prefix_ids` ⇒ unlock 恒非空；`delegation_issue_hitl_required`（nodes.py:714）是**唯一**可产空 unlock 的 HITL 类（单子任务 / 被拦步无已执行前缀依赖）；手工申请端点 router.py:486 默认 `prefix_touch_required` 且 unlock 由 payload 显式给。另核实 D2 措辞「**当** depends_on∩plan_prefix_ids 为空 **且** blocked_by=delegation_issue…」保留了非空时照旧取前缀的现状路径（nodes.py:1440-1445），不误伤。形态守卫「仅 delegation_issue 类回填 + router 409 保留不动（:404-411 实证在仓）」完备。 |
| 5 | **env 追加集对未知 key 生效是否削弱 fail-closed** | **PASS（不削弱默认面）** | 「fail-closed 管默认不管显式」裁定成立：① 既有先例 `CANDIDATE_CAPABILITY_IDS` 全局覆盖钩子（config.py:25-26 注释明示测试/运维显式覆盖），env 追加集半径反而更小（只追加不覆盖）；② env **不设**时含未知 key 在内各 key 对 master 逐字节零 diff（A4 断言 · 现状未知 key → [] 实证 config.py:42-44）；③ env 设的 id 仍须过下游四道闸——`build_allowlist_from_candidates` ∩visible（builder.py:180-182）、`deny_high_risk` 判序在前（registry.py:128-129 先于 `deny_write` :130-136）、Policy 写闸 `write_not_confirmed`（policy.py:101-105）、`_subtasks_have_valid_tool_ids`（nodes.py:147-157）；FP-5 断言「env 含高危/写 id 仍被裁」。env 只抬候选层，不是放行口——成立。 |
| 6 | **「仅 approved 未过期未撤销」读时活状态语义可审计性** | **PASS** | 消费=读取时刻 `status==approved` + `decided_at+TTL` 双条件，不写回单据；未来撤销端点把 approved 翻走即天然令消费失效（授权效力=读时活状态，非缓存快照）——与非范围「撤销端点另议」兼容且无隐式假设；台账记 request_id/subtask_id/capability_id/decision_by/TTL 余量，记动作不记内容（承 capability/metrics.py、visibility.py 先例）。审计链「谁批的（decision_by）· 批给哪步哪 tool（三元组）· 消费时余量多少」闭环可查。 |

**六条裁定计数**：PASS 6 · FAIL 0 · 退回 0（第 3 条附非阻塞 nit N2）。

---

## 二、通用清单核对

| # | 核对项 | 结果 | 证据 / 说明 |
|---|---|---|---|
| C1 | 范围可界：D1 消费门 / D2 unlock 回填 / D3 env 口 / D4 审计测试 | ✅ | §2 D1–D4 各有代码锚点且本帽逐一实读成立；三缺口与 30/40 invoke 源证据（30 :52-61 · 40 :33,42,44 · run 0eb059a5）对拍一致 |
| C2 | 非范围锁死：挂起/decide 落库 · UI · deny 判序与写闸 · 撤销端点 · 自动边界 · 新表 · 会话级授权 | ✅ | §3 七条显式排除 + 边界澄清立字据；与 D 块无重叠冲突 |
| C3 | 验收可机断 A1–A8 | ✅ | A2 变异式否定断言组（pending/rejected/超 TTL/键不匹配/旧单据缺键/store 异常六态）；A5/A7 以「git diff 为空 + 既有测试原样绿」双钉反回归；A8 pytest/ruff/graph-compile EXIT=0 均机断可行；A3 live 段留 40 分工承 testing-write-capability 先例（30 invoke :62-64 · task A4④） |
| C4 | failure_paths FP-1~FP-7 全正面裁定 | ✅ | FP-1 fail-closed 有仓内去重拉取同款先例（nodes.py:1428-1429）；FP-6 锚点 `_collect_decisions` router.py:287-316 实证在仓；FP-7 off/observe/enforce 三档语义与 `_delegation_active()` 短路（nodes.py:708-710 注释「off 模式整段短路」）实证一致 |
| C5 | R0–R5 思考轮闭合 · early_stop=no | ✅ | §7 控制表六轮全 done；Q1–Q5 均 ≥2 案对比 + 裁定理由；无提前停止理由 |
| C6 | 反回归钉死①：deny 判序不动 | ✅ | registry.py:112-140 实读：`deny_high_risk` :128-129 **在** `deny_write` :130-136 之前；`allow_write_tags_any` 只豁免 deny_write 一层（:131-135）；docstring 判序声明（:113-118）与 SPEC §1 纪律 1 逐字吻合 |
| C7 | 反回归钉死②：Policy 写闸不动 | ✅ | policy.py:96-105 实读：高危（:96-99）→ 写 `write_not_confirmed`（:101-105）→ sandbox（:107-110）→ cli（:112-114）闸序与 SPEC §1 纪律 2 一致；审批消费不豁免任何一层 |
| C8 | 反回归钉死③：off 零 diff | ✅ | nodes.py:710 `if _delegation_active() and ...` 短路实证；SPEC §1 纪律 3 + A6 断言（无 store 读 · 无新台账）可机断 |
| C9 | 维护者立项裁定原话留痕 | ✅ | SPEC 头部 :8 与 invoke :6 均引「另立task，此次完成后写入到spec文档中」（2026-10-09），与 40 invoke 裁定建议 :65,76「另立 task」衔接一致 |
| C10 | 图谱义务与 freeze 声明 | ✅ | freeze_id=无（无新 SSE 事件 · 无新路由 · 无新表 · payload jsonb 增键零 alembic）与代码实证一致；graph_change_layer=G-L1 行备注四行在册、不新增一级模块，HG-GRAPH-MODULES 00 代录路径明确 |

**核对计数**：10 项 · 通过 10 · 不通过 0。

---

## 三、阻塞清单

无。六条留转全部裁定 PASS，范围/非范围边界清晰可执行，验收与 failure_paths 均可机断，全部代码锚点与仓内真值逐一实读一致。未发现需退回 10-spec 的实质缺口。

## 四、非阻塞清单（nits · 不阻签收 · 移交 task 阶段）

| # | 级别 | 内容 | 建议 |
|---|---|---|---|
| N1 | 文献 nit | SPEC 锚点 `router.py:403-411` 实测 409 raise 在 :404-411（:403 为 `_collect_decisions` 调用行）；区间覆盖无误 | task 引用时可用 :404-411 更精确；SPEC 本体无需升版 |
| N2 | 交付提示 | async 化波及面 SPEC 未点名：nodes.py:711 调用点 + tests/test_capability_testing_write.py:492 sync 直调（须改 async） | 00 拆 task 时在范围/验收中显式点名两处；A6 off 零 diff 断言须含「sync 测试改造后行为不变」 |
| N3 | 交付提示 | TTL env 越界回退的 low/high 未给数值 | 承 delegation.py:107（low=1 high=86400）先例，由 task 钉死具体界与断言 |
| N4 | 实现陷阱提示（SPEC 未点名 · 不属 SPEC 缺陷） | `decided_at` 两 store 类型不一：InMemory `adecide` 写 `time.time()` float（store.py:98），Db `_DECIDE` 写 `now()` 回读为 datetime（store.py:159-163） | 消费端 TTL 比较须归一两种类型；建议 task 验收 A2 补「InMemory 与 Db 双 store 下 TTL 判定一致」断言 |

---

## 五、HG-SPEC-SIGNOFF 建议

**建议签收（pass）**。本帽**不代签** human_gate；维护者签录 `HG-SPEC-SIGNOFF=approved` 后，由 00 在 `task/hitl-approval-consumption`（自 master 分出）起草 task → 20-task-audit → HG-AUDIT-R1 人签 → 30。拆 task 时携带 N1–N4 回填；本帽不附 30 Prompt。

### HG-SPEC-SIGNOFF 维护者签闸清单（待维护者人签 · 本帽不代签）

| 项 | 内容 |
|---|---|
| human_gate_id | `HG-SPEC-SIGNOFF` |
| 对象 | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v0.md`（v0 · commit 2fd69c8） |
| 前置 | 20-spec-audit R1 书面审 PASS-WITH-NITS（本文） |
| 维护者签署 | ______________（姓名 / 日期 / approved 或退回意见） |
| 签后下一棒 | 00 起草 task（invoke_slug=`hitl-approval-consumption` · 携带 N1–N4）→ 20-task-audit → HG-AUDIT-R1 |

## 六、结论：R1 PASS-WITH-NITS

R1 书面审 **PASS-WITH-NITS**：起草者留转六条逐条裁定全 PASS（payload 增键不越非范围边界 · TTL 3600s 读时过期语义成立且可审计 · async 化冲击面有界 · unlock 形态守卫完备 · env 追加集不削弱默认面 fail-closed · 读时活状态语义可审计）；通用核对 10 项全过；反回归三面（deny 判序 / Policy 写闸 / off 零 diff）与 decide 落库不动均以源码实读钉死；四条非阻塞 nits 移交 task 阶段，不影响 HG-SPEC-SIGNOFF 进入维护者人签。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-10-09 | R1 首审 PASS-WITH-NITS：留转六条全 PASS · 通用清单 10 项全过 · nits N1–N4 · 建议维护者签 HG-SPEC-SIGNOFF（不代签） |
