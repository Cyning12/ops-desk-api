# invoke_20261115_30_implement

## 内容

30 实施：goals/inject.py 纯模块（闸三件套+GOAL_HEADER+GOAL_GUIDE+0.3s 上限）· store.find_active_goal 只读 · continuity importlib 运行期解析+wait_for 降级+归因第四分支 · slots SlotSpec guide 扩展+goal_objective 注册+_FORGE_ESCAPES 补双节首 · tests/test_goal_inject.py 9 件。

## 结果

- tests/test_goal_inject.py 9 passed（真 PG）。
- 回归 test_goal_store/input_isolation_wiring/prompt_slots/splittability/session_continuity/memory_injection(+consumer)：120 passed 1 skipped。
- ruff I001 一件（asyncio 导入序）--fix 修复，复检绿。

## 偏差记录

- test_prompt_slots::test_registry_covers_six_slots 红 → 六槽白名单断言按设计扩为七槽（goal_objective），改名 test_registry_covers_seven_slots；registry allowed_tree_files 同步补该文件。
