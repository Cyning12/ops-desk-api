# Task：融合权重调参循环（tuning loop · 收敛判据驱动）

> **状态**：`done`（2026-09-21 闭环：三闸 approved · 30 调参循环**达标停止**（R2/R3 连续两轮 top3=1.0 · 定稿 90d/0.3/0.8 · top1=0.9167）· 40 独立核验 PASS（8/8 · 藏丑核查通过）· 代码在 `task/memory-fusion-weight-tuning`（worktree）· **PR 待开**）  
> **类型**：调参 / 记忆轨（执行 SPEC-memory-golden-eval §2 D3「改值另 task 按报告裁决」）  
> **上游**：`docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md`（signed）· live 重跑报告 `reports/memory_golden_eval_20260921_post_tzfix.yaml`（top3=0.75 · 扫参推荐 90d/0.3/0.8 达内部线）  
> **分支**：`task/memory-fusion-weight-tuning`（base：`task/memory-golden-eval` 叠放 · #146 合并后 PR 改指 master · **worktree `../ops-desk-api-wtune`**）  
> **00 注**：2026-09-21 · 维护者令「同意安排 · task 改为循环任务 · 改一次跑一次 · 调整到结果超过 3 次变化不大或达到目标位置」（同模式授权延续：00 代录闸 · 30/40 子 Agent）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-fusion-weight-tuning` |
| **git_branch** | `task/memory-fusion-weight-tuning` |
| **implement_repo** | `ops-desk-api`（**worktree `../ops-desk-api-wtune`** · 主检出被 llm-layer-hardening 占用） |
| **test_strategy** | `required` |
| **test_strategy_note** | CI：fake 红线/单测全绿（常量改动受影响的排序期望须如实更新并注明依据）；live：调参循环每轮全真跑（tenant=memory-eval · 跑后清场）· 调参日志逐轮落盘 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（`memory` 行备注：权重经调参循环定稿） |
| **graph_delta_note** | 不新增模块 · 00 代录签行 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 依据=SPEC D3 + live 报告 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 00 代录 → 30（**循环执行**）→ 40 → CLOSE → 维护者裁决开向量开关 |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-21 维护者令循环任务 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-21 维护者令循环任务（同模式授权）· 00 代录（20 R1 终轮零阻塞） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-21 同上 · 00 代录 · `01_modules.md` memory 行备注 + 人签记录已落 |

---

## 背景与目标

live 重跑（tz 修复后）：复述 top3=0.75（门槛 ≥0.8 差 0.05）· top1=0.08（干扰项霸榜）；扫参方向性证据：半衰期偏短、sim_floor 偏高在误杀"老而相关"的事实；推荐组合（90d/0.3/0.8）在 12+3 条小样本上 1.0/1.0/1.0 达内部线。

**一句话目标**：用**调参循环**把融合权重定稿——每轮「调常量 → 全量 live → 记录 → 决策下一轮」，直到**达标**或**收敛**，交付一次常量改动 + 完整调参日志 + 确认轮报告。**不是每次改权重起一个 task**。

---

## 循环协议（钉死 · 30 必须逐轮留痕）

### 每轮动作

1. 定本轮参数（首轮 = 扫参推荐 `(half_life=90, sim_floor=0.3, swe=0.8)` · 后续轮由上一轮数据 + 扫参聚合方向决定）
2. 改 `service.py` 常量（**只允许改三个常量值**）
3. 全量 live：`run_eval.py --backend live --golden evals/memory/golden_v1.yaml --sweep`（tenant=memory-eval · 跑后确认清场 0 残留）
4. 调参日志追加一轮：`{round, params, paraphrase_top1, paraphrase_top3, recency_top1（sweep 内）, errors, 决策与依据}`

### 停止条件（任一命中即停）

| 条件 | 判据 | 收尾 |
|---|---|---|
| **达标** | **连续 2 轮**全量 live `paraphrase_top3 ≥ 0.8`（防单次运气） | 以第 2 轮参数为定稿 |
| **收敛** | 连续 3 轮 `top3` 变化 |Δ| ≤ 0.05 且 `top1` |Δ| ≤ 0.05 且无上升趋势 | 如实收尾：最佳组合 + **未达标结论**（不粉饰） |
| **上限** | 8 轮全量 live（成本控制 · 每轮 ~50 用例真实调用） | 同收敛收尾 |
| **异常** | 任一轮 `errors > 0`（环境/回归异常） | 立即停 · 查明并报告 · 不得带病继续 |

### 防过拟合纪律

- 确认轮（定稿参数的最后一轮）必须是**完整 50 用例全量跑**，不接受只用 sweep 场景分当裁决分
- 调参日志如实记录每一轮（含变差轮）· 40 核验「不许藏丑」
- 金样只有 12 复述 + 3 时效场景：报告必须写明样本量限制（继承 SPEC residual）

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **可改范围** | 仅 `HALF_LIFE_DAYS` / `SIM_FLOOR` / `SOURCE_WEIGHT_EXTRACTED` 三个常量**值**；融合算法结构/公式零改 |
| **目标位置** | 全量 live `paraphrase_top3 ≥ 0.8`（SPEC D5 锁 · 连续 2 轮确认） |
| **抽取指标** | precision/噪声/supersede 本轮**不要求达标**（那是抽取校准 task 的事）· 但必须逐轮记录不得藏丑 |
| **测试维护** | 常量改动使既有 fake 测试排序期望失效时：**如实更新期望 + 注记依据**（禁止为过测试改语义） |
| **环境** | 每轮跑前剥全部代理 env；tenant=memory-eval；每轮跑后核验清场 0 残留 |
| **零越面** | `now_utc`/模型/migration/conftest/闸/状态机/注入块 零 diff |
| **诚实路径** | 收敛/上限停止但未达标 → 报告如实给「未达标 + 最佳组合 + 后续建议」· 禁止硬凑 |

---

## 范围

- [x] **W1 · 循环执行**：按循环协议跑到达标/收敛/上限 · 调参日志 `evals/memory/tuning_log_20260921.md`（或 yaml）逐轮留痕
- [x] **W2 · 常量定稿**：`service.py` 三常量改最终值（一次 commit 的代码改动）
- [x] **W3 · 确认轮报告**：定稿参数全量 50 用例报告 `reports/memory_golden_eval_tuned_20260921.yaml`（头部四门槛达成如实写）
- [x] **W4 · 测试与文档**：受影响 fake 测试期望如实更新 + README 权重表更新 + `memory` 行图谱备注

### 非范围

- 抽取 prompt/key 校准（另 task）；金样扩样（另议 · 防过拟合的正面解）；改融合算法结构
- 开生产开关（维护者 env 动作 · 本 task 只交裁决依据）；embedding 回填；画像
- `now_utc`/模型/migration/conftest 改动

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` / `HG-GRAPH-MODULES` pending 即 30 | **拒开工** | 是 | 是 |
| 任一轮 errors>0 | 立即停循环 · 查明报告 | 是 | 是（报告） |
| 用 sweep 场景分冒充全量裁决分 | 40 拒收（确认轮必须全量 50） | 是 | 否 |
| 8 轮后未达标却宣称达标 | 40 拒收（诚实路径） | 是 | 否 |
| 为让 fake 测试过而改测试语义 | 审查拒收（只许更新期望+注记） | 是 | 否 |
| 改三个常量以外的生产代码 | 审查拒收（零越面契约） | 是 | 否 |
| 清场失败残留 | 停止并报告 · 人工核查 dev 库 | 是 | 否 |

---

## 验收标准

- [x] 人工闸：`HG-AUDIT-R1` · `HG-GRAPH-MODULES` approved 后方可勾选下列码项
- [x] W1：调参日志逐轮齐（≥2 轮 · 每轮含 params/三指标/errors/决策依据）· 停止条件命中记录
- [x] W2：`service.py` 仅三常量值 diff
- [x] W3：确认轮全量报告落盘 · `paraphrase_top3 ≥ 0.8`（或如实的未达标结论）
- [x] W4：fake 测试全绿（期望更新处注记依据）· README 权重表 · 图谱 `memory` 行备注
- [x] **旧测 grep 影响面**：memory 系 6 测试文件（P0 34 + P1 22 + golden 10 + tz 18 基线全绿 · 排序期望更新必须逐处注记）
- [x] `ruff` 触及路径绿；`pytest` 本波 + memory 全量回归绿
- [x] `npx spec-wave task lint --file docs/tasks/active/task_memory_fusion_weight_tuning.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md`（§2 D3 改值裁决条款） |
| 数据基础 | `reports/memory_golden_eval_20260921_post_tzfix.yaml`（top3=0.75 · 扫参 27 组） |
| tz 修复 | PR #147 merged（`eb8e718`） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md` · 2. 本 task（循环协议 · 停止条件 · 诚实路径）· 3. SPEC §2 D3/D5 · 4. `reports/memory_golden_eval_20260921_post_tzfix.yaml`（扫参聚合 reasons）· 5. `docs/standards/CODING_BACKEND_L2_v1_zh.md` · 6. `app/ops/memory/service.py`（三常量与 `_fuse_recall`）· 7. `FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 循环调参 · 维护者钦定循环形态 | no | — | none |
| R1 | 范围=日志+定稿+确认轮+测试文档；非范围=抽取/扩样/开开关 | no | — | 无 |
| R2 | 循环协议钉死（首轮=扫参推荐 · 三停则 · 防过拟合两条） | no | — | 无 |
| R3 | 诚实路径：收敛未达标如实 · sweep 分不冒充全量分 | no | — | 无 |
| R4 | 验收锚定确认轮全量报告；fake 期望更新须注记 | no | — | 金样 15 场景小样本（继承 SPEC residual ①②） |
| R5 | 可交 20 | no | — | 单 goldenset 调参的过拟合残余（扩样另议） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定
D3 早有"改值另 task"条款；维护者新要求是把"另 task"从单次改成循环——本 task 的核心设计就是把循环协议本身钉死成可验收物。

### R1 · 范围
循环+定稿+确认轮+测试文档同 task；一切不属于权重的事（抽取/扩样/开开关）排除。

### R2 · 循环协议
首轮用扫参推荐（有数据背书）；三停则覆盖达标/收敛/上限/异常；防过拟合两条（全量确认轮 + 逐轮留痕）。

### R3 · 诚实路径
调参类工作最大的恶是"调到过为止再编故事"——停止条件、藏丑禁令、sweep 分与全量分的区分全部钉死。

### R4 · 可测性
验收锚在确认轮全量报告与调参日志完整性；fake 测试期望更新必须注记依据（防止为绿而绿）。

### R5 · 交接就绪
可交 20；过拟合残余风险如实继承（正面解=金样扩样 · 另议）。

---

### 自检结论（执行者）

> **hat 40** · 2026-09-21 · **40 PASS**（独立核验 · 不复信 30 · 全部亲跑亲读）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| ruff check service.py + 3 测试 + evals/memory/ | 0 | All checks passed |
| pytest memory 8 文件 -q --tb=short | 0 | 117 passed |
| pytest tests -q --tb=short（全量） | 1 | 1117 passed / 1 skipped / 2 failed（chat_ws×2 既有环境失败 · 无新增） |
| diff tuning_round_3.yaml vs tuned 报告 | 0 | IDENTICAL（确认轮复制关系属实 · run id 相同） |
| git merge-base --is-ancestor eb8e718 HEAD | 0 | 是（restack 正确 · tz 修复在场） |
| 清场核验 SELECT count(*) tenant=memory-eval | 0 | 0 行残留 |
| npx spec-wave task lint | 0 | LINT: PASS |

**验收摘要**：8/8 全 ✅。达标停止属实——R2/R3 连续两轮全量 live top3=1.0（确认轮=完整 50 用例 · 分母 12 复述用例 · 非 sweep 场景分）；定稿 90/0.3/0.8 · service.py 仅 2 常量行 diff（swe 本即 0.8）；**藏丑核查通过**：R3 变差项（noise 0.2857→0.3571 · supersede 0.4→0.3 · precision 0.2286→0.2059）与三项抽取 NOT-MET 全部如实记录；3 处测试期望更新带注记且反向 patch（7d/0.7/1.0）抑制性经独立演算成立（target 0.5^(90/7)≈1.35e-4 << 0.7）；R1 异常轮（叠放 base 缺 tz 修复）经 00 restack（077f500）解除 · 协议异常分支实战验证有效。

**已知未测项**：① live 轮次 40 未重跑（成本控制 · 核验基于报告内部一致性+日志交叉+DB 清场实证）；② 复述金样 12 例小样本过拟合残余（继承 SPEC residual · 扩样另议）；③ chat_ws×2 既有 DB 环境失败（与本 diff 无因果）。

**结论**：**40 PASS** · 可进 PR 流程 · 开向量开关属维护者 env 动作（本 task 交裁决依据）

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 10-task 落稿（循环任务 · 三停则 + 防过拟合纪律）· HG-AUDIT-R1/HG-GRAPH-MODULES pending → 30 拒开工 |
| 2026-09-21 | 20 R1 终轮零阻塞签收 · 00 代录两闸 · 30 开工 |
| 2026-09-21 | R1 异常停（base 缺 tz 修复）→ 00 restack 077f500 → R2/R3 连续 top3=1.0 达标停止 · 定稿 90/0.3/0.8 → 40 PASS（8/8）→ 00 回写 · 归档 done · CLOSE |
