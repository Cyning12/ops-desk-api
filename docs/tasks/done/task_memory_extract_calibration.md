# Task：记忆抽取校准循环（prompt/key 约定 · 校准循环）

> **状态**：`done`（2026-09-22 闭环：三闸 approved · 30 校准循环 5 轮（v3 经 40 R1 泄题判定作废 → v4 整改 · R4/R5 连续两轮四门槛全达）· 40 R2 PASS（8/8）· 代码在 `task/memory-extract-calibration`（worktree）· **PR 待开**）  
> **类型**：校准 / 记忆轨（执行 SPEC-memory-golden-eval §2 D5「不达标 → prompt 迭代另 task」条款）  
> **上游**：`docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md`（signed · D5 门槛）· live 报告 `reports/memory_golden_eval_tuned_20260921.yaml`（precision 0.21 · noise 0.36 · supersede 0.3 · 三轮 NOT-MET）  
> **分支**：`task/memory-extract-calibration`（base：`origin/master` 07b0eba · **worktree `../ops-desk-api-excal`** · 主检出被 multi-replica-verify 占用）  
> **00 注**：2026-09-22 · 维护者令「已合并，继续回到刚才的150结束后的任务」+ 循环任务模式确立（同模式授权延续：00 代录闸 · 30/40 子 Agent）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-extract-calibration` |
| **git_branch** | `task/memory-extract-calibration` |
| **implement_repo** | `ops-desk-api`（**worktree `../ops-desk-api-excal`**） |
| **test_strategy** | `required` |
| **test_strategy_note** | CI：fake 抽取红线全绿（prompt 内容变化不得破坏罐头通路 · 版本 bump 断言若存在须同步）；live：校准循环每轮全真跑（tenant=memory-eval · 跑后清场核验）· 校准日志逐轮落盘 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（`memory` 行备注：抽取校准循环） |
| **graph_delta_note** | 不新增模块 · 00 代录签行 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 依据=SPEC D5 + live 报告 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 00 代录 → 30（**循环执行**）→ 40 → CLOSE → 维护者裁决开抽取开关 |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-22 维护者令继续 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-22 维护者令继续（同模式授权）· 00 代录（20 R1 终轮零阻塞） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-22 同上 · 00 代录 · `01_modules.md` memory 行备注 + 人签记录已落 |

---

## 背景与目标

权重定稿后 live（tuned 报告）：向量召回达标（top3=1.0 连续两轮）· **抽取侧三指标三轮全 NOT-MET**：precision 0.21–0.26 · noise 0.29–0.36 · miss 0.64–0.71 · supersede 0.2–0.4。已定位两大病：

1. **key 漂移**：prompt 示例教 `project.primary_repo` 风格，金样 supersede 约定锚在 `deploy.target` 等——LLM 自由发挥出 `project.deploy_target` → 同义不同 key → supersede 失效（旧值不失效 · 双值并存）。
2. **准入过松**：闸只拦格式（volatile 前缀/空值/超长），语义噪声（一次性事件/通用知识/他人事实）全靠 prompt 自觉——live 显示 prompt 自觉不够（noise 0.36）。

**一句话目标**：校准循环把抽取三指标调到门槛——每轮「改 prompt 资产（版本 bump）→ 全量 live → 日志 → 决策」，直到达标或收敛。交付 = 定稿 prompt + 校准日志 + 确认轮报告。

---

## 循环协议（钉死 · 承 weight-tuning 形态）

### 每轮动作

1. 定本轮改动（依据上一轮报告的**逐条失败 detail**——报告里每条用例有 written/expect 对照，先看数据再动笔）
2. 改可改面（见钉死契约）；**prompt 内容每轮变更必须 bump asset version**（v1→v2→… · 日志记 version↔指标对应 · 版本加在模型看得见的那一层）
3. 全量 live：`run_eval.py --backend live --golden evals/memory/golden_v1.yaml --out reports/extract_calib_round_<N>.yaml`
4. 校准日志 `evals/memory/extract_calib_log_20260922.md` 追加一轮：round / prompt version / 改动摘要 / precision / noise / miss / supersede / paraphrase_top3（回归哨兵）/ errors / 决策与依据
5. 清场核验：`SELECT count(*) ... tenant_id='memory-eval'` = 0

### 停止条件（任一命中即停）

| 条件 | 判据 | 收尾 |
|---|---|---|
| **达标** | **连续 2 轮**全量 live 三指标同达：precision ≥ 0.9 · noise ≤ 0.1 · supersede = 1.0（且 paraphrase_top3 ≥ 0.8 回归哨兵不破） | 以第 2 轮 prompt 定稿 |
| **收敛** | 连续 3 轮 precision |Δ| ≤ 0.05 且无上升趋势 | 如实收尾：最佳版本 + **未达标结论** + 下一步建议（不粉饰） |
| **上限** | 8 轮全量 live | 同收敛收尾 |
| **异常** | 任一轮 errors > 0 | 立即停 · 查明报告 · 不带病继续 |

### 防过拟合纪律（承前 · 加强）

- 确认轮必须全量 50；逐轮留痕含变差轮；报告写样本量限制
- **金样 `golden_v1.yaml` 一字不改**（它是契约锚 · 改金样=移动球门 · 40 拒收）
- prompt 里可以加金样同域的 few-shot 示例，但**禁止直接把金样用例原文抄进 prompt**（那是泄题 · 40 拒收）

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **可改面** | ① `app/ops/prompts/assets/memory.extract.system.md`（正文 + frontmatter version bump）② **可选**：`extract.py` 新增 key 别名归一表（仅当数据显示漂移持续 · 一个小映射常量 · 须注记依据） |
| **不可改** | golden_v1.yaml / 闸判据 / 抽取管道结构（structured_output · 重试 · 超时）/ 融合与召回 / service.py / 开关默认值（保持 false） |
| **version 纪律** | 每轮内容变更 bump version；日志记 version↔指标；报告能看出命中哪版 |
| **回归哨兵** | 向量侧 top3 ≥ 0.8 不许被校准弄坏（prompt 改动不应影响 · 但每轮必看） |
| **环境** | 每轮跑前剥全部代理 env；tenant=memory-eval；每轮清场核验 0 残留 |
| **诚实路径** | 收敛/上限未达标 → 如实报告 + 建议（如 key 别名单独成 task）· 禁止硬凑 |
| **零越面** | gate/service/continuity/models/migration/conftest 零 diff；禁止 commit |

---

## 范围

- [x] **C1 · 校准循环**：按协议跑到达标/收敛/上限 · 校准日志逐轮留痕（version↔指标对应）
- [x] **C2 · 定稿**：prompt 资产定稿版（version bump 链完整）· 可选 key 别名表（若启用须注记依据）
- [x] **C3 · 确认轮报告**：`reports/memory_extract_calibrated_20260922.yaml`（全量 50 · 头部四门槛如实）
- [x] **C4 · 测试与文档**：prompt 版本相关断言同步（若存在）· `evals/memory/README.md` 增校准日志指针 · 图谱 `memory` 行备注

### 非范围

- 改金样 / 闸 / 管道结构 / 融合 / 开关默认值；开生产抽取开关（维护者裁决 · 本 task 交依据）
- 画像 / 回填 / 摘要（并行窗口已做或另议）；向量权重（已定稿）
- 抽取精度要求的 prompt 大改版式重构（只许渐进迭代 · 版式重构另 task）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 闸 pending 即 30 | **拒开工** | 是 | 是 |
| 任一轮 errors>0 | 立即停 · 查明报告 | 是 | 是（报告） |
| 改金样移动球门 | 40 拒收（一字不改契约） | 是 | 否 |
| 金样原文抄进 prompt（泄题） | 40 拒收 | 是 | 否 |
| 改了 prompt 没 bump version | 40 拒收（归因断链） | 是 | 否 |
| 收敛未达标却宣称达标 | 40 拒收（诚实路径） | 是 | 否 |
| 校准弄坏向量回归哨兵 | 停 · 回退该轮改动 · 报告 | 是 | 否 |
| 清场残留 | 停 · 人工核查 dev 库 | 是 | 否 |

---

## 验收标准

- [x] 人工闸：`HG-AUDIT-R1` · `HG-GRAPH-MODULES` approved 后方可勾选下列码项
- [x] C1：校准日志逐轮齐（≥2 轮 · version↔指标对应 · 每轮三指标+哨兵+errors+决策依据）· 停止条件命中记录
- [x] C2：定稿 prompt version 链完整；若启用别名表：映射常量 + 注记依据
- [x] C3：确认轮报告落盘 · 三指标达标（或如实的未达标结论 + 建议）
- [x] C4：fake 测试全绿（版本断言同步）· README 指针 · 图谱备注
- [x] **旧测 grep 影响面**：memory 系 + prompts 系测试全绿；`render("memory.extract.system")` 调用方仅 extract.py（30 复核）
- [x] `ruff` 触及路径绿；`pytest` 本波 + memory + prompts 回归绿
- [x] `npx spec-wave task lint --file docs/tasks/active/task_memory_extract_calibration.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md`（D5 门槛 + 「不达标另 task」条款） |
| 数据基础 | `reports/memory_golden_eval_tuned_20260921.yaml` + tuning 三轮报告（抽取侧逐轮数据） |
| prompt 资产化 | PR #155（merged · `memory.extract.system` 资产形态 · version 字段） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md` · 2. 本 task（循环协议 · 可改面/不可改面 · 防泄题）· 3. SPEC §2 D5 · 4. `reports/memory_golden_eval_tuned_20260921.yaml`（逐条失败 detail 是第一轮依据）· 5. `app/ops/prompts/assets/memory.extract.system.md` + `app/ops/memory/extract.py` · 6. `docs/standards/CODING_BACKEND_L2_v1_zh.md` · 7. `FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 校准循环 · 承 weight-tuning 形态 · 维护者令继续 | no | — | none |
| R1 | 可改面=prompt 资产+可选别名表；金样/闸/管道不可改 | no | — | 无 |
| R2 | 循环协议承前 + 加强两条（version bump 归因 · 防泄题） | no | — | 无 |
| R3 | 诚实路径与回归哨兵钉死 | no | — | 无 |
| R4 | 验收锚确认轮报告 + 日志 version 对应 | no | — | supersede=1.0 对自由生成 key 很硬 · 收敛未达标概率不低 |
| R5 | 可交 20 | no | — | 小样本过拟合残余（继承）· 别名表可能才是正解（首轮数据说了算） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定
向量侧已定稿达标；抽取侧三指标离门槛远且病灶已定位（key 漂移 + 准入过松）。本 task 是唯一挡在 `MEMORY_FACTS_EXTRACT_ENABLED` 前面的东西。

### R1 · 可改面钉死
prompt 资产是唯一一等可改面（已资产化 · 有 version 字段）；别名表留作数据驱动的备选（首轮若漂移收敛则不需要）；金样一字不改是循环可信度的根基。

### R2 · 循环协议
承 weight-tuning 已被实战验证的骨架，加两条校准特有纪律：version bump（归因）与防泄题（金样原文禁令）。

### R3 · 诚实路径
supersede=1.0 是硬门槛，很可能要别名表甚至多轮才够到——收敛收尾的「未达标+建议」路径必须提前钉死，免得 30 硬凑。

### R4 · 可测性
逐轮 version↔指标对应表是验收锚；回归哨兵（top3≥0.8）防校准波及向量侧。

### R5 · 交接就绪
可交 20；残余风险两条如实继承。

---

### 自检结论（执行者）

> **hat 40** · 2026-09-22 · **R1 FAIL（few-shot 泄题退回）→ 30 整改（v4 重写示例 + 报告 prompt_version + 日志补记）→ R2 PASS**

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| 防泄题人工比对（prompt × golden_v1 逐条） | — | R1 FAIL（v3：4/5 近义改写）→ R2 PASS（v4：4 条真·新文本 · 骨架/场景/主体均不同） |
| diff round_5 ↔ memory_extract_calibrated_20260922.yaml | 0 | IDENTICAL · cases=50 · 四门槛 met · prompt_version: v4 在场 |
| diff 作废轮 R2 vs R5 逐条 verdict+detail（50 条） | 0 | IDENTICAL（干净 prompt 复现 · 泛化有效关键佐证） |
| git diff origin/master（金样+管道七件套） | 0 | 零 diff · extract.py 未动 · 开关默认 false |
| ruff check（触及路径） | 0 | All checks passed |
| pytest -k "memory or golden or prompt"（旗标显式 false+剥代理） | 0 | 351 passed |
| pytest tests（全量 · 同 env） | 1 | 1355 passed / 3 failed（chat_ws×2 + reconcile flake 既有基线 · 无新增） |
| 清场 SELECT count(*) tenant=memory-eval | 0 | 0 残留（每轮核验） |
| npx spec-wave task lint | 0 | LINT: PASS |

**验收摘要**：8/8 全 ✅。定稿 prompt **v4**（链 v1→v2→v3[40 作废]→v4 完整）；R4/R5 连续两轮全量 50 四门槛达标：precision 0.96 · noise 0.0714 · supersede 1.0 · paraphrase_top3 1.0（哨兵不破）· errors 0。别名表未启用（数据驱动判定）。NG09 残余如实注记。

**已知未测项 / 提请裁决知悉**：① 40 未重跑 live（四方交叉核对替代）；② run_eval.py 的 prompt_version 字段改动超出原 task 可改面（系 40 R1 退回项 B2 明令整改 · diff 仅头部字段级）；③ 样本量 50 · confidence=low 口径继承；④ chat_ws×2 与 reconcile flake 为既有基线红。

**结论**：**40 R2 PASS** · 可进 PR 流程 · 定稿 v4 可作为开 `MEMORY_FACTS_EXTRACT_ENABLED` 的裁决依据

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | 10-task 落稿（校准循环 · 承 weight-tuning 形态 + version bump/防泄题两条新纪律）· HG-AUDIT-R1/HG-GRAPH-MODULES pending → 30 拒开工 |
| 2026-09-22 | 20 R1 终轮零阻塞签收 · 00 代录两闸 · 30 开工 |
| 2026-09-22 | 30 循环 R1–R3「达标」→ 40 R1 FAIL（泄题 4/5）退回 → v4 整改 → R4/R5 连续两轮四门槛全达（干净 prompt 与作废轮逐位一致 = 泛化佐证）→ 40 R2 PASS（8/8）→ 00 回写 · 归档 done · CLOSE |
