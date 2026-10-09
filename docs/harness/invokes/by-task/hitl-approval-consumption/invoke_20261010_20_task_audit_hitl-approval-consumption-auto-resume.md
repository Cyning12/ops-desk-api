# Invoke：20-task-audit R1 · hitl-approval-consumption-auto-resume（T2 D5 自动 resume 可配置面）

> **hat_id**：20-task-audit · **轮次**：R1 · **日期**：2026-10-10 · **分支**：`task/hitl-approval-consumption`（worktree · merge-base=master `4d905e0` ✓）
> **审查对象**：`docs/tasks/active/task_hitl_approval_consumption_auto_resume.md`（draft）
> **对照基准**：SPEC v1（`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` · HG-SPEC-SIGNOFF=approved 2026-10-10 · spec 分支只读）
> **skill**：harness-20-task-audit 已加载 · **纪律**：骨架先行增量落盘 · 不改 task 实质 · 不代签 human_gate
> **审查文**：`docs/harness/reviews/task_hitl_approval_consumption_auto_resume_audit_R1_20261010.md`

## 结论

| 维度 | 结论 |
|------|------|
| 内容 | **PASS**（零内容阻塞 · 非阻塞注记 N-1~N-3） |
| 流程闸 | 三闸 pending（属实时序）+ **T1 未 merge 前置未满足**（T1 本审 FAIL 待修复 · 串行顺序不变） |

## 核对过程（实证留痕）

- **锚点实读 11 组**（逐组结论见审查文「锚点实读抽查」表）：router.py:112-116（Literal/422 · R2-N1 前提）/ :175-232（decide 成功分支 · R2-N2 挂点空间）/ :235-275（OA callback 签名面 · 不挂触发器实证）/ :377-430 + :319-374（恢复段两件套 · 抽取复用面）· resume.py:285（签名）· store.py:127-228（四方法 · diff 空切法）· main.py:12-16（lifespan 挂点）· event_store.py 全函数定义（**无 run 终态谓词 · 实操-E 实证成立**）· hitl/persistence.py · tests/conftest.py。
- **R2-N1（400 vs 422）**：`decision` 既有 Literal→422 docstring 实证 → `resume_mode` 钉 str+手工白名单=400 为唯一干净路径；否 Literal（422 违 SPEC FP-10/A10）与否 validator 抛 HTTPException（绕 FastAPI 语义）理由成立。
- **R2-N2（挂点）**：router decide 成功分支实证；否 store 层（违 A7）与 OA callback（签名面零 diff）成立；与 D1「按单据不看来源」对称性论证成立（消费面同源对称 · 触发面不对称由补偿扫描兜底 → N-1 推论）。
- **R2-N3（行锁）**：20 亲跑 grep `FOR UPDATE`/`SKIP LOCKED`/`for_update`/`skip_locked` 全 app/ **零命中**——「仓内无先例」属实；DbHitlStore 新增方法 + InMemory 禁假断言分组钉 TB2③ 正确。
- **TB1–TB8 ↔ SPEC A9/A10 + 存续面**：逐条核对全对上。
- **T1 依赖链**：六钉点核齐（头部 :6-7 · failure_paths 首行 · 验收首条 · 依赖表首行 · 必读列表 1/10 · T1 侧互指）——「依赖 T1 merge」钉在依赖表/验收/闸行三处 ✓。

## 非阻塞注记

- N-1：补偿扫描四条件不看 decide 来源 → OA 批准单在全局 auto 下仍会被扫描补触发（「OA 面不挂」=不即时 ≠ 全 manual）；fail-safe 方向无安全洞，建议 10-task 顺手补一行语义明示（可随 T1 退回修复同批 · 不单独阻塞 T2 签收）。
- N-2：`aclaim_approved_for_resume` 与 idempotency.py 既有 `aclaim` 同名不同义 · 提示 30 docstring 写明差异。
- N-3：扫描周期 60s 建议值口径（R3 residual 如实）维持。

## lint / verify 复跑

| 命令 | 结果 |
|------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_auto_resume.md` | **PASS**（EXIT=0 · `LINT: PASS · task_hitl_approval_consumption_auto_resume.md`） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_auto_resume.md` | **EXIT=2 符合预期**（VERIFY: BLOCKED · 三闸 pending 属实时序 · 另 T1 merge 前置未满足） |
