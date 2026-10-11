# 20-spec-audit R2 书面审：SPEC-hitl-approval-consumption v1

> **hat_id**：20-spec-audit（R2 · 重派 · 前任卡滞已中断）
> **审查对象**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（commit 6eb509f · 259 行 · draft · HG-SPEC-SIGNOFF=pending）
> **对照**：R1 审查文 `spec_hitl-approval-consumption_audit_R1_20261009.md`（v0 PASS-WITH-NITS · 六裁定 + N1–N4）
> **审查日期**：2026-10-10 · **审查人**：Harness 20-spec-audit（子 Agent · 不代签）
> **结论**：**R2 PASS-WITH-NITS**（八条重点逐条裁定：PASS 8 · FAIL 0 · 退回 0 · 非阻塞 nits R2-N1~N3 移交 task 阶段）· 建议维护者签 HG-SPEC-SIGNOFF（本帽不代签）
> **实证复核范围**：SPEC v1 全文 259 行逐行 · R1 审查文全文 · 终局文档 §4 :77-86 实读 · handoff PROMPT 全文实读 · 源码实读：`router.py:112-116,175-275,377-434`（decide/callback/resume 三端点）· `delegation.py:85-107`（_env_int）· `store.py:55-169`（双 store adecide/_DECIDE）· `db/models.py:464-487`（decided_at 列型）· `resume.py:1-80`（无状态重建三硬事）· `nodes.py:277-301,1397-1471` · `strategy/config.py:1-45` · `builder.py:170-189` · `git log b1d74be..6eb509f -- app/ tests/` 为空（R1 后代码零漂移，R1 全部锚点裁定存续有效）

## 结论表（R2 八条 · 逐条裁定）

| # | 审查点 | 裁定 | 摘要 |
|---|---|---|---|
| 1 | D5 三件套闭合性 | **PASS** | 触发器=进程内 asyncio（Q6 S1 · 走 resume.py 同路径）+ PG 行锁认领（:108 FOR UPDATE SKIP LOCKED 或等价）+ 补偿扫描启动/定时兜底（:109）三环齐备；触发器不载状态由设计纪律 6（:68）SPEC 级锁死；resume.py:16-23 实证现行恢复本就事件表重建，纪律原生兼容 |
| 2 | 配置面 fail-closed + decide 载荷零 diff | **PASS**（附 R2-N1/N2） | env 非法回退 manual（:105）· resume_mode 白名单+缺键 inherit（:106）· 实读 `_DecidePayload`（router.py:112-116）增带默认值可选键对既有调用零 diff 成立；未知值 400 与同端点 Pydantic 422 先例形态落差 → R2-N1；OA /callback dict 面承接与否 SPEC 未点名 → R2-N2 |
| 3 | A9/A10 可机断性 | **PASS** | A9（:215）env/单据级两路触发 → 无需手动 resume → done{completed}，pytest 集成断言 + live 留 40 可逐帧断言；A10（:216）四条（无内存载体 grep 审 / 补偿幂等 / 行锁并发仅一执行 / 400+env 回退）全部机断可行 |
| 4 | FP-8~FP-11 充分性 | **PASS** | FP-8 重复触发=行锁+状态机守卫（resume 端点 not_interrupted 409 先例 router.py:428 实证，手动/自动/补偿三源并发同此幂等兜底）；FP-9 崩溃兜底=补偿扫描；FP-10 覆盖键滥用=白名单+台账；FP-11 auto 后仍拦=单次触发上限不循环；TTL 过期单据补偿边界由 D5 :109「approved 且未过 TTL 且 run 未终态」显式过滤闭合 |
| 5 | v0 存续性 | **PASS** | A1–A8 逐条在册（A2 增双 store TTL、A7 注 decide 载荷键边界，均为合理扩展非破坏）；Q1–Q5 表内逐格标注「v0 存续 · R1 裁定 N PASS」；FP-1~FP-7 原文不动；D1–D4 仅 D1 吸收 N3/N4 两处增量；R1 六裁定逐条复核未被破坏 |
| 6 | N3/N4 吸收正确性 | **PASS** | N3：delegation.py:85-94 `_env_int` low/high 界 + :107 `low=1, high=86400` 实读一致，SPEC D1 :78 域 [1,86400] 逐字承接；N4：store.py:98 InMemory `time.time()` float vs :159-163 Db `now()` + db/models.py:485 `Mapped[datetime | None]` 实读一致，SPEC D1 :79 归一 + A2 双 store 断言吸收正确 |
| 7 | 终局 §4 :82-83 逐字对齐 | **PASS** | :82 五要素（三选一触发器/补偿扫描/行锁防重/两级可配置/无状态幂等）→ Q6/Q7/D5 逐项对应无漏；:83 无状态恢复纪律 → 设计纪律 6 逐字承接并锁「破坏=红线退回」；§4 MQ 决议「不需要 MQ」→ 非范围 :124 + Q6 S2/S3 弃选理由在案 |
| 8 | handoff 验收令落实 | **PASS** | handoff :18 令「A1 第四段补全实录：decide(approved)→resume→done{completed} 全真可达」→ SPEC A9 升级为 auto 模式「无需手动 resume」全链可达 + A3 保手动模式成环，双模式都钉终态；handoff 两约束（无状态恢复纪律 :21 / 可配置不单边改死 :22）分别由设计纪律 6 与 Q7 裁定承接 |

## 逐条裁定（正文）

### 1. D5 三件套闭合性 · **PASS**

逐环核实（SPEC :102-111）：

- **触发器（进程内 asyncio）**：Q6 S1 裁定「decide(approved) 持久化成功后派发进程内 asyncio 后台任务，走与手动 resume 同一条恢复路径（resume.py · 从事件表重建）」。实证：resume.py:16-23 现行恢复三硬事（定位靠 thread_id checkpoint / checkpointer 同源不猜 / Command(resume=...) 喂值）全部不依赖进程内存挂起态——自动触发复用此路径无机制冲突。Q6 三选一表（S1 进程内/S2 独立轮询工人/S3 LISTEN-NOTIFY）与终局 §4 :82 三选一枚举逐项一致，S2/S3 弃选理由为机制性（P1 零新增服务纪律 / 连接生命周期+丢通知面），非敷衍。
- **PG 行锁 FOR UPDATE SKIP LOCKED**：:108 钉死「执行前以 PG 行锁认领防重触发；重复触发幂等（resume 状态机守卫：非 pending/unlocked 态重入无副作用 · 断言化）」。仓内先例核查：`grep -rn 'FOR UPDATE' app/` 为空——仓内**无**行锁先例，所引 task_multi_replica_verify（docs/tasks/done/ 在册）为多副本部署形态先例而非行锁实现先例。裁定：SPEC 层写「`SELECT … FOR UPDATE SKIP LOCKED` **或等价**」留有实现余量，属新机制立项，SPEC 级可接受；行锁具体锚点（锁哪行/哪表、认领标记写哪）移交 task 钉死（并入 R2-N3 提示）。
- **补偿扫描**：:109 钉死「启动时 + 定时扫『已批准未恢复』（approved 且未过 TTL 且 run 未终态），行锁认领后补触发；进程重启零丢失」。「已恢复」判据走 run 终态（事件表可查），无需新增状态载体——与无状态恢复纪律自洽。
- **触发器不载状态**：设计纪律 6（:68）逐字锁死「进程内后台任务只是触发器，不是状态载体；进程重启不丢任何待恢复审批（补偿扫描兜底）。破坏此条 = 红线退回」。

三件套互为冗余的设计闭环（触发器快路径 + 行锁防重 + 扫描兜底）完整，无单点缺口。

### 2. 配置面 fail-closed + decide 载荷零 diff · **PASS**（附 R2-N1/N2）

- **`OPS_HITL_AUTO_RESUME` 非法回退 manual**：D5 :105「manual（默认 · 现状语义零 diff）/ auto；非法值回退 manual（fail-closed）」——与仓内 `delegation_mode()`（delegation.py:97-102「非法值回退 off」）同款白名单回退先例，纪律一致。默认 manual = 现状（decide 不自动 resume，router.py:184-186,226-231 两步钉死实证），零 diff 成立。
- **resume_mode 白名单 + 未知值 400**：D5 :106「∈ {inherit, immediate, manual}（缺省=inherit 用全局默认）；键白名单 + 未知值 400」。实读 decide 端点：`_DecidePayload`（router.py:112-116）以 Pydantic `Literal["approved","rejected"]` 收 `decision`，**非法值由 Pydantic 挡成 422**（:113 docstring 明示）；而同文件 callback 端点（dict payload）对非法 decision 显式抛 **400**（router.py:253-257）。SPEC 选 400 与 callback 先例一致、与本端点 Pydantic 422 先例有形态落差——两者皆仓内既有形态，SPEC 不构成错误，但实现路径（显式 HTTPException 400 vs Literal 422 改口）须 task 钉死，立 **R2-N1**。
- **缺键 inherit 对既有调用零 diff**：实读 `_DecidePayload` 两键皆带默认（`note: str = ""`），增 `resume_mode` 带默认值的可选键后，既有调用（只带 decision/note）解析结果与响应行为逐字节不变——零 diff 成立。A7 v1 注（:213）与 §3 非范围第一条（:117）边界字据一致。
- **OA /callback 承接面未点名**：callback 为 `payload: dict[str, Any] = Body(...)` 自由 dict（router.py:236-238），与 decide 同语义复用 `store.adecide`（:259）。SPEC D5 只点名 decide 端点增 `resume_mode`；若自动 resume 触发器只挂 decide 端点，OA 批准的单据在全局 auto 下不会自动 resume——与 D1 消费门「按单据不看来源」不对称。属 task 阶段须裁定的挂点问题（触发器挂 decide 端点 vs 挂 adecide 成功点；callback 是否承接 resume_mode 或显式声明 OA 面不承接），立 **R2-N2**。

### 3. A9/A10 可机断性 · **PASS**

- **A9（:215）**：触发条件两路（`OPS_HITL_AUTO_RESUME=auto` 全局 / 单据级 `resume_mode=immediate`）均可 env/请求体注入；链路断点可逐帧断言——hitl.waiting SSE 帧、pending 列表可见（GET /pending 实证 router.py:151-172）、decide 200、**无手动 resume 调用**（可由测试不调 resume 端点直接断言）、终态 `done{completed}` 事件帧。pytest 集成断言 + live HTTP/SSE 实录留 40 的分工承 testing-write-capability 先例（R1 C3 已裁可接受）。「本波必须达成 · D2 留的正是这段」与 handoff 令对齐（见条 8）。
- **A10（:216）四条逐项可机断**：① 「恢复路径只读事件表+DB · grep/审查断言无进程内存挂起态载体」——静态审查断言可行（resume.py 现行实现即如此，30 阶段保持 + 新增触发器路径同纪律）；② 补偿扫描幂等「重复扫描不重入非 pending 态」——pytest 双跑扫描断言；③ 行锁认领「并发双触发仅一执行」——双 session/双任务并发断言可行；④ 「resume_mode 未知值 400 与非法 env 回退 manual」——HTTP 断言 + env 注入断言。四条无一条依赖人工判断。

### 4. FP-8~FP-11 充分性 · **PASS**

| FP | 路径 | 裁定核实 |
|---|---|---|
| FP-8 | 自动 resume 重复触发（decide 重入/多副本并发） | 双保险成立：① PG 行锁认领（执行前）；② resume 状态机守卫（执行时）——仓内实证：resume 端点对非已决态 409（router.py:397-402）、`not_interrupted` → 409（router.py:428 · resume.py:44），图已恢复后重入即被此守卫无副作用挡下。「并发双触发仅一执行」断言化。**补偿扫描与手动 resume 并发**亦被同一组保险覆盖（三源同走 resume.py 同路径 + 行锁认领），D5 :108 明确「重复触发幂等」，闭合。 |
| FP-9 | 触发进程崩溃/重启致丢失 | 补偿扫描（启动时+定时）兜底认领补触发；触发器不载状态承设计纪律 6。「重启后已批准未恢复单据被补触发」断言化。 |
| FP-10 | resume_mode 覆盖键滥用/未知值 | 白名单 + 未知值 400 + 缺键 inherit + 非法全局 env 回退 manual + 台账（decision_by + resume_mode），与 D5 :105-106 与 A10④ 三点互锁。 |
| FP-11 | 自动 resume 后仍被拦（过期/键不匹配） | 「单次 decide 最多触发一次自动 resume」上限 + 回到挂起态等人 + 台账留痕——防循环关键裁定，与 D5 :111「判定逻辑零改 + 不循环」互锁。 |

**TTL 过期单据补偿边界**（本帽专项核）：补偿扫描过滤条件「approved 且**未过 TTL** 且 run 未终态」（D5 :109）使过期单据不进补偿；即便漏网触发，D1 消费门读时 TTL 判过期不消费（:78）+ FP-2 过期重走挂起→审批——双层闭合，无「过期单据被补偿扫描无限重推」路径。

### 5. v0 存续性 · **PASS**

前提核实：`git log b1d74be..6eb509f -- app/ tests/` 为空——R1 后业务代码零漂移，R1 全部源码锚点裁定（六留转 + C1–C10）对 v1 依然有效。

| v0 资产 | 存续核实 |
|---|---|
| D1–D4 | D1 仅两处增量（TTL 域 [1,86400] 吸收 N3 · 双 store 归一吸收 N4），消费点/消费键/单据守卫/auto_approve_ok 纯函数各条原文不动；D2/D3/D4 原文存续 |
| Q1–Q5 | 五表逐格标注「裁定（v0 存续 · R1 裁定 N PASS）」，弃选案与理由原文保留 |
| FP-1~FP-7 | 七条原文不动 |
| A1–A8 | 逐条在册；A2 增「InMemory + Db 双 store 各一组 · decided_at 类型归一断言」（合理扩展，加严非放松）；A7 增 v1 注「decide 端点载荷增可选键属 D5 范围内 · 既有键语义 diff 为空」（与 §3 边界字据互锁，非开洞） |
| R1 六裁定 | ① payload 增键不越界 → §3 第一条字据存续（:117）；② TTL 读时判过期 → Q5 S1 存续且吸收 N3/N4；③ 消费点 async 化 → Q2 S1 存续，N2（nodes.py:711 + 测试 :492 两处点名）仍显式移交 task（:143）；④ unlock 形态守卫 → Q3 S1/D2 存续；⑤ env 追加集 → Q4 S1/D3 存续；⑥ 读时活状态 → 设计纪律 4（:66）存续 |

无一条 R1 裁定被 v1 增量破坏或暗改。

### 6. N3/N4 吸收正确性 · **PASS**

- **N3（TTL 界值）**：实读 delegation.py:85-94 `_env_int(name, default, *, low, high)` ——`value if low <= value <= high else default`（:94），非法/越界一律回退默认；:107 `_env_int(ENV_TTL_SECONDS, DEFAULT_TTL_SECONDS, low=1, high=86400)` 先例逐字成立。SPEC D1 :78 吸收为「合法域 **[1, 86400]**（承 delegation.py:107 _env_int low/high 先例），非法/越界回退默认」——数值与语义双对拍一致，且 Q5 S1 表（:165）同步更新「域 [1,86400]」。R1-N3「由 task 钉死具体界」被 v1 提前吸收进 SPEC 层，正确且更优。
- **N4（decided_at 双 store 类型）**：实读 store.py:98 InMemory `adecide` 写 `row["decided_at"] = time.time()`（float 时间戳）；:159-163 Db `_DECIDE` 写 `decided_at = now()`，回读经 db/models.py:485 `decided_at: Mapped[datetime | None]` 为 datetime——两类不一实证成立。SPEC D1 :79 吸收为「消费端统一归一为可比时间戳后再做 TTL 比较；归一函数落消费助手内，双 store 各一组 TTL 断言（A2）」；A2（:208）同步增「**InMemory + Db 双 store 各一组** · decided_at 类型归一断言」。吸收位置（D1 设计条 + Q5 S1 裁决列 + A2 验收条）三处一致，无漏面。

### 7. 终局 §4 :82-83 逐字对齐 · **PASS**

实读终局文档 §4（:77-86）逐要素对拍：

| 终局 §4 :82-83 要素 | SPEC v1 落点 | 对拍 |
|---|---|---|
| 触发器「进程内后台任务 / PG 轮询工人 / PG LISTEN-NOTIFY 推送**三选一**」 | Q6 三案表（:171-175）逐项同名 | ✅ 逐字 |
| 补偿扫描「**启动时+定时**扫『已批准未恢复』· 无状态恢复保证幂等」 | D5 :109「启动时 + 定时扫『已批准未恢复』」+ FP-9 | ✅ 逐字 |
| 「多副本用**数据库行锁认领防重**」 | D5 :108「PG 行锁认领（FOR UPDATE SKIP LOCKED 或等价）防重触发」 | ✅ 逐字 |
| 「自动/手动做成**可配置**（全局默认 + 可按审批单选『立即执行/稍后手动』）」 | Q7 裁定（:181）全局 env + 单据级 inherit/immediate/manual（immediate=立即执行 · manual=稍后手动 · inherit=用全局默认） | ✅ 语义逐字（inherit 为缺省桥接键，不减损两级裁定） |
| :83「任何时候不得引入『恢复依赖进程内存』的挂起态…当前 resume 从事件表重建是对的，**SPEC 级锁死**」 | 设计纪律 6（:68）逐字承接 + 「破坏此条 = 红线退回」 | ✅ 逐字 |
| §4 MQ 决议「HITL 核心**不需要 MQ**」 | 非范围 :124「❌ MQ/外部调度器/独立轮询工人引入（终局『不需要 MQ』决议 · Q6 双弃理由在案）」 | ✅ 逐字 |

五要素 + 纪律 + MQ 排除共七处对拍全部命中，无改写、无漏项、无加戏。

### 8. handoff 验收令落实 · **PASS**

实读 handoff PROMPT 全文（54 行）逐令对拍：

- **验收令**（handoff :18）：「验收必须含 **A1 第四段补全实录**：decide(approved) → resume → 终态 `done{completed}` 全真可达（D2 留的 40 缺口正是这段）」→ SPEC v1 双模式落实：**A9**（:215）auto 模式「decide(approved) → **无需手动 resume** → 自动恢复 → 终态 done{completed} 全真可达 · pytest 集成断言 + live 留 40 · 本波必须达成」；**A3**（:209）手动模式「decide(approved) → resume 200 → 图恢复 → done{completed}」+ live 留 40。两模式各自钉到终态帧，覆盖并超过验收令下限。
- **约束一**（handoff :21 · 无状态恢复纪律）→ 设计纪律 6（条 7 已裁逐字）。
- **约束二**（handoff :22 · 自动/手动之争做成可配置，不单边改死）→ Q7 两级裁定 + D5 :110「manual（默认）下行为与现状完全一致——POST resume 端点路径不动」。
- **约束三**（handoff :23 · 既有链零回归 · D2 A1–A8 与测试全绿保持）→ A5 反回归钉死组 + A8 `pytest tests` 全绿条存续。

handoff 链路「10-spec 完稿 → 20-spec-audit → HG-SPEC-SIGNOFF 人签 → 10-task」与本 SPEC 头部下游链（:12）及本审查所处位置一致。

## 阻塞项 / 非阻塞 nits

**阻塞项**：无。八条重点全部 PASS，未发现需退回 10-spec 的实质缺口。

**非阻塞 nits（R2-N1~N3 · 不阻签收 · 移交 task 阶段）**：

| # | 级别 | 内容 | 建议 |
|---|---|---|---|
| R2-N1 | 形态落差提示 | `resume_mode` 未知值 SPEC 钉 400，但 decide 端点既有同字段级先例是 Pydantic `Literal` 挡 **422**（router.py:113,115 `decision` 非法值）；400 先例在 callback dict 面（router.py:253-257）。两形态皆仓内既有，SPEC 不算错，但实现路径二选一须显式 | task 钉死：显式 HTTPException 400（保 SPEC 字面）或 Literal 422（顺 Pydantic 先例）并在 task 验收中同步口径；勿让 30 临场自选 |
| R2-N2 | 覆盖角提示 | D5 只点名 decide 端点承接 `resume_mode`；OA `/callback` 为自由 dict payload（router.py:236-238）与 decide 同语义复用 `adecide`。自动 resume 触发器挂点若只在 decide 端点，OA 批准单据在全局 auto 下不触发——与 D1 消费门「按单据不看来源」不对称 | task 裁定：① 触发器挂点（decide 端点 vs adecide 成功点/编排层统一钩）；② callback 载荷是否承接 resume_mode，或显式立字据「OA 面不承接 · 单据级覆盖仅限浏览器 decide」 |
| R2-N3 | 实现提示 | `FOR UPDATE SKIP LOCKED` 仓内无先例（grep app/ 为空）；补偿扫描「已批准未恢复」的判据组合（approved + 未过 TTL + run 未终态）跨 hitl 表与事件表 | task 给行锁具体锚点（锁 ops_hitl_requests 行 · 认领语义）与并发断言基建（双 session）；扫描判据的 SQL/查询落点在 task 范围钉死 |

（承 R1 惯例：N1–N4 中 N3/N4 已被 v1 吸收进 SPEC 层；N1/N2 仍移交 task，本 R2 三条与其叠加，拆 task 时一并携带。）

## 五、HG-SPEC-SIGNOFF 建议

**建议签收（R2 PASS-WITH-NITS）**。本帽**不代签** human_gate；维护者签录 `HG-SPEC-SIGNOFF=approved` 后，由 00 在 `task/hitl-approval-consumption`（自 master 分出）起草 task → 20-task-audit → HG-AUDIT-R1 人签 → 30。拆 task 时携带 R1 留存 N1/N2 + 本 R2-N1~N3 回填；本帽不附 30 Prompt。

### HG-SPEC-SIGNOFF 维护者签闸清单（待维护者人签 · 00 依「授权00签收所有过程文档」代录口径 · 本帽不代签）

| 项 | 内容 |
|---|---|
| human_gate_id | `HG-SPEC-SIGNOFF` |
| 对象 | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（v1 · commit 6eb509f · draft） |
| 前置 | 20-spec-audit R1（v0 PASS-WITH-NITS · 2026-10-09）+ R2（v1 本文 · PASS-WITH-NITS · 八条全 PASS · R2-N1~N3 移交 task） |
| 维护者签署 | ______________（姓名 / 日期 / approved 或退回意见） |
| 签后下一棒 | 00 起草 task（invoke_slug=`hitl-approval-consumption` · 携带 R1-N1/N2 + R2-N1~N3）→ 20-task-audit → HG-AUDIT-R1 |

## 六、结论：R2 PASS-WITH-NITS

R2 书面审 **PASS-WITH-NITS**：八条重点逐条裁定全 PASS——D5 三件套（进程内 asyncio 触发器 + PG 行锁认领 + 启动/定时补偿扫描）闭环且触发器不载状态由设计纪律 6 锁死；配置面 fail-closed（env 非法回退 manual · resume_mode 白名单 · 缺键 inherit）与 decide 载荷零 diff 经 `_DecidePayload` 实读成立；A9/A10 全条可机断；FP-8~FP-11 含补偿扫描/手动 resume 并发与 TTL 过期边界双层闭合；v0 资产（A1–A8/Q1–Q5/FP-1~FP-7/D1–D4 · R1 六裁定）存续无破坏（R1 后代码零漂移已核）；R1-N3/N4 吸收与 delegation.py:107、store.py:98/:159-163 实读逐字对拍一致；终局 §4 :82-83 七要素逐字对齐；handoff 验收令以 A9+A3 双模式钉 `done{completed}` 终态落实。三条非阻塞 nits（R2-N1 400/422 形态落差 · R2-N2 callback 承接面 · R2-N3 行锁锚点）移交 task 阶段，不影响 HG-SPEC-SIGNOFF 进入维护者人签。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-10-10 | R2 书面审（重派 · 前任卡滞中断后接手）：v1 八条重点全 PASS · R2-N1~N3 移交 task · 建议维护者签 HG-SPEC-SIGNOFF（不代签）· 骨架先行增量落盘纪律执行 |
