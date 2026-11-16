# task_p2b_t2_mcp_transport_session · R1 审查文（20 帽）

- 时刻：2026-11-16
- 审查人：exec-p2b-t2（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03216 · 00 代签体系）
- 对象：`docs/tasks/active/task_p2b_t2_mcp_transport_session.md` v1

## 审查项

1. **范围对账**：task 范围 9 条与 11-p2b-mcp-skill-design.md 终稿 §8 T2 行
   （mcp transport 双实现 · McpSessionManager · lifespan 挂接 · 熔断按 server ·
   shutdown 清理）+ 委派书 m00002 内联协议面（协议子集五件 / -32601 防挂起 /
   通知忽略 / 握手降级 / 双超时 clamp / env 白名单 / identity mismatch 拒连）
   1:1 落入；§5.1 启动建连 · 单 server 失败隔离 · shutdown 逆序 close +
   unregister（R5）· §5.3 env_allowlist 不继承 os.environ · §5.4 熔断
   breaker.calling()（call_async Tornado-only 钉案）全部锚定。GO。
2. **非范围**：manifest.py kind 词表与翻译器（T3）· skill 面（T4 已闭环）·
   config.py MCP 键面与 .env.example（T1 已定）· 真社区 server 互操作（T5b）·
   listResources/listPrompts（P2c · 仅注释挂点）· alembic/ · scripts/ ·
   lg_rag/ · skill_registry/ 均明示排除；manager 只到 session 面，register
   行为不在本单。GO。
3. **节号漂移处理**：委派书引用的 §5-①~⑥ / §5-② / §5-④ / §7-① / §9.2 (a)-(g)
   在终稿、architect 初稿、09 映射文、issue #23 评论 grep 零命中（32601 /
   握手降级 / 120000 / 20+2 均无）；task 档 R0 节与偏差 D1 如实登记，
   以委派书内联技术细节为操作真源——符合「最小改动 + 如实登记偏差」授权口径。GO。
4. **D2 握手降级调和**：委派书降级回退 vs 终稿 §11「仅钉版 2025-06-18」+ T1
   mcp_config.py 钉版校验——task 调和为「config 钉版=首选版本语义不变 +
   session 单回退链三版本 + 应答版本支持集断言」，不改 mcp_config.py 既有 API，
   理由成立、改动最小。GO。
5. **D4 e2e 口径**：零新外部依赖纪律下仓内无 mcp 包，采委派书明示备选
   「最小手工 JSON-RPC stdio 脚本充当 server 并登记偏差」——tests/fixtures/
   mcp_stdio_stub.py 经 sys.executable 起真子进程，零外网 CI 可跑。GO。
6. **验收可机判**：12 条验收逐条锚到测试/文件证据；FakeTransport 谱系 +
   stdio stub e2e + 负例三枚 + 五键 blank 前缀 + CI 终裁口径明；import 零网络
   断言用 AST 源检查（承 T1 教训不查 sys.modules）。GO。
7. **思考轮**：R0-R5 表 + actual_last_round=R5 + R0/R1/R2/R3/R4/R5 小节齐备；
   R3 记录 transport 接口形态 / 回退链 / 熔断 key / 包结构 / settings 注入
   五决策。GO。
8. **registry N3 entry**：base=575ab69b · allowed_app_files 七件精确列举 ·
   allowed_tree_files 十一件 · allowed_tree_prefixes=invokes 目录 ·
   banned_prefixes=[alembic/, scripts/, app/ops/lg_rag/, app/ops/skill_registry/]
   · yaml safe_load 验证通过（21 waves · 末 entry=p2b-t2-mcp-transport-session）。GO。
9. **人工闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三行 approved，
   依据 issue #23 m03064/m03216 夜间授权；01_modules.md 签收承 :135/:136 先例。GO。

## 结论

**GO · 通过（零阻塞项）** —— task v1 可进 30 实施（夜间授权窗口 · 30 台账见 invoke_20261116_30_impl.md · 40 验收台账见 invoke_20261116_40_acceptance.md）。
