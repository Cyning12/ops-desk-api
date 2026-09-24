# 审查文：task_host_v1_episodic_memory_feedback · 20-task-audit R1（2026-09-23）

> **hat_id**：20-task-audit · **轮次**：R1 · **审查对象**：`docs/tasks/active/task_host_v1_episodic_memory_feedback.md`（draft · 265 行）
> **对照真值**：SPEC `docs/spec/host-v1-episodic-memory-feedback/SPEC-host-v1-episodic-memory-feedback_v0.md`（signed · 225 行）· 种子 `08_host_v1_wave_spec_outlines_v0.md` §4 · 事实记忆面 `SPEC-memory-facts-p0_v1.md`（signed）
> **方法**：全部真读真跑——task/SPEC/种子逐行读；代码锚点 5 处亲读；grep 亲跑；pytest collect 亲跑；alembic head 链亲验；B1 组计数与行内用例数逐文件复核

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS-WITH-NITS** · 阻塞项为零 · 3 条非阻塞修正/建议（N1–N3） |
| **流程闸** HG-AUDIT-R1 | **pending（如实）** → 30 拒开工维持；本帽不签发 |

**总结论：PASS-WITH-NITS · 阻塞项为零**。task 与 signed SPEC 实质差异为零；验收 14 条分解式自加总一致（1+1+3+3+2+1+3=14）；diff 白名单与钉死落点一致（V1-B 的 catch-22 型矛盾本轮不存在）；alembic 义务落成可执行断言（upgrade 建表/downgrade 可逆/off 态读写不炸）；零互写（U4）为变异检验式可证伪（双向计数对拍 + import 守护 + 「注入互写→必挂」）。锚点、命名冲突、基线、B1 计数全部经得起亲跑复核。N1–N3 为精度级修正建议，可由 00 签闸前微修或留痕豁免。

---

## 一、逐面核对（证据带行号）

### 面 1 · 范围 / 非范围 / 验收 / failure_paths 与 SPEC 一致性 ✅

| 核对项 | task 证据 | SPEC 证据 | 结论 |
|--------|-----------|-----------|------|
| 范围 D1–D6 | task :97-102（实现序 D1→D2→D3→D4→D5→D6） | SPEC §2 :63-117（D1–D6） | 一致（底座→闸→召回→聚类→建议→收口 · 依赖方向成立） |
| 非范围 | task :108 | SPEC §3 :123-130（八条 ❌） | 八条全收（跨进程/自动回写/实时聚类/用户面端点/subtask 级/embedding/改事实记忆/freeze），task 增「历史文档回改」标准项无越界 |
| failure_paths | task :116-125（10 行：SPEC FP-1~7 + 过程三） | SPEC §5 :163-169（FP-1~FP-7） | 逐条翻四列语义一致（FP-1 三层防线 :119 ↔ SPEC :163；FP-7 双写漂移零互写+来源分立 :125 ↔ SPEC :169）；计数 10 与 R3 :225/:245 自述一致 ✅（前两波的计数 nit 本轮未重现） |
| 验收 ↔ SPEC §6（11 条） | task :133-162（14 条） | SPEC :175-185 | §6-1→:139 · §6-2→:140 · §6-3/4→:145-147 · §6-5→:151-152 · §6-6→:156 · §6-7→:141 · §6-8→:135 · §6-9→:161 · §6-10→:160 全映射；§6-11 PR merge 由 orchestration :32 承载（见 N2） |
| 种子方向偏离 | task 全文 | 种子 08 §4 :153-190（D1–D6 大纲 · U4 铁律）· 07 §3 V1-D（依赖 V1-A） | 零偏离；种子三开放裁定已由 SPEC Q1/Q2/Q3 作答未重开；「D3 跨进程不建」「建议人工确认」种子原话入非范围 |
| U4 零互写 | task :54 · :86 · :98 · :139 · :166 | SPEC :36 · :52 · :87 · :109 | 一致且可证伪（见面 3③） |

### 面 2 · R0–R5 思考轮控制 ✅

- 控制表 :222-227 六轮齐全 · early_stop 全 no · residual 两条（指纹碰撞方向已锁 · 聚类建议质量依赖人工复盘）如实携带至 :229。
- R2 :224 正确「继承 SPEC §4 三组裁定不重演」（Q1 run 级弃 subtask · Q2 指纹规则弃 embedding · Q3 三闸弃动态百分比）。
- R0 :233 如实点出「本波是五波中唯一有 alembic 义务的波」；分支告诫（master → 须切任务分支）在案。
- 计数自洽：R3「10 条」✓ · R4「14 条」✓ · B1「6+1 组」✓ —— 思考轮与正文计数全部一致。

### 面 3 · 验收 14 条可执行性（防空真）✅

- 实点：人工闸 1（:131）+ D1×1（:135）+ D2×3（:139-141）+ D3×3（:145-147）+ D4×2（:151-152）+ D5×1（:156）+ D6×3（:160-162）= **14 条**，与 R4 :226 分解式自加总一致 ✅。
- **① diff 白名单 vs 钉死落点（V1-B 教训专项）**：:162 白名单 = episode_gate.py + episode_service.py + continuity.py + db/models.py + alembic/versions/ + scripts/episode_pattern_mine.py + 测试/图谱/文档；钉死落点 D1（models+alembic :84）· D2（两新文件 :85-86）· D3（continuity :87）· D4（scripts :88）· D5（仅报告字段 · reports/ 在 app/ 外无需入列）——全部在列且无外溢，**一致 ✅**（redlines/manifest 要求零 diff :156，恰是「不在白名单且零变化」的自洽形态）。
- **② alembic 义务可执行形态**：:135「upgrade 建表（列/索引齐全断言）· downgrade 可逆断言 · off 态（表不存在）读写路径不炸断言」三件套齐全且可机验；head 接 20260922_session_summaries 亲验（见锚点表 #5）。
- **③ 零互写变异检验式可证伪**：:139 双向表计数对拍 + import 守护；变异检验 ① :166「临时让 episode_service 写一行 ops_memory_facts → 断言必挂 · 恢复全绿」—— falsifiable ✅；②闸恒放行→必挂（:167）· ③摘分节头→必挂（:168）同款达标。

### 面 4 · B1 旧测影响面处置三态 ✅

- 三态齐全：回归×5 组（:176-180）· 新增×1（:181 三个新测试文件）· 迁移新增×1（:182）。
- **亲跑复核**：`ls tests/ | grep -iE 'memory|episode|run_event|continuity|inject|gate'` → **13 文件**（与 :172 一致）；组划分精确覆盖：g1×6 + g2×3 + g3×1 + g4×2 + g5×1 = 13，无缺漏无重叠。
- 行内括注用例数复核：括注口径=测试函数数（`grep -c 'def test_'`）——gate 15 ✓ · service_db 13 ✓ · vector_p1 9 ✓ · extract_p1 14 ✓ · time_decay 6 ✓ · injection 23 ✓ · backfill 15 ✓ **七文件全中**（pytest collected 为参数化展开数，口径分立无矛盾）。

### 面 5 · 钉死契约与 SPEC §2/§4/§5 锁死一致 ⚠（1 处转译弱化 · N3）

| 钉死项 | task | SPEC | 结论 |
|--------|------|------|------|
| 表 10 列 + 三索引 | :84 | SPEC :67-81 | 逐列一致（类型/约束/截断/默认值/索引全对齐） |
| 独立闸五判据 | :85「归因齐全/outcome 合法/序列≤16/摘要截断/failure 必 class」 | SPEC :85「①归因②outcome 词表③≤16④截断⑤failure 时 failure_class 必填**合法**」 | ⚠ 判据⑤转译丢「合法」（词表内）一半 → N3 |
| service 零 import 事实写面 · revoke_by_run | :86 | SPEC :87 | 一致 |
| 召回 Q3 三闸 + 分节 + 降级 + span | :87 | SPEC :91-94 | 一致（top-N created_at desc · 3/200/800 · [相似经验] · memory_episodes_injected） |
| 聚类 Q2 指纹规则 + 阈值 3 + 报告字段族 | :88 | SPEC :98-100 | 逐字段一致 |
| 建议零自动回写 | :89 | SPEC :104-105 | 一致 |
| 双开关 off 态不炸 | :90 | SPEC :53 · FP-4 :166 | 一致 |
| 图谱 memory/db 行 | :91 | SPEC :21 | 一致 |

### 面 6 · 闸表四行诚实 ✅

| 闸 | task 表 :39-42 | 本帽复核 | 结论 |
|----|----------------|----------|------|
| HG-TASK-DRAFT approved（00 代录 · 双令） | :39 | 与 SPEC :4 状态行双令原话一致 | 诚实 |
| **HG-AUDIT-R1 pending（blocks 30）** | :40 | 本审查文落盘前确为 pending；本帽不代签 | **诚实 · 维持 pending** |
| HG-GRAPH-MODULES approved | :41 | 亲读 `01_modules.md`：签录链末行 = 2026-09-23 V1-A 回写行；memory 行 :36 · db 行 :41 在表（db 行登记至 head 20260922_session_summaries 与本波衔接点一致） | 诚实 |
| HG-PILOT-OPSDESK-GLAYER n/a | :42 | 不涉物理分层试点 | 诚实 |

---

## 二、代码锚点抽验（抽 5 亲读）+ 命名冲突/基线/迁移亲跑

| # | 锚点 | 复核结果 |
|---|------|----------|
| 1 | `memory/gate.py:115-147` | ✅ 亲读：`should_write(candidate) -> Decision` 纯函数 :115-147 逐行吻合 · Decision frozen dataclass :107-112 · 「任一规则不过即拒，调用方不得落库」:116 在案 —— episode 闸「物理不同函数」先例成立 |
| 2 | `continuity.py` 五锚 | ✅ 亲读：`[已知事实]`/`[用户偏好]` 节首标记 :115-117 · `memory_facts_enabled` 默认 false 非法回退+warning :128-136 · `render_memory_facts_block` 单块双节互不串节 :212 · `inject_memory_facts_block` 独立 SystemMessage 零 diff :236 · 召回失败降级不注入 `memory_degraded` :369 —— 五锚全中 |
| 3 | `step_contract.py:23-30` | ✅（V1-A 审查已亲读复核）：MAX_FIELDS=16 :23 · MAX_VALUE_CHARS=200 :26 · MAX_CONTEXT_BLOCK_CHARS=800 :30 · 「单值截断挡不住累加」整块闸注释 :28-30 —— 三闸先例属实 |
| 4 | `db/models.py` OpsMemoryFact | ✅ 亲验：`class OpsMemoryFact` :490 · `__tablename__="ops_memory_facts"` :498 · status/kind CHECK 与召回索引在案 —— episode 模型落点同文件成立 |
| 5 | alembic head | ✅ 亲验：`20260922_session_summaries.py` down_revision=20260922_memory_kind_preference · 全目录无任何文件以其为 down_revision → **head 确认**；task :71/:182「head 接其后」成立 |
| 6 | service.py 先例 | ✅ `write_fact` :88 · `revoke_by_source` :137 在案（task :68 属实） |
| 7 | 命名冲突扫 | ✅ 亲跑 8 词（should_write_episode\|ops_memory_episodes\|MEMORY_EPISODES\|episode_gate\|episode_service\|revoke_by_run\|context_fingerprint\|相似经验）于 app/tests **零命中** —— task :74 属实 |
| 8 | 测试基线 | ✅ 亲跑 → **1420 collected**（与 :75 一致） |
| 9 | 报告先例 | ✅ `reports/memory_embedding_backfill/backfill_20260921T*.yaml` 在案（task :73 属实）；`scripts/` 无 episode/pattern 文件（新增落点零冲突） |
| 10 | 依赖文件 | ✅ memory-facts-p0 SPEC · task_memory_preference_profile · task_session_summary_fallback · task_intent_schema_v1 全部存在 |

---

## 三、阻塞项清单

阻塞项为零。

## 四、非阻塞修正 / 建议清单

| # | 级别 | 内容 | 建议处置 |
|---|------|------|----------|
| N1 | 修正建议 | 映射标注欠准：D1 头部「映射 SPEC §6-8/9」（:133）——SPEC §6-9 实为 pytest/ruff（内容落在 D6 :161），D1 内容只对应 §6-8（off drop 安全+迁移可逆） | 改「映射 SPEC §6-8」 |
| N2 | 建议 | SPEC §6-11「PR+CI 绿+merge」既无勾选也无注记（V1-B R2 已立同款注记先例 :164 · 本 task 未承形态）；orchestration :32 虽有承载但验收节无显式映射 | 建议 D6 末补注记（不计验收计数）：「PR+CI merge 承 orchestration 流程项」 |
| N3 | 修正建议 | 闸判据⑤转译弱化：task :85「failure 必 class」与验收 :140「failure 缺 class 全拒」只覆盖「缺失」；SPEC :85 判据⑤为「failure_class 必填**合法**」（词表 :77 capability_blocked\|so_failure\|budget_exhausted\|upstream_error\|contract_violation\|other）——「非法 failure_class 值 → 拒」在 task 验收层无对应断言 | 建议闸判据⑤与 D2 验收补「非法 failure_class → 拒不落库」半句（对齐 SPEC 词表面） |

以上三条均属于精度级转译问题，SPEC 锁死语义本体未受影响（SPEC 为 30 必读 #3 真值）；构成退回 10-task 的实质问题为零。若 00 选择豁免，须在签闸记录留痕。

---

## 五、纪律自查

- 本帽未改 task/SPEC 实质内容 · 未动 `app/` 代码 · 未签发任何 human_gate。
- HG-AUDIT-R1 在 task 闸表仍 **pending**（task :40），本审查文不附 30 Prompt。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NITS · 阻塞项为零 · N1–N3 三条微修/豁免留痕）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者授权 · 00 代录 · 日期 + 原话留痕）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt（30 由 00 委派子 Agent · 分支 `task/host-v1-episodic-memory-feedback` · 当前在 master 须先切分支）

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 20-task-audit R1：六面全核 + 锚点 5+5 亲读亲跑（gate/continuity 五锚/step_contract/models/alembic head · grep 8 词零命中 · pytest 1420 · B1 13 文件+七文件用例数全中）→ **PASS-WITH-NITS · 阻塞项为零**（N1 映射标注 · N2 §6-11 注记 · N3 failure_class 合法性断言）· HG-AUDIT-R1 维持 pending |
