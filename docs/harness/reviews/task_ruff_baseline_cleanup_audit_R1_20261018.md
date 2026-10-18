# 审查文：ruff-baseline-cleanup · 20-task-audit R1（2026-10-18）

> **帽位**：20-task-audit（书面审查 · 只审不改实质内容 · 零 git 操作 · 零码改）
> **对象**：`docs/tasks/active/task_ruff_baseline_cleanup.md`（draft · 10-task 2026-10-18 落稿）
> **方法**：全部实证锚点 20 独立亲跑/亲读复核，不信用 10 自报。

## 元信息

| 字段 | 值 |
|------|-----|
| task_slug | `ruff_baseline_cleanup` |
| 审查轮 | R1 |
| 审查日期 | 2026-10-18 |
| 门禁实录 | `npx spec-wave verify --target . --task docs/tasks/active/task_ruff_baseline_cleanup.md` → **EXIT=2**，尾行 `VERIFY: BLOCKED · HG-AUDIT-R1 pending · task_ruff_baseline_cleanup.md`（闸 pending 期预期阻断，fail-closed 正常）；`npx spec-wave task lint` → **EXIT=0 · LINT: PASS** |

## 结论摘要

- **内容面**：**签收（无需退回）**。范围/非范围/验收/failure_paths/思考轮 R0–R5 齐备闭合；实证锚点全部亲核命中（明细见下）；关键裁定（F3 独立 commit 收口、F4 CI 改动注明、pytest 硬闸形态、N818 noqa、E402 互证）合理且有失败路径兜底。
- **流程闸**：HG-TASK-DRAFT pending · HG-AUDIT-R1 pending · HG-GRAPH-MODULES n/a——三闸状态照登，20 不代签；30 开工授权真值在 task 表，须维护者签。
- **行为变更类 checklist（K7）**：本 task 以零语义变更为硬约束（非范围第一条），非改默认值/校验/策略门/fallback 语义类，「旧测 grep 影响面」项不适用，照登说明。

## 阻塞 B 级：零项

## 非阻塞 nit（照登 · 10-task 可顺手修，不阻签收）

- **N1 · F4/FP-7 内部措辞张力**：FP-7 与 TC-RC-5 要求 CI ruff 步骤「走 uv.lock 同源安装（仓既有 uv 面），禁 pip 漂移版」；但 20 亲读 `.github/workflows/pytest.yml:44`，既有安装面实为 `uv pip install "ruff>=0.5,<1"`（非 lock 同源，specifier 区间未来可漂出非 0.15.21）。「与既有 uv 安装面一致」与「uv.lock 同源/禁漂移」两要求并存时 30 会有二义。建议 10-task 顺手把落点措辞钉死为「CI 步骤安装 `ruff==0.15.21`（与 uv.lock 钉版一致）」或签闸时由维护者明裁；FP-7 已含「出现漂移即修正步骤」兜底，故不定阻塞。

## 实证锚点亲核明细（20 独立复核 · 全部命中）

| 锚点 | task 声称 | 20 亲核结果 |
|------|-----------|-------------|
| ruff 版本 | 0.15.21 · `uv.lock:1831-1835` · `pyproject.toml:47` specifier `>=0.5,<1` | ✅ `uv.lock:1833` `version = "0.15.21"`；`pyproject.toml:47` 命中；`ruff --version` 实跑 0.15.21 |
| ruff 配置 | `pyproject.toml:64-73`（py311 · line-length 100 · select E,F,I,N,W,UP,B,C4,SIM · ignore E501,B008） | ✅ 逐行命中 |
| check 总量 | 52 errors · 28 fixable · 8 hidden unsafe | ✅ 实跑一致 |
| check 分布 13 类 | F811×9 · I001×9 · C408×7 · SIM117×7 · E402×5 · SIM300×4 · UP035×3 · F401×2 · UP045×2 · C401×1 · N814×1 · N818×1 · UP034×1 | ✅ `--statistics` 逐项一致；可修 28（I001+SIM117+SIM300+UP035+F401+UP045+UP034）与人工 24（F811+C408+E402+C401+N814+N818）加总闭合 |
| F811 九对行号 | redlines 572→777/617→822/640→845/703→908/743→948 · manifest 468→523/476→531/554→597/581→624（含对名） | ✅ `--select F811 --output-format concise` 九对行号与测试名全数一致 |
| E402 五处 | http_generic.py:65-66 · test_lg_rag_sse_token_stream.py:32,33,39 | ✅ 命中 |
| E402 有意布局互证 | http_generic.py:63-64 注释共用 jsonpath 实现 · :66 既有 `# noqa: F401` | ✅ 亲读命中，「疑似有意布局」判断有据 |
| C408 七处坐标 | redlines:113 · domain_allowlist:50 · http_adapter:59 · idempotency:70 · persistence_db:166,228 · visibility:44 | ✅ 全数命中 |
| C401/N814/N818 | nodes.py:1922 · test_admin_capability_observability.py:214（`_A`）· circuit.py:76 `CircuitOpen` | ✅ 全数命中；亲读 circuit.py:76-80 确认为 app 侧公开异常类，N818 默认 noqa 不改名裁定合理 |
| format 漂移 | 223 reformat / 103 ok（app 115/74 · tests 108/29） | ✅ 实跑三组数字全数一致 |
| CI 闸实况 | pytest.yml:52-53 Ruff 段整段注释 · 其余五 workflow 无 ruff | ✅ 亲读命中；`.github/workflows/` 共六件，grep 仅 pytest.yml 含 ruff |
| pytest 本地基线 | 19 failed / 1828 passed / 1 skipped | ✅ 20 独立复跑：**19 failed, 1828 passed, 1 skipped（66.33s）**，FAILED 尾清单与 10 invoke §四 对拍一致 |
| 基线红集留档 | 清单须可复核 | ✅ 10 invoke `invoke_20261018_10_task_draft.md` §四 落 19 条逐名清单 |

## 关键裁定合理性复核

1. **F3 一次性 format 独立 commit 收口（223 文件 · 68% 面）**：风险（diff 巨、review 难）已在 R3 识别，对策=独立 commit 零手改混入 + review 可整 commit 跳过；**破约回退路径写明**（FP-5：回退 format commit、明裁「不修只钉现状」+ 数据留档，不带红交付）。裁定有据。
2. **F4 CI 接入 pytest.yml**：task 显式注明「此属 CI workflow 改动，须在 PR 描述与 30 invoke 显式注明」（范围 F4 · TC-RC-5），且留维护者签闸改判「不接」的出口。合规。
3. **pytest 硬闸「CI 绿 + 本地红集 ⊆ 基线 19 零新增」**：基线 19 红集逐名清单已留档 10 invoke §四，可机断对拍；FP-6 含环境抖动甄别路径。合理。
4. **N818 默认 noqa 不改名**：亲核 `CircuitOpen` 为 app 公开异常，重命名=API 语义变更，归非范围并留「另立 task」出口。合理。
5. **E402 有意布局互证**：:63-64 注释 + :66 既有 noqa 旁证成立，裁定路径（noqa+理由 或 上移 · FP-4 破约改回）闭合。

## 思考轮审查（阶段 C）

- 控制表 R0–R5 六轮齐备，`actual_last_round=R5（early_stop）`，理由「基线全部亲跑量化，F1–F5 边界闭合，再轮无新信息」成立（20 复核实证 indeed 齐备）。
- 回填闭合：R0 框定 / R1 证据 / R2 方案 / R3 反例 / R4 验收 / R5 收口各节均在正文展开，无空槽。
- residual_risks 如实（闸未签 · F811 发散停派 · format 大 diff · F3/F4 待签闸确认），无隐瞒。
- **思考轮审查通过**。

## failure_paths 复核

FP-1 闸拒开工 · FP-2 语义可疑剔出 · FP-3 F811 意图不明停派上抛 · FP-4 E402 误判改回 · FP-5 format 破约回退明裁 · FP-6 本地新增红甄别 · FP-7 CI 版本漂移修正（见 nit N1 措辞张力）· FP-8 配置另立 task——八条覆盖主要风险面，均可重试、留痕点明确。

## 回填清单

零项（无内容阻塞 · 无需 task 回填；nit N1 为顺手修性质，不改签收结论）。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT、HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] 签闸时确认 F3 收口形态（默认：一次性 format 独立 commit）与 F4 接闸与否（默认：接 pytest.yml · uv.lock 钉版同源 · PR 注明 CI 改动；可参考 nit N1 钉死 `ruff==0.15.21`）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
