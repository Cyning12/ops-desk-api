# R1 审查 · task_p1_t4_goal_entry

- 时刻：2026-11-15 · 审查人：本窗口（组织人）
- 对象：task 档 + registry entry + 勘察定论

## 审查项

1. 范围与 07 §5 T4 行逐字对齐：入口接线 + uq 索引 + ORM 漂移补齐，无溢出（goal 自动流转 / /invoke / SSE 帧均明确非范围）。
2. 红线：闸 off 零触达（store 调用计数=0）；回退=关闸+回撤迁移互不影响；freeze 零触碰。
3. 契约：importlib 运行期解析守 lg-rag-outbound（承 T3 先例），.importlinter 零改动。
4. 竞态：T1 已实现 IntegrityError 重读；本单索引就位后路径激活，并发用例实证。
5. registry allowed 面完整（含 alembic 迁移 → banned_prefixes=[]）。

## 结论

GO，可进 30 实施。
