# R1 审查 · p1-t2-goal-rest（2026-11-15）

## 结论

GO（薄 HTTP 面 · store 接口已验收 · 错误映射显式）。

## 核查项

1. **设计一致性**：范围与 07 §5 T2 行对齐；O-1 人工复活 = PATCH paused→active 经 store 转移矩阵（_ALLOWED_TRANSITIONS paused→{active,done,abandoned}）天然支持。
2. **防探测**：404（非 403）于跨租户——store 查询带 tenant_id 谓词，存在性不外泄；与 hitl 面先例一致。
3. **词表外 422**：pydantic Literal 前置校验，不触达 store（TransitionError 语义不被污染）。
4. **tenant 解析**：复用 resolve_header_against_session（session 真源 · 头不一致 403 · 未知租户 422），不新造轮子。
5. **契约**：goals 不在任何 import-linter source 名单，router→deps/tenant_context 零契约风险。

## 风险登记

- R-1：goal_id 为 String UUID，路径参数格式错误由 FastAPI str 收（不会 500），到 store 查无 → 404。登记。
