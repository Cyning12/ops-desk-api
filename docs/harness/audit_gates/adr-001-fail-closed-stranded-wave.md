# ADR-001：浅克隆「脏树 + tip 不可解析」组合的 fail-closed 裁定

> 状态：**accepted（维持不修正 · 正式立档）** · 2026-11-07
> 来源：api#337 CLOSE invoke 遗留挂账第 3 项（「浅克隆『脏树 + tip 不可解析』组合下
> 回归牙保守 fail-closed——真实 CI 干净树不受影响 · 语义维持 fail-closed 不修正」）。
> 关联：20-R1 N2 规格 · `tests/test_wave_gate_registry.py` · `test_tc8_diff_whitelist`。

## 背景

固定波次窗闸（00 签认形态②）的 committed 面 = `base..wave_tip` 闭窗。浅克隆
（`--depth 1`）环境下 `wave_tip` 可能不可解析，此时按 N2 规格：带审计输出**跳过**
committed 面，绝不退化为 vs HEAD 增长窗。

但存在第三种组合：**工作区脏树（有在途改动）∧ tip 不可解析**。此时并集面只剩
在途 + untracked，而 `_touched_in_wave` 的既有契约（越界分类：钉锚不可解析 →
保守 True 保牙）会让「在途越界文件」被分类为波次内 → 闸 fail。

## 裁定

**维持 fail-closed，不修正。** 理由：

1. **方向正确**：在「看不清 committed 历史」的环境里，对「在途触碰声明面外文件」
   从严，是把不确定性挡在门外而不是放进门内——与 banned 前置（O2）、内存 saver
   拒恢复（checkpointer fail-closed）同一伦理；
2. **真实 CI 零影响**：CI 是干净树 + 全量历史，该组合不可达（40 棒浅克隆实证：
   干净浅克隆命中的是态②退化基线，正常 pass）；
3. **修正成本高企**：要区分「脏树在途文件属于本波次」需要波次身份的外生证据，
   恰是自注册簿（N3）提供的声明面——有了 registry entry，该文件应登记在
   allowed 集合里而非靠判定放宽。

## 触发条件（何时会看到这个 fail）

浅克隆 + 工作区有未提交改动 + 改动触碰声明面外文件。处置：提交或 stash 在途改动，
或（确属波次内）走自注册程序登记。

##  revisit 条件

若未来出现「合法开发流频繁撞此 fail」的实证（非假想），优先解法是完善 registry
声明面（第 3 条理由），而非放宽 `_touched_in_wave` 的保牙语义。
