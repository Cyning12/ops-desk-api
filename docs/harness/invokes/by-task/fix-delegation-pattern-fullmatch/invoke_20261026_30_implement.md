# invoke：fix-delegation-pattern-fullmatch · 30_implement · 2026-10-26

- **hat**：30（实施 · 红测先行）
- **分支**：`task/fix-delegation-pattern-fullmatch`（自 master `e952984` 切出 · base 与 origin/master 一致 · 工作区 M `docs/arch-browser/dist/site-data.json` 随切分支带走未触碰）
- **契约锚**：task（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 approved）+ 20-task-audit R1（fail·B1/B2/B3）/R2（pass）审查文 + SPEC host-v1-delegation-token :67
- **写入面**：app/ops/capability/delegation.py（:304 一行 + check_param_constraints docstring）· tests/test_capability_delegation.py（新增对抗用例 TC1–TC5）· docs/_tech_graph/l1/01_modules.md（capability 行 delegation 段备注 + 闸登记表新行）· 本 invoke。gateway.py / validate_param_constraints(:252) / enum(:297) / max_len(:299-302) 零触达。

## 〇、GATE_VERIFY（30 首输出闸扫描 · 真值以 task 人工闸表为准）

| human_gate_id | task表status | 30可开工？ |
|---|---|---|
| HG-TASK-DRAFT | approved | — |
| HG-AUDIT-R1 | approved | ✅ |
| HG-GRAPH-MODULES | approved（graph_change_layer=none 预期 · 承 01_modules.md:130 在册先例） | 条件满足（不阻塞） |

`npx spec-wave verify --target . --task docs/tasks/active/task_fix_delegation_pattern_fullmatch.md` → **VERIFY: PASS**（EXIT=0）；reviews R1/R2 均在册；pre-30 invoke hats（10/30）齐。

## 一、兼容性复扫（FP-4 · 红测前对拍 00 预扫）

- `grep -rn "pattern" app/ops/capability/manifests/*.yaml` → 零命中（EXIT=1）✓
- 全仓 `param_constraints` 出现点：app 侧仅 delegation.py 十五处（:178,195,225,239,252,262,265,268,289,291,405,425,426,454,555 · 与预扫逐一对拍一致）+ tests/test_capability_delegation.py + SPEC/task/review/invoke 文档 ✓ **零漂移**
- 模块内 `re.search` 唯一命中 :304；docstring/注释无显式 search 语义描述（:248 节注释与 :290 docstring 均未写匹配语义）——语义描述补写于 check_param_constraints docstring（「整串匹配（fullmatch）」）

## 二、红测先行记录

对**未改** delegation.py 跑 `.venv/bin/python -m pytest tests/test_capability_delegation.py -q -k "pattern"`（系统 python3 缺 asyncpg · 用仓内 .venv）：

- **3 failed**：TC1 `\d+`+"123abc"、TC2 `^[a-z]+$`+"abc\n"、TC3 `^[\w./-]+$`+"../../etc/passwd\n" 均 `AssertionError: assert True is False`（verdict.ok=True 即 re.search 放行 · **红如预期**）
- **5 passed**：TC4 正向 ×1 + TC5 非 str ×3 + 既有 `test_constraint_pattern_pass_and_fail`（:233-237 · ^[0-9]+$ 已锚定）
- 插曲：新 docstring 内裸 `\d`/`\w` 触发 DeprecationWarning（invalid escape sequence）→ 四个 docstring 改 `r"""` 前缀消除（零行为变更）

## 三、实施

- delegation.py:304 `re.search(rule[_CONSTRAINT_PATTERN], value)` → `re.fullmatch(rule[_CONSTRAINT_PATTERN], value)`（**一行** · commit b9689a0）
- check_param_constraints docstring 同步（:290 起）：pattern 约束按**整串匹配**（re.fullmatch · fail-closed 收紧）· 未锚定 pattern 不退化子串包含 · `$` 不匹配换行前
- 禁动面核验：enum(:297)/max_len(:299-302)/validate_param_constraints(:252)/gateway.py 零触达（git diff 仅 :290 docstring 块 + :304 一行）

## 四、转绿与验证面

| 验证 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `.venv/bin/python -m pytest tests/test_capability_delegation.py -q` | **42 passed**（TC1–TC5 全绿 · 既有委派验签测试零 diff） |
| 全量 pytest | `.venv/bin/python -m pytest tests -q` | 38 failed / 1731 passed / 184 skipped；与 base `e952984` worktree（**拷入同份 .env** 对拍）FAILED 清单 **IDENTICAL 38 项**（既有 .env 噪声 + `test_tc8_diff_whitelist` wave 锚点守护 · 本 task 零新增失败） |
| ruff | `.venv/bin/ruff check app tests` | **All checks passed!** |
| graph-compile | `./scripts/graph-compile.sh` | **EXIT=0**（各 flow OK · mermaid normalize check 9 md OK） |
| TC8 | `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | **LINT-WIKI-DELTA: PASS**（scanned 191 · issues 0） |

## 五、graph_delta 落点

- `docs/_tech_graph/l1/01_modules.md` **:34** capability 行 delegation 段备注：「参数约束 pattern=re.fullmatch 整串匹配（fail-closed 收紧 · 2026-10-26 fix-delegation-pattern-fullmatch）」（commit 200b4b2）
- 同文 **:132** 闸登记表新行（承 :130 delegation-naming-boundary「在册」先例格式）：fix-delegation-pattern-fullmatch 回写一行（不新增一级模块 · 零新跨模块边 · 不增 implementedBy · 零新路由/表/SSE 事件类型）

## 六、偏差登记

1. 全量 pytest 无法「全绿」：工作区 `.env` 在场致 37 项既有噪声失败 + `test_tc8_diff_whitelist` wave 锚点守护失败，base e952984 同条件对拍 IDENTICAL——本 task 零新增失败，既有委派验签测试零 diff（承 task TC6 对拍口径）。
2. 新测试 docstring 由 `"""` 改 `r"""`（消除 DeprecationWarning · 零行为变更）。
3. 基线对拍用 `git worktree add /tmp/od-base-master e952984` 并拷入 `.env`（未动主工作区任何文件 · 对拍毕即清理 worktree）。
4. 禁 push/禁 PR 遵守：仅分支本地 commit（dd9f50a docs · b9689a0 代码+测试 · 200b4b2 图谱 + 本条 invoke/task 记录 docs commit）。
