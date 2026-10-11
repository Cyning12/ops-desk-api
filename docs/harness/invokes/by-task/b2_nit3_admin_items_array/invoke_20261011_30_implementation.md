# invoke：30-实现（b2_nit3_admin_items_array · 2026-10-11）

> **帽位**：30-implementation（红测先行 → 实现 → GREEN → 全量验收）
> **task**：`docs/tasks/active/task_b2_nit3_admin_items_array.md`（三闸 approved · R1 审查在案）
> **worktree/分支**：`ops-desk-api-worktrees/t-b2-nit3-admin-items-array` · `task/b2-nit3-admin-items-array`（未切分支）
> **委托**：父 agent 30 棒委派令（红测先行 TC1–TC6 · invoke 本档 · commit feat 前缀带 slug → push → PR → 回报）

## 闸验证（首输出 · 重定向取真码）

`npx spec-wave verify` → **EXIT=0**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 approved 一致，30 解锁条件成立。

## 改动清单（git diff HEAD 实证）

| 文件 | 改 | 要点 |
|---|---|---|
| `app/ops/admin/capability.py` | 改 | ①导入增 `evaluate_visibility`/`get_registry`（包顶既有导出 · 未动 `__init__.py` 公共面）+ `CapabilitySpec`；②新增 `_project_catalog_item(spec, hidden)` 14 键精确投影（`capability_id`→`id` 承 capability_mine `project_capability` 先例 · adapter/args_schema/http/idempotency_key/hitl_* 不出站）；③`catalog` 路由增顶层 `items` 键：`get_registry().list_specs()` 全量在册（含 disabled）→ `evaluate_visibility(specs, principal)` hidden 条目按 id 索引 → 逐条投影按 id 排序 |
| `tests/test_admin_capability_catalog_items.py` | 新 | TC1 全覆盖+14 键集精确+denied 对拍 evaluate_visibility 直出+恒出键 None；TC2 既有 10 键在场+与 `capability_catalog_snapshot` 直出逐键对拍+三组 query 下 items 覆盖集不变；TC3 register/unregister try/finally 三探针 disabled/denied:department_mismatch/visible；TC4 响应体禁 `adapter|local_fn:|`+`args_schema|secret_param|PROBE_BASE_URL` 子串 |
| `tests/test_capability_manifest.py` | 改（NIT-3） | :334/:359 两处 `meta` 断言前加 `set(meta.keys()) == {"version", "capability_manifest_count"}`（键集相等升级 · 被测面零 diff） |
| `tests/test_admin_capability_manifest_errors.py` | 改 | TC2 键面并集增 `"items"`（预期内涟漪：items 是本任务交付的新增顶层键 · 既有键逐键零 diff 断言 :104 未动） |

零新依赖 · 零新 env · 零 `.importlinter` 改动 · 零迁移。

## 关键实现裁定（留痕）

**denied 判定复用 `evaluate_visibility` hidden 条目，不直导 visibility 子模块**。初版实现 `from app.ops.capability.visibility import VISIBILITY_REASON_TEXTS` + 路由内 `check_visible` 直判，被 admin-outbound forbidden 契约拦（lint-imports 逐项白名单不覆盖 `capability.visibility` 子模块 · `tests/test_splittability_hardening.py` D2 双用例红）。改走任务文件 :61 本意：包顶已导出 `evaluate_visibility`（`__init__.py:101`），其 summary `visibility_hidden` 条目自带 `reason` + `visibility_reason` 中文映射（visibility.py:135-141 · 词表单源 · 未知码原样兜底）——路由层零重算，且 `disabled` 优先判定在投影层承 `registry._match_filter` 首判语义。比直导更贴单源（码+文本一体），零契约改动零公共面扩张。

## 红测 RED → GREEN 实证

- **RED**（实现前）：TC1/TC2/TC3 FAILED `KeyError: 'items'`；TC4 空转绿（items 未出响应时无泄露面 · 实现后咬合 · 照实录）；TC5 目标用例 `test_s3b_metadata_and_explicit_reload` 基线即绿（断言补强面已合规 · NIT-3 属测试加固非行为修复 · 照实录）。
- **GREEN**（实现后）：新测试文件 4 件 + TC5 + 受击面（manifest_errors 全文件、splittability D2 双用例）共 11 件全绿。

## 验收矩阵

| 验收项 | 结果 | 实证 |
|---|---|---|
| pytest 全量（1787 passed · 6 failed） | ✅ 零回归 | 6 红逐项钉案全环境性：①`test_hitl.py::test_db_store_alist_really_executes_on_asyncpg` ②`test_multi_replica_dualproc.py::test_hitl_cross_instance_resume` ③`::test_resume_without_checkpointer_503` —— **主仓基线同红**（钉案「4-7 红环境性」命中）；④`test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker` ⑤`test_memory_embedding_backfill.py::test_write_recheck_race_marks_skipped` ⑥`::test_preflight_bad_dimension_exit_2` —— worktree 无 `.env` 缺 `SILICONFLOW_API_KEY`（`RuntimeError: 缺少 SILICONFLOW_API_KEY` embedder.py:81），**带主仓 `.env` 复跑 3 件全绿**（主仓基线亦绿） |
| dualproc parity | ✅ | `test_runtime_scope_and_catalog_parity` 绿（visible_ids 多副本对拍零 diff · items 不入对拍面符合既有契约） |
| ruff check（三改动文件） | ✅ | All checks passed（ruff 0.15.21 锁版对齐） |
| ruff format --check | ⚠️ 分支既有漂移 | `capability.py`/`test_capability_manifest.py` 未过，但全部 hunk 落在**本棒未触的既有行**（:78/:96/:229/:310 等）· **主仓锁版 ruff 0.15.21 基线同挂这两文件** → 非本棒引入；本棒新增码面（投影函数/items 块/新测试文件）零 format 命中。遵「勿当回归修」不修 |
| lint-imports | ✅ | Contracts: 12 kept, 0 broken（EXIT=0） |
| `./scripts/graph-compile.sh` | ✅ | EXIT=0 · `docs/_tech_graph/shared/graph.json` 噪音已 `git checkout` 还原 |
| `npx spec-wave task lint --file <task>` | ✅ | LINT: PASS（W3 自检占位符提醒属 draft 期合法 · close 棒回填义务在案） |
| `uv.lock` 噪音 | ✅ 已还原 | uv run 自动改写 103 行 · `git checkout HEAD -- uv.lock` 还原，终态 diff 不含 |

## 环境坑留痕（worktree 冷启动）

1. worktree 无 venv：`uv pip install -r requirements.txt` + `uv pip install -e ".[dev]"`（dev 在 `project.optional-dependencies`，非 dependency-groups · `uv sync --group dev` 会报 Group not defined）。
2. **测试须 `uv run python -m pytest`**：裸 `uv run pytest` 命中 venv 外 pytest 9.1.1（pyproject 钉 <9），conftest `import asyncpg` 炸 ModuleNotFoundError。
3. `.env` 不随 worktree 分发：embedder/backfill 三件需 `SILICONFLOW_API_KEY`，对拍时显式 source 主仓 `.env`。
4. `git stash pop` 部分应用坑：stash 含 uv.lock 时 pop 冲突会留 stash entry 且两改动文件未落盘——须 `git checkout stash@{0} -- <files>` 取回再 drop（本棒实操实证）。

## 遗留 / 移交 40 棒

- `tests/test_capability_manifest.py` F811 四件（:468/:476/:554/:581 被 :523/:531/:597/:624 重定义）为**分支基线既有**（git stash 实证 HEAD 同挂）· 未动 · 留 00 知悉。
- 任务文件 W3 自检结论占位符待 close 棒回填。
