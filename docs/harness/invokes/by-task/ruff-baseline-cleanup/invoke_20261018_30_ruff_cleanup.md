# Invoke：ruff-baseline-cleanup · 30 修复执行（2026-10-18）

> **帽位**：30-exec（worktree /Users/cyning/Desktop/Ops-desk/ops-desk-api-worktrees/t-ruff-cleanup · 分支 task/ruff-baseline-cleanup · base master c956d87）
> **闸**：spec-wave verify EXIT=0 · HG-TASK-DRAFT/HG-AUDIT-R1 approved（m01101 授权代录）· HG-GRAPH-MODULES n/a（graph_change_layer=none）
> **纪律**：ruff 钉 0.15.21 未升级 · 未启用 --unsafe-fixes · 零业务语义变更 · format 独立 commit 零手改混入

## 一 · 修复前后 statistics 对比（TC-RC-1/2/3）

修复前（master c956d87 亲跑复核，与 10/20 invoke 一致）：

| 规则 | 前 | 后 | 处置 |
|------|----|----|------|
| F811 redefined-while-unused | 9 | 0 | F2 人工裁定（§二 逐对裁定表） |
| I001 unsorted-imports [*] | 9 | 0 | F1 --fix |
| C408 unnecessary-collection-call | 7 | 0 | F2 手工 dict()→字面量 |
| SIM117 multiple-with-statements [*] | 7 | 0 | F1 --fix |
| E402 module-import-not-at-top-of-file | 5 | 0 | F2（noqa 留痕×2 + 上移×3） |
| SIM300 yoda-conditions [*] | 4 | 0 | F1 --fix |
| UP035 deprecated-import [*] | 3 | 0 | F1 --fix |
| F401 unused-import [*] | 2 | 0 | F1 --fix |
| UP045 non-pep604-annotation-optional [*] | 2 | 0 | F1 --fix |
| C401 unnecessary-generator-set | 1 | 0 | F2 手工 set comprehension |
| N814 camelcase-imported-as-constant | 1 | 0 | F2 去别名用原名 |
| N818 error-suffix-on-exception-name | 1 | 0 | F2 noqa 留痕不改名（task 明裁） |
| UP034 extraneous-parentheses [*] | 1 | 0 | F1 --fix |
| **合计** | **52** | **0** | `uv run --extra dev ruff check app tests` → Found 0 errors（exit 0）✅ |

- ruff --version：修复前后均 **0.15.21**（uv.lock:1831-1835 · pyproject.toml:47 specifier 未动）
- commit 序列：cd6d8af docs 三件套 → 65115f9 F1 → bc9c34b F2 → 710521c F3 format → 66a36eb F3 连锁 noqa 位移 → 67ef5a4 F4 CI

## 二 · F811 逐对裁定表（TC-RC-3 核心交付）

方法：AST 提取每对先定义/遮蔽定义**含装饰器栈全文本**逐字节比对（禁信转述，亲跑脚本实证）。

| # | 对名（文件） | 先定义行→遮蔽行 | 一致/发散 | 裁定 | 理由 |
|---|--------------|------------------|-----------|------|------|
| 1 | test_r10_declared_contract_rejects_nonconforming_result（tests/eval/test_capability_redlines.py） | 572-615 → 777-820 | **IDENTICAL** | 删先定义留后定义 | 逐字节全等，先定义为遮蔽死码 |
| 2 | test_r10_is_not_vacuous（同上） | 618-634 → 823-839 | **IDENTICAL** | 删先定义留后定义 | 同上 |
| 3 | test_r11_session_budget_and_kill_switch_block_before_downstream（同上） | 640-700 → 845-905 | **IDENTICAL** | 删先定义留后定义 | 同上 |
| 4 | test_r11_kill_switch_disables_capability（同上） | 703-741 → 908-946 | **IDENTICAL** | 删先定义留后定义 | 同上 |
| 5 | test_r11_is_not_vacuous（同上） | 744-765 → 949-970 | **IDENTICAL** | 删先定义留后定义 | 同上 |
| 6 | test_output_schema_bad_shape_rejected（tests/test_capability_manifest.py） | 459-473 → 514-528（含 parametrize 装饰器栈） | **IDENTICAL** | 删先定义留后定义 | 同上 |
| 7 | test_output_schema_valid_shape_loads（同上） | 476-493 → 531-548 | **IDENTICAL** | 删先定义留后定义 | 同上 |
| 8 | test_environmental_failure_classification（同上） | 554-578 → 597-621 | **IDENTICAL** | 删先定义留后定义 | 同上 |
| 9 | test_http_capability_error_exposes_structured_cause（同上） | 581-591 → 624-634 | **IDENTICAL** | 删先定义留后定义 | 同上 |

九对全 IDENTICAL → 零发散对 → 无停派上抛项。删除合计 262 行死码；pytest 通过数前后均为 1828（死码本就从未被收集运行，删之不减测试数）。

## 三 · F1 逐类复核记录（TC-RC-2）

全量 diff（14 文件 +95/-93）逐行亲核：

| 类 | 处数 | 复核结论 |
|----|------|----------|
| I001 | 9 | 纯 import 排序（含 isort order-by-type 常量优先，如 test_hitl.py STATUS_* 前移 DbHitlStore 前）· 无语义变更 |
| SIM117 | 7 | 嵌套 `async with` 合并为单层（idempotency.py×3 · receipts.py×1 · observability×2 · persistence_db×1）· 进入/退出顺序等价 |
| SIM300 | 4 | yoda 翻转（`_BUILTIN_IDS <= ids` → `ids >= _BUILTIN_IDS`）· 等价 |
| UP035 | 3 | typing.Iterator/Callable → collections.abc（circuit.py · tokenizer.py · redlines.py）· 等价 |
| UP045 | 2 | Optional[RunnableConfig] → RunnableConfig \| None（nodes.py×2）· 等价 |
| UP034 | 1 | manifest.py `set((...))` 去多余括号 · 等价 |
| F401 | 2 | nodes.py 删未用 CapabilityFilter · test_react_observe.py 删未用 get_hitl_store · 均为真未用 |

结论：28 处零语义可疑项，无需剔出类转人工。F1 后 52→24（恰剩人工裁定集）。

## 四 · F2 余项裁定（TC-RC-3）

- **C408×7**：七处 `dict(k=v)` 手工改字面量 `{"k": v}`（redlines.py:114 · domain_allowlist.py:50 · http_adapter.py:59 · idempotency.py:70 · persistence_db.py:165,227 · visibility_and_receipts.py:44）· 未启用 unsafe-fixes。内层 `dict(_ARGS)` 等拷贝调用不在 C408 面内，未动。
- **C401×1**：nodes.py:1922 `set(str(s) for s in ...)` → `{str(s) for s in ...}`；消费方仅 `|= approved` 与集合成员判断，集合语义自足。
- **N814×1**：observability.py:219 `GenericHttpAdapter as _A`。试改小写别名触发 N813（camelcase-as-lowercase）→ **终裁：去别名直接用原名**（函数内局部 import，无同名冲突），:235 同步。零语义变更。
- **N818×1**：circuit.py:77 `class CircuitOpen(Exception)` 加 `# noqa: N818 - 公开异常名，改名属 API 语义变更（另立 task）` · 遵 task 明裁不改名。
- **E402×5**：
  - http_generic.py:65-66 有意布局（:63-64 注释与 :66 既有 noqa:F401 互证）→ 加 noqa 留痕：:65 `# noqa: E402, I001`（I001 因独立 import 块连锁，一并注记）· :66 `# noqa: F401, E402`。
  - test_lg_rag_sse_token_stream.py:32,33,39 → **上移** import 至模块 import 块（fixture 仅测试期执行，import 时序无依赖，上移零语义变更；仓内 conftest/test_memory_episode_recall 的 noqa:E402 惯例属「先设 env 再 import」真有依赖，本处无此依赖故不采 noqa）。

## 五 · F3 format 收口（TC-RC-4）

- 前：`ruff format --check app tests` → **223 would reformat / 103 ok**（app 115/74 · tests 108/29）。
- 执行：`uv run --extra dev ruff format app tests` → 223 reformatted · commit 710521c **纯机器产物零手改混入**（223 文件 +1972/-2481）。
- 后：`ruff format --check app tests` → **326 files already formatted**（exit 0）✅
- 连锁 ×1：format 重排 test_hitl_approved_replan_quality.py TC2 签名致既有 `# noqa: F811` 注记从承载行（cap_env 行）漂到 caplog 行 → F811 复现 1 处。独立 commit 66a36eb 移注回 cap_env 行（零逻辑变更）→ check 复归 0。
- 无新增红 / 无 import-linter 破约（见 §六）→ 不回退，一次性收口成立。

## 六 · pytest 硬闸对拍（TC-RC-6 · FP-6 实证）

| 跑法 | 结果 | 说明 |
|------|------|------|
| worktree 无 .env 全量 | 4 failed / 1843 passed | 环境差：缺 SILICONFLOW_API_KEY → test_memory_vector_p1::test_embedder_failure_degrades_with_marker 伪新增红；基线 19 红中 15 条环境敏感项转绿 |
| **worktree 拷入主仓 .env 全量（对拍口径）** | **19 failed / 1828 passed / 1 skipped（66.56s）** | **FAILED 清单与 10 invoke §四 基线 19 红集逐名全等 · 零新增红 · 通过数 1828=1828 分毫不差** ✅ |

结论：红集 ⊆ 基线（实为全等）；无 .env 跑的差异全部可归因环境面（.env 在基线环境存在、worktree 初始缺失），本 task diff 零责任。FP-6 按「环境抖动 → 复跑实证 + 逐名对拍」路径关闭。

## 七 · F4 CI 接闸（TC-RC-5 · 维护者签注 m01101 明裁钉版）

- `.github/workflows/pytest.yml`：安装面 `"ruff>=0.5,<1"` → **`"ruff==0.15.21"`**（与 uv.lock:1831-1835 同源 · FP-7 禁漂移写法 · 顺手消 R1 nit N1）；解开 :52-53 注释段改写为生效步骤：
  ```yaml
  - name: Ruff
    run: .venv/bin/ruff check app tests
  ```
- 与既有 uv venv + uv pip 安装面一致（不用 uv run 免 sync 全项目）。
- 本 PR 含 CI workflow 改动，PR 描述已显式注明。

## 八 · 零越界核验（TC-RC-7）

`git diff --name-only master...HEAD` 全部落在白名单：app/** 与 tests/** 的 lint/format 修复 + .github/workflows/pytest.yml + docs/harness/{invokes,reviews}/ + docs/tasks/active/task_ruff_baseline_cleanup.md。pyproject.toml / uv.lock / alembic / docker-compose.yml / 图谱 / Wiki **零 diff**；ruff 仍 0.15.21。

## 九 · 门禁实录（30 亲跑）

- 开工：`npx spec-wave verify --target . --task docs/tasks/active/task_ruff_baseline_cleanup.md` → **EXIT=0 · VERIFY: PASS**
- 收尾复跑：verify EXIT=0 · `spec-wave task lint` LINT: PASS（见任务档自检结论节回填后实录）

## 十 · 交接

- 40/维护者：验收锚点 = §一 statistics 0 错 · §五 format 326 ok · §六 19 红集全等 · §七 CI Ruff 步骤绿（PR CI 实证）。
- 残余风险：无发散 F811 挂起项；CI 首次跑 Ruff 步骤若绿即闭环。
