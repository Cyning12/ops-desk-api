---
name: harness-00-gate-cosign-semantics
description: 人工闸签认在跟进消息重复送达时的认定规则（同签语义裁决落文 · gate 记录层唯一真源）。当同一维护者对同一工单的同一签认再次送达（平台重试/多线程重复表态/窗口授权续达/同一 review 重复投递）时使用。不用于：首次签认的受理（走闸表四列契约与代录纪律）；仓外运行时消费门内判定（随 task residual_risk 登记）。
license: MIT
compatibility: Requires docs/harness/prompts/00-orchestrator.md；机断锚 = tests/test_cosign_gate_semantics.py
metadata:
  hat_id: "00"
  track: starter
---

# FRAGMENT · 00 人工闸同签语义（HG-COSIGN-SEMANTICS-DESIGN 裁决落文）

> **裁决依据**：lead 签认 2026-11-06 · source = PR #351 review `5795679444` + issue #333 comment `6676780590` · 授权链 = 2026-11-06 08:48 维护者授权 + 12:17『验收333』指示。
> **裁决 = 案①幂等为主干**；覆盖不设默认；拒重复不设；落点 = gate 记录层（本文即机断可 grep 唯一真源）。

## 幂等锚（同签判定的同一性键）

**幂等锚 =（维护者, 工单, 闸集, 签认依据 comment id, 授权窗口）**——五元组全同才算「同一签认」：

| 字段 | 说明 |
|------|------|
| 维护者 | 签署人账号（GitHub login） |
| 工单 | 签认所承载的 issue/PR/任务档 |
| 闸集 | 本签认覆盖的 human_gate_id 集合（同签可一锚多闸） |
| 签认依据 comment id | 授权/签认原文所在评论（review/comment 的 id） |
| 授权窗口 | 授权时效锚（如「窗口授权至 2026-11-06 07:00」；无窗口即恒期） |

## 认定规则

1. **同锚重送达 = 同效力，不重复记录**：跟进消息再次送达同一签认（五元组全同）时，闸表/invoke/审查文不新增签认记录、不刷新依据；可在 invoke 记 **replay 附注**（重送达时间 + 触发源，观察痕而非新签）。重送达**不得**被解读为新签、不得扩张或刷新既有授权效力。
2. **覆盖不设默认**：审计链 append-only 是判例体系根基。仅当「同锚 **+ 维护者显式声明替换意图**」时允许覆盖——形态 = **追加新行**（新签认行），**旧行保留引注**（旧行注明被 supersede 及新行指针）；**禁止**原地改写旧签认行的依据或时间戳。
3. **拒重复不设**：补发/重送达是合法通路（F1/S3b 判例：平台重试与多线程补发承载同一人类意图），对重送达拒收必造成流程死点——不设拒重复分支。
4. **落点 = gate 记录层**：本认定规则作用于 Harness 过程资产（task 档闸表 + invoke + 审查文），机断可 grep（唯一真源 = 本文）。**消费门内**（GATE_VERIFY/verify 执行期判定）属仓外运行时面——不属本资产范围，随 task 档 `residual_risks` 如实登记，不在本 FRAGMENT 内展开。

## 00 执行纪律

- 代录/受理签认前先按幂等锚五元组判同：全同 → 规则 1（幂等，可记 replay 附注）；同锚 + 显式替换意图 → 规则 2（追加新行，旧行保留引注）；五元组不同 → 按新签认走闸表四列契约与代录依据引用纪律。
- 任何形态不得破坏闸表四列契约（human_gate_id / status / blocks_hats / 说明），GATE_VERIFY 仍是 30 唯一闸据。

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-11-06 | v1 · 裁决落文（案①幂等为主干 · HG-COSIGN-SEMANTICS-DESIGN · issue #333）· 机断锚 `tests/test_cosign_gate_semantics.py` 先红后绿 |
