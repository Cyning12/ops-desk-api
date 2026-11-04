# Invoke · 20 帽 · R1 审查（api-w-hitl-tenant-fix）

| 字段 | 值 |
|------|-----|
| **hat_id** | `20`（task 审查 · 20-R1 棒） |
| **时间** | 2026-11-03（Asia/Shanghai） |
| **task_slug** | `api-w-hitl-tenant-fix` |
| **task_paths** | `docs/tasks/active/task_api_w_hitl_tenant_fix.md` |
| **related_review_or_none** | 本文件即 20-R1 审查文（落档 PR #312 review 记录 · 维护者 auth311 令） |
| **git_branch** | `agent/hitl-tenant-fix-task-955c1cd011b6`（10 起草 PR #312 分支 · MERGED squash `04245ef`） |
| **created_utc_or_local** | 2026-11-03 |
| **notes** | 审查执行者 = 维护者本人（PR #312 review 5749075777 · 语义面逐项核对）；本棒为审查记录正式落档 + task 闸表签收同步（00 代录） |

---

## §1 · 审查对象

- **task 档**：`docs/tasks/active/task_api_w_hitl_tenant_fix.md`（10 起草壳 · commit `9b74a78` · PR #312 · 零 `app/` diff）
- **上游证据**：workspace `invoke_20261102_10_c8_evidence_archive.md`（§C6/§2）· `invoke_20261103_10_final_acceptance.md` §2 · backlog B2
- **授权**：维护者 issue [#311](https://github.com/Cyning12/ops-desk-api/issues/311) 令起草 + 审查（20-R1 由维护者亲自执行并 APPROVED）

## §2 · 审查记录（PR #312 review 原文落档）

> **APPROVED review of commit 9b74a78c686373edd81bc3cff778266e66a882c9**
>
> 20-R1 审查通过（维护者授权审查 · 语义面逐项核对）：
>
> **核对结论**
> - 证据链：invoke §C6/§2 锚点与码面锚点抽查一致（`hitl/router.py:447`、`tenant_context.py:24-26` 唯一回落、`nodes.py:2144`/`499-504`/`318-320`），缺陷定位可信；
> - 范围切分：租户同族三件套（N-R2-1+F3+守卫真空）合并立项正确，F7/F9/web UX 排除干净，与前 task（PR #307）不重叠；
> - 钉死契约：双 freeze 零 diff（SSE event_type / hitl-browser-decide-v1）、手动自动两入口同源单实现、守卫单一真源——三条红线入 failure_paths，可机检；
> - 验收：红测先行（B 租户负样本）+ 旧测 grep 影响面清单随 PR + 回接联调 C6 复测条款，均可复验；
> - 闸设计：HG-W-TENANT-DESIGN 承载三决策点恰当；`spec-wave task lint` PASS；零 `app/` diff 符合 10 帽授权。
>
> **HG-W-TENANT-DESIGN 三决策点裁决（维护者签认）**
> 1. resume 链 tenant 来源：**A+B 组合**——以单据 `tenant_id` 为唯一真源做快照还原（对齐守卫 `row.tenant_id` 语义）；手动入口若 session 租户存在且 ≠ 单据租户 → 403（对齐 `lg_rag/router.py:376-384` 先例）；auto-scan 无请求上下文 → 纯 A。fail-closed：单据 tenant 为空 → 拒 resume。
> 2. delegation 消费守卫：**扩列纳入租户校验**（T-fix-2 打戳后守卫查非空成立）；不选豁免文档化。
> 3. 历史 `tenant_id=''` 40 行：**默认从严**——一律 fail-closed 拒 resume，不回填；后续如有真实 resume 诉求，走单独授权的数据修复。
>
> 四闸签收与 30 授权指令见 issue #311 线程。

（来源：PR #312 review [5749075777](https://github.com/Cyning12/ops-desk-api/pull/312#pullrequestreview-5749075777) · 维护者 Cyning12 · 2026-11-03T08:27:43Z · state=APPROVED）

## §3 · 闸态落档（auth311 代录）

| human_gate_id | status | 签认依据 |
|---------------|--------|----------|
| HG-TASK-DRAFT | approved | 2026-11-03 · issue #311 评论（@/tmp/auth311.md）+ PR #312 review · 起草质量 20-R1 已过 |
| HG-AUDIT-R1 | approved | 2026-11-03 · auth311「审查文落档即签」· 本文件落档即满足 |
| HG-GRAPH-MODULES | approved | 2026-11-03 · auth311 · G-L1 薄备注 · 无新增一级模块 |
| HG-W-TENANT-DESIGN | approved | 2026-11-03 · PR #312 review 三决策点裁决（见 §2） |

## §4 · 30 授权指令（auth311 落档）

闸表更新 + 审查文落档完成后，30 改码（T-fix-1 + T-fix-2 + 守卫收口），六要求：

1. 红测先行：B 租户负样本先红后绿，随 PR 可见红→绿证据；
2. 旧测 grep 影响面清单随 PR 提交，逐条标注保留/修改/删除+理由，禁止静默改测；
3. 手动/自动两入口同一租户还原实现，禁止第二份实现/第二处回落；
4. 双 freeze 零 diff（SSE event_type / hitl-browser-decide-v1）；
5. 交付前本地 `ruff check app tests`、`pytest tests`、`./scripts/graph-compile.sh` 全绿；
6. PR 说明逐条对照 task 档验收标准勾选。

---

## 交付摘要（本棒）

- **验证命令**：`npx spec-wave task lint --file docs/tasks/active/task_api_w_hitl_tenant_fix.md` → LINT: PASS（闸表签收修订后复跑）
- **变更路径**：`docs/tasks/active/task_api_w_hitl_tenant_fix.md`（闸表四闸 approved + 钉死契约升格 + 状态 active/GO 30 + 修订行）· 本审查文
- **下一棒**：`30`（api-w-hitl-tenant-fix · GO）

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-03 | 20-R1 审查文落档棒（00 代录）：PR #312 review 5749075777 原文落 §2 · 四闸签认状态落 §3（auth311 依据）· 30 授权六要求落 §4 · task 档闸表/契约表/状态行同步修订 · lint 复跑 PASS |
