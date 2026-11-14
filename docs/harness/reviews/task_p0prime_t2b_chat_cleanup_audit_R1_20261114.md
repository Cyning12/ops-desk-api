# R1 设计审查 · p0prime-t2b-chat-cleanup

- 结论：GO。范围封闭（410 化两活跃端点 + 删三类 + drop 三表），无新功能面。
- 裁定 ①：410 墓碑镜像 /chat/stream 范式（auth 在前 401→登录 410），detail 统一 {error:"gone", migrate_to:"/api/ops/lg-rag/*", message} + Deprecation/Link 头。
- 裁定 ②：drop 顺序 events→runs→sessions_chat 顺 FK 依赖；downgrade 完整重建（参照 20260715_init:163-192），独立可回退。
- 裁定 ③：test_session_summary「原文 SoT 零污染」断言保留语义改写——ops_runs 表将不存在，改断言 ops_lg_rag_turns 行数不变 + 摘 OpsRun 引用。
- 裁定 ④：tenant_context 的 sessions/latest 切 B 回归改断言 410（租户头解析链路本身已由他件覆盖）。
- 风险：无（W1 已清零消费方；iOS 无活跃消费）。
