# 20-task-audit R1 书面审：task_delegation_naming_boundary v0.1

> **hat_id**：20-task-audit（R1 · 书面审 · 只审不改 · **不代签** HG-AUDIT-R1）
> **审查对象**：`docs/tasks/active/task_delegation_naming_boundary.md`（draft v0.1 · 191 行 · 分支 `docs/task-delegation-naming-boundary` · commit `84a44ba`）
> **对照 SPEC**：`docs/spec/delegation-naming-boundary/SPEC-delegation-naming-boundary_v0.md`（v0.1 · signed · HG-SPEC-SIGNOFF=approved 2026-10-19）
> **上游审查**：`docs/harness/reviews/spec_delegation-naming-boundary_audit_R1_20261019.md`（R1 conditional_pass → R2 pass）· 上游 SPEC `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` §4 Q3
> **审查日期**：2026-10-20 · **审查人**：Harness 20-task-audit 子 Agent
> **结论**：**conditional_pass（PASS-WITH-NITS）** · 门控锚点修正核验**成立** · banned 前置强化方向**确认正确** · 阻塞项（fail 级）**0** · **M1/M2 两条 TC1 牙对齐建议 10-task 签前修订**（不改实质）· 锚点实测 27 条：命中 24 / 漂移 2 / 事实错误 1
> **实证复核范围**：task 全文 191 行逐行 · SPEC v0.1 全文 · R1/R2 审查文全文 · master `31924af`（实证 = HEAD = origin/master）亲读：`app/ops/lg_rag/multi/nodes.py:405-425/:898-995/:1258-1292` 逐行 · `app/ops/capability/delegation.py:470-510` 逐行 · `tests/test_capability_delegation.py:330-365` 逐行 · `tests/test_memory_injection_consumer.py:600-660` 逐行 · `tests/test_strategy_scenario.py:445-540` 逐行 · `docs/_tech_graph/l1/01_modules.md:30-40/:105-130` · `docs/guides/GUIDE_env_inventory_v1.md` 全键表 · `app/ops/lg_rag/continuity.py:156-169`（SESSION_SUMMARY_ENABLED 先例）· 全仓 grep `auto_approve_ok`（master · app/ tests/ docs/_tech_graph/ 三面全量枚举）· `tests/test_lg_rag_supervisor_capability_catalog.py:10-20` · host-v1 SPEC §4 Q3 :155-162 · 分支 diff（仅 2 文档文件 · 零 app/ 改码实证）

## 一、八大委托重点核对

### 1. 门控锚点修正核验（R1-N3 校正）· **成立 ✅**

master `31924af` 逐行亲读 `nodes.py:898-995`：

| task 断言 | 逐行实证 | 裁定 |
|---|---|---|
| :903 条件建索引 | `write_done_keys = _write_success_call_keys(done, by_id) if _delegation_active() else {}` 逐字一致 | ✅ 真门控① |
| :931 guard-skip 块头 | `if _delegation_active() and str(row.get("type") or "") == "tool":` 逐字一致；块内 :932 `write_key = _guard_write_key(row)` · :933-963 异 sid 命中 guard-skip · **:941-942 `skipped["write_replay_guard_skip"] = True` / `skipped["replay_of"] = orig_sid` 台账钩子实证在册** · :964-967 同批双胞胎次发挂起 `continue` | ✅ 真门控② |
| :930 关联初始化 | `write_key = None` 逐字一致 | ✅ |
| :987-988 首发登记在门控块外 | `if write_key is not None: batch_write_keys[write_key] = sid  # 确认派发才登记首发` 逐字一致——位于 :931/:970 两块之外，由 write_key 惰性控；解耦 :931 后 write_key 随新开关自然跟随，跟随关系不破 | ✅ 30 核对点在案 |
| **:970 系签发审批门误并** | :968-969 注释「Host V1-A：委派签发审批…off 模式整段短路」+ :970 同形 `if _delegation_active() and ...` + **:971 `issue_reason = await _delegation_issue_block_reason(state, row)`**——实证为签发审批门块头，属 delegation 本体功能，**不在护栏解耦面** | ✅ **校正成立** |
| :1271 同理不动 | `if _delegation_active() and not fallback and subtasks:`（scope 声明∩裁剪门 · :1264-1286 块头）· delegation 本体功能 | ✅ 校正成立 |

**核验结论**：10-task 对 R1-N3 的校正**成立且必要**。R1 审查文 N3 列「解耦真正要改的正是 :903/:931/:970 这三行」——:970 与 :931 是同形 if 行但语义截然不同：若照 R1 字面把 :970 一并解耦，delegation off 时签发审批门将被错误启用（delegation 本体行为破坏）。护栏真门控仅 :903（条件建索引）+ :931（guard-skip 块头）两处；R1 审查文该条以本审查核验为准记录。

### 2. FP-2 行为变化验收三牙 · **完备可机断 ✅**

| 牙 | 设计核验 |
|---|---|
| TC3 默认开拦截（正牙） | env 全不设（delegation 默认 off · guard 默认开）→ write 双胞胎重放金样被拦；断言钩子 `write_replay_guard_skip`/`replay_of` 实证在 :941-942 真值在册，不依赖人工判断 |
| TC4 关恢复旧行为（逆牙） | `LG_RAG_WRITE_REPLAY_GUARD_ENABLED=false` + delegation off → 与 master 基线逐字节对拍；同时覆盖 SPEC FP-4「关态护栏不生效」反向漏拦面 |
| TC5 delegation on 矩阵 | on×on → 与 master 逐字节零 diff；on×off → 护栏不生效但签发审批门（:970）照常——与第 1 节校正互锁（:970 保持耦合的正确性有牙守护） |
| 应急口 | FP-2 行「应急口 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED=false` 恢复旧行为」口径明确，与 TC4 同一开关路径 |
| 「用户可见=是」落点 | 三层落位：FP 表 FP-2 行「用户可见=**是**（intentional behavior change）」· D2 FP-2 声明段（落 invoke + 图谱 lg_rag 行备注显式声明）· TC10 文档三落位断言。承 SPEC 四层声明义务闭合 |

### 3. 正名兼容处置 · **承 SPEC 一致（M1/M2 待闭合）**

- 直接改名不留别名无 deprecation：SPEC D1「内部符号无对外冻结面，直接改名不留别名（grep 全仓零残留断言）」→ task D1/TC1 逐字承接 ✅；新名 `issuance_policy_allows` 系 SPEC D1 首选（「或 task 阶段选定的等价名」未动用）✅
- 开关 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED`：SPEC D2「env 三档或布尔，task 阶段定键名，**默认开**」留口 → task 定布尔默认开，SPEC 依据充分 ✅；非法值回退开 = SPEC FP-7「回退默认开（安全方向 fail-closed）」逐字承接 ✅；`SESSION_SUMMARY_ENABLED` 解析先例实证 `continuity.py:156-169`（strip/lower/非法回退+warning 模式真实在册）✅（方向差异见 nit N-e）
- TC1 grep 三面 + 历史豁免：豁免逻辑（不可变历史记录不动）合理，但**实测残留面与豁免/白名单未对齐** → 立 M1/M2（见第四节）

### 4. 锚点全量实测（master `31924af` · 27 条）

**命中 24 / 漂移 2 / 事实错误 1**：

| # | task 锚点 | 实测 | 裁定 |
|---|---|---|---|
| 1 | `delegation.py:479-505` 定义三条件纯函数 | :479 `def auto_approve_ok(specs, *, effective_scope)` · :496-497 scope 越界 · :498-502 非只读 · :503-504 sandbox/cli · :505 `return True, ""` 逐行吻合 | ✅ |
| 2 | `nodes.py:408` docstring 提及 | :408 ```auto_approve_ok``` 在 docstring 内 | ✅ |
| 3 | `nodes.py:420` 调用 | `ok, why = dl.auto_approve_ok([entry[0]], effective_scope=scope)` 逐字一致 | ✅ |
| 4-9 | `nodes.py:903/:930/:931/:941-942/:964-967/:987-988` | 见第一节 · 全中 | ✅×6 |
| 10 | `nodes.py:970`（校正对象） | 签发审批门块头实证（:971 `_delegation_issue_block_reason`）· 校正成立 | ✅ |
| 11 | `nodes.py:1271` | `if _delegation_active() and not fallback and subtasks:` 逐字一致 | ✅ |
| 12 | `tests/test_capability_delegation.py:338` 首例 def | 实测 `def test_auto_approve_readonly_in_scope` 在 **:339**（:338 空行） | ⚠️ 漂移+1 |
| 13 | 同 :352 次例 def | 实测 `def test_auto_approve_denies_write_and_sandbox_cli` 在 **:353**（:352 为 parametrize 收尾 `)`） | ⚠️ 漂移+1 |
| 14 | 同 :359 第三例 def | `def test_auto_approve_denies_out_of_scope` 在 :359 | ✅ |
| 15 | 同调用 :340/:354/:360 | 三行 `dl.auto_approve_ok(...)` 逐字一致 | ✅ |
| 16 | `01_modules.md:34` capability 行 | 在册 · 备注含 host-v1-delegation-token 段 · 无 delegation 独立行（承 Q3） | ✅ |
| 17 | `01_modules.md:35` lg_rag 行 T1 备注字样 | 行内 T1 段含「`auto_approve_ok` 纯函数零 IO 逐字节零 diff」字样 | ✅ |
| 18 | `01_modules.md:110-128` 闸登记表先例（含 :116 T1 行） | :105-128 闸登记行在册 · :116 T1 行格式「闸|状态|签署说明|日期|回写摘要」吻合 | ✅ |
| 19 | `GUIDE_env_inventory_v1.md:35` 先例行 | `LG_RAG_VISIBILITY_SCENARIO_MODE` lg_rag 段在册（**该先例行本身已 deprecated 2026-10-20** → nit N-d） | ✅ |
| 20 | `SESSION_SUMMARY_ENABLED` 解析先例 | `continuity.py:156-169` 默认 false/非法回退 false+warning 实证（方向差异 → nit N-e） | ✅ |
| 21 | host-v1 SPEC §4 Q3 | :155-162「Q3 · 委派网关是否立新一级模块」裁定 S1 · :162 图谱义务=capability/lg_rag 两行备注 | ✅ |
| 22 | N6：catalog 测试 :15 单次 import | :14 `_SUPERVISOR_CAP_FILTER` · :15 `SupervisorPlanError` 单次 · 无重复——task「不可证不依赖」裁定实证成立 | ✅ |
| 23 | 蓝本 `test_memory_injection_consumer.py:608-632` | `_resolve_base` def :608 · 三级探测（:617 钉锚 / :621-631 merge-base 退化 / :632 skip 带实测 ref）逐行吻合 | ✅ |
| 24 | 蓝本同 :635-660（含 banned 置尾 :659-660） | 三路 diff :639-643 · untracked :645 · 第四态 :648-657 · **banned 断言确置尾 :659-660** | ✅ |
| 25 | 蓝本 `test_strategy_scenario.py:451-536` | `_WAVE_TIP = "63bad3d"` :456 · `_touched_in_wave` :487-505 · `_resolve_base` :508-532 · 闸 def :535 | ✅ |
| 26 | N7：SPEC :159 第 4 处 Q3 dangling | `SPEC §4 Q3 不新增一级模块的既有裁定` 无 host-v1 路径 · v0.1 后仍在 · 非阻塞裁定与 R2 一致 | ✅ |
| 27 | R1 轮「env 台账 delegation 系 env 未登记在先」 | **事实错误**：GUIDE :12-14 已登记 `LG_RAG_DELEGATION_TOKEN_MODE/SECRET/TTL_SECONDS`（capability 段）→ M3 修订措辞 | ❌ |

### 5. TC8 四态闸 + banned 前置确认 · **强化方向确认正确 ✅**

- 四态照抄蓝本核验：① `rev-parse --verify {钉锚}^{commit}`（蓝本 :617）→ ② merge-base HEAD origin/{GITHUB_BASE_REF 或 master} 双 ref 试（蓝本 :621-631）→ ③ 钉锚命中 ∧ 越白名单 ∧ 越出面全非本波次（_WAVE_TIP 判定 · 蓝本 :648-657 + scenario :487-505）→ 可审计 skip（含本波次仍 fail）→ ④ 仍不可得 `pytest.skip` 带实测 ref 状态（蓝本 :632）。task TC8 表述与蓝本四态逐一对应，无临场发明 ✅
- **banned 前置确认**：蓝本 banned 断言置尾（:659-660），其前存在两个 skip 出口（态④ :632 · 第四态可审计 skip :654-657）——任一 skip 命中，banned 检查即被跳过，「skip 掩盖禁区触碰」实证可能发生。task 将 banned（`scripts/` `alembic/` 白名单外 `app/`）前置于全部 skip 出口系 **fail-closed 方向强化，确认正确、无反效果**：banned 判定对 changed∪untracked 集合是确定性的，不依赖 skip 分支结果，前置不改变四态语义，只把被掩盖的禁区触碰从 skip 转为 fail（唯一实现注意见 nit N-a）

### 6. 闸表与 graph_change_layer=none 口径 · **成立 ✅**

- 正名（符号）+ 独立开关（env 键）均非图谱元素：不增图谱行（承 Q3 图谱义务=行内备注）· 零新跨模块边（lg_rag→capability 既有边复用）· 不增 implementedBy · env 键非路由/表/SSE 事件类型。承 :116 T1 闸登记先例（同形态「零 diff · 无需备注/行内备注」回写在册）
- HG-GRAPH-MODULES=approved 行附「30 实判越出（新行/新边）→ 回炉补签」回路，与 graph_delta_note 互锁 ✅
- 闸表三行齐：HG-SPEC-SIGNOFF approved（2026-10-19）· HG-AUDIT-R1 pending（blocks 30 · 00 代签授权在 · 落闸在本审查之后）· HG-GRAPH-MODULES approved（口径写明）✅
- 分支 diff 实证：仅 task 文件 + invoke 两处分，**零 app/ tests/ 改码、未改 SPEC、未代签** ✅

### 7. N5/N6/N7 处置 · **合理 ✅**

| 项 | 裁定核验 |
|---|---|
| N5 不补落盘 | R1 N5 原文给两选项（补落盘 / 注明 SPEC §1 为唯一转述真值）；task 取后者并落非范围，承 R1 备选口径，合理 |
| N6 不依赖不处置 | master 实证 `SupervisorPlanError` 单次 import 在 :15（本审查独立复核一致）；worktree 分支状态本仓不可证 → task 不依赖、不处置，合理 |
| N7 不代改移交维护者 | SPEC :159 dangling 实证仍在；R2 已裁定非阻塞「或移交 task 阶段吸收」；task 选择不代改 SPEC（守「不改 SPEC」纪律）+ 40 复核回路，合理 |

### 8. FP* 完备性 · **覆盖齐（M1/M2 闭合后严密）**

FP-1 改名残留 / FP-2 默认开误伤（用户可见=是）/ FP-3 enforce 回归 / FP-4 关态反向漏拦 / FP-5 改名等价 / FP-6 freeze 破坏（审计词表/拒绝码/SSE/HTTP · SSE 零变化有 TC6 grep+diff 牙）/ FP-7 env 非法 / FP-8 基线静默（task 级新增 · 承蓝本绝不静默口径）。SPEC FP-1~FP-7 全承接 + task 级 FP-8 补强；开关矩阵（TC5）/ SSE 零变化（TC6）/ 改名遗漏（TC1，待 M1/M2 闭合）均有牙。

## 二、问题清单

### 中等（建议 10-task 签前修订 · 不改实质）

| ID | 位置 | 内容 |
|---|---|---|
| **M1** | TC1（task :118）vs D1（:60/:86）· TC8 白名单（:125） | **TC1 grep 牙与实测残留面不齐（tests/ 面）**：全仓 grep 实证 `tests/test_capability_testing_write.py:185/:412/:468` 三处注释含 `auto_approve_ok`，落入 TC1 的 tests/ 断言面，但 D1 改名面未列该文件、TC8 白名单亦不含——30 若同步注释则 TC8 越白名单 fail，若不同步则 TC1 零残留 fail，**两牙互斥**。修订二选一：(a) D1 改名面 + TC8 白名单补 `tests/test_capability_testing_write.py`（注释同步 · 推荐，彻底）；(b) TC1 牙收窄为「符号级零残留 + 注释面豁免清单落 invoke」 |
| **M2** | TC1（task :118）豁免清单 | **TC1 grep 牙与实测残留面不齐（docs/_tech_graph/ 面）**：`01_modules.md:116` 闸登记表历史回写行含 `auto_approve_ok`（T1 回写摘要内），落入 TC1 的 docs/_tech_graph/ 断言面；该行属不可变历史记录（改之破坏闸登记史），但豁免清单（reviews/tasks/done/invokes/specs）未含图谱历史行——照字面 TC1 必 fail 或逼 30 改历史行。修订：TC1 豁免清单补「`01_modules.md` 闸登记表既有历史回写行」 |
| **M3** | R1 轮小节（task :165） | 「env 台账 delegation 系 env 未登记在先」**事实错误**：GUIDE :12-14 已登记 `LG_RAG_DELEGATION_TOKEN_MODE/SECRET/TTL_SECONDS`（capability 段）。wiki_delta 结论不受影响（新护栏键属 lg_rag 段仍须补登记），建议措辞改「delegation 三键已登记 capability 段 · lg_rag 段无护栏系键，新键补登记落 lg_rag 段」 |

### 非阻塞 nits

| ID | 位置 | 内容 |
|---|---|---|
| N-a | TC8（task :125） | banned 前置在**态④（基线不可解析 skip）**无 diff base 可算 changed 全集——三路 diff 均依赖 base。前置化落地口径 30 须以「工作区+暂存 vs HEAD + untracked」兜底禁区检测，或在实现注释注明该态例外；方向本身已确认正确（第一节 5），仅实现口径提示 |
| N-b | D1（task :60）· R1 轮（:165） | 测试函数 def 行实测 :339/:353/:359（task 写 :338/:352/:359 · 两处 off-by-one）；调用行 :340/:354/:360 准确。task 已声明「行号 30 按实校正」，记录即可；10 invoke 同笔误（:338/:352/:359）一并知照 |
| N-c | D2（task :75）· TC10 | GUIDE :35 先例行 `LG_RAG_VISIBILITY_SCENARIO_MODE` 本身已 deprecated（2026-10-20 scenario 摘除）；作为 lg_rag 段登记**位置**先例仍成立，30 回写时建议以非废弃行为插入位置参照 |
| N-d | D2（task :72）· R4（:177） | `SESSION_SUMMARY_ENABLED` 先例方向相反（默认关/非法回退关 vs 新键默认开/回退开）——解析模式（strip/lower/非法回退+warning）可承，默认方向系 SPEC FP-7 fail-closed 有意裁定；建议 invoke 注明「承解析先例 · 方向承 SPEC FP-7」防 30 误抄默认关 |
| N-e | TC1（task :118）vs SPEC FP-1 | SPEC FP-1 字面「全仓 grep 零残留」vs TC1 三面+历史豁免窄化——豁免合理（不可变历史记录 · D1 已述理由），建议 M1/M2 同轮修订时 TC1 注明「承 SPEC FP-1 的历史记录豁免窄化」保持可追溯 |

## 三、结构核对表（范围 / 非范围 / 验收 / failure_paths / 思考轮）

| 项 | 裁定 | 摘要 |
|---|---|---|
| 范围 D1/D2/D3/D4 与 SPEC 对齐 | ✅ | D1 正名 / D2 解耦默认开 / D3 图谱写实逐字承 SPEC；D4 测试同步+基线锚点系 SPEC test_strategy_note 的 task 级展开；新名/开关键名均在 SPEC 留口内收口 |
| 非范围与范围互斥 | ✅ | 承 SPEC 六条 + task 级五条（零改码/不动 :970·:1271/不代改 SPEC/N5/N6/历史 docs 不动）；「不改 :970/:1271」与本审查第一节校正互锁 |
| 验收可机断 | ⚠️ M1/M2 | TC1-TC10 全部机器可判；唯 TC1 残留面与豁免/白名单未对齐（M1/M2），闭合后全链严密 |
| failure_paths 充分 | ✅ | 见第一节 8；FP-8 系对蓝本「绝不静默」口径的 task 级显式化，补强方向正确 |
| R0–R5 思考轮闭合 | ✅ | 六轮表 + 各轮小节齐；R1 轮锚点亲读实录与本审查独立复核一致（除 M3/N-b 两处）；R4/R5 early_stop 理由成立（开放点全收口 · TC 全可机断——M1/M2 闭合后属实） |
| 人工闸纪律 | ✅ | 闸表三行齐；本起草阶段零 app/ 改码实证（分支 diff 仅 2 文档文件）；未代签任何闸；本帽亦不代签 HG-AUDIT-R1 |
| freeze 零变更承诺 | ✅ | freeze_id 行承 SPEC 全清单（词表/拒绝码/TTL/HITL TTL/三档默认/SSE/HTTP）+ 升级回路；TC6 有 grep+diff 牙 |

## 四、HG-AUDIT-R1 建议

**conditional_pass**：八大委托重点全部核验通过——门控修正**成立**（:903/:931 两处真门控 · :970 误并澄清防止了错误实施方向）· FP-2 三牙完备可机断 · 正名处置承 SPEC · 锚点 24/27 命中 · banned 前置强化方向**确认正确无反效果** · graph_change_layer=none 口径成立 · N5/N6/N7 处置合理 · FP 完备。阻塞项（fail 级）**0**。

**M1/M2/M3 建议 10-task 做一轮签前修订**（TC1 豁免/白名单对齐 + R1 轮措辞 · 不改实质 · task 修订记录追加 v0.2 行）后，维护者（或 00 依授权代签）可落 HG-AUDIT-R1=approved；若维护者认为 M1/M2 可移交 30 吸收（30 按实校正条款已部分覆盖 N-b 类），亦可直签并在 invoke 注明——但 M1 的两牙互斥（TC1×TC8）建议还是签前闭合，免 30 现场回炉。本帽**不代签**；人签前维持：30 拒开工。

## 五、下一棒

10-task 修订（M1/M2/M3 + nits 顺手）→ 20-task-audit R2 窄幅复核（M 闭合 + 无夹带）→ 00 代签 HG-AUDIT-R1（授权在案）→ 30 红测先行（必读列表 6 项已就位 · :987-988 跟随关系与 banned 前置落地口径 N-a 为 30 现场核对点）。

---

## 修订记录

| 日期 | 摘要 |
|---|---|
| 2026-10-20 | R1：conditional_pass · 锚点实测 24/27 命中（漂移 2 · 事实错误 1）· 门控修正核验成立（:903/:931 真门控 · :970 误并澄清）· banned 前置确认正确 · M1（TC1×TC8 互斥 · tests/ 面）/M2（TC1 豁免缺图谱历史行）/M3（env 台账措辞事实错误）签前修订建议 · N-a~N-e 五 nits · 阻塞 0 · 本帽不代签 |
