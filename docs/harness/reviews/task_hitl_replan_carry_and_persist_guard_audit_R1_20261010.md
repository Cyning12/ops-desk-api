# Task 审查：hitl-replan-carry-and-persist-guard（replan 保号 + _persist_hitl 建单前检查 · R1）

> **审查帽**：20-task-audit R1（书面审 · 不实现 · 不改 task 实质）
> **审查对象**：`docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md`（commit 848a5cb · draft 2026-10-10 · 维护者双裁定承接：① replan 保号 ② persist 建单前检查）
> **对照真值**：T1 40 invoke「重要发现」（:31-40）+ T2 40 invoke（:48 消费失配 · :55-57 孤儿 pending 观察）
> **实证 base**：worktree `t-hitl-carry-and-persist-guard` · 分支 `task/hitl-carry-and-persist-guard`（base=master bdd45f9 · 含 T1/T2 merge ✓）
> **审查人**：Harness 20-task-audit（子 Agent · R1 · 2026-10-10）

---

## 结论

**结论: PASS（内容 · 零阻塞 · 非阻塞注记 N-1~N-3）· 流程闸: HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三 pending（属实时序 · 如实登记 · 不代签）**

verify 机读口径（20 亲跑 · 2026-10-10）：
- `npx spec-wave task lint --file docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md` → **PASS**（EXIT=0）
- `npx --yes spec-wave task lint-wiki-delta --target .` → **PASS**（scanned 153 · issues 0）
- `npx spec-wave verify --target . --task docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md` → **EXIT=2 · VERIFY: BLOCKED**（三闸 pending → 拒 30 · 与 draft 期时序一致，非缺陷）

| 维度 | 结论 | 说明 |
|------|------|------|
| **内容** | **PASS**（零内容阻塞 · 三非阻塞注记 N-1~N-3） | 锚点 6 组抽核逐行吻合；起草者留转六条全部裁定成立；TB1~TB8 全可机断；FP-1~FP-8 每条有断言落点；R0–R5 闭合 |
| **流程闸** | 三闸 pending（属实时序） | 见文末签闸清单；30 开工以 task 表 approved 为唯一真值 |

---

## 核对项

| # | 核对项 | 结论 | 实证 |
|---|--------|------|------|
| 1 | 范围承接：维护者双裁定（背景节 :50-53 逐字引用）→ 范围表 nodes.py 单文件两段增量 | ✅ | 裁定①保号 → 范围①replan 三路径保号；裁定②建单前检查 → 范围②`_persist_hitl` acreate 前检查；一字不多 |
| 2 | 源证据对照（T1 40「重要发现」· T2 40 孤儿 pending） | ✅ | T1 invoke :31-40 实读：sid :1→:11 递增实证 · carry 仅 fallback 触发（nodes.py:1017-1054）· FP-3 循环——task 背景节复述逐点吻合；T2 invoke :48（sid :1→:2 · 零消费台账）· :55-57（孤儿 pending `hitl_5cefb116` · nodes.py:1725-1727 机制）实读一致 |
| 3 | 非范围完备性 | ✅ | 六条（replan 质量 / auto_resume 机制面 / TTL 语义本身 / deny 判序·Policy·gateway / 旧单据 Backfill / resume.py·store.py·freeze 面）逐条与范围无交集；钉死契约七（T1/T2 存续）与八（interrupt 语义不动）把「不动面」钉到函数级 |
| 4 | 验收可机断性（TB1~TB8） | ✅ | 全部机断：原 id 原行带回断言 / 三路径各一断言 / 变异反例断言 / 五键逐字节对拍 / 台账键断言 / store 行数断言 / 34+39 全绿存续 / live 帧形态基线一致——无人工目测项；人工闸前置为验收首条 |
| 5 | failure_paths FP-1~FP-8 | ✅ | 每条有现象/后果/规避+断言落点：FP-1→TB3 变异断言；FP-3→TB6④；FP-4→TB6⑤；FP-5→TB2③+TB4 总闸；FP-7→TB7+B1 清点流程；FP-8→TB3 防御断言（详见六条裁定节） |
| 6 | 思考轮 R0–R5 闭合 | ✅ | 控制表回填齐；R2 三裁定各有实证排除岔路（carry 语义复用 / fail-open / 缺键不匹配）；R3 交叉验证逐项镜像消费门；early_stop at R5 理由成立；residual_risks（保号拼装精确形态 30 定）已由契约二钉语义边界，留 30 自由度合理 |
| 7 | 行为变更类「旧测 grep 影响面」（K7 checklist） | ✅ | B1 表四行在册（T1 34 枚 / T2 39 枚 / observe·resume·decide 面 / 契约·接线面），每行有预期形态 + 处置流程；T1=34 / T2=39 枚 20 亲跑 collect 实证（借主仓 .venv 对 worktree 同文件 · 两文件 diff master 为空 · 34 tests / 39 tests collected） |
| 8 | 人工闸表 / invoke 目录 / lint 闸 | ✅ | 三闸 pending 如实；`required_invoke_hats=10,20,30,40` 含 20 → 本审 invoke 落盘义务履行；10 invoke 已在案（`invoke_20261010_10_task_hitl-replan-carry-and-persist-guard.md` · commit 848a5cb 同批）；验收末行含 task lint + lint-wiki-delta |
| 9 | 图谱/元信息纪律 | ✅ | `graph_change_layer=G-L1`（行备注 · 不新增一级模块）· `review_hat=20` · freeze_id=无（零新表/列/键/事件 · 与契约六「payload 不增新键」一致）· HG-PILOT-OPSDESK-GLAYER=n/a 口径正确 |

## 锚点实读抽核

（20 亲读 worktree 分支 `task/hitl-carry-and-persist-guard` · base=master `bdd45f9` 与 task 声明一致 · 抽核 6 组逐行比对）

| 锚点 | task 声称 | 20 实读结论 |
|------|-----------|-------------|
| `nodes.py:630-673` `_stamp_host_plan` | locked 前缀原行原 id 保留（:638 · :650 `full = locked_rows + plan`）；仅 LLM 项经 `_issue_plan` 盖章新 id（:642-649 · seq 递增 = sid :1→:11 机械来源）；`plan_prefix_ids`=locked ids · `recoverable_point`=len(locked)（:657-658） | ✅ 逐行一致（:638 `locked_rows` · :642-649 `_issue_plan` · :650 拼接 · :657-658 两键——全部字面吻合） |
| `nodes.py:960-1054` replan 三路径 | 空 allowlist 短路 :963-977（`items=[] if locked` · 仍走 stamp）；LLM 正常 :990-1009 → :1054 盖章；LLM 失败 fallback :1017-1051（仅此处 `_unresolved_suffix`+`_carry_plan` 保号） | ✅ 逐行一致（:975 `items = [] if locked else [...]` · :976 stamp · :1010-1011 LLM 异常 · :1030 `_unresolved_suffix` · :1049 `_carry_plan` · :1054 统一 stamp 收口）——**保号须覆盖三路径的判断实证成立**：正常路径与空 allowlist 路径当前均无保号面 |
| `nodes.py:1523-1611` `_persist_hitl` | 去重读失败退回 state 不崩（:1554-1555 fail-open 先例）；D2 空形态 unlock=sid（:1572-1578）；payload 增记 capability_id（:1579-1585 · 真源 `term.get("tool")` :1583）；建单 `acreate` :1601；挂点=:1558 循环内 acreate 之前 | ✅ 逐行一致（:1550-1555 去重 try/except「退回只认 state」· :1572-1578 D2 回填 · :1583-1585 capability 落键 · :1601 `acreate` · docstring :1526-1529「未落库必须显式带出来」既有红线字面在案——fail-open 裁定的两条先例引用均实证） |
| `nodes.py:318-372` `_approval_consumed`（消费门 · guard 镜像源） | `alist(status="approved", limit=200)` + blocked_by 守卫（:347）+ 三元组精确匹配（:349-357 · 缺 capability_id 键 fail-closed）+ 读时 TTL（:358-363） | ✅ 逐行一致（:335 alist · :347 blocked_by 守卫 · :349-357 三元组+缺键 continue · :358-363 `_decided_at_ts`+TTL 判过期 · :336-343 读失败 fail-closed+warning）——guard 镜像源语义逐项在案 |
| `nodes.py:268-301` TTL/归一 | `_approval_consumption_ttl_seconds()`：env `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS` 默认 3600 · 域 [1,86400] 非法回退；`_decided_at_ts`：float\|ISO str 双型归一 · 不可归一返 None | ✅ 逐行一致（:268-278 · :281-301 · bool 排除 :289-290 · naive dt 补 UTC :298-299）；`auto_resume.py:92-96`/:99-103 实读：TTL 与归一**两函数均惰性 import 复用 nodes.py 同一实现**——「禁第二份实现」先例比 task 引用更强（不止 TTL，归一也已复用） |
| `nodes.py:1644-1744` decide/observe 面 | approved ∪ 既有 → `hitl_unlocked_ids`（:1671-1676）；剪掉 approved 步旧结果（:1687-1689 `keep = plan_ids - approved`）⇒ approved 步必为未解决；observe 落库先于挂起（:1725-1727）→ `interrupt()` :1736 · resume 重放返回恢复值（:1739-1740） | ✅ 逐行一致（:1671-1676 union · :1687-1689 剪旧结果 · :1727 `_persist_hitl` 先于 :1736 `interrupt()` · :1739-1740 重放语义注释——P 集合「天然未解决」的操作定义依据与孤儿 pending 机械来源双双实证） |

附带核验：`state.py:239,279` `hitl_unlocked_ids: list[str]` 键在册 ✓；`store.py:55/161` 双 store 在册（`alist` InMemory :76 / Db :255 · guard 只读复用面真实）✓；`nodes.py:395-421` 消费门调用点 :419 实读（本 task 零改面）✓。

## 起草者留转六条 · 逐条裁定

### 1 · 保号集合 P=`hitl_unlocked_ids`∩未解决 的操作定义严格性（FP-1 授权面静默扩大）· 三路径全覆盖与空 allowlist 短路交互（FP-5）

**裁定：成立（零阻塞 · 附 N-1 措辞注记）。**

- **严格性实证闭环**：P 的两个维度各有代码级锚定——`hitl_unlocked_ids` 由 `_apply_hitl_decision` :1671-1676 以「既有 ∪ approved」维护（只进不出 · 授权面真源唯一）；「未解决」由 :1687-1689 `keep = plan_ids - approved` 保证（approved 步旧结果必被剪掉 ⇒ 必为未解决态）。契约一的字面实现「∩ 未解决」不是隐含假设而是显式过滤，FP-8 防御断言（approved 步有终态时 P 为空）把未来漂移也锁进断言。**FP-1 授权面静默扩大的反例由 TB3 变异断言锁死**（非 unlocked 未解决步骤 replan 后必须换新 id）——正反双向可机断。
- **三路径全覆盖实证必要**：20 实读确认正常 LLM 路径（:1054 统一 stamp 收口）与空 allowlist 短路（:975 `items=[] if locked` → :976 stamp）当前**均无保号面**，仅 fallback（:1030-1049）经 `_carry_plan` 保号——契约二「三路径均保号」不是冗余强调而是实证缺口清单。
- **空 allowlist 短路交互（FP-5）**：实读 :688 + :975 发现 task 未明说的一层——空 allowlist 且存在 unlocked 时，unlocked 步既被摘出 locked 又不进 items，**不保号就会从计划中整个消失**（比「膨胀」更险的方向是「丢失」）。task 规避面（TB2 第三路径断言「unlocked sid 均保号」+ TB4 空 unlocked 零 diff 总闸）实际覆盖「丢失/膨胀/漂移」三端，裁定覆盖成立。FP-5 现象描述「多出未授权行」措辞不精确（P 元素按定义均 approved·已授权；真风险是 approved 步丢失与空 unlocked 行为漂移两端）——落 N-1 建议 10-task 顺手精确化，不改裁定、不阻塞。

### 2 · fail-open 裁定采纳记录准确性 · 台账键与「记动作不记内容」纪律

**裁定：成立（零阻塞 · 附 N-2 键名张力注记）。**

- **采纳记录准确性**：契约五完整载明裁定链——维护者建议原话「fail-safe 建单 + warning」标注为本 task 采纳；理由链（漏建单=人干等不存在的审批 · 引用 `_persist_hitl` docstring :1526-1529 既有红线 · 实读字面吻合）+ 同向先例（:1554-1555 去重读失败「退回只认 state 不崩」· 实读吻合）+ 两害相权论证（fail-closed 抑制合法 pending 死等 vs 孤儿 pending 仅 UX/判定输入污染）——三段均实证在案，采纳记录无拔高无缩水。
- **台账纪律**：「记动作不记内容 · 承 delegation 台账纪律」与 `_audit_approval_consumed` :304-315 先例同构（只记 id/维度/TTL 余量 · 不记参数原值）✓。
- **键名张力（N-2）**：契约五写「新台账键**建议** `hitl_persist_guard_read_failed`」，而 TB6⑤ 按该字面值做台账断言——若 30 改名则验收自相矛盾。建议 10-task 顺手把键名从「建议」升为「钉死」（或 TB6⑤ 注明以契约五键名为准），一行改动 · 非阻塞。

### 3 · guard 复用同一 TTL/归一函数 vs 抽共享助手——「禁第二份实现」钉死强度（FP-6）

**裁定：成立（钉死强度足够 · 双向封口）。**

- 契约四「复用 `_approval_consumption_ttl_seconds`/`_decided_at_ts` 同一实现 · **禁第二份 TTL/env 解析实现**」+ R3 逐项镜像清单（blocked_by 守卫 / 三元组 / 缺键不匹配 / 归一 / TTL 同一函数调用）+ FP-6 语义漂移推演（guard 建单而消费门命中或反向 → 孤儿 pending 复发/重复拦截）——漂移路径与锁死手段一一对应。
- **「抽共享助手」岔路已被范围表正面排除**：「仅本文件 · 不新增模块/助手函数出文件外」——复用走同文件函数直接调用，不抽共享助手，无第三态。
- **先例比引用更强**：task 引 `auto_resume.py:92-96` TTL 复用先例；20 实读发现 :99-103 归一函数（`_decided_at_ts`）同样惰性 import 复用——两个待复用函数均已有复用先例在案，钉死强度实证充分。

### 4 · B1 冲突面清点齐全性（「resume 重放重建 pending」「replan id 递增」假设断言 · T1 34 枚+T2 39 枚）

**裁定：成立（枚数亲跑实证 · 冲突面分组齐全 · 附 N-3 定位参考）。**

- **枚数实证**：20 亲跑 collect（借主仓 `.venv` 对 worktree 同路径文件 · 两测试文件 diff master 为空 · 环境等价）：`test_hitl_approval_consumption.py` → **34 tests collected** ✓；`test_hitl_auto_resume.py` → **39 tests collected** ✓，与 task B1/验收口径及 T1/T2 30·40 invoke 历史记录（29→34 枚增强 · 39 枚全绿）三方一致。
- **冲突面分组齐全性**：B1 四行覆盖 T1 全量（预期零 diff · 消费门签发侧零改）/ T2 全量（预期零 diff · 构造态断言）/ observe·resume·decide 面（「重放重建 pending」假设断言 · 关注面）/ 契约·接线面（「replan id 递增」假设断言 · 关注面）——两类假设断言各有归属行与处置流程（基线对拍 → 逐枚清点 → 修订须保留反向断言 + 理由落 invoke）。
- **抽核定位（供 30 参考 · N-3）**：B1 未逐枚点名具体函数。20 抽核定位：「重放重建/幂等」假设代表枚 = `tests/test_react_observe.py:474` `test_persist_hitl_is_idempotent_across_resume`（跨 resume 去重 · 无 approved 在场 → 预期零 diff）；「replan id 序列」假设代表枚 = 同文件 :208/:238/:285/:310（构造态无 unlocked → 由 TB4 总闸覆盖）。均落在 B1 已声明的分组内 → 清点无遗漏，逐枚点名靠 FP-7 流程兜底可接受，非阻塞。

### 5 · TB4 空 unlocked 逐字节对拍实现形态留 30 裁定是否过宽

**裁定：不过宽（断言目标已完全钉死 · 形态自由度不损可机断性）。**

- TB4 已钉死**对拍对象五键**（`subtasks`/`host_subtask_seq`/`plan_prefix_ids`/`recoverable_point`/`subtask_results` 修剪面——恰为 `_stamp_host_plan` :651-672 输出全集）与**判定口径**（与 master 对拍逐字节一致）。留给 30 的只是实现形态（golden 字面快照 / 双跑基线 / 序列化对拍工具选型）——属测试工程细节，不影响「断言什么、怎么判」。
- 周边闭环：TB3 钉非空 unlocked 的变异面，TB1/TB2 钉保号正面形态，TB4 钉空 unlocked 的零漂移面——三段合围后 TB4 无逃逸空间。FP-7 已要求 30 开工第一步基线对拍并把对拍/修订裁定落 invoke，对拍机制留痕义务已在案。无需回填。

### 6 · TB5 消费命中成环 done{completed} 机制段可达性论证

**裁定：成立（机制链逐环实证 · 有 T1 TA3③ 先例托底）。**

- 机制链逐环核：approved 单据在场（构造态可注入双 store）→ resume（`_apply_hitl_decision` :1671-1676 写 unlocked + :1687-1689 剪旧结果）→ replan 保号（本 task 新增段）→ 签发侧 `_delegation_issue_block_reason` :419 调 `_approval_consumed`（实读 · 三元组 sid 维度因保号可命中）→ 命中返 None 不拦（:420）→ 步骤执行 → 无 hitl_pending → `done{completed}`。每一环都有现存代码路径或本 task 钉死的新增段，无断环。
- **先例托底**：T1 TA3③ 已在 pytest 机制段证明「sid 保留形态消费成环」（T1 40 invoke :38「机制段（TA3③ pytest · sid 保留形态）消费成环已证」）——TB5 是在该先例上叠加保号段的真实 replan 路径，可达性论证充分。
- 边界清晰：TB5 断言到「不再二次拦截 + `delegation_approval_consumed` 台账 + done{completed} 机制段可达」；live 帧形态终验归 TB8（40）——30/40 分工与 test_strategy_note 一致。

## 通用清单核对

| 项 | 结论 | 实证 |
|----|------|------|
| 范围 / 非范围 | ✅ | 范围=nodes.py 单文件两段增量 + 三测试文件 + G-L1 行备注；非范围六条逐条与范围无交集（见核对项 1/3） |
| 验收可机断 | ✅ | TB1~TB8 全机断 · 人工闸前置首条 · 30/40 分工明确（核对项 4） |
| failure_paths FP-1~FP-8 | ✅ | 八条各有现象/后果/规避+断言落点（核对项 5 · 六条裁定节 1/2/3/4） |
| R0–R5 思考轮 | ✅ | 控制表回填齐 · early_stop at R5 理由成立 · residual 留 30 自由度有契约二兜底（核对项 6） |
| 反回归钉死 | ✅ | 契约七（消费门/auto_resume/store.py/deny 判序/Policy/gateway/resume.py 零改 · 函数级点名）+ 契约八（interrupt 语义不动 :1736-1740 实读吻合 · guard 跳过建单不改 `obs["hitl_pending"]` 与 interrupt 调用结构 · 不伪造行）+ TB7 34+39 全绿存续总门槛 |
| K7 行为变更类「旧测 grep 影响面」 | ✅ | B1 表在册（核对项 7） |
| lint / verify 复跑 | ✅ | task lint PASS · lint-wiki-delta PASS · verify EXIT=2（三闸 pending 属实时序 · 见「结论」节机读口径） |

## 阻塞项 / 非阻塞项

### 内容阻塞项：无（PASS）

### 非阻塞注记

- **N-1（FP-5 现象措辞不精确）**：FP-5「若保号段误向空计划注入 P → 多出**未授权**行」——P=`hitl_unlocked_ids`∩未解决，元素按定义均 approved·已授权；空 allowlist+unlocked 组合的真风险是 **approved 步从计划中丢失**（:688 摘出 locked + :975 items=[] 双实证），以及空 unlocked 时行为漂移。规避面（TB2③ + TB4 总闸）实际已覆盖三端，建议 10-task 顺手把 FP-5 现象描述精确化一行（不改裁定 · 不阻塞签收）。
- **N-2（台账键名「建议」与断言字面值的张力）**：契约五标 `hitl_persist_guard_read_failed` 为「建议」，TB6⑤ 按该字面值断言——建议键名升为钉死（或 TB6⑤ 注明以契约五为准），防 30 改名致验收自相矛盾。一行改动 · 非阻塞。
- **N-3（B1 未逐枚点名假设断言函数）**：20 抽核已定位代表枚（`test_react_observe.py:474` 幂等枚 · :208/:238/:285/:310 id 序列枚）供 30 开工第一步基线对拍参考；逐枚清点由 FP-7 流程兜底，可接受 · 非阻塞。

## 回填清单

无（内容 PASS · 零阻塞）。N-1~N-3 为非阻塞注记：建议 10-task 顺手补 N-1/N-2 各一行（可在维护者签 HG-TASK-DRAFT 同批进行 · 不单独阻塞签收）；N-3 供 30 参考。

> 注意：内容 PASS ≠ 可开工——30 前置为 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 approved（task 表为唯一真值 · 本审不代签）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | R1 骨架先行落盘 → 逐节增量回填完成：**结论 PASS（内容零阻塞 · N-1~N-3 非阻塞注记）· 流程闸三 pending 属实时序** · 锚点 6 组抽核逐行吻合（_stamp_host_plan/replan 三路径/_persist_hitl/消费门/TTL·归一/decide·observe 面）· 起草者留转六条全部裁定成立 · lint PASS · lint-wiki-delta PASS · verify EXIT=2 三闸 pending 机读口径在案 · T1=34/T2=39 枚亲跑 collect 实证 |
