# SPEC：continuity 重复实现合并（v1）

> **状态**：`draft-complete · 待人签`（HG-SPEC-SIGNOFF=**approved**（2026-09-21 · 维护者授权 00 本窗签收全部过程文档 · 原话「此spec完成后继续把完成后续spec，一个个进行，每次PR到main通过CI后自动merge」承前令「授权00签收所有过程文档」） · 人签前不出 task / 不改码）
> **track**：`refactor`（已知债清理 · 行为零变化 · **无 alembic 义务** · 图谱零变更按实判见 §2 D3；占位「待裁定」→ 本 SPEC 裁定）
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 §1.2.2 已知债 M7）
> **格式基准**：`docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md`（signed · PR #151 已合）
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 实现
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `continuity-dedup` |
| **invoke_slug** | `continuity-dedup`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | 行为零变化以**全量 pytest 绿**为证：删 `app/ops/session/continuity.py` + `__init__.py` 移除 re-export + `tests/test_session_continuity.py` 收敛（compress_window 两用例删除 · sse_replay 四用例保留）；lg_rag 侧既有覆盖（`tests/test_lg_rag_session_continuity.py` defaults/groups_head/short_noop/**failure_truncates_tail**）即合并后真源守护；grep 断言全仓零 `app.ops.session.continuity` 引用残留；变异检验三条（见 §6） |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/continuity-dedup` |
| **graph_change_layer（建议）** | 无（**零图谱变更按实判**：不新增路由/表/事件类型，仓规三类同步义务均不触发；删模块内文件 `app/ops/session/continuity.py` 未在图谱登记（2026-09-21 grep `docs/_tech_graph/` 证实零命中），`01_modules.md` chat 行 `app/ops/session/**` 覆盖不变（history/sse_replay 仍在）；若 30 阶段顺带把 chat 行「Session 连续性」备注补一句「窗口压缩已并 lg_rag」属备注级顺手更新，非义务） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 维护者签收本 SPEC 后方可 00 出 task / 30 改码（人签，不由 10-spec 代签） |

---

## 1. 背景与目标

### 现状（2026-09-21 实扫 · diff 级）

**两文件本体 diff 级对比结论：占位「逻辑相同」不成立——主路径行为等价，但 lg_rag 版是严格更强的超集。**

| 维度 | `app/ops/lg_rag/continuity.py`（生产 · 244 行） | `app/ops/session/continuity.py`（legacy · 36 行） | 差异性质 |
|---|---|---|---|
| 异常降级 | 整体 `try/except`：异常 → `max_full_turns<=0` 返 `[]` 否则截尾（`:38-62`）；有专门测试钉死（`test_compress_window_failure_truncates_tail` · `tests/test_lg_rag_session_continuity.py:81-85`） | **无 try/except**（docstring 声称「压缩失败时降级为截断」但无实现——docstring 撒谎） | **实质差异 ①**：异常输入下 session 版抛出、lg_rag 版降级 |
| roles 排序容错 | `sorted(str(r) for r in roles)`（`:54` · str 强转） | `sorted(roles)`（`:32` · 裸排序） | **实质差异 ②**：role 为非 str / 混合类型时 session 版 TypeError，lg_rag 版兼容 |
| 默认值来源 | 模块常量 `DEFAULT_MAX_FULL_TURNS=6` / `DEFAULT_GROUP_SIZE=2`（`:23-24`） | 字面量 `6` / `2`（`:9-10`） | 行为等价 · 维护面差异（双改风险正是本债） |
| `list()` 拷贝 | `list(turns[-max_full_turns:])` / `compressed + list(tail)` | `turns[-max_full_turns:]` / `compressed + tail` | 行为等价（切片本身即新 list） |
| 函数面 | `compress_window` + `assemble_graph_messages` + 记忆注入家族（`assemble_graph_messages_with_memory` / `render_memory_facts_block` / `inject_memory_facts_block` / env 助手 · memory-facts-p0/p1） | 仅 `compress_window` 一个函数 | lg_rag 版为功能超集 |

**取舍裁定**：主路径（dict 输入 · str role · 无异常）两版输出逐字节一致；差异 ①② 全是「lg_rag 更强」。统一到 lg_rag 不是「取舍」而是**真升级**——session 侧两个现存用例（`tests/test_session_continuity.py:13-27`）只走主路径，lg_rag 侧已有等价断言 + 额外的降级断言，覆盖无损收敛。

### 引用面实扫（2026-09-21 · 占位「只被测试引用」**不成立**）

| 引用点 | 类型 | 处置 |
|---|---|---|
| `app/ops/session/__init__.py:3` `from app.ops.session.continuity import compress_window` + `:8` `__all__` | **生产代码引用**（包级 re-export · import 即执行）——占位声称「只被测试引用」**不准确** | 随删除同步移除 import + `__all__` 条目 |
| 上述 re-export 的下游消费者 | **零**：全仓 `*.py` grep `app\.ops\.session` 命中仅 `__init__.py` 自身、注释禁令（`lg_rag/answer_stream.py:18` / `progress_stream.py:12` / `prompts/packs.py:9`）、依赖方向闸测试；无任何 `from app.ops.session import compress_window` 生产消费（router.py 失效 import 已在 `task_lg_rag_deprecate_chat_stream` 清理，见其 done 文档） | 删除安全的前提证据 |
| `tests/test_session_continuity.py:5` | 测试引用（compress_window 两用例 `:13-27`；同文件 sse_replay 四用例 `:30-45` 与 continuity 无关） | compress_window 两用例删除（lg_rag 侧等价+更强覆盖已就位）；sse_replay 用例保留 |
| 动态 import 面 | 全仓 `importlib`/`__import__`/`import_string` grep：命中均与 continuity 无关（`capability/manifest.py` /`scripts/acceptance/dump_agent_graph.py` / models.py uuid 工厂） | 无隐藏运行时引用面 |
| 图谱登记 | `docs/_tech_graph/` grep `continuity`：仅 l1 `10_flow_lg_rag.graph.yaml` 与 l2 indexes 登记 **lg_rag 侧**；`session/continuity.py` 零登记 | 图谱零变更 |
| 历史文档提及 | `docs/tasks/done/task_lg_rag_session_continuity.md`、`docs/spec/agent-infra/session/ROADMAP_chat_continuity_v0.md` 等 | **不回改**（done/归档文档是历史快照） |

### 痛点

1. **漂移风险**：同一压缩语义两份实现，改一处忘另一处即静默分叉（手册 §1.2.2 已知债 M7）。
2. **占位误判已实扫纠正**：① 「逻辑相同」不成立（lg_rag 版多降级保护与容错）；② 「只被测试引用」不成立（`__init__.py` re-export 是生产面）。
3. **legacy 面残留**：`app/ops/session/` 属 chat 轨（chat stream 已 410 下线 · `01_modules.md:22`），其窗口压缩无生产消费者，纯债务。

### 一句话目标

在 **lg_rag 生产路径一行不改、压缩语义/占位符格式一字不动** 的前提下，删除 `app/ops/session/continuity.py` 重复实现并收敛其测试，使 `compress_window` 单一真源 = `app/ops/lg_rag/continuity.py`，以全量测试绿 + grep 零残留 + 变异检验为证。

设计纪律（签收时锁死）：

1. **真源唯一且不动**：`lg_rag/continuity.py` 本体零改动；合并方向只有「删 session 侧」，禁止反向（往 session 侧搬 lg_rag 增强 = 养债）。
2. **依赖方向闸不反转**：`tests/test_lg_rag_session_continuity.py:22-37` AST 闸禁止 lg_rag→session/chat；本 SPEC 不得引入 session→lg_rag 之外的任何新依赖边，且**连 session→lg_rag 边也不引入**（方案对比 §4 裁决：re-export 会引入此边，弃）。
3. **测试收敛不丢断言**：session 侧删掉的每个用例必须在 lg_rag 侧有等价或更强断言已存在（逐条对账见 §2 D2）。
4. **删除即验证**：删文件后全量 pytest + ruff + grep 断言三件套为证；任何 import 残留靠 `__init__.py` 同步移除兜底，不靠「应该没人用」。

---

## 2. 范围

### D1 · 单一真源合并（必做）

| 项 | 约定 |
|---|---|
| 删除 | `app/ops/session/continuity.py` 整文件删除 |
| 包面同步 | `app/ops/session/__init__.py` 移除 `:3` import 与 `__all__` 中 `"compress_window"`（`:8`）；history / sse_replay 两行不动 |
| 真源 | `app/ops/lg_rag/continuity.py` **零改动**（行为零变化的物理保证） |
| 依赖边 | 不新增任何模块间 import（方案 S1 · §4） |

### D2 · 测试收敛（必做）

| 项 | 约定 |
|---|---|
| 删除用例 | `tests/test_session_continuity.py`：`test_compress_window_keeps_tail_full`（`:13-22`）· `test_compress_window_small_noop`（`:25-27`）及 `:5` import |
| 逐条对账 | `keeps_tail_full`（10 turns · max=4 · group=2 → 3 摘要+4 尾）↔ lg_rag 侧 `test_compress_window_defaults_and_groups_head`（`:65-73` 同构断言）+ `test_compress_window_failure_truncates_tail`（`:81-85` 同参数显式断言）；`small_noop` ↔ `test_compress_window_short_noop`（`:76-78` 同断言）——覆盖**等价或更强**，零断言丢失 |
| 保留用例 | 同文件 sse_replay 四用例（`:30-45`）与其 import（`:6-10`）**不动** |
| lg_rag 侧测试 | `tests/test_lg_rag_session_continuity.py` 零改动（合并后即为真源守护） |

### D3 · 图谱与文档（必做 · 按实判零图谱变更）

- **图谱零变更义务 = 无**：不新增路由/表/事件类型；`session/continuity.py` 未在 `docs/_tech_graph/` 登记（grep 零命中）；`01_modules.md` chat 行 `app/ops/session/**` 路径覆盖与「Session 连续性（历史加载 · SSE replay 契约）」描述在删除后仍然为真（history/sse_replay 保留）。**若 30 阶段顺带更新 chat 行备注**（补「窗口压缩已并 lg_rag · session 侧已删」）属备注级顺手，非义务；若实现形态偏离（如决定改 re-export 方案）→ 新增 chat→lg_rag 依赖边，**必须**回 10-spec 修订本 SPEC 并补 HG-GRAPH-MODULES 行。
- `./scripts/graph-compile.sh` 绿（回归保险，非新增义务）。
- 不回改 done/归档历史文档（`docs/tasks/done/**`、`docs/spec/agent-infra/**` 中对 session/continuity.py 的提及是历史快照）。

---

## 3. 非范围

- ❌ 改压缩语义 / 占位符格式（`[历史摘要 · N 轮 · roles=...]` 一字不动 · 占位草案原文保留）
- ❌ 真摘要（另 SPEC `session-summary-fallback` · 占位草案原文保留）
- ❌ `lg_rag/continuity.py` 本体任何改动（含「顺手」把差异 ①② 回移植到别处、改默认值、改注释）
- ❌ `app/ops/session/` 其余文件（history.py / sse_replay.py / __init__.py 中 history·sse_replay 行）——chat 轨整体清退是另一波次的事
- ❌ `app/ops/chat/**` 任何清理（已 410 但代码/图/表保留 · `01_modules.md:22` 裁定沿用）
- ❌ 仓外消费者兼容（实扫证实仓内零消费者；仓外脚本若引用属其自身债，本 SPEC 不为此保留兼容层）
- ❌ 历史文档回改（done task / ROADMAP / reviews 中的提及保留为快照）
- ❌ 表结构变更（无 alembic 义务 · 本 SPEC 不触 DB）
- ❌ web / ios

---

## 4. 方案对比（R2）

### 单真源收敛形态

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 硬删除 + 测试收敛（本 SPEC）** | 删 `session/continuity.py`；`__init__.py` 同步移除 re-export；测试 compress_window 两用例删除（lg_rag 侧等价覆盖已在） | 物理消灭漂移源，债清零；零新依赖边（图谱拓扑不变）；实扫证实生产零消费者，删除安全有证据链；session 包是 legacy chat 残留（stream 已 410），留兼容层无受益人 | 不可逆一步（但 git 可回 · 且真源功能超集无损）；仓外假设消费者会断（已列非范围） | **推荐** |
| S2 · re-export 兼容层 | `session/continuity.py` 改为 `from app.ops.lg_rag.continuity import compress_window` | 保留 `app.ops.session.continuity` 导入面不炸 | **新增 chat→lg_rag 模块依赖边**（`01_modules.md` chat 行出边 `llm, db, rag` 无 lg_rag → 图谱拓扑污染 · 触发 HG-GRAPH-MODULES 义务）；session 包 import 链拖入 langchain_core + tracing（变重）；兼容层本身就是「留着入口的债」——漂移风险表面消失、模块拓扑债新增；生产零消费者使兼容层零受益 | 弃 |
| S3 · 双保留 + 注释钉同步 | 两文件互加「同步修改」注释 | 零删除风险 | 债原样保留，注释无强制力，正是当前烂局的成因 | 弃 |

### 测试处置

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 删两用例 · 对账 lg_rag 覆盖（本 SPEC）** | 逐条对账后删除（§2 D2 对账表） | 测试面同样单真源；lg_rag 侧断言等价或更强（多降级断言） | 需对账留痕（本 SPEC 已做） | **推荐** |
| S2 · import 迁移 | 两用例改 `from app.ops.lg_rag.continuity import ...` 保留 | 用例数不变 | 与 lg_rag 侧既有用例**完全重复**（同参数同断言）——重复测试 = 第二种双份债；且会让 test_session_continuity.py 名实不符（文件测 session 却 import lg_rag） | 弃 |

---

## 5. 边界 / 失败路径 / 安全（failure_paths）

| 触发 | 行为 | 可重试 |
|---|---|---|
| 隐藏运行时引用被删断（grep 未覆盖的动态 import / 字符串拼接模块名） | 动态 import 面已专扫（`importlib`/`__import__`/`import_string` grep · 命中均与 continuity 无关 · §1 引用面表）；残余风险由**全量 pytest 绿** + 启动冒烟兜底——`import app.main` 链路任一残留引用即 ImportError 显式炸，不静默 | Y（恢复文件或修引用） |
| `__init__.py` re-export 残留（删文件忘改 `__init__`） | `import app.ops.session` 包加载即 `ModuleNotFoundError`；tests/test_session_continuity.py（import sse_replay 触发包 `__init__`）必挂 → CI 红显式暴露；**变异检验 ② 专门钉死本路径** | Y（补改 `__init__.py`） |
| `__all__` 残留 `"compress_window"`（改了 import 忘改 `__all__`） | `from app.ops.session import *` 才触发；仓内零 star-import（grep 可证）；ruff F822（undefined name in `__all__`）若启用即拦截——验收含 ruff 绿 | Y |
| re-export 方案假设性循环导入（S2 已弃 · 留痕） | 若 30 阶段擅自改走 S2：session→lg_rag 新边 + lg_rag 禁令闸（`test_lg_rag_package_does_not_import_chat_or_session` 只扫 lg_rag→session 方向，**不拦反向**）→ 循环/拓扑债无测试兜底；故本 SPEC 把「禁走 S2」写进设计纪律 2 | — |
| 测试误删 sse_replay 覆盖 | §2 D2 明示 sse_replay 四用例保留；task/30 阶段 diff 审查核对删除行只涉 compress_window | — |
| lg_rag 侧覆盖不如声称（对账失真） | §6 变异检验 ①：删真源 `compress_window` 函数体 → lg_rag 侧测试必须 import 失败/断言挂；检验 ③：摘掉真源 try/except → `test_compress_window_failure_truncates_tail` 必须挂（证明差异 ① 的守护真实存在） | — |
| 图谱编译断裂 | `graph-compile.sh` 绿为验收项；`session/continuity.py` 未登记图谱，删除不触发索引失配 | Y |
| 仓外脚本引用（仓外不可扫面） | 显式列非范围；若真实存在 → ImportError 显式炸（非静默错），由消费方各自迁移到 lg_rag 真源 | Y |
| 误改真源（30 手滑改 lg_rag/continuity.py） | 验收含「真源零 diff」断言：`git diff master -- app/ops/lg_rag/continuity.py` 为空 | Y（revert） |

安全：纯删除型重构，无新凭证面、无网络面、无 DB 面；压缩输出格式零变化，无 prompt 注入面变化。

---

## 6. 验收标准

### D1 · 单真源

- [ ] `app/ops/session/continuity.py` 已删除；`app/ops/session/__init__.py` 无 `continuity` import 且 `__all__` 无 `"compress_window"`；history / sse_replay 两行原样
- [ ] **真源零 diff**：`git diff master -- app/ops/lg_rag/continuity.py` 输出为空
- [ ] grep 断言：全仓 `*.py` 搜索 `session.continuity` / `session/continuity` / `ops\.session import compress_window` 零命中（docs 历史快照除外）
- [ ] 无新增模块依赖边：`git diff master -- app/` 中无任何新增 `import` 行

### D2 · 测试收敛

- [ ] `tests/test_session_continuity.py`：compress_window 两用例与其 import 已删；sse_replay 四用例逐字保留
- [ ] 覆盖对账留痕（task 验收中引用 §2 D2 对账表）：被删两用例 ↔ lg_rag 侧等价/更强断言逐条对应
- [ ] `tests/test_lg_rag_session_continuity.py` 零改动且全绿（含 `test_lg_rag_package_does_not_import_chat_or_session` 方向闸）

### 行为零变化

- [ ] 全量 `pytest tests` 绿（删除前基线 == 删除后，用例数差值 == 2 且仅为被删两用例）
- [ ] 生产路径零改动：`git diff master -- app/` 只含 `session/continuity.py` 删除 + `session/__init__.py` 两行移除

### 变异检验（不验收空真规则）

- [ ] ① 删真源函数：临时摘掉 `lg_rag/continuity.py` 中 `compress_window` 定义 → `tests/test_lg_rag_session_continuity.py` import 即失败（证明测试真钉住真源）；恢复后全绿
- [ ] ② 残留炸显式：临时只删 `session/continuity.py` 不改 `__init__.py` → 跑 `tests/test_session_continuity.py` 必须 `ModuleNotFoundError` 挂（证明删断无静默路径）；补改 `__init__.py` 后全绿
- [ ] ③ 降级守护真实：临时摘掉真源 `compress_window` 的 try/except → `test_compress_window_failure_truncates_tail` 必须挂（证明差异 ① 已随单真源收敛到强版且有守护）；恢复后全绿

### 工程

- [ ] `ruff check app tests` 绿（`__init__.py` 残面 / 死 import 由 ruff 兜底）
- [ ] `./scripts/graph-compile.sh` 绿；图谱零变更裁定与实现形态一致（若 30 走了 re-export 或新增任何依赖边 → 本 SPEC 回炉）

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游手册 §1.2.2 已知债 M7；占位两块声称（「逻辑相同」「只被测试引用」）经实扫**双双纠正**：① lg_rag 版多 try/except 降级 + str 强转容错（差异实质 · 统一到 lg_rag 是真升级非取舍）；② `__init__.py:3` re-export 是生产面引用（但其下游消费者为零） | done |
| R1 | 范围 = D1 硬删除单真源 / D2 测试收敛（删 2 留 4 · 对账 lg_rag 覆盖）/ D3 图谱零变更按实判；非范围 = 压缩语义 · 占位符 · 真摘要（占位原文全保留）+ 真源零改动 · session/chat 其余文件 · 仓外兼容 · 历史文档回改 | done |
| R2 | 两组对比各 ≥2：收敛形态选硬删除（弃 re-export：新增 chat→lg_rag 依赖边污染图谱拓扑 + import 变重 + 零受益人；弃双保留+注释：债原样保留）；测试处置选删例对账（弃 import 迁移：与 lg_rag 侧用例完全重复 = 第二种双份债） | done |
| R3 | failure_paths 10 条，核心四条：隐藏动态引用靠专扫+全量 pytest+启动冒烟兜底（显式炸不静默）；`__init__` 残留由变异检验 ② 钉死；re-export 反向循环无测试闸 → 设计纪律 2 禁走 S2；真源零 diff 断言防 30 手滑 | done |
| R4 | 验收全为可执行断言：grep 零残留 · 真源零 diff · 用例数差值 ==2 · sse_replay 逐字保留 · 变异检验三条（删真源函数 / `__init__` 残留 / 摘 try/except 各致指定测试挂） | done |
| R5 | SPEC draft-complete 可交人签 HG-SPEC-SIGNOFF；签后 00 出 task（单 task 小波次，可独立交付不依赖并入他波） | done |
| early_stop | no | — |
| residual_risks | ① 仓外脚本引用属不可扫面（已列非范围 · 炸了显式）；② ruff F822 是否启用未核——若未启用，`__all__` 残留靠 §6 grep 断言与 diff 审查兜（不影响主路径）；③ 删除是不可逆一步，靠 git 历史与真源功能超集保证无损 | 签收时知悉 |

---

## 8. 下一棒

1. **维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`
2. **00**：起草 `docs/tasks/active/task_continuity_dedup.md`（范围 D1–D3 · failure_paths 沿用 SPEC §5 · 人工闸表按实判：无 HG-GRAPH-MODULES 义务除非实现形态偏离为 re-export/新增依赖边）
3. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1`
4. **30**：`task/continuity-dedup` 分支实现（删除 + `__init__` 同步 + 测试收敛 · 真源零触碰）
5. **40**：验收（含变异检验三条 + 真源零 diff 断言）→ PR（与 memory-facts-p0/p1 同模式）

### 下一棒可复制 Prompt（20-spec-audit 预审 / 00 起草 task）

```text
你是 ops-desk-api 仓（/Users/cyning/Desktop/Ops-desk/ops-desk-api）的 <20-spec-audit ｜ 00>。
SPEC：docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md（draft-complete · HG-SPEC-SIGNOFF=pending）。
<20-spec-audit>：书面审范围/非范围/验收/failure_paths 与 R0–R5 思考轮，结论落盘 docs/harness/reviews/，不代签人闸。
<00>：待维护者签 HG-SPEC-SIGNOFF=approved 后，按 SPEC §8 起草 docs/tasks/active/task_continuity_dedup.md（D1–D3 · failure_paths 沿用 SPEC §5 · 图谱闸按实判零变更 · 变异检验三条入验收）。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 占位稿（范围草案 + 锚点 + 验收方向 + 接续指引） |
| 2026-09-21 | 10-spec 补全：实扫两文件本体 diff 级对比（**纠正占位「逻辑相同」**：lg_rag 版多 try/except 降级 + str 强转容错，统一到 lg_rag 为真升级）· 引用面全仓 grep（**纠正占位「只被测试引用」**：`__init__.py:3` re-export 为生产面但下游消费者为零 · 动态 import 面专扫零命中）· 图谱登记实扫（session/continuity.py 零登记 → 零变更义务按实判）；方案对比两组（硬删除 vs re-export vs 双保留 · 删例对账 vs import 迁移）；failure_paths 10 条（含 `__init__` 残留炸显式 · re-export 反向循环无闸 · 隐藏动态引用）；验收断言化 + 变异检验三条；R0–R5 回填；track 裁定 `refactor`（无 alembic · 图谱零变更）；HG-SPEC-SIGNOFF 保持 pending 待人签 |
