# task_diff_whitelist_anchor_drift 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_diff_whitelist_anchor_drift.md`（master `0358c3b` · PR #357 squash 合并点 · 全文逐节）
> **审查帽**：20-task-audit（R1 · 书面审 · 除「签认代录 + R2 对拍回填」外不改 task 实质内容 · **不代签** HG-AUDIT-R1 / HG-DIFF-WHITELIST-DIAGNOSIS · 未执行 30）
> **审查日期**：2026-11-06 · **审查时仓态**：master @ `0358c3b`（CI 4/4 绿 · 本地两枚 diff-whitelist 基线红与档内登记一致）
> **开窗授权**：issue #337 维护者 comment `6683541162`（2026-11-06 19:15）：「请执行 20-R1：书面审查 task_diff_whitelist_anchor_drift（审查文落盘出 PR 待审；task lint PASS 后出货）。审查重点：①六要素与闸表四列契约完整；②A1 锚点语义三要素自洽可执行；③刷新基线三子形态利弊对拍——特别关注重钉 `_BASE` 与 `_WAVE_TIP` 回归牙窗口的相容性」· 设计闸裁决预告 = whitelist 过期 → 刷新基线 · 子形态倾向「改固定波次窗语义」· 签认链 = 维护者 2026-11-06 13:40 多选授权 + 19:04 大授权窗口（lead 全程代行审查/合并/下发下一棒）
> **输入真值（全部实读/实跑）**：task 档全文 · issue #337 全线程 · PR #357 review `5799316636`（APPROVED · 六条件验收）· 两枚闸源码全文（`tests/test_lg_rag_write_replay_guard.py`:284-462 / `tests/test_strategy_scenario.py`:420-566）· 蓝本 `tests/test_memory_injection_consumer.py`:585-631 · 固定波次窗实跑模拟（本帽亲跑 · 下文 §3.4）· 上游 invoke 链（stage-w-write-expand / delegation-naming-boundary / scenario-stage-rewire）
> **结论**：**PASS（内容零阻塞 · 带 1 项三子形态对拍实质发现 F1 + 非阻塞观察 N1–N4）**——六要素齐备、闸表四列契约合规、A1 三要素自洽可执行、三子形态对拍**支持 lead 预告的「改固定波次窗语义」**并实证其 naive 落地有一枚波内未登记面暗礁（F1 · 随修复必登记项 · 已回填 task 档 R2）；**HG-AUDIT-R1 / HG-DIFF-WHITELIST-DIAGNOSIS 维持 pending 待 lead 随本 PR 签认（本帽不代签）**

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| ① 六要素完整 | ✅ **PASS**——范围（D-fix-1~3）/ 非范围（八条）/ 验收标准（八条可机断）/ failure_paths（FP-1~FP-9 · 触发→行为→可重试→用户可见四列齐）/ 人工闸表（四闸 · 四列契约）/ 思考轮（R0–R5 槽位 + 控制表 + `actual_last_round`/`early_stop`/`residual_risks` 齐）逐项在册 |
| ① 闸表四列契约 | ✅ **PASS**——`human_gate_id / status / blocks_hats / 说明` 四列齐 · id 单元格无内嵌粗体 · HG-TASK-DRAFT/HG-GRAPH-MODULES 签认已由 lead 在 issue #337 comment `6683541162` + PR #357 review `5799316636` 作出，**本审查随 PR 代录入闸表（引据在册 · 非自签）**；HG-AUDIT-R1 / HG-DIFF-WHITELIST-DIAGNOSIS 维持 pending |
| ② A1 三要素自洽 | ✅ **PASS**——证据先于裁决（A1① ↔ test_strategy_note + D-fix-1 + FP-6 三方互引一致）；二值归因（A1② ↔ R2 二支定义 + FP-5 禁混合口径互洽）；闸语义不破（A1③ ↔ FP-2 禁拆闸 + 验收「闸语义对拍」条闭合）——三要素各有承载面且互相不打架，30 可据以执行 |
| ③ 三子形态对拍 | ✅ **完成（对拍支持「改固定波次窗语义」· 与 lead 预告一致）**——①重钉 `_BASE` 与 `_WAVE_TIP` 回归牙窗口**不相容**（窗倒置 → 回归牙静默失效；诚实重装 → 结构性复发）；②固定波次窗语义自洽且为本闸「使命完成」语义的正解，但 naive 落地撞 **F1 暗礁**（波内 2 件未登记面须随修复登记）；③调 `_allowed` 面被拍否（banned/O2 语义被掏空 + 白名单无界增长）——详见 §3 |
| lint 复跑 | `npx spec-wave@3.5.0 task lint --file docs/tasks/active/task_diff_whitelist_anchor_drift.md` → **LINT: PASS** exit 0（2026-11-06 本帽复跑 ✓） |
| verify 闸态实跑 | `npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_diff_whitelist_anchor_drift.md` → **VERIFY: BLOCKED**（HG-AUDIT-R1 / HG-DIFF-WHITELIST-DIAGNOSIS pending · HG-TASK-DRAFT / HG-GRAPH-MODULES approved）——与「20-R1 出货时 lead 随档正式签」一致，签齐前 30 拒开工 |
| 基线红复核 | 本帽复跑两枚用例（`0358c3b` 干净树）：**2 failed** 与档内登记逐字一致（:450 banned 22 件 / :554 banned 2 件）——题面缺陷现状无漂移 |
| draft 洁净度 | 本 PR 全 docs 面（审查文 + 20 invoke + task 档回填）· `app/` / `alembic/` / `scripts/` / `tests/` 零触碰 |

本审查文按结论机读口径书写：「结论」起首节 · 通过词落节内 · 实质内容充足 · 无否定共现。

---

## 审查要点逐项核对

### 1. 六要素与闸表四列契约 ✅

**六要素**（对照 10-task-requirements 输出形状）：

| 要素 | 在册情况 | 核验 |
|------|----------|------|
| 范围 | D-fix-1（诊断裁决执行·按签认分支）/ D-fix-2（红转绿证据）/ D-fix-3（红线对拍） | ✅ 竖切收敛 · 与受理令「修锚点或刷新基线 whitelist · 纯测试基建」逐字对齐 |
| 非范围 | 八条（裁决自裁/实现/SSE·freeze/删闸/其他测试文件/回退他人合入/spec-wave 上游/web·iOS） | ✅ 把「会被顺手扩大」的面全部锁死 · 与 FP-1~FP-9 一一互锁 |
| 验收标准 | 八条（签认落表/红转绿命令级复验/证据链完整/闸语义对拍/红线对拍零命中/全量零新增红/机检四件/40 复跑） | ✅ 逐条可机断（命令/对拍/计数器断言级）· 含 R4「防恒绿失效」的回归牙对拍条 |
| failure_paths | FP-1~FP-9 四列（触发条件/系统行为/可重试/用户可见） | ✅ 四列齐 · 语义锚既有判例（拒开工/禁拆闸/freeze 零 diff/不改码面/决策点属闸/证据先行/不修史/收敛/闸表契约） |
| 人工闸表 | 四闸 · 四列 | ✅ 结构合规（见下） |
| 思考轮 | R0–R5 全轮 + 控制表 + `actual_last_round: R5` / `early_stop: no` / `residual_risks` 两条 | ✅ 槽位齐 · R0 实扫校正（题面编号↔用例锁定）与 residual_risks 照登 |

**闸表四列契约**：

| 核对点 | 裁定 |
|--------|------|
| 四列结构 | ✅ human_gate_id / status / blocks_hats / 说明 四列齐 · id 单元格无内嵌 `**`（外层整格包裹合规） |
| HG-TASK-DRAFT 签认 | ✅ lead 已签（issue #337 comment `6683541162`「HG-TASK-DRAFT 已签（PR #357 · squash 合并 `0358c3b` · CI 4/4 + 本地 task lint 对拍双证 · 六条件全过）」+ PR #357 review `5799316636` APPROVED）——本 PR 代录入闸表，引据两元组在册，**非无授权自签** |
| HG-GRAPH-MODULES 签认 | ✅ lead 已签（同上 comment「以 `none` 口径随档签认（纯测试基建面；30 实扫出图谱面须回签再动）」）——代录引据同上 · `none` 口径与 `graph_change_layer=none` / graph_delta_note 三方互洽 |
| 余两闸 pending 一致 | ✅ task 状态行 / 人工闸表 / orchestration 行 / verify 实跑（BLOCKED · 两 approved 两 pending）四方一致；HG-AUDIT-R1 说明「本审查文落盘即其前置交付 · 随档人签」与维护者令「20-R1 出货时 lead 随档正式签」逐字对齐 |
| 签认幂等锚（FRAGMENT_00 五元组） | ✅ 本次两闸代录 = 首次记录（闸集×依据 comment id×授权窗口五元组在册无重签）；无同锚重送达 / 无覆盖改写 |

### 2. A1 锚点语义三要素自洽可执行 ✅

| 要素 | task 承载面 | 自洽性核验 |
|------|-------------|------------|
| A1① 证据先于裁决 | A1 语义一 ↔ test_strategy_note「修复前 2 failed 输出全文入 invoke」+ D-fix-1「按 A1 语义先取证」+ FP-6「证据链缺失 → 退回 30」 | ✅ 三方互引无矛盾 · 10 档已示范（10 invoke 取证全文在册）· 30 可逐字执行（跑用例→留输出→逐路径 `git log` 溯源） |
| A1② 二值归因 | A1 语义二 ↔ R2 二支定义（锚真漂移=rev-parse 失败或对象不符 / whitelist 过期=锚可解析∧banned 全溯源合法波次）+ FP-5「禁混合口径和稀泥」 | ✅ 判据可机断（rev-parse 成败 + log 溯源清单）· 互斥完备（锚可解析性二分）· 与 10 档实测证据链（四锚全命中 + banned 溯源 6c9d0e6/51030a4）精确衔接 |
| A1③ 闸语义不破 | A1 语义三 ↔ FP-2「禁删闸/禁整段豁免 banned」+ 验收「闸语义对拍（构造波次窗内未登记面触碰须仍 fail 保牙）」 | ✅ 修复约束与验证方法成对闭合——防「恒绿失效」有明确验收路径（回归牙构造实证） |

三要素之间亦无环：A1① 产出证据 → A1② 据证据二值归因 → A1③ 约束修复形态；FP-5/FP-6 分别兜底「无证据裁决」与「自裁」。**可执行性结论：30 不需回到 10 补轮即可按档执行。**

### 3. 刷新基线三子形态利弊对拍（审查重点③）

> 方法：对每支子形态在 `0358c3b` 干净树上做语义推演 + 本帽亲跑固定窗模拟（命令：`git diff --name-only <base> <tip>` / `git log <base>..<tip> -- <path>` / 白名单集合复演 · 见 §3.4 实测记录）。

#### 3.1 子形态① 重钉 `_BASE`（锚点重置到当前 master 尖端）——**拍否：与 `_WAVE_TIP` 回归牙窗口不相容** ⚠️

| 面 | 推演 |
|----|------|
| 转绿机理 | 干净树 `diff _BASE(新)..HEAD` 为空 → 态① pass · 即刻转绿 |
| **回归牙相容性（维护者特别关注）** | 不相容，二选一皆坏：**(a) 保 `_WAVE_TIP` 不动**（新 `_BASE`= `0358c3b` 为 `c17e63b`/`63bad3d` 后代）→ `_touched_in_wave` 的 `git log _BASE.._WAVE_TIP -- <path>` 窗倒置恒空 → 返回 False → **回归牙静默失效**，而档内/注释仍声明「回归牙保留」= 记录层语义说谎；**(b) 同步重置 `_WAVE_TIP=None`** → 退回「未钉」分支 `git log _BASE..HEAD` → 闸重装为常驻新波次守卫 → 下一波触碰 `scripts/`/`alembic/` 即刻结构性复红——**今天的缺陷原样复发**，且每次复发都要人工重钉，锚点维护成本永续 |
| 白名单语义 | 原波次声明 diff 集（`_APP_ALLOWED`/`_TREE_ALLOWED`）锚的是 2026-10-20 波次文件面；对新窗仍前向生效但历史审计锚丢失 |
| 结论 | 治标不治本 · 与钉死 `_WAVE_TIP` 的裁定记录（5c38988/同名 scenario 先例）直接冲突——**拍否** |

#### 3.2 子形态② 改固定波次窗语义（lead 预告形态）——**对拍通过 · 附 F1 必修暗礁** ✅

| 面 | 推演 / 实测 |
|----|-------------|
| 转绿机理 | committed 面由增长窗 `_BASE..HEAD` 收窄为闭窗 `_BASE.._WAVE_TIP`（波次真实合并跨）；干净树实测 wave2 窗 13 文件全在白名单 → violations 空 → **态① pass**；wave1 窗 banned 面空（波次未触碰 scripts//alembic/ 与其余 app/） |
| 回归牙相容性 | **自洽**：committed 面与 `_touched_in_wave` 的窗（`_BASE.._WAVE_TIP`）从「面长牙短」改为**面牙重合**——牙评的恰是被评面，波次窗内未登记面触碰 → fail 保牙语义原样且更可解释 |
| 在途保护 | 工作区/暂存 vs HEAD + untracked 面保留（banned 前置照跑）——30 开发期与未来波次在途改动触碰禁改面仍即时 fail，O2 语义无损 |
| 复发风险 | 闭窗不随 master 增长 → 结构性常态红消除；下波如需 committed 面审计须自注册新闸（承 wave 闸先例 · 见 N3） |
| **F1 暗礁（本帽实测发现 · 随修复必修）** | wave1 闭窗 15 文件中 **2 件从未登记白名单**：`backups/local_qdrant_orphan_cleanup_20261018T005320Z/…snapshot`（82MB 二进制 · CLOSE 落盘面）与 `docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md`（前波次审查文入库面）——均出自 CLOSE commit `920c8e5` [00]。增长窗时代被「banned 前置先 fail」遮蔽从未显形；固定窗下走 violations→态③→`_touched_in_wave`（窗内被触碰 → True）→ **回归牙 fail**。naive 落地② = 用例①仍红（牙红非 banned 红）。修法：两件按 00 裁定式**逐路径登记入 `_TREE_ALLOWED_FILES` + 限定语**（落签 commit `920c8e5` 为据 · 属 whitelist 测试基建改动 · FP-2 安全——不拆闸、不豁免 banned、不动实现） |
| 结论 | **支持（与 lead 预告一致）** · 落地条件 = F1 两件登记 + 态④浅克隆退化规格（见 N2） |

#### 3.3 子形态③ 调 `_allowed` 面（把漂移文件补进白名单）——**拍否** ❌

| 面 | 推演 |
|----|------|
| 转绿机理 | drift 的 app/ 文件走 foreign→态③ skip 可「绿」；但 `scripts/graph-compile.sh` / `alembic/versions/20261105_capability_notes.py` 属 banned 前置面（O2：先于 skip 必 fail）→ 要绿只能将其**移出 banned 或加豁免** = 把 R1 时期钉死的「禁区不被 skip 掩盖」之牙（O2 本意） retro 拔掉 |
| 复发风险 | 窗仍随 master 增长 → 每波触碰 scripts//alembic/ 都要再豁免一次 → 白名单无界增长 + banned 面空心化 → 闸退化为恒绿装饰（恰是 FP-2/R4「恒绿失效」防的形态） |
| 结论 | **拍否**——它修的是「让断言别叫」而非「让基线正确」 |

#### 3.4 固定波次窗模拟实测记录（本帽亲跑 · `0358c3b` 干净树）

```
== wave1 test_tc8 (fixed window d337486..c17e63b) ==
 committed face: 15 files | banned: []
 violations: ['backups/local_qdrant_orphan_cleanup_20261018T005320Z/…snapshot',
              'docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md']
 internal(回归牙 fail): [同两件]
 => verdict: FAIL(保牙)   ← F1 实证（naive ② 仍红）
== wave2 test_diff_whitelist_scenario_stage_rewire (fixed window a1591e9..63bad3d) ==
 committed face: 13 files | banned: []
 violations: [] | internal: []
 => verdict: 态①pass       ← ②下该枚直接转绿
```

溯源补证：`git log d337486..c17e63b -- <两文件>` → 均 `920c8e5`（「docs(delegation-naming-boundary): CLOSE 归档 + 裁定链 invoke [00]」· 同批落盘 4 文件：snapshot / close invoke / query-coref 审查文 / task 归档更名——其中 close invoke 已被 invoke 前缀覆盖，余两件漏登记）。

### 4. 元信息 / 四字段纪律 ✅

| 字段 | 核验 |
|------|------|
| task_slug / git_branch / implement_repo | ✅ `diff-whitelist-anchor-drift` 三方一致（task 文件 / 30 预登记分支 / invoke 目录同名） |
| test_strategy + note | ✅ `required` · 红测先行命令级可复验 · 与维护者令第 2 条逐字对齐 |
| code_quality_bar | ✅ `L2_backend`（测试码适用） |
| graph_change_layer / graph_delta / graph_delta_note | ✅ `none` 三处互洽 · 与 HG-GRAPH-MODULES `none` 口径随档签认一致 |
| wiki_delta | ✅ `n/a` + note · lint-wiki-delta PASS（213 scanned / 0 issues）复核 |
| review_hat / required_invoke_hats / invoke_retention_profile | ✅ `20` / `10,20,30,40` / `default` |
| 自检结论段 | ✅ 10 自检在册（lint 双 PASS + 取证命令）· 本帽复跑 lint PASS 实证 |
| 修订记录 | ✅ 10 落稿行在册 · 本 PR 增 20-R1 行（签认代录 + R2 对拍回填声明） |

---

## 非阻塞观察项（不阻塞签闸 · 不阻 30 · 供维护者/30 参考）

| # | 项 | 性质 |
|---|----|------|
| N1 | wave1 闭窗 15 文件中 `docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md` 属**前波次**（query-coref）审查文、经 `920c8e5` 入库 | 登记限定语须写明「前波次审查文随 CLOSE commit 入库面」（区别于本波次 review40 的 00 裁定 A 登记），防 30 误写归属 |
| N2 | 态④浅克隆退化：浅克隆（fetch-depth=1）下 `_BASE`/`_WAVE_TIP` 对象缺失 → ②的 committed 面无从求值 | 30 落地规格：committed 面在 `_WAVE_TIP` 不可解析时**带审计输出跳过该面**（绝不退化为 vs HEAD 增长窗——否则浅克隆复现今日结构性红），工作区/暂存/untracked + banned 兜底面照常——此规格已回填 task 档 R2 |
| N3 | ②落地后两闸成为「闭窗档案 + 在途守卫」，不再审计未来波次 committed 面 | 系「使命完成」语义的正解（闸 docstring 自声明）；未来波次如需同类 committed 面审计须自注册新闸（承 2026-10-20 三闸先例）——非本 task 范围 |
| N4 | 题面 stage-w-004/stage-w-002 编号与仓内用例 id 无字面对应 | 10 档已按「实测 2 failed + 既有 invoke 登记链」双向锁定并照登 residual_risk；lead review `5799316636` 亲核未异议——维持 10 档锁定 |

## 阻塞项

**无内容阻塞。** F1 非阻塞——它是子形态②的**落地必修项**（登记动作属 whitelist 测试基建 · 已回填 R2 与验收，30 按档执行即可），不构成退回 10-task。

## 回填清单（本审查随 PR 落 task 档 · 均为记录/对拍回填非实质改写）

| # | 回填项 | 位置 |
|---|--------|------|
| 1 | HG-TASK-DRAFT / HG-GRAPH-MODULES 签认代录（引据 issue #337 comment `6683541162` + PR #357 review `5799316636`） | 人工闸表两行 |
| 2 | 三子形态对拍结论 + F1 暗礁 + N2 浅克隆退化规格 | R2 节「20-R1 对拍回填」块 |
| 3 | 固定窗转绿验收条（态① pass 口径 + F1 两件登记） | 验收标准增条 |
| 4 | 20 注 + 修订记录行 | 档头 / 修订记录 |

---

## 两闸签认建议（本帽不代签）

| 闸 | 建议 | 依据 |
|---|------|------|
| HG-AUDIT-R1 | 建议 lead 随本 PR 签 approved | 本审查 PASS（零内容阻塞 · F1 已回填为必修项）· 审查文落盘即前置交付 · 维护者令「20-R1 出货时 lead 随档正式签」 |
| HG-DIFF-WHITELIST-DIAGNOSIS | 建议 lead 随本 PR 签 approved · **裁决 = whitelist 过期 → 刷新基线 · 子形态 = 改固定波次窗语义**（committed 面收窄 `_BASE.._WAVE_TIP` 闭窗 + 工作区/暂存 vs HEAD + untracked · banned 前置只作用该面 · 四态/O2/回归牙原样）· 落地必修 = F1 两件逐路径登记（限定语引据 `920c8e5`）+ N2 浅克隆退化规格 | 10 档证据链（四锚命中 · banned 溯源合法波次）+ 本审查三子形态对拍（§3：①不相容 / ②自洽+正解 / ③拍否）· lead 预告与本审查对拍结论一致 |

**审毕停等两闸随档人签**（维护者令）：两闸签齐 + 30 授权令下达前，30 拒开工（verify BLOCKED 实证）；签齐后下一棒 = 30 实扫（改动面 ⊆ 两枚测试文件 · F1 登记 + 固定窗语义落码 + 红转绿双证据）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-11-06 | R1：task 档（master `0358c3b`）书面审——①六要素+闸表四列契约 PASS（HG-TASK-DRAFT/HG-GRAPH-MODULES 签认代录入表 · 引据 `6683541162`+`5799316636`）· ②A1 三要素自洽可执行 PASS · ③三子形态对拍完成：**①重钉 `_BASE` 与 `_WAVE_TIP` 回归牙窗口不相容（窗倒置→牙静默失效 / 诚实重装→结构性复发）· ②改固定波次窗语义正解（wave2 窗实测态① pass；wave1 窗实测 F1 暗礁=2 件波内未登记面（`920c8e5` CLOSE 落盘）须随修复登记）· ③调 `_allowed` 面拍否（banned/O2 空心化+无界增长）**——支持 lead 预告形态 · N1–N4 非阻塞 · **PASS 零内容阻塞** · HG-AUDIT-R1 / HG-DIFF-WHITELIST-DIAGNOSIS 维持 pending 不代签，审毕停等随档人签 |
