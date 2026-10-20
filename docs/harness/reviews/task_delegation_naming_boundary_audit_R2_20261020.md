# 审查文：delegation-naming-boundary task R2（窄幅复核 · 20-task-audit）

- **审查对象**：`docs/tasks/active/task_delegation_naming_boundary.md`（**v0.2 · 194 行** · 分支 `docs/task-delegation-naming-boundary` · commit `a892547`）
- **审查性质**：R2 窄幅复核——仅核 R1 M1–M3 闭合 + nits 吸收 + 修订面无夹带；R1 已实质通过面（门控修正核验 / FP-2 三牙 / 正名处置 / N5/N6/N7 / graph_change_layer / FP 完备性）不复核，沿用 R1 结论
- **上游**：本帽 R1 = conditional_pass（`docs/harness/reviews/task_delegation_naming_boundary_audit_R1_20261020.md` · commit `39101d9`）
- **master 基准**：`31924af`（R2 时点 origin/master 复验未变）
- **复核日期**：2026-10-20 · hat 20-task-audit（只审不改 · 不代签 HG-AUDIT-R1）

## 结论：pass（阻塞 0 · R1 M1–M3 全闭合 · 无新阻塞）

R1 conditional_pass 所列三项签前修订全部正确闭合，nits 吸收符合 R1 建议口径，修订面零夹带。task 可进入 00 依授权代签 HG-AUDIT-R1 → 30。

---

## 一、M 项闭合核验（v0.2 逐行坐标实证）

### M1：TC1×TC8 互斥消解 —— ✔ 闭合

- **D1 改名面补登**（task v0.2 :61）：`tests/test_capability_testing_write.py:185/:412/:468` 三处注释级改名同步 · 逻辑零改，并显式注明「落入 TC1 tests/ 断言面 · TC8 白名单已补登」。
- **TC8 白名单补登**（task v0.2 :126）：白名单新增 `tests/test_capability_testing_write.py`（限定「仅注释级改名 · R1 M1 补登」）。
- **互斥消解逻辑**：30 改注释 → 不越 TC8 白名单（✔ 已补登）→ 改后 `grep auto_approve_ok tests/` 零命中满足 TC1（✔ 已入 D1 改名面）。两牙不再互斥。
- **三处注释坐标复核**（master `31924af` 实测）：`tests/test_capability_testing_write.py:185` `# 触发 auto_approve_ok 条件②不放行`（引文逐字吻合）· `:412` `# ① 挂起：真判定链（auto_approve_ok 条件②不放行 → 委派签发需人工审批）` · `:468` `# ② 无消费形态…auto_approve_ok 仍判非只读 →`——**三坐标全部命中，零漂移**。
- **白名单限定语评价**：「仅注释级改名」约束精确——该文件内含 supervisor write 金样断言逻辑，限定注释级防 30 顺手改实质，口径正确。

### M2：TC1 豁免清单补② —— ✔ 闭合

- task v0.2 :119：豁免清单两类成形——① 历史 docs reviews/tasks/done/invokes/specs（不可变历史记录）；② `01_modules.md` **闸登记表既有历史回写行**（:116 等 · 同不可变历史记录 · 20-task-audit R1 M2 补登）。
- ② 与 ① 同法理（不可变历史记录），措辞自洽；`01_modules.md:116` 闸登记历史行含旧名但不再被 TC1 误判。图谱回写仅新增新行（闸登记表）与 lg_rag 行 T1 段字样同步（:35），历史行不动——处置闭环。

### M3：env 台账措辞事实校正 —— ✔ 闭合

- **D2 落点**（task v0.2 :76）：「delegation 三键（`LG_RAG_DELEGATION_TOKEN_MODE`/`SECRET`/`TTL_SECONDS`）已登记 :12-14 capability 段（20-task-audit R1 M3 事实校正）；新键 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 补登记 lg_rag 段」——与 R1 建议口径逐字对齐。
- **R1 轮小节落点**（task v0.2 :166）：「env 台账：delegation 三键已登记 GUIDE :12-14 capability 段（v0.2 M3 校正 v0.1『未登记在先』误述）· 新键补登记 lg_rag 段」——思考轮记录同步修正，v0.1 误述不再以事实形式残留（以「校正记录」形式留存，符合不可变历史原则）。

## 二、nits 吸收核验

| nit | 落点 | 核验 |
|---|---|---|
| N-a（态④ banned 兜底） | TC8 :126 实现注 | ✔「态④锚不可解析时 banned 检测以『vs HEAD + untracked』兜底，不可因基线缺失整体豁免禁区」——比 R1 建议更严（加禁整体豁免），fail-closed 方向正确 |
| N-d（先例方向防误抄） | D2 :73 | ✔「仅承解析模式：该先例默认关、本键默认开，方向相反，防误抄（R1 N-d）」 |
| N-e（窄化口径注明） | TC1 :119 | ✔「SPEC FP-1 表述『全仓』vs 本 TC 三面窄化——三面断言 + 两类豁免后等价全仓口径，非缩水」——「等价非缩水」论证成立：豁免两类均属不可变历史，断言面覆盖全部可变面 |
| N-b（def 行 off-by-one） | 维持 30 按实校正 | ✔ 未改（R1 已注明 30 核对点覆盖，维持正确） |
| N-c（GUIDE :35 先例行 deprecated） | 仅知会 | ✔ 未改（R1 定性「位置先例仍成立 · 仅知会」，维持正确） |

## 三、修订面无夹带核验（v0.2-only diff：`39101d9..a892547`）

- **改动文件仅 2 个**：task 文档（+15/-7）+ 10-task invoke 补第六节修订记录（+19）。零 `app/` 改码 · 未改 SPEC · 未代签任何闸。
- **task 文档逐处归因**：状态行升 v0.2（引 R1 审查文 ✔）· D1 +1 行（M1 ✔）· D2 两行（N-d + M3 ✔）· TC1 一行（M2 + N-e ✔）· TC8 一行（M1 + N-a ✔）· R1 轮小节一行（M3 ✔）· R5 自检 +1 行（v0.2 闭合记录 ✔）· 修订记录 +1 行（v0.2 ✔）——**全部改动可溯源至 R1 M 项/nits，零夹带**。
- **未触碰面实证**：范围/非范围、人工闸表三行、TC2–TC7/TC9/TC10 语义、failure_paths、思考轮 R0/R2–R4 实质——diff 零命中。
- **10-task invoke 第六节**：逐项列 M/nits 闭合落点坐标，与本审查实测坐标逐一对照全部吻合（:61/:73/:76/:119/:126/:166）。

## 四、30 开工提示（非阻塞 · 信息项）

- **30 按实校正项**（承 R1）：`tests/test_capability_delegation.py` def 行实测 `:339/:353/:359`（task 写 :338/:352/:359 · off-by-one×2）；R1 轮小节 :166 的「改名面 8 处」计数随 M1 已更新，30 无需再校。
- **TC1 grep 执行注**：`grep -rn` 可能命中 `__pycache__` 内 .pyc 二进制（本仓实测 `app/ops/capability/__pycache__/` 等在册残留）——30 执行 TC1 断言时建议加 `-I`（跳二进制）或 `--exclude-dir=__pycache__`，否则金样断言可能因构建产物误报。此为本轮新观察（R1 未列），属执行层口径提示，不要求 task 再修。
- **banned 前置实现**：30 照抄蓝本 `tests/test_memory_injection_consumer.py:608-660` 时须按 TC8 :126 将 banned 断言前置于全部 skip 出口 + 态④以「vs HEAD+untracked」兜底。

## 五、闸态与本帽纪律

- HG-SPEC-SIGNOFF=approved（2026-10-19 维护者）· HG-GRAPH-MODULES=approved（graph_change_layer=none 口径写明 · 越出回炉回路在案）。
- HG-AUDIT-R1=**pending**（blocks 30）——本帽不代签；R2 pass 后由 00 依授权代签。人签前维持：**30 拒开工**。
- 本帽本轮零 task/SPEC/app/ 实质改动（写入面仅本审查文 + 20 invoke 补记）。
