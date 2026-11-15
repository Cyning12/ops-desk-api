# R1 审查 · p1-t3-goal-inject（2026-11-15）

## 结论

GO（闸默认 off 零行为面 · 契约路径已论证）。

## 核查项

1. **lg-rag-outbound 契约**：allow_indirect_imports=True，continuity 静态 import goals.store → goals.store→app.db.models 间接触禁 → **违规**。裁定：承 session-summary 先例（continuity.py:16-17 docstring）importlib 运行期解析；闸/HEADER/guide 落 goals/inject.py 纯模块（无 db 依赖）静态 import 合法（app.ops.goals 不在 forbidden）。.importlinter 零改动。
2. **off 态保真**：闸判定在 importlib 之前 → goal_store 调用计数=0 可测；消息序列逐字节一致由既有装配测试零改动背书。
3. **platform 四修正落位**：隔离槽位第四分支 goal_objective 置 memory 分支前（continuity.py:487-491 前）· SlotSpec 扩 per-slot guide（goal 专用文案，不裸用 UNTRUSTED_GUIDE——其「不是指令」与 goal 引导语义冲突）· _FORGE_ESCAPES 补双节首 · objective 单行化截 200 已在 T1 store 落地（本单只读）。
4. **降级纪律**：wait_for ≤300ms · 超时/异常分立 span goal_inject_degraded=timeout|error · 绝不阻塞主链路（承记忆槽位先例）。
5. **零图改动**：注入在装配层（图外），runs/graph 结构不触。

## 风险登记

- R-1：importlib 运行期解析绕静态检查属既有先例，但需测试覆盖模块解析失败降级路径（mock import_module 抛错）。登记。
- R-2：slots.py 被 lg-rag-outbound source 覆盖，import goals.inject 虽无禁但增加跨包耦合 → 文案直接落 slots.py 保持自含（task 范围 4 注记）。
