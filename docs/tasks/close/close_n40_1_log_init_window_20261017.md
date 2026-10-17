# CLOSE：n40-1-log-init-window（logging 初始化窗口收口 · app/main.py 行序上移 · repo-logging-init CLOSE N-40-1 nit 落地）（2026-10-17）

> **task**：[../done/task_n40_1_log_init_window.md](../done/task_n40_1_log_init_window.md)（已归档 done/ · 状态行 CLOSED 回写）
> **类型**：上游 nit 收口（bugfix 性质 · nit 级 · 实证驱动 · repo-logging-init CLOSE N-40-1 裁定落地 · 交接档 §2.2 序2）
> **关账日期**：2026-10-17 · 批量关账分支 `close/active-batch-20261017`（批量关账 PR 待开）· 帽位：CLOSE（50 · 三闸 approved · 00 代录 · 授权 m00106）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `n40-1-log-init-window` |
| 依据 | 交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 2 项 · `docs/tasks/close/close_repo_logging_init_20261011.md` §四 N-40-1（nit 照登原文）+ §七 后续建议 1（修法候选留本 task 裁定）· `docs/harness/invokes/by-task/repo-logging-init/invoke_20261011_40_verify.md` :77/:91 NIT 登记 |
| 背景 | `app/main.py:9-12` 的 app 包 import 链先于 `app/main.py:38` 模块级 `_init_logging()` 调用——窗口内 root logger 无 handler：WARNING+ 走 `logging.lastResort` **裸格式**（启动首行「能力层持久化未配置…」无 asctime/name/level），INFO 级**整行被吞**（db 模式 `persistence.py:48` 不可见）；窗口发射源钉实为 `capability/__init__.py:112` 模块级装配 → `persistence.py:48/:54/:65-68`；nit 级（验收三键请求期发射不受影响） |
| 目标 | 首个 app 包 import 之前 root handler 已就位——窗口内 WARNING 以钉死格式落 stderr、db 模式 INFO 可见；`OPS_LOG_LEVEL` 语义 / 格式口径 / uvicorn logger 共存 / pytest·caplog 测试面全部零 diff |
| 分支 | `task/n40-1-log-init-window`（base master `286d825` · worktree `../ops-desk-api-worktrees/t-n40-1-log-init-window`） |
| 帽链 | 10-task 落稿（候选 A/B 开放倾向 A · C 否决入非范围 · R0–R5 early_stop at R5）→ 20 R1 **PASS-WITH-NITS**（NIT×4 随 30 回填）→ 三闸 approved（00 代录 · 授权 m00106 · 2026-10-11）→ 30（方向 A 裁定落地 · 红测先行 · NIT×4 回填闭合）→ PR #239 → **CLOSE（本档 · 批量关账）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#239](https://github.com/Cyning12/ops-desk-api/pull/239) · **MERGED 2026-10-11T05:56:16Z · squash commit `9c07ab4`** · head `task/n40-1-log-init-window` |
| 码面 | **方向 A 落地**：`app/main.py` +10/-5 行序上移（`_init_logging` 定义与模块级调用上移至首个 app 包 import 之前 · 纯 stdlib 零循环 import 风险 · 零新模块）· capability 发射点字面零 diff（`capability/__init__.py:112` / `persistence.py` 三行不动）· 图谱 n/a 照实成立（A 零新模块 · 不触发 G-L2 义务） |
| 方案裁定 | 30 裁定方向 A：根因即行序 · 最小面；方向 B（抽 `app/ops/logging_config.py`）复用价值当前无消费者、反触发 G-L2 义务，不采；方向 C（发射点挪窝）治标动业务装配面，10 帽已否决入非范围 |
| 测试面 | 红测先行 **RED(5) → GREEN(7+3)**：新建 `tests/test_log_init_window.py` 7 例 + 上游 `test_logging_init.py` 3 例全绿；子进程 import 顺序探针（`PYTHONPATH=$PWD` + 显式 env · 注入式口径不赌时机 · 承 CLOSE 偏差 4 坑位纪律） |
| 审查文 | 20 R1 **PASS-WITH-NITS**（NIT×4 已回填闭合：N-1 四处计全断言化 · N-2 门控面登记 · N-3 钉版执行 · N-4 memory 口径）· 址A 原件 `docs/harness/reviews/task_n40_1_log_init_window_audit_R1_20261011.md` · 址B 复制件 `docs/audits/task-review/20261011_n40-1-log-init-window_r1.md`（主会话已落盘 · 址A 原件不动） |
| invokes | `docs/harness/invokes/by-task/n40-1-log-init-window/`（30 实施明细见 `invoke_20261011_30_implementation.md`） |
| **CLOSE 增量** | task 档归档 done/（状态行 CLOSED + 修订记录 CLOSED 行）· 本档落盘 · 批量关账分支 `close/active-batch-20261017` |

## 三 · 核验结论（TC1–TC4 全绿）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC1 窗口格式反转（核心 · 红测先行） | ✅ | 修复前 stderr「能力层持久化未配置…」裸格式（RED 5 红实证）→ 修复后匹配钉死格式 `<asctime> app.ops.capability.persistence WARNING …`（GREEN） |
| TC2 窗口 INFO 可见性 | ✅ | `OPS_CAPABILITY_PERSISTENCE=db` 下探针 stderr 含钉死格式 INFO 行「能力层持久化：db（跨实例防重 + 回执落库）」（修复前整行被吞 → 修复后可见） |
| TC3 `OPS_LOG_LEVEL` 回归组 | ✅ | 非法值 → INFO 回退 + 格式化 ERROR 告警行存续 · DEBUG 生效 · 缺省 INFO（裸探针口径承 repo-logging-init TC1 存续） |
| TC4 工程面 | ✅ | `pytest tests` 全量对拍**零新增归因红**（master 基线 4 failed=capability_lookups×3+lg_rag_multi×1 环境性钉案照登）· ruff 触及路径净 · graph-compile EXIT=0 · `lint-wiki-delta@3.0.1` PASS |
| 合并闸 | ✅ | PR #239 MERGED（squash `9c07ab4` · 2026-10-11T05:56:16Z） |

## 四 · 偏差与 nit（如实照登）

1. **20 R1 NIT×4（已回填闭合）**：N-1 四处计全断言化 · N-2 门控面登记 · N-3 钉版执行 · N-4 memory 口径——均非阻塞，30 回填在案（task 档自检结论）。
2. **方向 B 未采（裁定照登非偏差）**：`app/ops/logging_config.py` 抽离形态（上游 CLOSE §七 建议）因当前无消费者且触发 G-L2 判定义务未落地——可演进性需求再现时另议，非欠账。
3. **环境性红存续（基线钉案照登）**：master 基线 4 failed（capability_lookups×3 + lg_rag_multi×1）为环境性钉案，本 task 对拍零新增归因红即过线；仓级测试基线收口归另案。
4. **40 帽槽未回填**：task 档自检结论「（40 回填）」占位未填——TC1–TC4 验收面（含 live 等效裸探针）已全绿闭环，40 invoke 明细照登：无实证（如需追证以 invokes 目录留档为准）。
5. **探针纪律留痕**：子进程探针须钉 `PYTHONPATH=$PWD` + 显式 env（承 repo-logging-init CLOSE 偏差 4：sys.path[0] 指错码 + 主仓 .env 渗入坑位）——复跑须知。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-11 00 代录（授权 m00106）· 初稿人扫 |
| HG-AUDIT-R1 | **approved** | 2026-10-11 00 代录（授权 m00106）· R1 PASS-WITH-NITS（NIT×4 随 30 回填 · 窗口发射点全集实证闭合）· 址A `docs/harness/reviews/task_n40_1_log_init_window_audit_R1_20261011.md` |
| HG-GRAPH-MODULES | **approved** | 2026-10-11 00 代录（授权 m00106）· 图谱预判 n/a 按实判复核通过（方向 A 落地零新模块 · 条件义务未触发） |
| 20 R1 审查 | **PASS-WITH-NITS** | 址A 原件（同上）· 址B 复制件 `docs/audits/task-review/20261011_n40-1-log-init-window_r1.md`（已落盘 · 址A 原件不动） |
| 合并 | **MERGED** | PR [#239](https://github.com/Cyning12/ops-desk-api/pull/239) · squash `9c07ab4` · 2026-10-11T05:56:16Z |

## 六 · 维护者验收 checklist（00 代录 · 授权 m00106 · 需人重新验收项）

- [ ] **窗口格式抽验（live）**：master 起服（显式清 `OPS_CAPABILITY_PERSISTENCE`）——启动 stderr 首行「能力层持久化未配置…」匹配钉死格式 `%(asctime)s %(name)s %(levelname)s %(message)s`（无裸格式残留）。
- [ ] **窗口 INFO 抽验**：`OPS_CAPABILITY_PERSISTENCE=db` 起服——stderr 可见钉死格式 INFO 行「能力层持久化：db（跨实例防重 + 回执落库）」。
- [ ] **零 diff 抽验**：`OPS_LOG_LEVEL` 非法值回退 INFO + ERROR 告警行存续 · uvicorn access 不吞不双行 · `--reload` 双 import 幂等 · capability 发射点字面零 diff（git diff `app/ops/capability/` 为空）。

## 七 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（批量关账分支 `close/active-batch-20261017`）：结构沿 CLOSE 模板（close_hitl_resume_async_20261015）· 档内证据全录（方向 A 落地 +10/-5 · 红测先行 RED(5)→GREEN(7+3) · TC1–TC4 全绿 · 三闸 approved · 20 R1 PASS-WITH-NITS NIT×4 已回填 · PR #239 MERGED）· 40 帽槽未回填处照登「无实证」不代编 · 址B 复制件引用在案 · 分支 `task/n40-1-log-init-window` 移交 00 统一清理 |
