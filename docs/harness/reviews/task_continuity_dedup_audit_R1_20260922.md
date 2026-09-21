# Task 书面审查：continuity-dedup（R1 · 20-task-audit）

> **审查帽**：20-task-audit（Harness V2 · 书面审 task，不改实质内容，不代签人闸）
> **审查日期**：2026-09-22
> **task**：`docs/tasks/active/task_continuity_dedup.md`（draft · 2026-09-22 10-task 落稿）
> **对照 SPEC**：`docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-21 · commit d0152e4/8fdd859 本帽 git log 复核在）
> **分支核验**：`git branch --show-current` = `task/continuity-dedup` ✅（审查全程未切分支 · 未 push）

---

## 一、结论摘要

| 维度 | 结论 |
|------|------|
| **内容审查** | **PASS（零阻塞 · 无须返工项）**：范围/非范围/验收断言化/failure_paths/R0–R5/闸表 与 SPEC 逐项核对一致；B1 十七处命中清单本帽复跑口径全数属实；变异检验三条可执行；SPEC 措辞偏差（sse_replay 用例数）留痕如实 |
| **流程闸** | **HG-AUDIT-R1 = pending**（blocks 30 · 待维护者/授权 00 代录签收）；HG-GRAPH-MODULES=approved 经本帽**亲读** `docs/_tech_graph/l1/01_modules.md` 复核成立；HG-TASK-DRAFT=pending；HG-PILOT-OPSDESK-GLAYER=n/a |
| **回炉 10-task** | 无 |
| **非阻塞备注** | 3 条（见第四节），均不阻塞签闸 |

**结论**：PASS。task 内容可交维护者签 HG-AUDIT-R1；pending 期间 30 拒开工，本审查文**不附 30 Prompt**。

---

## 二、核对项结果（逐项）

### 2.1 SPEC 对照（范围 / 非范围 / 验收 / failure_paths / 闸表）

| # | 核对项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 范围 D1–D3 与 SPEC §2 一致 | ✅ | task §范围 D1（删 `session/continuity.py` + `__init__.py` 同步 + 真源零改动 + 零新边）/ D2（测试收敛删 2 留 2 + 对账表）/ D3（图谱零变更按实判 + graph-compile 绿 + 历史快照不回改）逐块映射 SPEC §2 D1–D3；竖切结论（同 task 一次提交 · 纯删除无先行切分）承 SPEC §8 |
| 2 | 非范围与 SPEC §3 一致 | ✅ | 9 条全保留（压缩语义/占位符 · 真摘要 · 真源本体 · session 其余文件 · chat 清理 · 仓外兼容 · 历史文档回改 · 表结构 · web/ios），逐条比对无漏无改义 |
| 3 | 验收断言化：真源零 diff | ✅ | task D1 项 `git diff master -- app/ops/lg_rag/continuity.py` 输出为空 = SPEC §6-D1 逐字级一致；failure_paths 末区「误改真源」行配套兜底 |
| 4 | 验收断言化：grep 零残留 | ✅ | 三 pattern（`session.continuity` / `session/continuity` / `ops\.session import compress_window`）与 SPEC §6-D1 一致，docs 历史快照除外口径保留 |
| 5 | 验收断言化：用例数差值 == 2 | ✅ | 1178 → 1176 collected；基线 1178 本帽真跑复核一致（`pytest tests --collect-only -q` = **1178 tests collected**，exit 0） |
| 6 | 验收断言化：变异检验 ×3 | ✅ | ① 删真源函数 → lg_rag 侧 import 即失败；② 忘改 `__init__` → `test_session_continuity.py` 必 ModuleNotFoundError；③ 摘 try/except → `test_compress_window_failure_truncates_tail` 必挂。操作具体、预期明确、与 failure_paths「无变异检验却宣称收敛有效 → 拒收」闭环 = SPEC §6-变异检验一致 |
| 7 | failure_paths | ✅ | task 12 条 = SPEC §5 九条全收（re-export 假设性循环行并入「30 擅自走 S2 → 回炉」行 · R3 声明与表实一致）+ 过程三条（闸拒开工 / 无变异检验拒收 / B1 未落盘拒收） |
| 8 | R0–R5 思考轮 | ✅ | 控制表 6 行齐（R0–R5），actual_last_round=R5 · early_stop=no · residual_risks 三条继承 SPEC §7 并标明「签收知悉」；各轮子节（问题框定/开工闸/竖切/失败语义/可测性/交接就绪）有实质结论非空转 |
| 9 | graph_change_layer / 图谱裁定 | ✅ | `graph_change_layer=无` + `graph_delta_note` 含**回炉补闸条款**（30 偏离零变更预判/改走 S2 re-export/新增依赖边/端点/表/事件类型 → 退 10-spec 修订 SPEC + 补 HG-GRAPH-MODULES + 图谱如实登记，不得沿用本裁定）；同条款另见于闸表行、验收人工闸行、工程项、R1 子节，共 5 处钉死；与 SPEC §2 D3 裁定一致 |
| 10 | review_hat / test_strategy | ✅ | `review_hat=20` · `test_strategy=required` + note 与 SPEC 元信息一致（note 中 sse_replay 用例数按实测写 2 · 见 2.3 留痕核对） |
| 11 | 闸表：HG-AUDIT-R1 必须 pending | ✅ | 闸表行 `HG-AUDIT-R1 | pending | 30`，task 状态行同步声明「30 拒开工」，failure_paths 首行兜底；本帽不签 |
| 12 | 闸表：HG-GRAPH-MODULES 亲读复核 | ✅ | 本帽亲读 `docs/_tech_graph/l1/01_modules.md`：chat 行（:22）路径 glob `app/ops/chat/** · app/ops/session/**` 在表、出边 `llm, db, rag` **无 lg_rag**（S2 re-export 必污染拓扑的图谱依据成立）、410 下线裁定在（:22）；签录链完整（:57-66 含多条 approved 记录）。task 闸表说明与图谱真值**一致**，零图谱变更裁定成立 |

### 2.2 B1 旧测影响面 17 条抽查（本帽独立 grep 复核）

复跑扫描口径 `grep -oE 'compress_window|continuity|ops\.session' tests/test_session_continuity.py tests/test_lg_rag_session_continuity.py` = **17 命中（8 + 9）**，与 B1 声明逐字吻合。

| B1# | 抽查内容 | 复核结果 |
|-----|----------|----------|
| 1 | `tests/test_session_continuity.py:5` import · occ=3 | ✅ :5 行 `from app.ops.session.continuity import compress_window` 在，单 ops.session + continuity + compress_window = 3 occ 吻合 |
| 3 | `:13` `test_compress_window_keeps_tail_full` · `:18` 调用行 | ✅ 行号吻合（`:18` `out = compress_window(turns, max_full_turns=4, group_size=2)` 参数与对账表一致） |
| 8 | `tests/test_lg_rag_session_continuity.py:23` 依赖方向闸 | ✅ `forbidden = ("app.ops.chat", "app.ops.session")` 在 :23；方向闸语义描述（只扫 lg_rag→session/chat · 不拦反向）与 failure_paths S2 行互洽 |
| 13 | `:81` `test_compress_window_failure_truncates_tail` · `:84` 同参数调用行 | ✅ 行号吻合；差异①守护与变异检验③对象一致 |
| 16 | 辅扫禁令注释/断言四处 | ✅ `prompts/packs.py:9` · `progress_stream.py:12` · `answer_stream.py:18` · `test_prompt_packs.py:211` 本帽全仓 grep 复核四处全在，且除此之外生产零消费者（命中仅 `__init__.py` 自身与上述注释/断言） |
| 17 | 动态 import 面辅扫 | ✅ 本帽复扫 `importlib|__import__|import_string` 全仓 `*.py`：命中为 models.py uuid 工厂等，均与 continuity 无关 |

**B1 裁定**：17 条为实扫所得，抽查 6 组（覆盖主扫 #1-#14 的代表行与辅扫 #15-#17 全类）全数属实；处置三态（回归×11 / 删除×6 / 改编×0）定义清晰，「真源与生产路径零改动 → 回归与删除为主、无改编」的裁定与钉死契约/非范围一致。

### 2.3 SPEC 措辞偏差留痕核对（sse_replay 用例数）

SPEC §1/§2/§5 表述「sse_replay 四用例（:30-45）」；本帽亲读 `tests/test_session_continuity.py`：全文件 **4 个 test 函数** = compress_window 2 个（`:13` · `:25`）+ sse_replay **2 个**（`test_replay_events_after_seq` `:30` · `test_replay_cursor_and_payload` `:40`）。task R0/锚点表/test_strategy_note 按实测如实写「两用例」并留痕 SPEC 措辞偏差（范围语义零影响：删 2 留 2 · 差值==2 断言不受影响 · 不改 SPEC · 若修措辞走 10-spec 修订轨）。**留痕属实，处置得当**。

### 2.4 锚点真实性（现状锚点表抽核）

`app/ops/session/continuity.py` 36 行（`:9-10` 字面量 6/2 · `:32` `sorted(roles)` 裸排序）· `app/ops/lg_rag/continuity.py` 244 行（`:23-24` 模块常量 · `:38-62` 整体 try/except · `:54` `sorted(str(r) for r in roles)`）· `app/ops/session/__init__.py:3` import + `:8` `__all__` 中 `"compress_window"` · 图谱登记 grep `continuity` 仅 lg_rag 侧（`10_flow_lg_rag.graph.yaml` + l2 indexes）· `session/continuity.py` 图谱零登记 —— 本帽逐点 grep/sed 复核**全部在且行号吻合**。

---

## 三、阻塞项（回炉 10-task）

**无。** 内容零阻塞；流程闸 pending 属正常待签状态，非内容回炉。

---

## 四、非阻塞备注（不阻签闸 · 供维护者与下游知悉）

1. **20 invoke 快照**：task `required_invoke_hats=10,20,30,40` 含 20，按 Harness 惯例 20 过程 invoke 快照须落 `docs/harness/invokes/by-task/continuity-dedup/`（当前仅 10 快照在）。本次维护者指令限定「只写 reviews/ 下审查文」，本审查文即 R1 书面真值；若需严格对齐 invoke 留痕，维护者可令 00 在签闸时一并补录 20 invoke 摘要（指向本文件即可）。
2. **验收 17 条 vs SPEC §6 十五条**：task 多出「人工闸行」与「工程 · 闸前置 B1」两条，属过程化落地增补（task R5 已声明实质差异为零），非范围偏差，无需 SPEC 回炉。
3. **sse_replay 措辞偏差**：SPEC「四用例」与实测 2 个 test 函数不符，task 已如实留痕（见 2.3）；维护者若拟修订 SPEC 措辞，走 10-spec 修订轨，与本 task 签闸互不阻塞。

---

## 五、回填清单

无（零阻塞，无回炉回填项）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文件：内容 PASS 零阻塞）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期；或依本窗授权由 00 代录并留痕）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | 20-task-audit R1：对照 SPEC（signed · commit d0152e4/8fdd859 复核在）逐项核对 12 项全过 · B1 十七处复跑口径 17（8+9）吻合 · 抽 6 组全属实 · 锚点全核在 · pytest 基线 1178 真跑复核一致 · sse_replay 用例数留痕属实 · HG-GRAPH-MODULES 亲读 `01_modules.md` 复核成立 · 内容零阻塞 · HG-AUDIT-R1 仍 pending → 附维护者签闸清单，不附 30 Prompt |
