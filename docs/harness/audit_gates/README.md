# 波次审计闸自注册（N3 程序）

> 立档：2026-11-07 · task env-red-n3-governance · 承 api#337 CLOSE invoke 遗留挂账第 2 项
> （「未来波次 committed 面审计须自注册新闸（20-R1 N3 口径）· 同类守卫需求承 2026-10-20 三闸先例」）。

## 一句话

未来波次要在守卫面（`scripts/` · `alembic/` · 其余未登记的 `app/`）工作，**只在
[registry.yaml](registry.yaml) 登记数据，不写新闸代码**——`tests/test_wave_gate_registry.py`
对全部 entry 自动生效。

## 自注册三步（新波次作者执行）

1. **登记**：在 `registry.yaml` 的 `waves:` 追加 entry——
   - `task_slug` = 你的 task 档名；`status: active`；
   - `base` = 波次切出点钉锚（短 SHA）；`wave_tip` 先空（合并 commit 未定）；
   - `allowed_app_files` / `allowed_tree_files` / `allowed_tree_prefixes` = 你签认过的
     波次声明面（以闸签 invoke / 00 裁定的限定语为准，**不得宽于签认面**）；
   - `note` = 限定语与签认引用（谁签的·禁承载什么——照 00 裁定式登记范式）。
2. **即生效**：闸自动审计你的 committed 面（base..wave_tip 闭窗 ⊆ allowed）与在途
   面（banned 前置 · 禁改面在途触碰即 fail）。`wave_tip` 未钉期间 committed 面按
   N2 规格跳过（带审计输出），在途守卫不受影响的照咬。
3. **CLOSE 时**：把 `status` 改 `closed` 并钉 `wave_tip`（合并 commit）——闸转档案
   形态：committed 面审计封存，**在途守卫仍咬**（O2 语义不随闭窗退役）。

## 闸语义（与 test_tc8_diff_whitelist 逐条对齐 · 00 签认形态②）

| 面 | 语义 |
|----|------|
| committed 面 | `base..wave_tip` **闭窗**（不随 master 合入增长——whitelist 过期型锚点漂移的结构性修复） |
| 在途面 | 工作区/暂存 vs HEAD + untracked（含 closed entry） |
| banned 前置 | 先于一切 skip 出口：`banned_prefixes` 或未登记的 `app/` 触碰即 fail |
| N2 退化规格 | `wave_tip` 未钉/不可解析（浅克隆）→ 带审计输出跳过 committed 面，**绝不退化为 vs HEAD 增长窗** |
| fail-closed | 脏树 + tip 不可解析组合的保守保牙语义——立档见 [adr-001](adr-001-fail-closed-stranded-wave.md) |

## 与既有闸的关系

- 逐波 bespoke 闸（如 `test_tc8_diff_whitelist`）是**历史档案见证**，保留不删；
- 本簿 + 通用闸是**活着的闸**：新波次守卫需求一律走自注册，不再逐波复制测试代码
  （三闸先例的复制痛点即 N3 立项由来的另一半）；
- `test_registry_seed_entry_matches_tc8_whitelist` 是回归牙：种子 entry 的 allowed
  集合与原 TC8 声明白名单钉死一致，迁移不缩水。

## 已登记波次

- `diff-whitelist-anchor-drift`（status=closed · 2026-11-06 全链闭环 PR #357–#361）——种子档案。
