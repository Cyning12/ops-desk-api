# Invoke：20-task-audit R1 · hitl-approval-consumption-loop（T1 消费成环核心）

> **hat_id**：20-task-audit · **轮次**：R1 · **日期**：2026-10-10 · **分支**：`task/hitl-approval-consumption`（worktree · merge-base=master `4d905e0` ✓）
> **审查对象**：`docs/tasks/active/task_hitl_approval_consumption_loop.md`（draft）
> **对照基准**：SPEC v1（`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` · HG-SPEC-SIGNOFF=approved 2026-10-10 · spec 分支只读）
> **skill**：harness-20-task-audit 已加载 · **纪律**：骨架先行增量落盘 · 不改 task 实质 · 不代签 human_gate
> **审查文**：`docs/harness/reviews/task_hitl_approval_consumption_loop_audit_R1_20261010.md`

## 结论

| 维度 | 结论 |
|------|------|
| 内容 | **FAIL · 退回 10-task**（阻塞 B-1：B1 影响面漏 `scripts/acceptance/capability_step_contract_gate.py:152` sync 直调 · 附 B-1b redline「非默认跑」表述失准） |
| 流程闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending（属实时序 · 非阻塞） |

## 核对过程（实证留痕）

- **锚点实读 17 组**（逐组结论见审查文「锚点实读抽查」表）：nodes.py:277-295 / :644 / :708-726 / :1397-1471（:1440-1445 · :1457）/ :341-354 / :550-567 / :252-254 · graph.py:94 · delegation.py:488-514 / :105-107 · store.py:1-10 / :98 / :159-163 / :249（`_row_to_dict` → ISO str · **R1-N1 归一输入 float|str 钉实证成立**）· router.py:404-411 / :287-316 · pyproject.toml:76（asyncio_mode=auto）· test_capability_testing_write.py:488-493（实操-E 段逐字一致）。
- **TA1–TA7 ↔ SPEC A1/A2/A3/A5/A6/A7/A8 映射**：逐条核对全对上（A4 归 T3 · A9/A10 归 T2 · 划分正确）；fail-closed 断言组五项变异式全覆盖。
- **async 化甲案裁定复核**：裁定本身成立（乙案审计不可回卷实证 · 丙案违 P-13 + store.py:1-10 docstring 实证）；但「grep 全量落 B1（14 处）」声称与实证矛盾——20 亲跑 grep 另命中 `scripts/acceptance/capability_step_contract_gate.py:152`（`async def _drive` 内 sync 直调 · 被 `capability_acceptance.sh:165` 真跑 · 本地验收九层门禁）未入册 → B-1。
- **B-1b**：B1 redline 行「非默认跑（eval marker）」失准——pyproject 无 addopts 排除 · conftest 无 deselect 钩子 · CI `pytest.yml:47` 跑 `pytest tests -q` 无 `-m` 排除 → redline 文件默认就跑，「30 注记是否随改」措辞误导为可选。
- **R0–R5 思考轮**：回填闭合 · early_stop 理由成立 · residual_risks 如实。

## 退回清单（落 10-task）

1. B1 随改清单补第 15 处（scripts/acceptance/capability_step_contract_gate.py:152 · 修复=一行 await）。
2. 「14 处」口径统一改「15 处」（R1-N2 行 / 钉死契约 async 化裁定行 / F3 / 实操-A / R3 / R5）。
3. B1 redline 行改「默认跑 · 必须随改亲跑」（删「是否随改」可选措辞）。
4. （建议）实操-A 补「grep 范围须含 scripts/」。

> 修复为文档口径补齐 · 不动任何裁定结构；修复后 20 增量复核即可，无需重走全轮。

## lint / verify 复跑

| 命令 | 结果 |
|------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_loop.md` | **PASS**（EXIT=0 · `LINT: PASS · task_hitl_approval_consumption_loop.md`） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_loop.md` | **EXIT=2 符合预期**（VERIFY: BLOCKED · 三闸 pending 属实时序 · HG-AUDIT-R1 待维护者签） |

## 增量复核轮（10-task 修复 commit `0c5d148` · 2026-10-10）

退回四项逐点核对（仅核修复点 · 未重走全轮 · diff stat 确认裁定结构零改）：

| # | 退回项 | 结论 |
|---|--------|------|
| 1 | B1 补 scripts/acceptance/capability_step_contract_gate.py:152 | ✅（补 await 一行 · 门禁真跑后果写明） |
| 2 | 计数口径统一 | ⚠️ 残留 NIT（非阻塞）：R1-N2/R2 作「14 处」正确（join 13 + block_reason 1 · 20 逐枚复枚），但 B1 标题/F3/实操-A/R5/验收末行作「15 处」差 1——本 NIT 系 20 首轮退回清单以「声称数+1」为口径未枚举所致，20 自引并更正（真值 14 · B1 表枚举为准）；建议 10-task 顺手回改 · 不单独退回 |
| 3 | redline「非默认跑」→「默认跑 · 必须随改亲跑」 | ✅（B1 行 + R3 residual + R1-N2 标注三处同步） |
| 4 | 实操-A 补 grep 范围含 scripts/ | ✅（R3 grep 命令同步补） |

**增量裁定：内容转 PASS**（审查文「结论」节已按机读口径改为以「结论」起首 · PASS 落节内）。

| 增量复跑 | 结果 |
|----------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_loop.md` | **PASS**（EXIT=0 · 20 亲跑） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_loop.md` | **EXIT=2 符合预期**（VERIFY: BLOCKED · 三闸 pending 属实时序） |
