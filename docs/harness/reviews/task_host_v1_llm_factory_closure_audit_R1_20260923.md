# 审查文：task_host_v1_llm_factory_closure · 20-task-audit R1（2026-09-23）

> **hat_id**：20-task-audit（R1 轮 · 书面审查 · 不改 task/SPEC 实质 · 不动 app/ · 不签发 human_gate）  
> **审查对象**：`docs/tasks/active/task_host_v1_llm_factory_closure.md`（draft · 2026-09-23 10-task 落稿）  
> **对照真值**：`docs/spec/host-v1-llm-factory-closure/SPEC-host-v1-llm-factory-closure_v0.md`（signed · Q1 llm 层单检查点 / Q2 只缓存 plan·参数 / Q3 固定文案模板档）  
> **种子/规划**：`docs/spec/agent-infra/08_host_v1_wave_spec_outlines_v0.md` §3（L112-149）· `07_host_v1_landing_plan_v0.md` §3 V1-C 行（L74）  
> **复核方式**：全部锚点本帽真读亲跑（2026-09-23 · 工作目录 ops-desk-api/）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS-WITH-NITS**——阻塞项为零；3 条非阻塞 nit（计数/锚点描述/标题映射措辞） |
| **流程闸 HG-AUDIT-R1** | **pending**（闸表 L40 如实 · 本审查不落 30 Prompt · 维护者签闸清单见文末） |

**总评**：task 草稿与 SPEC 实质差异为零；锚点全部真读复核一致；命名冲突扫零命中、pytest 基线 1420、B1 三态、diff 白名单覆盖全部改造对象——**前波 R1 审查未过教训项（钉死落点 vs 白名单一致性）本轮核验全过**。3 条 nit 均不动语义，可由 10-task 一笔修订或维护者签闸时知悉即可。

---

## 逐面证据（带行号）

### 1 · 闸表四行诚实（task L37-42）

| 闸 | task 记载 | 本帽复核 |
|----|-----------|----------|
| HG-TASK-DRAFT | approved · 00 代录 · 双令原话留痕 | 留痕在文（L39）· 与 SPEC 状态行（SPEC L4）同令源一致 ✓ |
| HG-AUDIT-R1 | **pending** · blocks 30 · 待本审查文落盘后 00 代录 | **pending 属实** ✓（本帽不代签） |
| HG-GRAPH-MODULES | approved · 真读 01_modules.md · llm 行在表 · 签录链至 2026-09-23 V1-A 回写行 | 真读复核：`docs/_tech_graph/l1/01_modules.md` L40 `llm` 行在表；签录链 L105 = 2026-09-23 V1-A（task_host_v1_delegation_token）00 代录行 ✓ |
| HG-PILOT-OPSDESK-GLAYER | n/a · 不涉物理分层试点改码 | 范围仅 app/llm + capability 先例只读，成立 ✓ |

### 2 · 代码锚点抽验（5 抽全过 · 本帽亲读）

| 锚点 | task 声称 | 复核结果 |
|------|-----------|----------|
| `app/llm/usage.py` | ContextVar run 上下文 · 无帧不落 · 不写 0 假账 · 落表故障不挡主答 | L44-46 ContextVar；L7-8「不写 0 假账」docstring；L142-153 异常→log+计数+False 不挡主答 ✓ |
| `app/llm/providers/base.py:136-152` | 末帧落账纪律 | L135-152 `_record_usage_safe`（解析失败/落表故障不挡主答 · 不写 0 假账）；末帧消费点 L105-112（见 usage meta 才落）✓ |
| `app/llm/model_catalog.py:118-177` | TASK_TYPES 五档 · 解析序 · 非法回退+warning（:157-167） | L118 五档（answer/grader/extract/structured/summary）；L122-131 TASK_TIER_MODELS；L144-177 resolve_task_model 解析序 explicit>env 档>rag_grader>档默认>default；L157-167 warning+回退不炸请求 ✓ |
| `app/ops/capability/fallback.py:23-38` | B1–B4 铁律 · ACTION_STATIC :81 | L25 B1 写能力永不降级 · L28 B2 显式标记 · L31 B3 链条有界（max_depth 默认 2 · ceiling 5 见 L88-89）· L34 B4 只有下游不可用才降级；L81 ACTION_STATIC ✓（task 钉死链长≤3 在 B3 ceiling 内，自洽） |
| `app/ops/capability/budget.py` | 进程内配额先例 | L51-56 dict+threading.Lock；L62 MAX_TRACKED_SESSIONS=512 有界；L65-73 `_int_env` 非法/负值回退默认（task 钉死「非法/负值回退 0」承此形态 ✓）；L22-27 + L246 进程内边界显式报出不假装全局 ✓ |
| `app/llm/factory.py` | 检查点接线面 | 全文 19 行 provider 注册表；complete/stream 统一入口实际在 base.py L31-52 `__init_subclass__` 包装——见 **N2** |

### 3 · 命名冲突扫与 pytest 基线（本帽真跑复核）

- grep `TASK_TIER_FALLBACKS|check_budget|infer_cache|BudgetVerdict|resolve_fallback_chain` 于 `app/` → **零命中** ✓（task L71 声称一致）
- `app/llm/` 目录真列：`__init__.py / factory.py / schema.py / circuit.py / retry.py / usage.py / model_catalog.py`——**无 budget.py · 无 infer_cache.py** ✓
- `.venv/bin/python -m pytest tests --collect-only -q` → **1420 tests collected** ✓（task L72/L162 基线数一致）

### 4 · SPEC 一致性（范围 / 非范围 / failure_paths / 验收）

- **范围**：task L95-100 D1–D6 逐块映射 SPEC §2 D1–D6（SPEC L60-98），无自加无缩水；实现序 D4→D1→D2→D3→D5→D6（task L32/L102）与 SPEC 依赖向（链声明是底座）自洽 ✓
- **非范围**：task L106 八条 = SPEC §3（L102-110）七条全收 + 「中途截断流」（即 SPEC L110 第七条）逐字对应，零遗漏 ✓
- **failure_paths**：task 11 条 = SPEC FP-1~FP-8（L143-150）翻四列全收（逐条核对：FP-1 预估偏差 L117 / FP-2 陈旧 plan L118 / FP-3 链末端 L119 / FP-4 灰度误伤 L120 / FP-5 重启归零 L121 / FP-6 缓存击穿 L122 / FP-7 缺单价 L123 / FP-8 成环过长 L124）+ 过程三（L114-116 闸前置/拒收×2）✓
- **Q1/Q2/Q3 锁死**：钉死契约表（task L82/L85/L86）与 SPEC §4 裁定逐字一致（单检查点 · 只缓存结构化产物终答不缓存 · `rule:<name>` 固定文案档）✓
- **图谱义务**：llm 行备注 + 人签新行 00 代录位 · 零新一级模块，与 08 §3 总览表（L16「llm 行备注 · 无新模块预判」）及 07 §3 V1-C 行（L74）一致 ✓
- **回炉补闸条款**（task L24）：偏离预判七触发列举完整（新模块/新表列/SSE 事件/路由/freeze/provider 契约/usage 末帧纪律），诚实 ✓

### 5 · 验收可执行性（防空真 · 分解式自加总核对）

实际 checkbox 清点：**人工闸 1（L130）+ D1×3（L134-136）+ D2×3（L140-142）+ D3×3（L146-148）+ D4×2（L152-153）+ D5×1（L157）+ D6×3（L161-163）= 16 条**，另变异检验 ×3（L167-169）。

- 每条均为否定性/可机验形态（断言 · grep 守护 · 迁移 diff 为空 · 基线零改动 · diff 白名单），无空真 ✓
- SPEC §6 十条全有落点：6-1→D1 · 6-2/3→D2 · 6-4→D3 · 6-5→D4 · 6-6→D5 · 6-7→D3「默认关零 diff」+D6 基线零改动 · 6-8→D6 L162 · 6-9→D6 L161 · 6-10→orchestration 行（L32 · 见 **N3**）✓
- 变异检验三条（标记摘除/版本入键摘除/检查点恒放行 → 必挂 → 恢复）符合「不验收空真」规则 ✓
- **分解式自加总发现计数不一致 → N1**

### 6 · B1 旧测影响面（行为变更类 task 必查 · checklist K7）

三态齐全：**回归×4（行 1-4）+ 新增×1（行 5）+ 迁移无×1（行 6）** ✓。扫描口径真跑复核：9 个命中测试文件全部存在（test_model_catalog / test_llm_routing / test_llm_usage / test_llm_usage_cache / test_llm_circuit / test_llm_retry / test_llm_providers / test_supervisor_budget / test_lg_rag_supervisor_capability_catalog）· 2+2+3+2=9 归并 4 组自洽 ✓。正交性声称（llm 层预算 vs supervisor 步预算）与 `capability/budget.py` L5-8 docstring（管的是工具调用次数非 token）互证 ✓。

### 7 · diff 白名单 vs 钉死落点一致性（**前波 FAIL 点 · 本轮重点**）

| 改造对象（依赖表 L195 / 钉死契约 L82-88） | 白名单（L163）覆盖 |
|---|---|
| `app/llm/budget.py`（新增） | ✓「llm/budget.py 新增」 |
| `app/llm/infer_cache.py`（新增） | ✓「llm/infer_cache.py 新增」 |
| `app/llm/model_catalog.py`（链+单价表） | ✓「llm/model_catalog.py（链+单价表）」 |
| `app/llm/factory.py`（接线） | ✓「llm/factory.py … 检查点/缓存接线」 |
| `app/llm/providers/base.py`（接线） | ✓「providers/base.py … 最小侵入」 |
| 测试 / 图谱 / 文档 | ✓ 显式列入 |

**白名单覆盖全部改造对象 · 零遗漏零多出** ✓。旁证：env 直读先例（capability/budget.py 用 os.environ · catalog 用 os.getenv）→ `app/config.py` 无需入白名单；degraded 标记可走 chunk meta dict → `schema.py` 零改成立；Q1 单检查点在 llm 层 → `app/ops/` 零改与白名单一致。

### 8 · 思考轮 R0–R5 充分性

控制表六轮齐全（L219-228）· `actual_last_round=R5` · `early_stop=no` · 无跳轮；各轮回填闭合（R0 框定 L230-232 / R1 闸 L234-236 / R2 竖切+继承 SPEC 三组裁定不重演 L238-240 / R3 失败语义+残余风险三条 L242-244 / R4 可测性 L246-248 / R5 交付判定 L250-252）；residual_risks 自 R3 携带至 R5 不丢 ✓。

---

## 阻塞清单（内容）

**无。**

## 非阻塞 nit（3 条 · 建议 10-task 一笔修订或维护者知悉）

- **N1 · 验收计数不自洽**：R4 行（L225）与自检结论（L256）称「验收 **15 条**」，但其括号分解（人工闸 1 / D1×3 / D2×3 / D3×3 / D4×2 / D5×1 / D6×3）自加总 = **16**，实际 checkbox 也是 16（另有变异检验 ×3）。建议改为「验收 16 条」或明确「码项 15 + 人工闸 1」。实际清单本身无歧义，不影响 30 执行。
- **N2 · 锚点描述微差**：L70 将 `factory.py` 标为「complete/stream 统一入口 · 检查点接线面」；真读 factory.py 仅 19 行 provider 注册表，统一入口实际在 `providers/base.py` L31-52 `__init_subclass__` 包装。白名单两文件均已覆盖，30 落地时接线大概率主落 base.py、factory.py 可能零 diff——建议 10-task 顺手把描述改准，避免 30 误读为「必须两个文件都改」。
- **N3 · D6 标题映射轻微过述**：L159「映射 SPEC §6-7/8/9/**10**」，但 SPEC §6-10（PR 经 CI 绿后 merge）未落实为验收 checkbox，仅由 orchestration 行（L32）覆盖。建议措辞「§6-7/8/9（§6-10 走 orchestration/40 棒）」。

## 观察（不要求处置）

- O1：`usage.py` L40 注释 task_type 枚举「answer | grader | extract | structured」缺 summary（陈旧注释 · 既有代码面 · 本 task 不动 usage.py · 不属本波范围）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NITS · 阻塞项为零 · nit N1–N3 可一并修订或直接知悉）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者/00 代录 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 20-task-audit R1 落盘：结论 PASS-WITH-NITS（阻塞项为零 · nit×3）· 锚点 5 抽全过 · 命名零冲突 · 基线 1420 复核一致 · 白名单全覆盖（前波 R1 审查未过教训项 · 白名单 vs 钉死落点一致性 · 本轮核验通过）· HG-AUDIT-R1 仍 pending 待维护者签 |
