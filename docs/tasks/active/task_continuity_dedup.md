# Task：continuity 重复实现合并（S1 硬删除 + 测试收敛 · continuity-dedup）

> **状态**：`signed`（2026-09-22 · R1 PASS 零阻塞 · HG-TASK-DRAFT/HG-AUDIT-R1=approved（维护者授权 00 代录）· 可 30）  
> **类型**：refactor / 已知债清理（**行为零变化 · 无 alembic 义务**；图谱零变更按实判，偏离回炉条款见闸表与 D3）  
> **上游 SPEC**：`docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-21 · commit d0152e4/8fdd859）  
> **分支**：`task/continuity-dedup`（**禁止 master 直改 · 禁止 push**）  
> **10 注**：2026-09-22 · 维护者授权 00 本窗签收全部过程文档（原话「此spec完成后继续把完成后续spec，一个个进行，每次PR到main通过CI后自动merge」承前令「授权00签收所有过程文档」，留痕于 SPEC 状态行）· HG-TASK-DRAFT / HG-AUDIT-R1 由 00 在该授权下于 20 审后代录，**本帽不签**

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `continuity-dedup` |
| **git_branch** | `task/continuity-dedup` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 行为零变化以**全量 pytest 绿**为证：删 `app/ops/session/continuity.py` + `__init__.py` 移除 re-export + `tests/test_session_continuity.py` 收敛（compress_window 两用例删除 · sse_replay 用例逐字保留）；lg_rag 侧既有覆盖（`tests/test_lg_rag_session_continuity.py` defaults/groups_head/short_noop/**failure_truncates_tail**）即合并后真源守护（本 task 零改动）；grep 断言全仓零 `app.ops.session.continuity` 引用残留；用例数差值 == 2；变异检验三条（删真源函数 / 忘改 __init__ / 摘 try/except · 见验收「变异检验」） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | 无（**零图谱变更按实判** · SPEC §2 D3 裁定：不新增路由/表/事件类型；`session/continuity.py` 未在 `docs/_tech_graph/` 登记（2026-09-21 SPEC 实扫零命中 · 2026-09-22 本帽复核一致）；`01_modules.md` chat 行 `app/ops/session/**` 路径覆盖与描述在删除后仍为真（history/sse_replay 保留）） |
| **graph_delta** | 无 |
| **graph_delta_note** | **回炉补闸条款**：若 30 阶段实现形态偏离零变更预判（如改走 S2 re-export → 新增 chat→lg_rag 依赖边（`01_modules.md` chat 行出边 `llm, db, rag` 无 lg_rag → 拓扑污染）· 或新增任何路由/表/事件类型），**不得沿用本裁定**——退回 10-spec 修订 SPEC + 10-task 补 HG-GRAPH-MODULES 新行义务 + `docs/_tech_graph/` 如实登记后方可续 30；30 顺带把 chat 行「Session 连续性」备注补「窗口压缩已并 lg_rag」属备注级顺手更新，非义务 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `continuity-dedup` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20-task-audit → 维护者授权 00 代录闸 → 30（D1 删除 + `__init__` 同步 + D2 测试收敛一次提交 · 真源零触碰）→ 40（含变异检验三条 + 真源零 diff）→ CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1` / `lc-evidence-http-v1`） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-22 · 00 验收 10-task 稿通过（维护者本窗授权 00 签收过程文档 · 原话留痕 SPEC 状态行） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-22 · 20-task-audit R1 PASS 零阻塞零返工（`docs/harness/reviews/task_continuity_dedup_audit_R1_20260922.md`）· 维护者本窗授权 00 代录签收 |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-22 本帽**真读** `docs/_tech_graph/l1/01_modules.md`：模块表已建置（chat 行 `app/ops/chat/**` · `app/ops/session/**` 在表 · 出边 `llm, db, rag` 无 lg_rag）。SPEC §2 D3 判本 task **零图谱变更**（不新增路由/表/事件类型 · `session/continuity.py` 图谱零登记 · chat 行覆盖与描述删除后仍为真）→ **无新签义务**；**若 30 改走 re-export（S2）或新增任何依赖边/端点/表/事件类型 → 回炉补闸**（见 graph_delta_note，不得沿用本裁定） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点 |

---

## 背景与目标

现状（SPEC §1 实扫锁死 · 2026-09-22 本帽复核一致）：`compress_window` 存在**两份实现**——`app/ops/lg_rag/continuity.py`（生产 · 244 行 · 功能超集）与 `app/ops/session/continuity.py`（legacy · 36 行 · 仅 `compress_window`）。占位「逻辑相同」**不成立**：lg_rag 版多整体 `try/except` 降级（`:38-62`）与 `sorted(str(r) ...)` 容错（`:54`），统一到 lg_rag 是**真升级非取舍**；占位「只被测试引用」**不成立**：`app/ops/session/__init__.py:3` re-export 是生产面（但其下游消费者实扫为零）。双份实现 = 漂移风险（手册 §1.2.2 已知债 M7：改一处忘另一处即静默分叉）。

一句话目标（SPEC 锁死）：在 **lg_rag 生产路径一行不改、压缩语义/占位符格式一字不动** 的前提下，删除 `app/ops/session/continuity.py` 重复实现并收敛其测试，使 `compress_window` 单一真源 = `app/ops/lg_rag/continuity.py`，以全量测试绿 + grep 零残留 + 变异检验三条为证。

设计纪律（30 不得违反 · 承 SPEC §1 签收锁死四条）：

1. **真源唯一且不动**：`lg_rag/continuity.py` 本体零改动；合并方向只有「删 session 侧」，禁止反向（往 session 侧搬 lg_rag 增强 = 养债）。
2. **依赖方向闸不反转**：本 task 不得引入任何新模块间 import 边，**连 session→lg_rag 边也不引入**（SPEC §4 裁决：re-export S2 会引入此边，弃；`tests/test_lg_rag_session_continuity.py:22-37` AST 闸只扫 lg_rag→session 方向，反向无测试兜底 → 禁走 S2）。
3. **测试收敛不丢断言**：session 侧删掉的每个用例必须在 lg_rag 侧有等价或更强断言已存在（逐条对账见范围 D2 表）。
4. **删除即验证**：删文件后全量 pytest + ruff + grep 断言三件套为证；任何 import 残留靠 `__init__.py` 同步移除兜底，不靠「应该没人用」。

---

## 现状锚点（只读 · 30 必读 · 10 已扫 · 承 SPEC §1）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| legacy 重复实现（删除对象） | `app/ops/session/continuity.py`（36 行） | 仅 `compress_window` 一个函数；**无 try/except**（docstring 声称「压缩失败时降级为截断」但无实现——docstring 撒谎）；`:32` `sorted(roles)` 裸排序（非 str role → TypeError）；默认值字面量 `6`/`2`（`:9-10`） |
| 真源（零改动） | `app/ops/lg_rag/continuity.py`（244 行） | `compress_window`（`:38-62` 整体 try/except：异常 → `max_full_turns<=0` 返 `[]` 否则截尾）；`:54` `sorted(str(r) for r in roles)` 容错；`:23-24` 模块常量 `DEFAULT_MAX_FULL_TURNS=6` / `DEFAULT_GROUP_SIZE=2`；功能超集（`assemble_graph_messages` + 记忆注入家族） |
| 包面 re-export（同步移除） | `app/ops/session/__init__.py:3` `from app.ops.session.continuity import compress_window` + `:8` `__all__` 中 `"compress_window"` | **生产代码引用**（包级 re-export · import 即执行）；history / sse_replay 两行（`:4-5`）与 `__all__` 其余三条（`:9-11`）**不动** |
| re-export 下游消费者 | 全仓 `*.py` grep `app\.ops\.session` | **零生产消费者**：命中仅 `__init__.py` 自身、注释禁令（`lg_rag/answer_stream.py:18` / `progress_stream.py:12` / `prompts/packs.py:9`）、依赖方向闸测试（`test_lg_rag_session_continuity.py:23` / `test_prompt_packs.py:211`）；无任何 `from app.ops.session import compress_window` 生产消费（2026-09-22 本帽复核） |
| 动态 import 面 | 全仓 `importlib`/`__import__`/`import_string` grep | 命中均与 continuity 无关（SPEC §1 实扫）→ 无隐藏运行时引用面 |
| session 侧测试（收敛对象） | `tests/test_session_continuity.py`（4 用例） | `:5` import 待删；compress_window 两用例 `test_compress_window_keeps_tail_full`（`:13-22`）· `test_compress_window_small_noop`（`:25-27`）待删；sse_replay 两用例 `test_replay_events_after_seq`（`:30-37`）· `test_replay_cursor_and_payload`（`:40-45`）与其 import（`:6-10`）**逐字保留**（SPEC 表述「sse_replay 四用例」与实测 2 个 test 函数有措辞偏差 · 范围语义零影响 · R0 留痕） |
| 真源守护测试（零改动） | `tests/test_lg_rag_session_continuity.py` | `test_compress_window_defaults_and_groups_head`（`:65-73`）· `test_compress_window_short_noop`（`:76-78`）· `test_compress_window_failure_truncates_tail`（`:81-85` 差异①守护）· 依赖方向闸 `test_lg_rag_package_does_not_import_chat_or_session`（`:22-37`） |
| 图谱登记 | `docs/_tech_graph/` grep `continuity` | 仅 l1 `10_flow_lg_rag.graph.yaml` 与 l2 indexes 登记 **lg_rag 侧**；`session/continuity.py` **零登记** → 图谱零变更 |
| 历史文档提及 | `docs/tasks/done/task_lg_rag_session_continuity.md` 等 | **不回改**（done/归档文档是历史快照 · SPEC §3） |
| 测试基线 | `python -m pytest tests --collect-only -q` | **1178 collected**（2026-09-22 本帽真跑）；删除后应为 1176（差值 == 2） |

---

## 钉死契约（自 SPEC §1/§2 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **删除面** | `app/ops/session/continuity.py` 整文件删除；`app/ops/session/__init__.py` 仅移除 `:3` import 与 `__all__` 中 `"compress_window"`（`:8`）；history / sse_replay 两行原样 |
| **真源** | `app/ops/lg_rag/continuity.py` **零改动**（行为零变化的物理保证；含「顺手」改默认值/注释/回移植差异①②均禁止） |
| **依赖边** | 不新增任何模块间 import（方案 S1 · SPEC §4）；**禁走 S2 re-export**（新增 chat→lg_rag 边污染图谱拓扑 + import 链拖入 langchain_core/tracing 变重 + 零受益人） |
| **压缩语义** | `[历史摘要 · N 轮 · roles=...]` 占位符格式一字不动；真摘要另 SPEC `session-summary-fallback`，本 task 不触 |
| **测试删除面** | `tests/test_session_continuity.py`：仅删 `:5` import + 两用例（`:13-27`）；sse_replay 两用例（`:30-45`）与其 import（`:6-10`）逐字保留 |
| **测试守护面** | `tests/test_lg_rag_session_continuity.py` 零改动（合并后即为真源守护） |
| **覆盖对账** | `keeps_tail_full`（10 turns · max=4 · group=2 → 3 摘要+4 尾）↔ lg_rag `test_compress_window_defaults_and_groups_head`（`:65-73` 同构断言）+ `test_compress_window_failure_truncates_tail`（`:81-85` 同参数显式断言）；`small_noop` ↔ `test_compress_window_short_noop`（`:76-78` 同断言）——等价或更强，零断言丢失 |
| **图谱** | 零变更（按实判）；`./scripts/graph-compile.sh` 绿为回归保险；不回改 done/归档历史文档 |
| **安全** | 纯删除型重构：无新凭证面、无网络面、无 DB 面（无 alembic 义务）；压缩输出格式零变化，无 prompt 注入面变化 |

---

## 范围（同 task 竖切）

- [ ] **D1 · 单一真源合并（必做）**：删 `app/ops/session/continuity.py`；`app/ops/session/__init__.py` 同步移除 `:3` import + `__all__` `"compress_window"`；`lg_rag/continuity.py` 零改动；零新增依赖边
- [ ] **D2 · 测试收敛（必做）**：`tests/test_session_continuity.py` 删 compress_window 两用例与 `:5` import（对账表逐条留痕）；sse_replay 两用例与 `:6-10` import 逐字保留；`tests/test_lg_rag_session_continuity.py` 零改动
- [ ] **D3 · 图谱与工程（必做 · 按实判零图谱变更）**：`./scripts/graph-compile.sh` 绿；grep 零残留断言；不回改 done/归档历史文档；chat 行备注顺手更新可选（非义务）

**竖切结论**：D1–D3 同 task 一次提交（纯删除型重构，拆开会出现 `__init__.py` 残留炸的中间态 · failure_paths 行 2）；无「先行提交」切分空间（对照 memory-embedding-backfill 的 D3 先行模式不适用于纯删除）。

### 非范围

- ❌ 改压缩语义 / 占位符格式（`[历史摘要 · N 轮 · roles=...]` 一字不动）
- ❌ 真摘要（另 SPEC `session-summary-fallback`）
- ❌ `lg_rag/continuity.py` 本体任何改动（含「顺手」回移植差异①②、改默认值、改注释）
- ❌ `app/ops/session/` 其余文件（history.py / sse_replay.py / `__init__.py` 中 history·sse_replay 行）——chat 轨整体清退是另一波次的事
- ❌ `app/ops/chat/**` 任何清理（已 410 但代码/图/表保留 · `01_modules.md:22` 裁定沿用）
- ❌ 仓外消费者兼容（实扫证实仓内零消费者；仓外脚本若引用属其自身债，本 task 不保留兼容层）
- ❌ 历史文档回改（done task / ROADMAP / reviews 中的提及保留为快照）
- ❌ 表结构变更（无 alembic 义务 · 本 task 不触 DB）
- ❌ web / ios

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| 隐藏运行时引用被删断（grep 未覆盖的动态 import / 字符串拼接模块名） | 动态 import 面已专扫（SPEC §1 引用面表）；残余风险由**全量 pytest 绿** + 启动冒烟兜底——`import app.main` 链路任一残留引用即 ImportError 显式炸，不静默 | Y（恢复文件或修引用） | 是（CI 红） |
| `__init__.py` re-export 残留（删文件忘改 `__init__`） | `import app.ops.session` 包加载即 `ModuleNotFoundError`；`tests/test_session_continuity.py`（import sse_replay 触发包 `__init__`）必挂 → CI 红显式暴露；**变异检验 ② 专门钉死本路径** | Y（补改 `__init__.py`） | 是（CI 红） |
| `__all__` 残留 `"compress_window"`（改了 import 忘改 `__all__`） | `from app.ops.session import *` 才触发；仓内零 star-import（grep 可证）；ruff F822 若启用即拦截——验收含 ruff 绿 | Y | 否 |
| 30 擅自改走 S2 re-export（SPEC 已弃） | session→lg_rag 新边 + lg_rag 禁令闸只扫 lg_rag→session 方向**不拦反向** → 循环/拓扑债无测试兜底；故设计纪律 2 禁走 S2；发生 → **回炉**（退 10-spec 修订 SPEC + 补 HG-GRAPH-MODULES）· 验收「工程」项拒收 | — | 否 |
| 测试误删 sse_replay 覆盖 | 范围 D2 明示 sse_replay 两用例逐字保留；30 diff 审查核对删除行只涉 compress_window（`:5` · `:13-27`） | — | 否 |
| lg_rag 侧覆盖不如声称（对账失真） | 变异检验 ①：删真源 `compress_window` 函数体 → lg_rag 侧测试必须 import 失败/断言挂；检验 ③：摘掉真源 try/except → `test_compress_window_failure_truncates_tail` 必须挂 | — | 否 |
| 图谱编译断裂 | `graph-compile.sh` 绿为验收项；`session/continuity.py` 未登记图谱，删除不触发索引失配 | Y | 是（CI 红） |
| 仓外脚本引用（仓外不可扫面） | 显式列非范围；若真实存在 → ImportError 显式炸（非静默错），由消费方各自迁移到 lg_rag 真源 | Y | 是（ImportError） |
| 误改真源（30 手滑改 `lg_rag/continuity.py`） | 验收含「真源零 diff」断言：`git diff master -- app/ops/lg_rag/continuity.py` 为空 | Y（revert） | 否 |
| 无变异检验三条却宣称收敛有效 | 40/verify **拒收**（不验收空真规则） | 是 | 否 |
| 30 开工前旧测影响面清单未落盘或逐条无处置 | 验收「工程 · 闸前置」项不满足 → **拒收**（B1） | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：`HG-AUDIT-R1` approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved · 本 task 零图谱变更无新签义务；**若 30 偏离零变更预判/改走 re-export → 回炉补闸**，见闸表与 graph_delta_note）

### D1 · 单真源（映射 SPEC §6-D1）

- [ ] `app/ops/session/continuity.py` 已删除；`app/ops/session/__init__.py` 无 `continuity` import 且 `__all__` 无 `"compress_window"`；history / sse_replay 两行（`:4-5`）与 `__all__` 其余三条原样
- [ ] **真源零 diff**：`git diff master -- app/ops/lg_rag/continuity.py` 输出为空
- [ ] **grep 零残留**：全仓 `*.py` 搜索 `session.continuity` / `session/continuity` / `ops\.session import compress_window` 零命中（docs 历史快照除外）
- [ ] 无新增模块依赖边：`git diff master -- app/` 中无任何新增 `import` 行

### D2 · 测试收敛（映射 SPEC §6-D2）

- [ ] `tests/test_session_continuity.py`：compress_window 两用例（`:13-27`）与 `:5` import 已删；sse_replay 两用例（`:30-45`）与 `:6-10` import **逐字保留**
- [ ] 覆盖对账留痕（引用钉死契约对账表）：被删两用例 ↔ lg_rag 侧等价/更强断言逐条对应（`keeps_tail_full` ↔ `:65-73`+`:81-85` · `small_noop` ↔ `:76-78`）
- [ ] `tests/test_lg_rag_session_continuity.py` 零改动且全绿（含 `test_lg_rag_package_does_not_import_chat_or_session` 方向闸）

### 行为零变化（映射 SPEC §6-行为零变化）

- [ ] 全量 `pytest tests` 绿（删除前基线 == 删除后，**用例数差值 == 2** 且仅为被删两用例：1178 → 1176 collected · 基线 2026-09-22 本帽真跑）
- [ ] 生产路径零改动：`git diff master -- app/` 只含 `session/continuity.py` 删除 + `session/__init__.py` 两行移除

### 变异检验（不验收空真规则 · 映射 SPEC §6-变异检验）

- [ ] ① **删真源函数**：临时摘掉 `lg_rag/continuity.py` 中 `compress_window` 定义 → `tests/test_lg_rag_session_continuity.py` import 即失败（证明测试真钉住真源）；恢复后全绿
- [ ] ② **忘改 __init__ 炸显式**：临时只删 `session/continuity.py` 不改 `__init__.py` → 跑 `tests/test_session_continuity.py` 必须 `ModuleNotFoundError` 挂（证明删断无静默路径）；补改 `__init__.py` 后全绿
- [ ] ③ **摘 try/except 降级守护真实**：临时摘掉真源 `compress_window` 的 try/except → `test_compress_window_failure_truncates_tail` 必须挂（证明差异①已随单真源收敛到强版且有守护）；恢复后全绿

### 工程（映射 SPEC §6-工程）

- [ ] **闸前置**：30 开工前旧测影响面清单已落盘且逐条有处置（回归/删除理由）——清单见下「旧测影响面清单（B1）」，30 逐条执行处置并在提交说明逐条回填
- [ ] `ruff check app tests` 绿（`__init__.py` 残面 / 死 import 由 ruff 兜底）
- [ ] `./scripts/graph-compile.sh` 绿；图谱零变更裁定与实现形态一致（若 30 走了 re-export 或新增任何依赖边/端点/表/事件类型 → 回炉补闸 + SPEC 回炉）

### 旧测影响面清单（B1 · 2026-09-22 10-task 实扫落盘）

> 扫描口径（真跑）：`grep -oE 'compress_window|continuity|ops\.session' tests/test_session_continuity.py tests/test_lg_rag_session_continuity.py` = **17 处命中**（8 + 9 · 两测试文件）；辅以全仓 `*.py` grep `app\.ops\.session` 复核消费者面。本波行为变更源裁定：**真源与生产路径零改动**，变更面 = `session/continuity.py` 删除 + `__init__.py` 两行移除 + `test_session_continuity.py` 收敛；故影响面以**回归**（真源守护测试）与**删除**（被收敛用例）为主，**无改编**。处置三态：**回归**（不受影响，全波次重跑确认）/ **改编**（随本波更新，本清单无）/ **删除**（附对账理由）。

| # | 锚点 | 命中（occ） | 旧测/调用点现状 | 本波影响 | 处置 |
|---|------|------------|----------------|----------|------|
| 1 | `tests/test_session_continuity.py:5` `from app.ops.session.continuity import compress_window` | 3（ops.session · continuity · compress_window） | 被删模块的 import | 随 D2 删除（触发包 `__init__` 加载 · 变异检验②钉死残留路径） | 删除（import 面随模块消失 · SPEC §2 D2） |
| 2 | `tests/test_session_continuity.py:6` `from app.ops.session.sse_replay import (` | 1（ops.session） | sse_replay import（`:6-10` 引入三符号） | sse_replay 保留 → import 不动；`__init__.py` 移除 continuity 行后包加载仍正常（变异检验②反向佐证） | 回归（逐字保留） |
| 3 | `tests/test_session_continuity.py:13` `def test_compress_window_keeps_tail_full():` | 1 | 10 turns · max=4 · group=2 → 3 摘要+4 尾 | 用例删除；对账 lg_rag `:65-73`（同构断言）+ `:81-85`（同参数显式断言） | 删除（覆盖等价或更强已在真源侧 · SPEC §2 D2 对账表） |
| 4 | `tests/test_session_continuity.py:18` `out = compress_window(turns, max_full_turns=4, group_size=2)` | 1 | 上用例调用行 | 随用例删除 | 删除（同 #3） |
| 5 | `tests/test_session_continuity.py:25` `def test_compress_window_small_noop():` | 1 | 小输入原样返回 | 用例删除；对账 lg_rag `:76-78`（同断言） | 删除（覆盖等价已在真源侧） |
| 6 | `tests/test_session_continuity.py:27` `assert compress_window(turns, max_full_turns=6) == turns` | 1 | 上用例断言行 | 随用例删除 | 删除（同 #5） |
| 7 | `tests/test_lg_rag_session_continuity.py:14` `from app.ops.lg_rag.continuity import assemble_graph_messages, compress_window` | 2（continuity · compress_window） | 真源 import | 真源零改动 → 不受影响；合并后即为唯一真源守护入口 | 回归（零改动 · 全波次重跑确认） |
| 8 | `tests/test_lg_rag_session_continuity.py:23` `forbidden = ("app.ops.chat", "app.ops.session")` | 1 | 依赖方向闸（AST 扫 lg_rag→chat/session） | 本 task 不引入 session→lg_rag 边（S1 零新边）→ 闸语义不受触；若 30 走 S2 本闸**不拦反向**（failure_paths 已钉 · 回炉条款兜底） | 回归（零改动） |
| 9 | `tests/test_lg_rag_session_continuity.py:65` `def test_compress_window_defaults_and_groups_head() -> None:` | 1 | 默认值 + 头部分组断言 | 对账接收方（承接被删 #3 覆盖）· 真源零改动 | 回归（零改动） |
| 10 | `tests/test_lg_rag_session_continuity.py:67` `out = compress_window(turns)` | 1 | 上用例调用行 | 同上 | 回归（零改动） |
| 11 | `tests/test_lg_rag_session_continuity.py:76` `def test_compress_window_short_noop() -> None:` | 1 | 短输入 noop 断言 | 对账接收方（承接被删 #5 覆盖） | 回归（零改动） |
| 12 | `tests/test_lg_rag_session_continuity.py:78` `assert compress_window(turns, max_full_turns=6, group_size=2) == turns` | 1 | 上用例断言行 | 同上 | 回归（零改动） |
| 13 | `tests/test_lg_rag_session_continuity.py:81` `def test_compress_window_failure_truncates_tail() -> None:` | 1 | 差异①守护（异常 → 截尾） | 真源降级守护；变异检验③对象 | 回归（零改动 · 变异检验③钉死） |
| 14 | `tests/test_lg_rag_session_continuity.py:84` `out = compress_window(turns, max_full_turns=4, group_size=2)` | 1 | 上用例调用行（与 #3 同参数显式断言） | 对账接收方（同参数） | 回归（零改动） |
| 15 | 全仓 `*.py` grep `app\.ops\.session` 生产命中：`app/ops/session/__init__.py:3` | （辅扫） | 包级 re-export（生产面） | D1 同步移除对象 | 删除（随 D1 · import + `__all__` 条目） |
| 16 | 全仓辅扫命中：`lg_rag/answer_stream.py:18` · `progress_stream.py:12` · `prompts/packs.py:9`（注释禁令）；`tests/test_prompt_packs.py:211`（禁令字符串断言） | （辅扫） | 依赖方向禁令注释 / 禁令断言 | 只读注释与禁令断言，不引用 `session.continuity` 符号 → 不受影响 | 回归（不动） |
| 17 | 全仓动态 import 面（`importlib`/`__import__`/`import_string`） | （辅扫） | SPEC §1 实扫：命中均与 continuity 无关 | 无隐藏运行时引用面 | 回归（无处置） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-21） |
| 上游设计 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 §1.2.2 已知债 M7） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 2026-09-22 真读核验） |
| 真源 | `app/ops/lg_rag/continuity.py`（零改动 · `:23-24` / `:38-62` / `:54`） |
| 删除对象 | `app/ops/session/continuity.py` + `app/ops/session/__init__.py:3,:8` |
| 测试锚点 | `tests/test_session_continuity.py`（收敛）· `tests/test_lg_rag_session_continuity.py`（零改动守护 · 含 `:22-37` 方向闸） |
| 格式基准 | `docs/tasks/done/task_memory_embedding_backfill.md`（signed → done 五棒全通 · PR #151） |
| 同模式闭环先例 | `docs/tasks/done/task_memory_embedding_backfill.md` · `docs/tasks/done/task_lg_rag_session_continuity.md`（历史快照不回改） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md`（§1 差异表 / §4 方案裁决 / §5 failure_paths / §6 验收）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/session/continuity.py`（删除对象）· `app/ops/session/__init__.py`（`:3` / `:8` 同步移除）· `app/ops/lg_rag/continuity.py`（真源 · 零触碰）
6. 测试：`tests/test_session_continuity.py` · `tests/test_lg_rag_session_continuity.py`
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-21）；范围 D1–D3 承 SPEC §2 不重开辩论；本帽实扫复核：分支正确（`task/continuity-dedup`）· B1 口径 17 命中（8+9）· pytest 基线 1178 collected；**发现 SPEC 措辞偏差一处**：「sse_replay 四用例」与实测 2 个 test 函数不符（范围语义零影响 · 留痕不改 SPEC） | no | — | none |
| R1 | 开工闸：HG-TASK-DRAFT=pending（00 代录）· HG-AUDIT-R1=pending（blocks 30 · 本帽不签）· HG-GRAPH-MODULES=approved（2026-09-22 真读 `01_modules.md` 核验模块表已建置 · chat 行出边无 lg_rag）· 零图谱变更 + 回炉补闸条款钉死 · HG-PILOT-OPSDESK-GLAYER=n/a | no | — | 无 |
| R2 | 竖切：D1–D3 同 task 一次提交（纯删除型重构 · 拆开出现 `__init__.py` 残留炸中间态）；方案对比继承 SPEC §4 两组裁决（S1 硬删除 · 删例对账），不重演 | no | — | 无 |
| R3 | failure_paths 12 条 = SPEC §5 九条翻四列（re-export 假设性循环并入「30 擅自走 S2 → 回炉」行）+ 过程三（闸 / 变异检验 / B1 闸前置）；核心纪律：真源零 diff 断言防手滑 · 变异检验②钉死 `__init__` 残留 · 禁走 S2 | no | — | 无 |
| R4 | 验收 17 条全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×4 / D2×3 / 行为零变化×2 / 变异检验×3 / 工程×3）；B1 实扫 17 处命中逐条处置落盘（回归×11 · 删除×6 · 改编×0 · 含辅扫 3 行） | no | — | ruff F822 是否启用未核（继承 SPEC residual ② · `__all__` 残留靠 grep 断言与 diff 审查兜） |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（B1 / 闸行 / 基线数均为过程化落地；sse_replay 用例数为如实记录 SPEC 措辞偏差，非范围偏差）；HG-AUDIT-R1 待人签（00 依授权代录） | no | — | ① 仓外脚本引用属不可扫面（继承 SPEC residual ①）；② 删除是不可逆一步，靠 git 历史与真源功能超集保证无损（继承 SPEC residual ③） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

SPEC 已签收，本 task 只做可执行化拆解：`compress_window` 双份实现（lg_rag 生产超集 vs session legacy 36 行）· 手册 §1.2.2 已知债 M7。本帽实扫复核：分支 `task/continuity-dedup` 正确；两测试文件 17 处命中（口径 `compress_window|continuity|ops\.session` occurrence 级 · 8+9）；pytest 基线 1178 collected（删后应 1176）；`app/ops/session/__init__.py` 实读确认 `:3` import + `:8` `__all__` 锚点与 SPEC 一致。**SPEC 措辞偏差留痕**：SPEC §1/§2 表述「sse_replay 四用例（:30-45）」，实测该区间仅 2 个 test 函数（`test_replay_events_after_seq` `:30-37` · `test_replay_cursor_and_payload` `:40-45` · 全文件 4 用例 = 2 删 + 2 留）；范围语义（删 compress_window 两用例 · 其余逐字保留 · 差值==2）零影响，本 task 按实测如实写，不阻塞、不改 SPEC（若维护者要修措辞走 10-spec 修订轨）。

### R1 · 开工闸

HG-TASK-DRAFT / HG-AUDIT-R1 均 pending（00 在维护者「授权00签收所有过程文档」令下于 20 审后代录，本帽不签）；HG-GRAPH-MODULES **真读** `docs/_tech_graph/l1/01_modules.md` 核验：模块表已建置，chat 行路径 glob 含 `app/ops/session/**`、出边 `llm, db, rag`（**无 lg_rag** → S2 re-export 必污染拓扑 · 回炉条款的图谱依据）；本 task 按 SPEC §2 D3 判零图谱变更（不新增路由/表/事件类型 · `session/continuity.py` 图谱零登记 · 删除后 chat 行覆盖与描述仍为真）→ 无新签义务；**回炉补闸条款**钉死：30 改走 re-export 或新增任何依赖边/端点/表/事件类型 → 退 10-spec 修订 SPEC + 补闸 + 图谱如实登记，不得沿用本裁定。

### R2 · 竖切

D1（删除+`__init__` 同步）与 D2（测试收敛）强耦合：只删文件不改 `__init__.py` 即中间态必炸（failure_paths 行 3 · 变异检验②），只改测试不删文件则债原样保留；故 D1–D3 同 task 一次提交，无 memory-embedding-backfill「D3 纯测先行」式切分空间。方案对比不重演，直接继承 SPEC §4 两组裁决（S1 硬删除弃 S2/S3 · 删例对账弃 import 迁移）。

### R3 · 失败语义

SPEC §5 失败面全收并翻四列：隐藏动态引用（专扫+全量 pytest+启动冒烟兜底 · 显式炸不静默）· `__init__` 残留（变异检验②钉死）· `__all__` 残留（star-import 零命中 + ruff F822 若启用）· S2 反向循环无闸（设计纪律 2 + 回炉条款）· 误删 sse_replay（D2 明示保留 + diff 审查）· 对账失真（变异检验①③）· 图谱编译（回归保险）· 仓外引用（非范围 · 显式炸）· 误改真源（零 diff 断言）。补过程三行：闸未签拒开工 · 无变异检验拒收（防空真规则）· B1 未落盘拒收。

### R4 · 可测性

验收 17 条全部可执行断言：真源零 diff（`git diff master -- app/ops/lg_rag/continuity.py` 为空）· grep 零残留（三 pattern）· 用例数差值==2（1178→1176 · 基线本帽真跑）· app/ diff 白名单（只含两处）· sse_replay 逐字保留 · 变异检验三条（各致指定测试挂）· ruff + graph-compile 绿。B1 实扫落盘：两测试文件 17 处命中逐条处置（删除×6 = session 侧 import/两用例 · 回归×8 = lg_rag 真源守护 · 辅扫×3 = 生产 re-export/禁令注释/动态 import 面），无改编。

### R5 · 交接就绪

思考充分可交 20-task-audit；与 SPEC 逐条核对**实质差异为零**（验收 17 条 = SPEC §6 各块 + 人工闸行 + 闸前置 B1，均过程化落地；sse_replay 用例数 2 为如实记录 SPEC 措辞偏差 · R0 留痕，非范围偏差）。残余风险三条继承 SPEC §7 residual 签收知悉项（仓外不可扫面 · ruff F822 未核 · 删除不可逆靠 git+超集兜底）。

---

### 自检结论（40 核验 · 2026-09-22 回填）

**总判定：PASS**（17 条口径全过 · 16 个勾选项逐条亲核 16/16 · WARN×1 不阻塞）。30 交付 commit `ecaec39` 自称逐项属实。

- **验收逐条计数**：人工闸1（HG-AUDIT-R1=approved 闸表核对）· D1×4（删文件+__init__ 亲读 / 真源零 diff 亲跑 wc=0 / grep 三 pattern exit=1×3 / app diff 零 `+` 行）· D2×3（两用例删+sse_replay 区块与基线逐字 diff 空 / 对账接收方 :65-73·:76-78·:81-85 实存 / lg_rag 测试零 diff 15 绿含方向闸）· 行为零变化×2（1176 collected 差==2 · app diff 白名单两处）· 变异×3 · 工程×3
- **变异检验复做记录**：③亲复做——摘真源 `compress_window` try/except → `test_compress_window_failure_truncates_tail` 真挂（AttributeError 传播 · 1 failed/14 passed）→ `git checkout` 还原后 15 绿且真源 vs HEAD/origin/master 双零 diff；①②采信 30 真跑留痕（ImportError / ModuleNotFoundError 具体报错在 30 invoke）
- **基线对照**：worktree detached @ `origin/master` c9739e7（补同 .env）真跑 **1178 collected · 1173p/4f/1s**；任务分支 **1176 collected · 1172p/3f/1s**；3 红（chat_ws×2 + capability proxy）两分支同集合 = 基线环境红；基线第 4 红 `test_reconcile_mismatch_marks_failed` 为随机序 flaky（事件循环关闭类 · 任务分支单跑 1 passed）与本波无关
- **B1 处置核验**：抽查 6 处实核属实——#1 import 已删 · #2 sse_replay 逐字保留 · #3 对账接收方实存 · #8 方向闸原样 · #15 `__init__.py` re-export 已删 · #16 禁令注释三处+断言原样（`app/ops/prompts/packs.py:9` 实路径）
- **ruff**：57 == 基线 57 · concise 明细 diff 为空（零新增零减少）
- **graph-compile**：exit 0 · `shared/graph.json` 仅 generated_at 漂移已 `git checkout` 还原
- **WARN 清单**：① ruff 验收字面「绿」不成立（57=基线存量 · 零新增口径判过 · 承 SPEC residual ②）；② 基线 flaky 第 4 红留痕；③ 措辞偏差两处（sse_replay 实 2 用例 · packs.py 锚点省 `app/ops/` 前缀）均不影响实质
- 证据全文：`docs/harness/invokes/by-task/continuity-dedup/invoke_20260922_40_verify_continuity_dedup.md`

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | 10-task 落稿 · R0–R5 全轮无 early_stop · 验收 17 条逐块映射 SPEC §6 实质零差异 · B1 旧测影响面 17 处命中实扫落盘（口径 `compress_window|continuity|ops\.session` · 8+9 · 逐条处置）· pytest 基线 1178 collected 真跑 · SPEC 措辞偏差留痕（sse_replay 实 2 用例非 4 · 范围零影响）· HG-TASK-DRAFT=pending · HG-AUDIT-R1=pending → 30 拒开工 · HG-GRAPH-MODULES=approved（真读 `01_modules.md` · 零图谱变更 + 回炉补闸条款）· HG-PILOT-OPSDESK-GLAYER=n/a |
| 2026-09-22 | 40 核验回填自检结论：**PASS**（17 条口径全过 · 真源零 diff / grep 零残留 / app diff 白名单亲核 · pytest 1176 vs 基线 1178 差==2 且 3 红同集合 · ruff 57==57 明细 diff 空 · graph-compile 绿漂移已还原 · 变异③亲复做闭环 · B1 抽查 6 处属实 · WARN×3 留痕不阻塞）· 证据 invoke_20260922_40_verify_continuity_dedup.md |
