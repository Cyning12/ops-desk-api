---
# task_p3_t6_idempotency_db_default · R1 审查文（20 帽）
---

- 时刻：2026-11-16
- 审查人：exec-p3-t6（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03498/m03551 · 00 代签体系）
- 对象：`docs/tasks/active/task_p3_t6_idempotency_db_default.md` v1

## 审查项

1. **范围对账**：task 范围 6 条与委派书 + 14 终稿 §6.4 R9 逐条对账——①
   默认值翻转（persistence.py:39 未设/空串 → db）② docstring 改写（装配是
   部署动作 / 刻意不做自动探测 / 配置面默认值变更非运行时自适应）③ env
   四分回归矩阵（显式 db / memory / null / 未设）④ fail-closed 回归 +
   显式 null 回退回归 ⑤ 风险登记 R-P3-10 ⑥ 测试/文档/图谱三面同步——
   全部锚定到测试名或文件行。GO。
2. **真源冲突裁定（15 §7.3/§7.5 vs 14 终稿）**：契约 15 §7.3 写「代码默认
   仍是未设（null），不在代码里改默认值」并把 R9 条件记作「T2b 附带条件」，
   与 14 终稿 §0/§6.4/§10（T6 承载「默认 null→db」）+ 委派书（未设=新默认
   db）矛盾。14 终稿为三方评审合并终稿（R1-R23 全关闭）且委派书明确翻转，
   裁定照 14 终稿 + 委派书；契约 15 不改（跨仓 · 非本波 allowed_tree），
   矛盾如实登记偏差 D1 供 lead/00 跨仓和解。GO。
3. **翻转点唯一性**：全仓 grep 钉死文案仅 persistence.py 与
   tests/test_log_init_window.py 存活引用；`describe_persistence()` 从实际
   对象推导 mode 故翻转后逻辑零改（仅 null 分支 note 口径同步）；hitl 面
   同形装配（OPS_HITL_PERSISTENCE）明确非范围。翻转点唯一 = :39 一行。GO。
4. **fail-closed 语义承接核查**：DB 故障路径为既有语义链（adapters/
   http_generic.py `_aclaim` → `_astore_call` 异常直传 → gateway.py
   `_aerr_result` ok=False · 绝不静默放行重复执行），本波**零新码**只补
   回归测试（假 session_factory 注入模拟连接故障 → ainvoke ok=False +
   下游传输零调用）。可用性耦合反转（忘配静默不防重 → DB 故障显式失败）
   已在 task 失败路径与 R-P3-10 风险登记写明。GO。
5. **观测面零改实证**：tests/test_admin_capability_observability.py 靠
   fixture reset 后从实际对象推导 mode（非 env），翻转后断言（mode=null ·
   「不可上生产」·「第二张单据」子串存续）不依赖默认值——零改实证已列入
   范围第 3 条核销项。GO。
6. **非范围**：熔断/预算/nonce 维持进程内声明 · device_tokens（R3 已降契约
   草案）· hitl 面默认值 · 契约文档 15 均明示排除；零 DDL/零迁移/零新路由/
   零 SSE 事件 → banned_prefixes=[alembic/, scripts/]。GO。

## 结论

**GO**——范围对账完整、真源冲突有裁定有登记、翻转点唯一、fail-closed
零新码只补回归、观测面零改可实证。准入 30。
