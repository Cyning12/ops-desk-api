# 审查文 · task_api_w_hitl_tenant_fix · 20-R1（2026-11-03）

| 字段 | 值 |
|------|-----|
| **task_slug** | `api-w-hitl-tenant-fix` |
| **task_paths** | `docs/tasks/active/task_api_w_hitl_tenant_fix.md` |
| **审查轮次** | R1 |
| **审查对象** | 10 起草壳 commit `9b74a78`（PR #312 · MERGED squash `04245ef` · 零 `app/` diff） |
| **审查执行者** | 维护者 Cyning12 本人（PR #312 review 5749075777 · 2026-11-03T08:27:43Z · state=APPROVED） |
| **审查方式** | 语义面逐项核对（证据链锚点抽查 · 范围切分 · 钉死契约红线 · 验收可复验性 · 闸设计） |
| **过程存档** | `docs/harness/invokes/by-task/api-w-hitl-tenant-fix/invoke_20261103_20_r1_audit.md`（auth311 令落的 invokes/by-task/ 过程档 · 本址A 档供 verify 门禁机读 · 双址规约 v1 §二） |
| **签认授权** | 维护者 issue #311 评论（@/tmp/auth311.md）+ PR #312 review |

---

## §1 · 审查记录逐项核对（维护者 review 原文）

> **核对结论**
> - 证据链：invoke §C6/§2 锚点与码面锚点抽查一致（`hitl/router.py:447`、`tenant_context.py:24-26` 唯一回落、`nodes.py:2144`/`499-504`/`318-320`），缺陷定位可信；
> - 范围切分：租户同族三件套（N-R2-1+F3+守卫真空）合并立项正确，F7/F9/web UX 排除干净，与前 task（PR #307）不重叠；
> - 钉死契约：双 freeze 零 diff（SSE event_type / hitl-browser-decide-v1）、手动自动两入口同源单实现、守卫单一真源——三条红线入 failure_paths，可机检；
> - 验收：红测先行（B 租户负样本）+ 旧测 grep 影响面清单随 PR + 回接联调 C6 复测条款，均可复验；
> - 闸设计：HG-W-TENANT-DESIGN 承载三决策点恰当；`spec-wave task lint` PASS；零 `app/` diff 符合 10 帽授权。

## §2 · HG-W-TENANT-DESIGN 三决策点裁决（维护者签认）

1. resume 链 tenant 来源：**A+B 组合**——以单据 `tenant_id` 为唯一真源做快照还原（对齐守卫 `row.tenant_id` 语义）；手动入口若 session 租户存在且 ≠ 单据租户 → 403（对齐 `lg_rag/router.py:376-384` 先例）；auto-scan 无请求上下文 → 纯 A。fail-closed：单据 tenant 为空 → 拒 resume。
2. delegation 消费守卫：**扩列纳入租户校验**（T-fix-2 打戳后守卫查非空成立）；不选豁免文档化。
3. 历史 `tenant_id=''` 40 行：**默认从严**——一律 fail-closed 拒 resume，不回填；后续如有真实 resume 诉求，走单独授权的数据修复。

（来源：PR #312 review [5749075777](https://github.com/Cyning12/ops-desk-api/pull/312#pullrequestreview-5749075777) · APPROVED · 四闸签收与 30 授权指令见 issue #311 线程 auth311）

## 结论 · 20-R1 审查 PASS（维护者签认 · 零阻塞）

本席审查（语义面逐项核对 · 证据链/范围/红线/验收/闸设计五面）结论：**PASS 通过 · 零阻塞问题**。task 档缺陷定位可信、范围切分干净、三条红线可机检、验收可复验；HG-W-TENANT-DESIGN 三决策点由维护者同 review 签认（A+B 组合 / 守卫扩列 / 历史 '' 从严），task 档钉死契约表已据此升格。HG-TASK-DRAFT 随本审查通过签认（issue #311 评论依据），HG-AUDIT-R1 随本审查文落档签认（auth311），HG-GRAPH-MODULES 与 HG-W-TENANT-DESIGN 由 auth311 签认——四闸齐 · **GO 30**（auth311 六要求）。后续 30 棒按裁决值接线，不得静默改义。
