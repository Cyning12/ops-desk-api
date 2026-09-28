# Agent Host v1.0 · 三方验收报告（00 独立复核 · 对代跑交付不信任重验）

> **日期**：2026-09-24  
> **验收人**：00（落地长程原窗 · 本报告为**三方验收**：V1-A/B/C 由本窗亲验亲收；V1-D/E/出口复核/SLI 由另一 agent 代完成，本窗**不采信其自述、逐项独立重验**）  
> **依据**：维护者令 2026-09-24「中间没有额度，已经交由其他agent完成后续任务，进行三方验收」  
> **验收对象真值点**：master `1cae38f`（#194 收口后）  
> **方法**：detached worktree 独立重跑（pytest/import-linter/graph-compile）+ 闸链/签录链真读 + 断言存在性抽验 + CI 终态核对

---

## 总裁定

| 项 | 值 |
|---|---|
| **三方验收结论** | **PASS（签收 v1.0 全轨落地）** |
| 含义 | V1-A~E 五波 + dualproc fix + 出口复核 + SLI 跟进全部 CLOSE，独立重验未发现造假/假绿/断链；唯一残余=文档级 G2（见下 · P2 不阻塞出口） |
| 残余 GAP | **G2（P2 · 文档面）**：post-#190 的 dualproc 更新版 `REGRESSION_*` 报告文件未落盘（功能面已 PASS——本窗亲跑 9 passed · 证据散在 #190 KPI/CI，报告文件仍记 BLOCKED-ENV） |
| 存量背景（非本验收面） | 仓级 reviews 裸扫描 92 缺口全部为 legacy 历史任务（**host_v1 面零缺口** · --json 过滤实证）；本地 `test_import_from_supabase` 3 ERROR = 环境性（本地 PG create database 权限）· CI pytest pass |

## 分面独立核验（07 §4 八面）

| # | 面 | 结论 | 本窗独立证据（非代跑者自述） |
|---|---|---|---|
| 1 | 委派链路（V1-A） | **PASS** | 本窗亲验亲收（PR #179 · 六类拒绝+篡改+重签发断言 · 变异检验 3/3） |
| 2 | 可见集（V1-B） | **PASS** | 本窗亲验亲收（PR #181 · B-1 回炉澄清轨迹 · 40 新用例全绿亲跑） |
| 3 | manifest 四字段（V1-B） | **PASS** | 同 #181（加载期三硬规则+三档派生亲验） |
| 4 | LLM 工厂（V1-C） | **PASS** | 本窗亲验亲收（PR #183 · 43 新用例亲跑 · degraded 标记/版本入键/拦截变异 3/3） |
| 5 | 记忆（V1-D） | **PASS** | 独立重验：episode 三测试文件真在（20+30+14 测试函数 · `test_memory_episode_gate/recall`/`episode_pattern_mine`）· HG-AUDIT-R1 approved 行真读（维护者令原话留痕）· PR #184 MERGED（669e76a）· 40 invoke 记载 84 passed+12 ERROR 基线实证 |
| 6 | 工程（V1-E + #190） | **PASS**（G2 文档残余） | 独立重跑：`lint-imports` **12 kept / 0 broken** · `test_multi_replica_dualproc.py` **本窗亲跑 9 passed**（master · 直接反驳「报告仍 BLOCKED」的功能面疑虑）· `RegistryReader`/`RegistryWriter` Protocol + `set_registry` 真在（registry.py:33/:48 · gateway.py:95）· PR #187 MERGED（164f3fc）· CI 四绿（含 import-linter workflow） |
| 7 | 指标（SLI 跟进 #193） | **PASS** | `evals/agent/sli/aggregate_sli.py` 真在（聚合面实存）· task done（HG-AUDIT-R1 00 代录 approved · R1 审查文在）· PR #193/#194 MERGED CI 四绿 · 出口 G1 closed |
| 8 | 图谱签录链 | **PASS** | `01_modules.md` 签录表 47 行 · V1-A~E 回写行真读（105→110 · 每行 00 代录+维护者令原话留痕）· graph-compile exit 0（本窗亲跑） |

## 全量验证（本窗亲跑 · master 1cae38f）

| 命令 | 结果 |
|---|---|
| `pytest tests`（全量） | **1599 passed / 1 skipped / 3 errors**——3 errors = `test_import_from_supabase`（本地 PG create-database 权限 · 环境性）；对照：V1-A 时点基线 1368 → 现 1599（+231 净增） |
| `lint-imports --config .importlinter` | **Contracts: 12 kept, 0 broken** |
| `./scripts/graph-compile.sh` | exit 0 |
| `pytest tests/test_multi_replica_dualproc.py` | **9 passed**（双进程面功能直证 · #190 修复有效） |
| CI（#193/#194 终态） | check · import-linter · lint-wiki-delta · pytest 四绿 |
| `npx spec-wave verify`（仓级 reviews 裸扫描） | 92 缺口全 legacy（**host_v1 零缺口**）· 各波 per-task verify 均 PASS（各波 CLOSE 时亲跑） |

## 闸链完整性（五波+跟进 · 真读）

| 波 | SPEC signed | task 闸（DRAFT/R1） | 审查文 | 图谱签录 | PR |
|---|---|---|---|---|---|
| V1-A | ✅ 00 代录 | ✅/✅ 00 代录 | R1 PASS-WITH-NITS | ✅ | #179/#180 |
| V1-B | ✅ 00 代录（含 B-1 澄清） | ✅/✅ 00 代录 | R1 FAIL→R2 PASS-WITH-NITS | ✅ | #181/#182 |
| V1-C | ✅ 00 代录 | ✅/✅ 00 代录 | R1 PASS-WITH-NITS | ✅ | #183 |
| V1-D | ✅ 00 代录（本窗 SPEC/task） | ✅/✅ 00 代录 | R1 PASS-WITH-NITS | ✅ | #184/#186 |
| V1-E | ✅ 00 代录（本窗 SPEC · 顺序纪律留痕） | ✅/✅ 00 代录 | R1（20260924） | ✅ | #187/#188/#189 |
| dualproc fix | —（fix task · FINDINGS#1） | ✅ | — | — | #190/#192 |
| SLI 跟进（G1） | —（出口复核 follow-up） | ✅/✅ 00 代录 | R1（20260924） | n/a（none） | #193/#194 |

## 残余与建议

1. **G2（P2 · 不阻塞出口）**：补写 post-#190 dualproc `REGRESSION_*` 更新报告（result=PASS · 引 git sha 1cae38f/recorded_at/本窗亲跑 9 passed 可作证据源）——docs-only 微修，随时可做。
2. 代跑窗口与本窗的过程档已双轨留痕（D 波有 30_resume invoke · C 波 CLOSE 由代跑者补登 40 invoke 与归档）——本窗过时的 C-CLOSE 在制品已弃置（stash dropped · Hub 重复行已还原），无残债。
3. 另一 agent 的在制品（`docs/agent-host-current-architecture-20260924` 分支 + 未跟踪 09-24 讨论稿）**本窗未触碰**。

## 签收

| 产物 | status | 留痕 |
|---|---|---|
| 本验收报告 | **signed** | 2026-09-24 · 00 三方验收 · 维护者令原话：「中间没有额度，已经交由其他agent完成后续任务，进行三方验收」 |

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 初版：八面独立重验全 PASS（G2 文档残余 P2 如实登记）· 全量/分项验证证据在案 |
