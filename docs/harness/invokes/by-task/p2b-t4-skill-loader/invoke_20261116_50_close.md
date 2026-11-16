# invoke_50 · close（p2b-t4-skill-loader）

## 内容

50 CLOSE 关账：feat PR #410 squash merge 完成（wave_tip=e7609269），registry
status active→closed 钉 wave_tip，task 档 active→done（回填状态行与关联 PR）。

## 验证台账

| 项 | 结果 |
|---|---|
| feat PR | #410 · squash merge `e7609269` |
| CI 四绿 | pytest pass (2m54s) · check pass · import-linter pass · lint-wiki-delta pass |
| wave_tip | `e7609269`（feat(p2b-t4-skill-loader): … (#410)） |
| registry | status=closed · base=bf1c23f2 · wave_tip=e7609269 |
| task 档 | docs/tasks/active/ → docs/tasks/done/task_p2b_t4_skill_loader.md |
| 全量 pytest（rebase 后净树） | 2218 passed, 2 skipped（·两守卫净树 3 passed） |
| ruff / graph-compile | `ruff check app tests` 绿 · `./scripts/graph-compile.sh` 绿 |
| §9.2 六项注入证据 | a 逐字节+零调用 · b catalog ≤max_chars · c skill_ref 全文注入逐字节 · d 未知 ref fail-open span · R9b off/on schema 对拍（7 例全绿） |
| workspace 侧 | `ops-desk-workspace@1c3b879` skills/panel-data-guide/SKILL.md + skills/README.md 作者指南（直推 main） |

## 偏差终录

1. **D1 · SlotBlock.content 坑**：`wrap_slot` 返回 `SlotBlock` 是 str 子类**无**
   `.content` 属性——`nodes.py::_worker_state` 注入改隐式 str 拼接
   `task["input"] + "\\n\\n" + skill_block`；冒烟逐字节核过（input+两换行+SKILL.md
   全文含 frontmatter）。
2. **D2 · rebase 冲突处置**：并行 P2b-T1 先合 master（64791fc5/ea63843b），本波
   rebase 四件冲突（capability/adapters 两 `__init__.py` · `adapters/mcp.py` UD
   · `01_modules.md` 双段）；解法 master 为基重放本波（三 import/docstring 删除 ·
   mcp.py 保删除 · 01_modules 保 T1 capability 行+本波 lg_rag 行 · 签收行双方并留）；
   rebase 后全量 pytest 2218 passed + ruff + graph-compile 复绿。
3. **D3 · policy 门坑**：gateway boom 用例原 MockMcpAdapter 换 cli 撞
   `cli_disabled`、换 sandbox 撞 `sandbox_disabled`——终解 kind=sandbox +
   `invoke(ctx={"_host_policy": {"allow_sandbox": True}})`（policy.py:105 闸序
   host 键放行），异常串 sandbox-probe-boom。
4. **D4 · .venv 符号链接误入库**：rebase 解冲突 `git add -A` 把 untracked `.venv`
   symlink 卷入提交 d7de960e，CI import-linter `uv venv` File exists 挂起暴露；
   `git rm --cached` + amend 剔除（64c05250）· 仅符号链接无内容泄漏 · master
   树确认零 venv 残留。
5. **D5 · 脏树守卫两红机制**：全量 pytest 中 `test_tc8_diff_whitelist` /
   `test_wave_gate_registry` 红为在途未提交 app/ 面咬 registry closed entries
   （fail-closed 设计如此）· 净树复跑 3 passed · 非本波回归。
6. **D6 · `_issue_plan` stamped 白名单**：plan 签发固定键白名单原丢 `skill_ref`，
   补透传两行（`if item.get("skill_ref"): stamped["skill_ref"] = str(...)`）·
   e2e 测试 c 捕获。

## 结果

CLOSE GO · P2b-T4 关账完成。skill 面可用：`OPS_SKILL_LOADER_ENABLED=true` +
workspace `skills/<name>/SKILL.md` 目录包（作者指南见 workspace skills/README.md）。
