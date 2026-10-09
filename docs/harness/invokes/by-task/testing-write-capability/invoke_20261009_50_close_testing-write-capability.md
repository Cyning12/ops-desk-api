---
hat: 50
task_slug: testing-write-capability
date: 2026-10-09
---

# invoke · 50+CLOSE · testing-write-capability（D2 · 注册非只读测试 capability · 补齐 HITL 全链可审对象）

## 收口结论

- 链路全通：10-task 落稿（behavior 小 task · 免 SPEC · 依据=验收登记偏差 #1 处置令 · R0–R5 early_stop at R5 · `invoke_20261009_10_task_testing-write-capability.md`）→ 20 R1 审查（PASS 零阻塞 · 观察项 O1–O4 · `task_testing_write_capability_audit_R1_20261009.md`）→ 维护者三闸人签（00 代录）→ 30 GATE_STOP（loader V1/V2/V7 夹击实证 · 探针复现 ManifestError · 零 diff 留档 `invoke_20261009_30_implement_testing-write-capability.md`）→ 10-task 修订（维护者裁定四=乙：manifest 顶层 `idempotency_key` + loader V1 二选一放宽）→ 20 R2 复审（PASS · 裁定四逐条成立 · 观察项 O5–O7 · `task_testing_write_capability_audit_R2_20261009.md`）→ 维护者重签 HG-TASK-DRAFT / HG-AUDIT-R1（00 代录 · `invoke_20261009_00_human-gate-resign_testing-write-capability.md`）→ 30 R2 交付（`f192d1c`/`26aa844`/`83bb883`/`2b2f1f8` · 钉死契约全守：独立 testing.v1.yaml 不进默认加载面 · env 门控 tag 白名单不全局松 deny_write · 罐头 adapter 零 IO · 判定逻辑零改动 · off 三 env 零 diff）→ 40 核验（逐项独立复跑不采信自报 · `invoke_20261009_40_verify_testing-write-capability.md`）。
- 闸链：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved（维护者签 · 00 代录 · 含 R2 重签留痕）。
- PR [#209](https://github.com/Cyning12/ops-desk-api/pull/209)：CI 四绿（check / pytest / import-linter / lint-wiki-delta）→ merge master `ca4148f`（2026-10-09）。
- 归档：task → `done/`（头部状态 done · 验收 A1–A8 勾选 · A1 注明三段 live 可达 / done 末段 409=既有链设计缺口另立 task · 修订表 CLOSE 行）；active README 登记表补行；Hub `docs/tasks/done/README.md` engineering 域表行 + 修订记录行补登；本 CLOSE invoke 落盘。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `app/ops/capability/manifests/testing.v1.yaml`（测试专用罐头 write capability · 仅 EXTRA_MANIFESTS 显式加载）· `defaults.py::testing_write_echo`（语义 mock 零 IO）· `CapabilityFilter.allow_write_tags_any` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS`（豁免 deny_write 一层 · deny_high_risk 无豁免口）· 裁定四 loader：manifest 顶层 `idempotency_key` + V1 二选一放宽 + V8 对称适配 · 验收单测 14 枚 · 图谱 l1 在册同步 |
| **验收** | A1 enforce 全链 **三段 live 可达**（挂起 blocked_by=`delegation_issue_hitl_required` → pending 可见 → decide 200 ✓）· `done{completed}` 末段 resume 409（unlock_subtask_id 为空 · router.py:404-410）=**既有链设计缺口 · 非本 task 回归 · 另立 task** · A2 off 零 diff（1661 passed 对拍零新增红）· A3 加载≠可见 · A4 新增 14 测全绿 · A5 罐头防线（AST + 逐行核）· A6 字段钉死 · A7 B1 十二处 14 文件 234 passed · A8 loader 校验四断言（V1/V8 文案对 master 逐字节零改动） |
| **40 结论** | **PASS 带偏差登记**：偏差 #1 闭环裁定（可审对象目的达成 · 末段缺口另立 task 由维护者裁定）· 40 新发现第四道门（strategy 候选 map 静态不含 testing.write.echo · live 链以测试等价 shim 补位 · 仓内代码零改动）· UP038 一枚偏差 `ddd515e` 修复闭环 |
| **红线** | deny_write 基线不动（baseline.py:43）· 全局松 deny_write / deny_high_risk 豁免口 / DOMAIN_ALLOW_TAGS 加 testing 全禁 · builtin.v1.yaml 五枚零 diff · HITL 链与 auto_approve_ok 判定一行未改 |

## 留痕

- 30 GATE_STOP 零 diff 留档为裁定四直接来源（甲乙丙丁选项表见 30 invoke）；loader V1/V2/V7 夹击实证探针可复现。
- 40 核验 live 链 env 组三件套前置 import app 前生效；第四道门 shim 仅测试运行期覆盖，生产路径与 master 零 diff。
- CI ruff 步骤注释中现状下 UP038 不阻合并；`ddd515e` 顺手修复闭环。
- worktree `d2-testing-write-capability` 与分支 `task/testing-write-capability` 清理留维护者裁决（active README 已登记）。

## 移交

- **留转①**：签发审批消费回路（resume 409「已批准但拿不到待解锁的步骤」缺口 + strategy `CAPABILITY_ALLOWLIST_BY_KEY["supervisor"]` env 口第四道门）**另立 task** 由维护者裁定——本 task 只补齐可审对象与可见性口径，不改审批消费语义。
- **留转②**：SPEC（chat-history-hitl-ux 后续 · 审批消费回路）**起草中**，归下一棒。
- off（默认）形态与 master 逐字节零 diff：三 env 皆不设即回到全只读能力面现状。
