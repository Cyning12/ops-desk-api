# Task Audit R1：b2-nit3-admin-items-array · PASS-WITH-NITS（n-1 消歧照登 · 内容零阻塞）

> **复制说明（双址过渡 · 2026-10-11 CLOSE 棒落）**：本档系址A 原件 `docs/harness/reviews/task_b2_nit3_admin_items_array_audit_R1_20261011.md` 的逐字复制件（审查门禁双址规约 v1 §二 过渡期口径 · 址B 存档命名 `YYYYMMDD_<slug>_r<n>.md`）；址A 原件原址原内容不动，正文与本件逐字一致（仅本行与下一行说明为增量）。
> **来源**：址A（verify 门禁消费址）→ 址B（20 书面审存档址）· CLOSE 文档 `docs/tasks/close/close_b2_nit3_admin_items_array_20261011.md`

> **hat_id**：20-task-audit
> **task**：`docs/tasks/active/task_b2_nit3_admin_items_array.md`（审查时 HEAD 3e4d610 · 分支 `task/b2-nit3-admin-items-array` 本帽 `git branch --show-current` 核实 · 自立 worktree 勿切）
> **上游**：SPEC `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（HG-SPEC-SIGNOFF approved 2026-10-11）+ CLOSE 档 `docs/tasks/close/close_tool_catalog_page_b1b2_20261011.md`（§4 NIT-3 · §7 后续建议四条）+ 交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 4 项
> **日期**：2026-10-11
> **task lint**：本帽复跑 `npx --yes spec-wave@3.0.1 task lint --file docs/tasks/active/task_b2_nit3_admin_items_array.md` → **LINT: PASS · EXIT=0**（W3 自检结论占位符 · draft 期合法 · close 前须回填）
> **task 回填**：零阻塞 · **未改** task 正文 / 人工闸表 / `app/` / `tests/`

## 结论

**PASS-WITH-NITS · 内容零阻塞**：范围/非范围与 CLOSE §7 四条取舍一致（第 2/3 条入范围 · 第 1/4 条入非范围 · 逐字照录核真）；R2 数据源裁定 S1（全量在册无 filter）推理链成立且为 disabled 三态唯一可达路径；钉死契约七条与 SPEC :75-78/§3/§5 FP-4/FP-5/FP-6/纪律 #2/#3/#4 逐条对齐；14 键精确键集与 SPEC :75 逐字一致、与 types.py:77-130 字段族对拍无缺；TC1–TC6 全可机断；思考轮 R0–R5 闭合 early_stop 理由成立；机械闸 lint PASS。唯 n-1 一处键集/缺省表述张力照登（留 30 消歧，不阻）。

**流程闸（分列）**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸均 **pending 照实 · 本帽不代签 · 30 拒开工**；HG-PILOT-OPSDESK-GLAYER n/a 无外部试点面。闸表 4 列契约符合。

## 核对表（内容面 · 逐组亲读实证）

| # | 核对项 | 结果 | 证据 |
|---|--------|------|------|
| C1 | **R2 数据源裁定 S1 推理链** | ✅ | registry.py:85-91 `list_specs(filter=None)` 回全量在册（:89-90 `if filter is None: return list(specs)`）；registry.py:120-121 `_match_filter` 首判 `if not spec.enabled: return False` 逐字在仓；admin/capability.py:179-181 默认 `baseline=True` → `baseline_filter(node_role="admin_preview")` → `capability_catalog_snapshot(filter=cap_filter)`（:190-192）——经 cap_filter 路径 disabled 永不出现，S1 确为 disabled 三态唯一可达路径；gateway.py:133-143 `capability_catalog_snapshot` → :142 `_registry.list_specs(filter=filter)` → :143 `evaluate_visibility` 链路核实 |
| C2 | **契约 2 与 :179-181 默认行为自洽** | ✅ | 「query baseline/filter 只影响 visible_ids/summary 零 diff · items 恒全覆盖」——baseline 默认 True 仅构造 cap_filter 喂 snapshot（影响既有 visible_ids :214 + **summary :215），items 为新增顶层键、数据源独立于 cap_filter，与现状行为零冲突；TC2 以 baseline=false + query 组合断言覆盖集不变，机断可行 |
| C3 | **14 键精确键集对拍** | ✅ | SPEC :75 字段族逐字：id/kind/description/when_to_use/when_not_to_use/tags/risk_level/side_effect/enabled/tenant_scoped/reversible/execution_type/status/visibility_reason = 14 键；types.py:77-130 CapabilitySpec 十二字段全部在册（capability_id→id 投影改名承 capability_mine.py:42 先例）；排除面成立：`adapter` 非 spec 字段（registry 条目/manifest 键 · FP-5）· `args_schema` SPEC §3 :95 钉死；SPEC :77 status 三态逐字一致 |
| C4 | **status 三态语义锚点** | ✅ | disabled 优先判定承 registry.py:120 同款首判语义；denied 四码 visibility.py:38-41（REASON_DEPARTMENT/ROLE/PROJECT/CLASSIFICATION）逐字核；词表单源 VISIBILITY_REASON_TEXTS :44-49 + 未知码原样兜底 :140（`.get(reason, reason)`）；check_visible :93-117 回 (visible, reason) · evaluate_visibility :120-151 回 (kept, summary) · hidden 附 visibility_reason :135-141 |
| C5 | **NIT-3 锚点与契约 6** | ✅ | tests/test_capability_manifest.py:331-333 / :354-356 实测仅逐键值断言（`meta["version"] == 9/10` · `meta["capability_manifest_count"] == 1`）· 无键集相等——NIT-3 观察属实；`_LAST_META` 两键 manifest.py:102-105 + getter :150-152 `return dict(_LAST_META)`；契约 6「断言升级 + 被测面零改动」与 close 档 §4 偏差 2「对拍口径偏强不偏弱」口径一致 |
| C6 | **CLOSE §7 四条照录 + 范围取舍** | ✅ | close_tool_catalog_page_b1b2_20261011.md:84-87 四条原文与 task :49-52 逐字一致；第 2 条（admin items 数组）+ 第 3 条（NIT-3）入范围、第 1 条（前端 F1 分仓 SPEC）+ 第 4 条（冒烟脚本化）入非范围，与交接档 §2.2 第 4 项（PROMPT_00 :47）立项令一致；NIT-3 原文（close :49）照登一致 |
| C7 | **钉死契约七条 vs SPEC/close** | ✅ | 契约 1 只增不删=纪律 #2+FP-4（既有键清单 filter/principal/visible_ids/visibility_*/manifest_errors/manifest_error_details 与 admin/capability.py:194-218 返回字典逐键对拍一致）；契约 2=SPEC :75「每个在册一条」；契约 3=SPEC :77；契约 4=纪律 #3+FP-6；契约 5=SPEC :75+纪律 #4+FP-5；契约 6=NIT-3+B2 钉死存续；契约 7 只读零写+AdminSyncAuth :166 实证 |
| C8 | **TC1–TC6 可机断性** | ✅ | TC1 长度==全量在册数+键集相等+evaluate_visibility 直出对拍（pytest 机断）；TC2 逐键零 diff+baseline=false 组合覆盖集不变；TC3 fixture 注入三态同现+disabled 不在 visible_ids 不附 reason；TC4 响应体子串断言（adapter/local_fn:/args_schema · FP-5）；TC5 两处 `set(meta.keys()) == {"version","capability_manifest_count"}` 在前+原断言存续+实现零 diff；TC6 ruff/lint-imports/graph-compile EXIT=0/task lint——无人工判断残留 |
| C9 | **B1 旧测影响面表** | ✅ | 五文件锚点亲核：test_admin_capability_observability.py :54 鉴权/:62 runtime/:113 hidden 解释/:149 kinds 裁剪/:173 filter/:185 deny_write 逐一处实测在仓；test_multi_replica_dualproc.py:674-728 `test_runtime_scope_and_catalog_parity` 在仓（catalog 两实例一致断言）；行为变更类 checklist 项以专节「B1 · 旧测影响面」承载（等价于验收内 grep 影响面 · 满足 K7 提醒精神） |
| C10 | **闸表契约 + graph n/a 条件回写** | ✅ | 闸表 4 列（human_gate_id/status/blocks_hats/说明）· 三闸纯 pending 未代签 · HG-PILOT-OPSDESK-GLAYER n/a；graph_change_layer/graph_delta=n/a 预判照实写 + 条件回写表述在案（:19-21 + F5）；modules.md :34 capability 行「观测快照 metrics.py/visibility.py（经 admin 模块端点暴露）」与 :38 admin 行「Capability 观测端点 GET /admin/capability/{runtime,catalog,...}」既有备注覆盖语义属实 |
| C11 | **思考轮 + 流程面** | ✅ | R0–R5 控制表回填闭合 · early_stop at R5 理由成立（范围/非范围/验收/failure_paths/锚点齐备 · 数据源裁定闭合）· residual_risks 如实留 30（投影落点 · visibility_reason 形态）；orchestration 10→20→维护者签→30 与 required_invoke_hats `10,20,30,40` 一致；修订记录在案；10 invoke 已留档 |
| C12 | **非范围八条 vs SPEC §3** | ✅ | 前端 F1/冒烟脚本化（close 四条取舍）+ B1 mine 零改动 + args_schema 出站（SPEC §3 :95）+ meta 被测面 + 加载/校验/执行语义 + SSE/freeze/表/env + 跨用户对比视图（SPEC §3 :96）——逐条与 SPEC §3 非范围/close 档一致，无越界承诺 |

## 非阻塞清单（nits · 照登 · 不阻）

| # | 级别 | 内容 | 建议 |
|---|------|------|------|
| n-1 | 表述张力（留 30 消歧） | 钉死契约 5「每条目键集精确 14 键」与同条「visibility_reason 其余 `None` **或缺省**由 30 裁定」并存：若 30 选「缺省」（非 denied 条目不出该键），TC1「每条目键集精确 14 键（键集相等断言）」对非 denied 条目即不成立——两者只能取一 | 30 钉死时二选一并消歧：①恒出键（非 denied = `None`）保 14 键全条目相等（推荐 · 与「键集精确」表述自洽）；或②键集断言按 status 分档（denied 14 键 / 其余 13 键）并同步修订 TC1 措辞。task 已明示「由 30 裁定并钉入测试」，裁定路径在案，不阻 |

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NITS · n-1 照登留 30 消歧）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT / HG-AUDIT-R1 改为 approved（维护者 · 日期）（HG-GRAPH-MODULES 按 task :38 实判 · 预判 n/a · 30 实证触发行备注则随交付回填代录）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。**HG-AUDIT-R1 = pending，本审查文不附 30 Prompt。**

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 20 R1：锚点七组+SPEC/close/交接档逐组亲读核真（C1–C12 ✅ · lint PASS EXIT=0 复跑）· R2 S1 数据源裁定推理链成立 · 14 键与 SPEC :75 逐字一致 · TC1–TC6 可机断 · 三闸 pending 不代签 → **PASS-WITH-NITS**（n-1 键集/缺省表述张力照登留 30 消歧）· 未改 task 正文/闸表/app/tests |
