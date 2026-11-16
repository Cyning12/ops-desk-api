# task_p3_t2b_create_schedule_capability · R1 审查文（20 帽）

- 时刻：2026-11-16
- 审查人：exec-p3-t2b（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03498 · 00 代签体系）
- 对象：`docs/tasks/active/task_p3_t2b_create_schedule_capability.md` v1

## 审查项

1. **范围对账**：task 范围 7 条与 15-p3-contracts.md（commit 62af6ea）§2
   逐字对照——§2.1 manifest 字段族（id=ops.schedule.create · write/medium/
   tenant_scoped · hitl.required + snapshot_fields 九键 · idempotency_key
   {{request_id}} · args_schema required 四键 + additionalProperties false ·
   output_fields 四键）· §2.2 加载放行纪律（EXTRA_MANIFESTS 显式加载 ·
   ALLOW_WRITE_TAGS=schedule 只豁免 deny_write · deny_high_risk 永不豁免）·
   §2.3 W1 卡题钉字「创建定时任务 = 承诺未来 LLM 花费」· §2.4 执行语义
   （直调 T2 store 同校验路径 · 幂等防重 · 422 文案透传 · 不发 run）
   1:1 落入；委派书内联面（双上限 20/200 · interval≥300 · 归属=调用者 ·
   allowlist 9→10 · 图谱登记 · 五字符 p3t2b 测试前缀）全部锚定。GO。
2. **非范围**：worker/点火循环/补链/OPS_SCHEDULE_ENABLED（T3 并行）· REST
   面（T2 已交付只复用 store）· web（HitlApprovalCard 既有渲染）·
   runs/events（T4 已合）· scripts/ · skill_registry/ · lg_rag/ 编排层本体
   均明示排除。GO。
3. **422 文案透传纪律**：§2.4-3「配额/校验失败 → 抛 §1.8 同款 422 文案
   （Agent 把 detail 原文转述给用户，不改写）」落入 adapter 设计与验收 5——
   adapter 不吞 ScheduleValidationError、不二次包装 detail；测试逐字断言
   （非模糊匹配）。GO。
4. **三偏差最小性**：D1 adapter 嵌套 map → 冒号串（loader 白名单约束 ·
   _resolve_local_fn_adapter 只收字符串前缀 · 扩 _PREFIX_TO_MODULE 第三
   前缀为最小改动 · 不放开任意 import/eval）；D2 output_schema JSON-schema
   风 → JSONPath required 词表（V10 未知键整文件拒 · 语义等价 ·
   output_fields 四键逐字不动）；D3 request_id 不在契约 required 且
   additionalProperties:false → 可选 property + 回退键
   f"{run_id}:{subtask_id}"（HITL resume 重放同键不双写 · 两者皆无
   ValueError 不落笔）。三者均为「契约字面 vs 落地面约束」的最小和解，
   语义等价，如实登记 task 偏差节。GO。
5. **归属谓词 fail-closed**：tenant_id/user_id 只取 ctx（与 Principal 同源 ·
   禁取模型产出）；委派 off 模式 ctx 无 user_id → 不落笔（限制 L1 · 生产
   .env LG_RAG_DELEGATION_TOKEN_MODE=enforce 委派常开）；user_id str →
   uuid.UUID 转换对齐 OpsSchedule.user_id UUID(as_uuid=True)。GO。
6. **幂等链路**：claim(capability_id+tenant_id+key) → duplicate 直返首执
   对账载荷 · in_flight → RuntimeError · 失败 release（可安全重试）· 成功
   acomplete（回执 id 由 gateway 落完回执后补上）——承 defaults.py
   ops_write_run_note 先例逐环对齐；gateway _build_receipt 从
   output["idempotency_key"]/output["receipt"]dict/output["duplicated"]
   取回执料的消费面已核实（adapter 输出形状匹配）。GO。
7. **HITL 零新码核实**：编排层 tool_exec_node 既有闸链（write 无批准 →
   blocked=capability_write_hitl_required + write_intent{capability_id,
   tenant_id, args_summary, idempotency_key=原始模板} → _persist_hitl →
   interrupt；批准注入 _host_policy.allow_write + ctx.approval_id 重派）
   逐行核实可消费本 manifest 声明；HitlApprovalCard 既有渲染零改动
   （freeze 帧 hitl.waiting 不变）。GO。
8. **schedule→capability 新边**：service.py 函数内延迟 import
   capability.idempotency（T2 自注「schedule 禁引 capability」为本波必要
   豁免 · importlinter 无 schedule 契约零静态违规 · 01_modules schedule
   行 deps 如实登记 · 偏差 D4）。GO。
9. **体例对账**：registry entry base=17337d35 · banned_prefixes=[]（承 T2
   先例）· invokes by-task 四件（承 p3-t4 四件先例）· 本审查文 GO 机读词 ·
   spec-wave task lint PASS 为闸 · 仓规条款一遵守（走 20-R1 审查文非
   --allow-no-review）。GO。
10. **验收可机判**：11 条验收逐条锚到
    tests/test_p3_t2b_create_schedule_capability.py 或文件证据；脏树期
    wave_gate 红为在途面咬禁改面常态（commit 后转绿 · CI 终裁）；本地
    环境性红（tests/test_check_vector_waterline.py 裸 load_dotenv 渗仓根
    .env · base 同路径复现）与基线逐签对照后登记不纠缠。GO。
11. **思考轮**：R0-R5 表 + actual_last_round=R5 + 六小节齐备；R3 记录
    D1/D2/D3/D4 四决策与归属 fail-closed。GO。

## 结论

**GO（PASS · 通过 · 零阻塞）**——范围/非范围/验收/失败路径/思考轮与 15 契约 §2 + 14 终稿对齐，
三偏差一豁免如实登记且均为最小和解，可进 30。
