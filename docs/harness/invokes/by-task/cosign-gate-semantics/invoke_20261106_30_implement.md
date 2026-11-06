# invoke · 30 实现 · cosign-gate-semantics（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `30`（实现棒 · 承 issue #333 comment `6676780590` 六条件授权） |
| task_slug | `cosign-gate-semantics` |
| task 文件 | `docs/tasks/active/task_cosign_gate_semantics.md` |
| 分支 | `fix/cosign-gate-semantics`（base = 10 分支头 `f72ab1d` · 含四闸签认代录档） |
| 授权 | issue #333 comment `6676780590`（2026-11-06 12:19 · 30 授权六条件 · 签认依据 = PR #351 review `5795679444` + 授权链 2026-11-06 08:48 + 12:17『验收333』） |
| 设计闸裁决 | 案①幂等为主干（幂等锚五元组）· 覆盖不设默认（append-only）· 拒重复不设 · 落点 = gate 记录层 |

## 交付（六条件逐条对照）

| # | 条件 | 对照 |
|---|------|------|
| ① | 机断判据为主（条文 grep 锚 + 结构断言）；涉码红测先行（负样本 = 同锚重复送达不误读为新签 · 真实送达→认定→记录路径） | ✅ `tests/test_cosign_gate_semantics.py` 8 断言（FRAGMENT 存在/frontmatter · 幂等锚五元组 · 同锚重送达同效力不重复记录+replay · 覆盖不设默认 append-only · 拒重复不设 · 落点=gate 记录层 · orchestrator 可达 · 闸表四列契约）——**先红**（`d2d9eaf`：7 failed 1 passed，裁决落文缺失 = 认定路径无规则）→**后绿**（`c25336c`：8 passed）。承载面 = 本仓 gate 记录层过程资产（FRAGMENT 即真实落点），非直造记录直调 |
| ② | 旧测适配不放宽随 PR | ✅ 实扫零适配：`test_prompt_packs.py` 仅锚 delegate_only/reanchor 两档（55 passed 不扰动）；docs/harness 面其余测试族 grep 零关联；全量 2083 passed · 4 failed = 既有红基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1）· 零新增红 |
| ③ | 改码面收敛（裁决落文为主 · 实扫溢出口径回闸） | ✅ 改码面 = docs/harness prompts（FRAGMENT 新档 + 00-orchestrator 引用行 2 处）+ tests 新档 1 枚；实扫未溢出（无 spec-wave 上游/机检扩展需求 → 无回闸事项） |
| ④ | 红线零 diff 对拍（SSE 事件表 / freeze / 闸表契约四列机读不破坏——GATE_VERIFY 仍是唯一闸据） | ✅ `git diff origin/master`：app/ · alembic/ 零 diff；SSE 面（subtask_message/progress_stream/answer_stream/chat router/event_store）零命中；TASK_TEMPLATE 闸表四列 header 断言恒绿；verify 四闸 approved PASS |
| ⑤ | ruff + pytest + graph-compile 全绿 | ✅ ruff All checks passed（F541 一枚即修即 amend）· 全量 pytest 2083 passed 零新增红 · graph-compile EXIT=0 |
| ⑥ | PR 逐条对照验收 | ✅ 本 invoke + task 档自检 hat 30 逐项对照表随 PR |

## 过程

1. `f72ab1d` 四闸签认代录（10 分支 · PR #351）：闸表四行 approved + R2 裁决回填 + 30 注六条件入档。
2. 30 分支 `fix/cosign-gate-semantics` 自 `f72ab1d` 切出。
3. 红测先行：`d2d9eaf` 8 断言先红（7 failed——裁决落文缺失）。
4. 裁决落文：`c25336c` FRAGMENT 新档（幂等锚五元组表 + 认定规则四条 + 00 执行纪律）+ 00-orchestrator 引用行（不改默认表语义）→ 8 断言后绿。
5. 20-R1 审查文 + 20 invoke 落盘（维护者令「随 30 PR 落盘」）· task 档自检 hat 30 回填。

## 产出

- `docs/harness/prompts/FRAGMENT_00_gate_cosign_semantics_v1_zh.md`（裁决落文 · gate 记录层唯一真源）
- `docs/harness/prompts/00-orchestrator.md`（引用行 · 修订记录一行）
- `tests/test_cosign_gate_semantics.py`（机断 8 断言）
- `docs/harness/reviews/task_cosign_gate_semantics_audit_R1_20261106.md` + `invoke_20261106_20_r1_audit.md`（20 棒留痕）
- task 档 30 注 / 自检 hat 30 / 修订表回填

## 禁区复核

- 未改 `app/` / `alembic/`；SSE 事件表 / freeze 文件本体零 diff。
- 未触碰任何 human_gate（四闸 approved 承签认档）；未代签新闸。
- spec-wave 上游 / task lint 规则本体零改动。
