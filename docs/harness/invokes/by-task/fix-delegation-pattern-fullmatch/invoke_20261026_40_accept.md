# invoke：fix-delegation-pattern-fullmatch · 40_accept · 2026-10-26

- **hat**：40（交付验收 · 只验不改实质）
- **分支**：`task/fix-delegation-pattern-fullmatch`（自 master `e952984` 切出 · 验收时 HEAD=`1a9cae4`）
- **契约锚**：task 全文（验收 TC1–TC8 / failure_paths FP-1~FP-6 / 非范围 / freeze_id）+ 20-task-audit R2 §一 B1 实证表（grep 对拍基线）+ 30 invoke（`invoke_20261026_30_implement.md`）
- **写入面**：本 invoke + task 修订记录 40 验收行（仅此两处 · 其余文件零触达 · 未动 `docs/arch-browser/dist/site-data.json`）

## 一、提交与改动面（验收清单 1）—— PASS

- `git log master..HEAD` 四 commit 与派单逐一对拍：
  - `dd9f50a5e644498160598b7cee5d3391fde44fa8` docs(harness)：task 落稿 + 10 invoke + R1/R2 审查
  - `b9689a0e59276c46fdb5bdcaf1182a5767a9ff50` fix(capability)：pattern 改 re.fullmatch + 测试
  - `200b4b26d516bbd0275ae2e988f71674abfda233` docs(graph)：01_modules 备注 + 闸登记表行
  - `1a9cae4b3b65375b9e2f69d16fad59496928157f` docs(harness)：30 invoke 回填 + task 修订记录 30 行
- `git diff master...HEAD --stat`：8 文件 = `app/ops/capability/delegation.py`(+8-3 含上下文) + `tests/test_capability_delegation.py`(+54) + `docs/_tech_graph/l1/01_modules.md`(+4-2) + task/10 invoke/30 invoke/R1/R2 五份 harness docs ✓ 改动面零越界

## 二、diff 精读（验收清单 2）—— PASS

- `delegation.py` 全 diff 仅两块：① `check_param_constraints` docstring（:290 起）补「pattern 约束按整串匹配（re.fullmatch · fail-closed 收紧）…」三行；② :305 `re.search(rule[_CONSTRAINT_PATTERN], value)` → `re.fullmatch(...)` 一行（行号随 docstring 增量 +1，task 锚 :304 按实校正成立）
- 禁动面零触达（diff 佐证）：enum 分支（:297 区）、max_len 分支（:299-302 区）、`validate_param_constraints`（:252）、`app/ops/capability/gateway.py`（不在 diff 文件清单）
- 测试 diff 仅追加 TC1–TC5 五个用例（既有 `test_constraint_pattern_pass_and_fail` :233-237 零 diff 对照保持）；图谱 diff 仅 :34 行内备注 + :132 闸登记表新行

## 三、验收 TC1–TC8 逐项（验收清单 3/5/6）

| TC | 内容 | 结论 | 证据 |
|---|---|---|---|
| TC1 | `\d+`+"123abc" → 拒（reject_class + violated_field="q"） | PASS | `test_constraint_pattern_fullmatch_rejects_substring_hit` 断言三项齐 |
| TC2 | `^[a-z]+$`+"abc\n" → 拒 | PASS | `test_constraint_pattern_fullmatch_rejects_trailing_newline` |
| TC3 | `^[\w./-]+$`+"../../etc/passwd\n" → 拒（两态判别） | PASS | `test_constraint_pattern_fullmatch_rejects_path_traversal_newline` 值与 task :113 逐字一致；本帽 python3 复证：search(v1)=True/fullmatch(v1)=False · search(v2)=fullmatch(v2)=True（原值归因=纯字符集过宽 out_of_scope 成立，与 R2 §一 B1 表逐格一致） |
| TC4 | 正向防误伤 `\d+`+"123"、`^[a-z]+$`+"abc" → 通过 | PASS | `test_constraint_pattern_fullmatch_positive_no_false_reject` |
| TC5 | 非 str（int/list/None）→ 拒 | PASS | `test_constraint_pattern_fullmatch_rejects_non_str` parametrize 三值 |
| TC6 | 目标文件 42 passed · 既有委派测试零 diff · ruff 绿 | PASS | `.venv/bin/python -m pytest tests/test_capability_delegation.py -q` → **42 passed in 0.06s**（本帽重跑）；ruff 见下 |
| TC7 | 图谱回写 + graph-compile EXIT=0 | PASS | 01_modules.md **:34** capability 行 delegation 段备注「参数约束 pattern=re.fullmatch 整串匹配（fail-closed 收紧 · 2026-10-26 fix-delegation-pattern-fullmatch）」亲读在文；**:132** 闸登记表新行（维护者签「在册」· 承 :130 先例 · 格式逐字段对拍 :130 成立）亲读在文；`./scripts/graph-compile.sh` 本帽重跑 **EXIT=0**（各 flow OK · mermaid normalize 9 md OK） |
| TC8 | `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | PASS | 本帽重跑：**LINT-WIKI-DELTA: PASS**（scanned 191 · issues 0）· 命令与 task :118 / CI `.github/workflows/lint-wiki-delta.yml:39` 钉版逐字一致 |

## 四、全量 pytest 对拍（验收清单 4）—— PASS（零新增失败）

- 本帽重跑 `.venv/bin/python -m pytest tests -q`：**38 failed / 1731 passed / 184 skipped** —— 与 30 invoke 留痕数目逐项一致
- FAILED 清单 38 条全量落 `/tmp/pytest40_failed.txt` 亲读分类：含 `tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist`（wave 锚点守护 1 项 ✓）；其余 37 项分布于 lg_rag http/sse/session/hitl/react/strategy/capability eval 等 —— **无任何 delegation 相关失败**；抽查 `test_lg_rag_http.py::test_invoke_basic_mode_dispatch` 失败根因 = asyncpg/SQLAlchemy 连库 500（工作区 `.env` 既有噪声，与 30 对拍结论一致）
- 结论：零新增失败，承 task TC6 对拍口径成立

## 五、freeze_id 核验（验收清单 7）—— PASS

diff master...HEAD 文件面 = delegation.py（docstring+一行）/ 测试 / 图谱备注 / harness docs。拒绝码 R-a~R-f / 审计词表 / TTL 600s / 三档模式默认值（`LG_RAG_DELEGATION_TOKEN_MODE` 默认 off）/ SSE（lg-rag-sse-v1）/ HTTP（lg-rag-http-v1）**全零变更**——diff 未触 gateway.py / lg_rag / 任何 freeze 面文件，佐证成立

## 六、工作区卫生（验收清单 8）—— PASS

- `git status --short`：仅 `M docs/arch-browser/dist/site-data.json`（别人分支既有 M · 全程未触碰未 commit）✓
- 分支无 push：`git status -sb` 无 upstream 跟踪 · `git ls-remote origin refs/heads/task/fix-delegation*` 零命中 ✓

## 七、验收结论

**PASS（建议开 PR）**。逐项亲验无 FAIL 项：四 commit 与改动面零越界 · 一行修法+docstring 精确落点 · TC1–TC8 全绿（TC3 两态判别 python3 复证）· 全量 38 failed 与 base 对拍一致零新增 · freeze 全零变更 · 禁 push/禁动 site-data.json 遵守。遗留：宽字符集路径穿越（`^[\w./-]+$`+"../../etc/passwd" 原值）已登记 task out_of_scope 另 task，不阻塞本 PR。

## 八、验收边界声明

本帽只验不改实质：唯一写入面 = 本 invoke + task 修订记录 40 验收行；未改 app//tests/ 任何代码 · 未代签任何人闸 · 未 push · 未开 PR · 未触碰 `docs/arch-browser/dist/site-data.json`。
