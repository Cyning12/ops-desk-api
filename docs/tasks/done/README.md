# done/ · 已完成任务导航（Hub）

> **用途**：日常浏览 **只打开本文件**；`_views/done.md` 为薄指针。  
> **真值**：各 task 文件头部 `状态` + 本目录（或域子目录）物理位置。  
> **落盘约定**：业务仓 `docs/tasks/done/` · 工作区 Harness `docs/harness/tasks/done/`（路径替换下方 `{tasks_root}`）。

---

## 域目录（domain）

| 域 slug | 目录 | 典型前缀 / 规则 |
|---------|------|-----------------|
| `harness` | `done/harness/` | `task_harness_*`（非产品里程碑） |
| `cyning-harness` | `done/cyning-harness/` | `task_harness_cyning_harness_*` · `task_harness_m2_cyning_*` |
| `engineering` | `done/engineering/` | `task_engineering_*` |
| `governance` | `done/governance/` | `task_governance_*` · `task_gov_*` |
| `chatbi` | `done/chatbi/` | `task_chatbi_*` |
| `standards` | `done/standards/` | `task_standards_*` |
| `epics` | `done/epics/` | Epic / MANIFEST 母单 · CLOSE 卡 |

**推断**：关账时按文件名前缀落入域目录；歧义时 task 元信息填 **`domain`** 字段。

---

## harness

| 关账日 | task | freeze_id / 摘要 |
|--------|------|------------------|
| 2026-08-24 | [`task_dsh_coding_kit_upgrade_1_5_1.md`](./task_dsh_coding_kit_upgrade_1_5_1.md) | kit 1.5.1 过程轨升级 · PR #47 |
| 2026-08-24 | [`task_dsh_kit_graph_migrate_probe.md`](./task_dsh_kit_graph_migrate_probe.md) | 迁移探针：不切命令面 + FEEDBACK · PR #47 |
| 2026-08-25 | [`task_dsh_coding_kit_upgrade_1_5_2.md`](./task_dsh_coding_kit_upgrade_1_5_2.md) | kit 1.5.2（K1/K4 被 DEF-028/029 修复） · PR #48 |
| 2026-08-25 | [`task_dsh_coding_kit_upgrade_1_6_1.md`](./task_dsh_coding_kit_upgrade_1_6_1.md) | kit 1.6.1（反哺项全关闭） · PR #50 |
| 2026-08-25 | [`task_dsh_kit_graph_command_switch.md`](./task_dsh_kit_graph_command_switch.md) | 命令面正式切换 · PR #51 |
| 2026-08-26 | [`task_tech_graph_legacy_cleanup.md`](./task_tech_graph_legacy_cleanup.md) | 清理根双写 / 01_struct stub / QUICKREF·legacy · PR #61 |
| 2026-08-26 | [`task_dsh_coding_kit_upgrade_1_7_1.md`](./task_dsh_coding_kit_upgrade_1_7_1.md) | kit 1.7.1（CLOSE dogfood + 00 条文手补） · PR #63 |
| 2026-08-27 | [`task_dsh_coding_kit_upgrade_1_8_0.md`](./task_dsh_coding_kit_upgrade_1_8_0.md) | kit 1.8.0（K1–K7 核对 + prompts 手同步） · PR #76 |
| 2026-08-31 | [`task_dsh_coding_kit_upgrade_1_10_0.md`](./task_dsh_coding_kit_upgrade_1_10_0.md) | kit 1.10.0（sync prompts + re-anchor / 00-delegate） · PR #98 |
| 2026-09-11 | [`task_dsh_coding_kit_upgrade_2_1_0.md`](./task_dsh_coding_kit_upgrade_2_1_0.md) | kit 改名 spec-wave 2.1.3（依赖改名 + IDE 块 + prompts 同步） · PR #132 |
| 2026-09-11 | [`task_specwave_cleanup_2_1_3.md`](./task_specwave_cleanup_2_1_3.md) | 8 根级 SPEC 归位 + cursor rules 命令替换（R3 PASS） · PR #133/#134 |
| 2026-09-17 | [`task_specwave_upgrade_2_4_2.md`](./task_specwave_upgrade_2_4_2.md) | spec-wave 2.1.3→2.4.2 + 旧命令字面收编（R1 PWN · 验收 14/14） · PR #136 |
| 2026-09-18 | [`task_specwave_upgrade_3_0_0.md`](./task_specwave_upgrade_3_0_0.md) | spec-wave 2.4.2→3.0.0 major（R1 PWN · 验收 13/13） · PR #139 |
| 2026-09-23 | [`task_specwave_upgrade_3_0_1.md`](./task_specwave_upgrade_3_0_1.md) | spec-wave 3.0.0→3.0.1 patch + 长程任务反馈 F-1~F-4（R1 PASS · 机械闸全绿） · PR #172 |
| 2026-10-11 | [`task_specwave_verify_baseline.md`](./task_specwave_verify_baseline.md) | 仓级 verify 缺口基线收口：93 存量豁免 yaml + 审查门禁双址规约 v1（R1 BLOCKER→R2 PWN · 40 PASS V1-V5 · TC3 反向实证） · PR #228 |

---

## cyning-harness（产品里程碑）

| 关账日 | task | tag / 摘要 |
|--------|------|------------|
| YYYY-MM-DD | [`cyning-harness/task_<slug>_v1.md`](./cyning-harness/task_<slug>_v1.md) | … |

---

## engineering

| 关账日 | task | 摘要 |
|--------|------|------|
| 2026-08-22 | [`task_lg_rag_phase1.md`](./task_lg_rag_phase1.md) | PLAN Phase 1（basic 图/checkpointer/Langfuse） · PR #45 |
| 2026-08-22 | [`task_lg_rag_phase2.md`](./task_lg_rag_phase2.md) | Phase 2 Router 三路（50 PASS 8/8） · PR #45 |
| 2026-08-22 | [`task_lg_rag_phase3.md`](./task_lg_rag_phase3.md) | Phase 3 自纠错回环（验收裁定通过） · PR #45 |
| 2026-08-22 | [`task_lg_rag_phase4.md`](./task_lg_rag_phase4.md) | Phase 4 Multi-Agent Supervisor（50 PASS） · PR #45 |
| 2026-08-26 | [`task_structured_output_gateway_p0.md`](./task_structured_output_gateway_p0.md) | Structured Output Gateway P0（parse_only） · PR #58 |
| 2026-08-26 | [`task_structured_output_gateway_p1.md`](./task_structured_output_gateway_p1.md) | Structured Output Gateway P1（complete_structured） · PR #58 |
| 2026-08-26 | [`task_structured_output_gateway_p2.md`](./task_structured_output_gateway_p2.md) | Structured Output Gateway P2（lg_rag 接入） · PR #58 |
| 2026-08-26 | [`task_structured_output_gateway_p3.md`](./task_structured_output_gateway_p3.md) | Structured Output Gateway P3（ensure/validate） · PR #58 |
| 2026-08-26 | [`task_capability_gateway_p0.md`](./task_capability_gateway_p0.md) | Capability Gateway P0（Registry + tool_exec） · PR #59 |
| 2026-08-26 | [`task_capability_gateway_p1.md`](./task_capability_gateway_p1.md) | Capability Gateway P1（schemas_for_llm） · PR #59 |
| 2026-08-26 | [`task_capability_gateway_p2.md`](./task_capability_gateway_p2.md) | Capability Gateway P2（mock 探针） · PR #59 |
| 2026-08-26 | [`task_capability_gateway_p3.md`](./task_capability_gateway_p3.md) | Capability Gateway P3（skill stub） · PR #59 |
| 2026-08-26 | [`task_agent_infra_spec_hierarchy.md`](./task_agent_infra_spec_hierarchy.md) | Agent Infra SPEC L0/L1/L2 分层 · PR #65 |
| 2026-08-26 | [`task_cap_portable_core.md`](./task_cap_portable_core.md) | Capability 可迁移内核 Mode A · PR #66 |
| 2026-08-26 | [`task_so_schema_hygiene.md`](./task_so_schema_hygiene.md) | SO 域 schema 迁 lg_rag · PR #67 |
| 2026-08-26 | [`task_cap_mcp_real.md`](./task_cap_mcp_real.md) | Capability 真 MCP adapter · PR #68 |
| 2026-08-24 | [`task_inform_graph_backfill_w1_g0_chat.md`](./task_inform_graph_backfill_w1_g0_chat.md) | 图谱 W1（G-L0 + chat 追平） · PR #46 |
| 2026-08-24 | [`task_inform_graph_backfill_w2_bypass_flows.md`](./task_inform_graph_backfill_w2_bypass_flows.md) | 图谱 W2（旁路 flows，graphs 4→6） · PR #47 |
| 2026-08-25 | [`task_inform_graph_backfill_w3_chat_g2.md`](./task_inform_graph_backfill_w3_chat_g2.md) | W3 chat G-L2 indexes · PR #49 |
| 2026-08-25 | [`task_inform_graph_backfill_w4_rag_flow.md`](./task_inform_graph_backfill_w4_rag_flow.md) | W4 10_flow_rag（graphs 6→7） · PR #49 |
| 2026-08-25 | [`task_inform_graph_backfill_w5_coverage.md`](./task_inform_graph_backfill_w5_coverage.md) | W5 anchors + coverage warn · PR #49 |
| 2026-08-28 | [`task_eval_goldenset_lg_rag.md`](./task_eval_goldenset_lg_rag.md) | Eval E2 模块金标最小集 · PR #93 |
| 2026-08-28 | [`task_eval_langfuse_experiment_ci.md`](./task_eval_langfuse_experiment_ci.md) | Eval E3 Dataset/Experiment mock · PR #94 |
| 2026-08-28 | [`task_eval_online_sample_scores.md`](./task_eval_online_sample_scores.md) | Eval E4 线上抽样 score · PR #95 |
| 2026-08-29 | [`task_eval_token_cost_ledger.md`](./task_eval_token_cost_ledger.md) | Eval E5 Token/费用账本 · PR #96（2026-08-31 Hub 补登） |
| 2026-08-30 | [`task_lg_rag_sse_t0_t1_spec.md`](./task_lg_rag_sse_t0_t1_spec.md) | T0+T1 Spec 签收 · docs-only |
| 2026-08-31 | [`task_lg_rag_sse_stream_updates.md`](./task_lg_rag_sse_stream_updates.md) | T2 lg-rag `/stream` + Obs I/O · PR #97 |
| 2026-08-31 | [`task_lg_rag_session_continuity.md`](./task_lg_rag_session_continuity.md) | T3 Session 连续性（thread_id） · PR #100 |
| 2026-08-31 | [`task_siliconflow_default_catalog_cost.md`](./task_siliconflow_default_catalog_cost.md) | SiliconFlow catalog/grader 默认 + Host 价表 cache export · PR #101 |
| 2026-08-31 | [`task_langfuse_cached_input_tokens.md`](./task_langfuse_cached_input_tokens.md) | Langfuse 上报 `cached-input-tokens` · PR #101 |
| 2026-08-31 | [`task_lg_rag_sse_resume.md`](./task_lg_rag_sse_resume.md) | T4 SSE resume（cursor + replay · `ops_lg_rag_run_events`） · PR #103 |
| 2026-08-31 | [`task_lg_rag_sse_token_stream.md`](./task_lg_rag_sse_token_stream.md) | T5 answer token delta 流（delta 多帧 + 终帧 final） · PR #105 |
| 2026-09-01 | [`task_lg_rag_deprecate_chat_stream.md`](./task_lg_rag_deprecate_chat_stream.md) | T6 `/chat/stream` 410 下线（保留 models/sessions.latest/WS · 不删码） · PR #108 |
| 2026-09-01 | [`task_host_comms_boundary_spec.md`](./task_host_comms_boundary_spec.md) | C0 Host 沟通边界 SPEC 06 签收（docs-only） · PR #111 |
| 2026-09-01 | [`task_host_harness_cli_capability.md`](./task_host_harness_cli_capability.md) | C1 harness CLI 白名单 Capability（verify/task_lint · Policy 默认关） · PR #114 |
| 2026-09-01 | [`task_host_comms_prompt_pack.md`](./task_host_comms_prompt_pack.md) | C2 comms Prompt Pack + route_intent（纯函数层 · 无路由） · PR #116 |
| 2026-09-01 | [`task_host_comms_task_writer.md`](./task_host_comms_task_writer.md) | C3 受控 task 写盘（allowlist · dry-run · 人确认 · 禁代签机械挡） · PR #118 |
| 2026-09-01 | [`task_host_obs_comms_ui.md`](./task_host_obs_comms_ui.md) | C4 obs-comms 契约 v0 + web Prompt（api 无码） · PR #120 |
| 2026-09-01 | [`task_lg_rag_sse_delta_realtime_spec.md`](./task_lg_rag_sse_delta_realtime_spec.md) | T5.1 SPEC §10.4.1 pacing / anti-buffer（docs-only） |
| 2026-09-01 | [`task_lg_rag_sse_delta_realtime.md`](./task_lg_rag_sse_delta_realtime.md) | T5.1 终答 delta 实时投递（persist 不阻塞 yield） · PR #122 |
| 2026-09-07 | [`task_lg_rag_sse_idle_keepalive.md`](./task_lg_rag_sse_idle_keepalive.md) | §10.6 SSE idle keepalive（comment 30s · 不落盘） · PR #123 |
| 2026-09-07 | [`task_lg_rag_sse_subtask_live.md`](./task_lg_rag_sse_subtask_live.md) | §10.7 subtask.progress running 起步帧 · PR #125（2026-09-08 Hub 补登漏行） |
| 2026-09-08 | [`task_lg_rag_sse_subtask_steps.md`](./task_lg_rag_sse_subtask_steps.md) | §10.7 step 里程碑 + provider 真流式（删 aread 假缓冲） · PR #127 |
| 2026-09-08 | [`task_lg_rag_sse_subtask_message.md`](./task_lg_rag_sse_subtask_message.md) | §10.7 subtask.progress 可选可读 `message`（确定性模板 ≤200 字） · PR #130 |
| 2026-09-18 | [`task_supervisor_budget_h_beta.md`](./task_supervisor_budget_h_beta.md) | 阶段 H β · supervisor 总预算（默认 32 · 耗尽→aggregate · 墙钟默认关） · PR #141 |
| 2026-09-23 | [`task_host_v1_delegation_token.md`](./task_host_v1_delegation_token.md) | **Agent Host V1-A** · 委派令牌（六字段 HMAC 令牌 + 验签门 + 签发审批 + requested_scope 声明∩裁剪 · 三档模式默认 off） · PR #179 |
| 2026-09-23 | [`task_host_v1_visibility_scenario_policy.md`](./task_host_v1_visibility_scenario_policy.md) | **Agent Host V1-B** · 可见集两阶段（scenario_trim 场景维+剔除台账+intent_fallback channel）+ manifest 可撤销性四字段（加载期三硬规则+缺失三档派生） · PR #181 |
| 2026-09-23 | [`task_host_v1_llm_factory_closure.md`](./task_host_v1_llm_factory_closure.md) | **Agent Host V1-C** · LLM 工厂闭环（预算硬闸 + 耗尽降级链 degraded + 推理缓存 + 档级 fallback + Cost per Successful Task） · PR #183 |
| 2026-09-24 | [`task_host_v1_episodic_memory_feedback.md`](./task_host_v1_episodic_memory_feedback.md) | **Agent Host V1-D** · 情景记忆闸/库分离 + `[相似经验]` 召回 + 指纹规则聚类建议面（`ops_memory_episodes`） · PR #184 |
| 2026-09-24 | [`task_host_v1_splittability_hardening.md`](./task_host_v1_splittability_hardening.md) | **Agent Host V1-E** · 可拆性硬化（import-linter · registry 协议 · 策略包试点 · multi-replica 承继+边界补扫）· PR #187 · **v1.0 收尾** |
| 2026-09-24 | [`task_multi_replica_dualproc_tenant_session.md`](./task_multi_replica_dualproc_tenant_session.md) | **bugfix** · dualproc fixture 补 `ops_sessions.tenant_id`（FINDINGS #1）· PR #190 |
| 2026-09-24 | [`task_host_v1_sli_four_metrics.md`](./task_host_v1_sli_four_metrics.md) | **出口跟进 G1** · SLI 四项定稿（定义/有数/看板）· docs-only · PR #193 |
| 2026-09-24 | [`task_host_v1_wrap_up.md`](./task_host_v1_wrap_up.md) | **v1.0 收尾 D1** · 文档闭环四件（07 转 completed · REGRESSION PASS · SPEC 实施态 · invoke 终条）+ BACKLOG 登记 · docs-only · PR #196 |
| 2026-09-24 | [`task_host_v1_delegation_token_observe.md`](./task_host_v1_delegation_token_observe.md) | **D2 第一闸** · 委派令牌本地观察准备（RUNBOOK checklist + compose env 透传默认 off + 报告模板）· config+docs · PR #198 |
| 2026-10-09 | [`task_compose_hitl_persistence_env.md`](./task_compose_hitl_persistence_env.md) | **config** · compose 透传 `OPS_HITL_PERSISTENCE`（默认空零 diff · 解锁全 docker 形态 HITL db 持久化验收通道）· 40 核验 7/7 · PR #207 |
| 2026-10-09 | [`task_testing_write_capability.md`](./task_testing_write_capability.md) | **D2 可审对象** · 注册非只读测试 capability（testing.v1.yaml 罐头 write + env 门控 allow_write_tags_any 放行口径 + 裁定四 loader V1 放宽 · 三层显式打开 · off 零 diff）· 40 核验 PASS 带偏差登记（A1 三段 live 可达 · done 末段 409 另立 task）· PR #209 |
| 2026-10-10 | [`task_hitl_approval_consumption_strategy_env.md`](./task_hitl_approval_consumption_strategy_env.md) | **T3 · D3** · strategy 候选 map env 追加口 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`（逗号分隔/strip/去空去重/调用点读取 · 默认不设逐字节零 diff · 含未知 key · 覆盖口隔离 · 下游闸全链不动）· 40 核验 PASS（七项全绿 · 全量 1679 passed）· PR #213 |
| 2026-10-10 | [`task_hitl_approval_consumption_loop.md`](./task_hitl_approval_consumption_loop.md) | **T1 · D1/D2/D4** · 签发审批消费门（三元组消费键 + TTL 读时判过期 fail-closed · decided_at float\|ISO str 归一 · async 化甲案 B1 十四处随改）+ unlock 空形态回填（unlock=sid 形态守卫 · resume 409 修复）+ 台账/34 枚新测 · 40 核验 PASS 带偏差（全量 1713 passed · live resume 200 达成 · 末段 replan 重盖章上抛 T2/SPEC v2）· PR #216 |
| 2026-10-10 | [`task_hitl_approval_consumption_auto_resume.md`](./task_hitl_approval_consumption_auto_resume.md) | **T2 · D5** · 批准后自动恢复可配置面（`OPS_HITL_AUTO_RESUME` 全局 env manual 默认零 diff + decide 载荷 `resume_mode` 白名单 400 + 进程内触发器走手动 resume 同源路径 + Db 行锁认领 `FOR UPDATE SKIP LOCKED` + lifespan 启动/周期补偿扫描 · 台账三件套）· 40 核验 PASS 带偏差（39 枚新测 · 全量 1748 passed · live auto 全链达成 · 末段 replan 重盖章+孤儿 pending 上抛 SPEC v2）· PR #218 · **签发审批消费回路 SPEC v1 全链（T3+T1+T2）收官** |
| 2026-10-10 | [`task_hitl_replan_carry_and_persist_guard.md`](./task_hitl_replan_carry_and_persist_guard.md) | **D1/D2 · SPEC v1 FP-3 偏差裁定落地** · replan 保号三路径（hitl_unlocked_ids∩未解决原 sid 带回 · locked 后 LLM 新后缀前 · 空 unlocked 逐字节零 diff）+ `_persist_hitl` 建单前检查（镜像消费门 blocked_by/三元组/归一/TTL · 读异常 fail-open+warning）· TB1–TB6 14 枚 · 40 核验七项全过（live 双靶点闭合：consumed 命中原 sid · hitl_persist_guard_skip 每次重放 · done{resumed} 语义终态 · 终态 run 零 pending）· PR #221 |
| 2026-10-11 | [`task_repo_logging_init.md`](./task_repo_logging_init.md) | **仓级基建 · SPEC §9 序2** · 仓级 logging 初始化（裸 uvicorn 台账可观测性收口）：app/main.py import 期 `logging.basicConfig`（D1=A · `OPS_LOG_LEVEL` 默认 INFO 非法值 fail-closed D2=A · 格式 `%(asctime)s %(name)s %(levelname)s %(message)s` 钉死 · uvicorn propagate=False 共存）· TC1 红测先行 3 枚 · 40 核验 PASS-WITH-NITS（TC2 坑位1 反转实证 after 可见/before grep 空 · TC4 4 请求 4 access 行零双行 · TC5 master 基线对拍零新增红）· N-40-1 import 窗口裸格式 nit 照登 · PR #227（squash `e5b5c3d`） |
| 2026-10-11 | [`task_hitl_auto_resume_claim_race.md`](./task_hitl_auto_resume_claim_race.md) | **T2 验收 D1 偏差收口（bugfix）** · auto_resume 认领竞态：方向 A 认领后·执行前只读就绪校验 `_interrupt_metadata_visible`（stranded 判定快照 → defer 等下轮 · 手动 409 零 diff）+ 台账 `hitl_auto_resume_deferred` · TC1/TC2 红测先行（79b6485→51e17ca）· 40 核验七项全 PASS（TC3 live：零 stranded_checkpoint · 零执行失败 ERROR · 恰好一次执行 · deferred×5 机制本体实证挡重复认领 · 全量 4failed/1764passed 基线零新增）· PR #224 |
| 2026-10-11 | [`task_capability_mine_endpoint.md`](./task_capability_mine_endpoint.md) | **tool-catalog-page B1** · 用户态可见能力目录端点 GET /api/ops/capability/mine（CurrentUser 鉴权 401 · principal 会话构造 · `evaluate_visibility` 单源求值路由层零过滤 · 精确九键白名单投影 · 防探测空集 200 如实 · 只读零写）· 红测先行 e30b7ca（6 红）→f79fe3f（6 绿）· 20 审 R1 BLOCKER（B-1 lint E5）→f6c041f→R2 PASS · 40 核验 PASS（契约八条 diff 复核 · 全量基线独立对拍零新增红 · live 冒烟五场景 viewer⊆maintainer）· PR #231（squash `a7d748b` · 与 B2 同 PR） |
| 2026-10-11 | [`task_catalog_manifest_errors_surface.md`](./task_catalog_manifest_errors_surface.md) | **tool-catalog-page B2** · catalog manifest 故障可见性（顶层 `manifest_errors`/`manifest_error_details` 透出按 path 排序 · 错误态留存含首次失败+修复 pop · hidden 条目附 `visibility_reason` 词表四码中文映射 · 既有键零 diff）· 红测先行 520425f→2a2503d · 20 审 R1 PASS-WITH-NITS（锚点 14 组全核真 · NIT-1/2 随 2bf0bd1 消化 · NIT-3 照登）· 40 核验 PASS（契约七条 · live 坏 manifest 精确点名 · 中文映射真实出站 · runtime 两键回归）· PR #231（squash `a7d748b` · 与 B1 同 PR） |
| 2026-10-11 | [`task_hitl_approved_replan_quality.md`](./task_hitl_approved_replan_quality.md) | **SPEC §9 序1 质量收口** · approved 恒 replan+盲循环收口：replan 保号注入去盲（suffix v2 `$preserved_block` 保号行+locked 终态摘要截断 200）+ write 孪生 guard-skip 结构护栏（`_join_subtasks` 分发层先于签发 · canonical tool+规范化入参命中异 sid 成功终态不派发不消费 · `write_replay_guard_skip`/`replay_of` 台账 · off 零触达）· 红测先行 9b56343→ebe2a01 · 新测 8 枚+TC2 边界六枚 · 40 核验 PASS-WITH-NITS（TC3 live 双 run 对照：run1 护栏命中 · run2 注入零孪生 · write 执行均=1 · TC4 全量 1769 过/7 红基线逐枚吻合零新增 · TC5 台账链可断）· N1 locked 空注入缺口留另立 task · PR #233 |
| 2026-11-05 | [`task_stage_w_write_expand.md`](./task_stage_w_write_expand.md) | **阶段 W 扩写 · Q1=S1 仓内落笔型写** · 第二条真实窄写 `ops.write.run_note` 端到端接入既有受控写闸链（issue #323 签收链同日全棒）：manifest 三层显式打开（独立写 tag `run_note`）+ 真落笔 adapter（tenant 只取 ctx · approval_id 串链 · 幂等 store+DB 唯一约束双保险）+ loader V13（write 级 tenant_scoped 强制 · mock 特例清单不扩容）+ 新表 `ops_capability_notes`（Q3 随签 · FP-4 DB 级兜底）+ 16 枚红测先行 + G-L1 图谱回写 · 30 PR #327 squash `51030a4` / 40 PR #328 squash `3d08529` CI 4/4 绿 ×2 · 40 live 全链八段实录（PASS 带偏差登记 · shim 补位实证既有缺陷 `_worker_state` 丢 `run_id` → 另立 fix task）· 红线零破 registry/policy/lg_rag/gateway/SSE 零 diff |

---

## epics（母单 · MANIFEST）

| 关账日 | Epic / CLOSE | 子 task 索引 |
|--------|--------------|--------------|
| YYYY-MM-DD | [`epics/epic_<slug>.md`](./epics/epic_<slug>.md) | 见母单 §编排主表 |

---

## 关账维护（checklist）

1. `git mv {tasks_root}/active/<file>.md {tasks_root}/done/<domain>/`  
2. 头部 `> **状态**：done（YYYY-MM-DD 验收通过）`  
3. **本 Hub** 对应域表 **追加一行**（日期 · 链接 · freeze_id 一行摘要）  
4. **禁止**向 `_views/done.md` 追加长列表（保持 ≤15 行薄指针）  
5. 可选：同步 `_views/done_by_domain.md` 分组表  

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| YYYY-MM-DD | 初版 Hub（cyning-harness 模板嵌入） |
| 2026-08-25 | 补录 15 件归档（task_task_closeout_hygiene）：harness 域 5 件 + engineering 域 10 件；本仓 done/ 为平铺布局，链接用 ./task_*.md |
| 2026-08-26 | 补录 tech-graph-legacy-cleanup（harness 域 · PR #61） |
| 2026-08-31 | CLOSE T2 `#97` + kit 1.10.0 `#98`；Hub 补登 E5 / T0-T1 Spec |
| 2026-08-31 | CLOSE T4 `#103`（lg-rag-sse-resume 归档 done/ · Hub 补登） |
| 2026-08-31 | CLOSE T5 `#105`（lg-rag-sse-token-stream 归档 done/ · Hub 补登） |
| 2026-09-01 | CLOSE T6 `#108`（lg-rag-deprecate-chat-stream 归档 done/ · Hub 补登） |
| 2026-09-01 | CLOSE C0 `#111`（host-comms-boundary-spec 归档 done/ · Hub 补登） |
| 2026-09-01 | CLOSE C1 `#114`（host-harness-cli-capability 归档 done/ · Hub 补登） |
| 2026-09-01 | CLOSE C2 `#116`（host-comms-prompt-pack 归档 done/ · Hub 补登） |
| 2026-09-01 | CLOSE C3 `#118`（host-comms-task-writer 归档 done/ · Hub 补登） |
| 2026-09-01 | CLOSE C4 `#120`（host-obs-comms-ui 归档 done/ · Hub 补登）· **串行波次 T4–C4 全 CLOSE** |
| 2026-09-07 | CLOSE idle-keepalive `#123`（lg-rag-sse-idle-keepalive 归档 done/ · Hub 补登） |
| 2026-09-18 | CLOSE H β supervisor-budget（Hub 补登 · commit/PR 同轮） |
| 2026-09-23 | CLOSE **V1-B host-v1-visibility-scenario-policy** `#181`（可见集两阶段+manifest 四字段 · R1 FAIL→10-spec 澄清→R2 PASS 轨迹 · 归档 done/ · Hub 补登 · 00 代录签录链完整） |
| 2026-09-23 | CLOSE **V1-A host-v1-delegation-token** `#179`（Agent Host v1.0 五波之首 · 归档 done/ · Hub 补登 · 00 代录签录链完整：HG-SPEC-SIGNOFF/HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES） |
| 2026-09-24 | CLOSE **V1-C host-v1-llm-factory-closure** `#183`（LLM 工厂闭环 · 码已合入 · 本 PR 补登 40 invoke + 归档 done/ · Hub 补登） |
| 2026-09-24 | CLOSE **V1-D host-v1-episodic-memory-feedback** `#184`（情景记忆 + 失败模式库 · 过程档 SPEC/审查/invokes 补登 · 归档 done/ · Hub 补登 · **V1-A~D 全 CLOSE · V1-E 可启**） |
| 2026-09-24 | CLOSE **fix-multi-replica-dualproc-tenant-session** `#190`（dualproc 9 passed · FINDINGS #1 closed · 归档 done/） |
| 2026-09-24 | CLOSE **V1-E host-v1-splittability-hardening** `#187`（可拆性硬化 · CI 四绿含 import-linter · dualproc 环境红如实记 FINDINGS#1 · 归档 done/ · Hub · **V1-A~E 全 CLOSE · Agent Host v1.0 工程出口**） |
| 2026-09-24 | CLOSE **host-v1-sli-four-metrics** `#193`（出口复核 G1 · SLI 四项定稿 · docs-only · 归档 done/ · Hub · **G1 closed**） |
| 2026-09-24 | CLOSE **host-v1-wrap-up** `#196`（v1.0 文档闭环 D1 四件 + D4 BACKLOG · docs-only · CI 四绿 · R1 PASS-WITH-NITS · 归档 done/ · Hub 补登 · **07 规划转 completed · 长程令全链路闭合**） |
| 2026-09-24 | CLOSE **host-v1-delegation-token-observe** `#198`（D2 六闸灰度第一闸 · 本地观察准备 · compose 透传默认 off 零 diff · R1 PASS · 归档 done/ · Hub 补登 · **观察期执行与首份报告归下一棒**） |
| 2026-09-30 | CLOSE **chat-history-api**（B1）`#204`（会话历史只读 API · 事件表真源 · 20 R1 退回→R2 通过 · 裁定 A1/B1 · SSE freeze 对拍锁死 · 验收 14/14 · 归档 done/ · Hub 补登） |
| 2026-09-30 | CLOSE **hitl-browser-decide**（B2）`#204`（HITL 浏览器决策面 · cookie maintainer pending+decide · 20 R1 通过 4 nit 随 30 闭合 · 裁定 D1/E1 · OA 签名面零 diff · 验收 14/14 · 归档 done/ · Hub 补登 · **SPEC chat-history-hitl-ux §2 B1/B2 双双闭合 · 前端 F1/F2 另立 SPEC**） |
| 2026-10-09 | CLOSE **compose-hitl-persistence-env** `#207`（config 小 task · compose api.environment 透传 `OPS_HITL_PERSISTENCE` 默认空零 diff · 三闸维护者签（00 代录）· 40 核验 7/7 · CI 四绿 merge `61e44a8` · 归档 done/ · Hub 补登 · **验收阶段 5 全链复走留维护者另行组织**） |
| 2026-10-09 | CLOSE **testing-write-capability**（D2）`#209`（behavior 小 task · 注册非只读测试 capability 补齐 HITL 全链可审对象 · 30 GATE_STOP→裁定四=乙（manifest 顶层 idempotency_key · loader V1 二选一放宽）→ 20 R2 PASS → 维护者重签（00 代录）· 40 核验 PASS 带偏差登记（A1 三段 live 可达 · done 末段 resume 409=既有链设计缺口）· CI 四绿 merge `ca4148f` · 归档 done/ · Hub 补登 · **留转：签发审批消费回路另立 task + SPEC 起草中**） |
| 2026-10-10 | CLOSE **hitl-approval-consumption-strategy-env**（T3 · D3）`#213`（SPEC 承接 · strategy 候选 map env 追加口 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS` 默认不设零 diff · 三闸维护者签（00 代录）· 40 核验 PASS 七项全绿（18 枚新测 · 全量 1679 passed · B1 八文件 114 passed · nit×3 吸收）· CI 四绿 merge `7853334` · 归档 done/ · Hub 补登 · **T1/T2 在途 · 签发审批消费回路全链 CLOSE 待后续**） |
| 2026-10-10 | CLOSE **hitl-approval-consumption-loop**（T1 · D1/D2/D4）`#216`（SPEC 承接 · 审批消费门+unlock 空形态回填 · resume 409 修复 · 三闸维护者签（00 代录）· 40 核验 PASS 带偏差登记（七项 · 34 枚新测 · 全量 1713 passed · B1 十四处+门禁失败 0 · live 六 env 组 resume 200 达成 · 偏差：末段 replan 重盖章消费键失配=非本 task 回归上抛 T2/SPEC v2）· CI 四绿 merge `3f6a630` · 归档 done/ · Hub 补登 · **T2 auto-resume 在途 · 全链 CLOSE 待 T2 收口**） |
| 2026-10-10 | CLOSE **hitl-approval-consumption-auto-resume**（T2 · D5）`#218`（SPEC 承接 · 批准后自动恢复可配置面（env+resume_mode 双级 · 触发器+行锁认领+补偿扫描 · 无状态恢复纪律 · store 既有方法 diff 空）· 三闸维护者签（00 代录）· 40 核验 PASS 带偏差登记（TB1–TB8 · 39 枚新测全绿 · 全量 1748 passed · 4 failed=基线环境性 · live 六 env 组+auto 全链：decide→triggered→claimed→同源恢复→图继续 · 偏差：末段 done{completed} replan 重盖章失配=T1 已登记上抛项 · 孤儿 pending 附带观察 · 均上抛 SPEC v2）· CI 四绿 merge `0e13fc4` · 归档 done/ · Hub 补登 · **签发审批消费回路 SPEC v1 全链（T3+T1+T2）收官 · SPEC v2 裁定项留维护者**） |
| 2026-10-10 | CLOSE **hitl-replan-carry-and-persist-guard** `#221`（SPEC v1 FP-3 偏差维护者双裁定落地 · replan 保号三路径+`_persist_hitl` 建单前检查 · 三闸维护者签（00 代录）· 20 R1 PASS 零阻塞 · 40 核验七项全过（TB1–TB6 14 枚 · 全量 4failed/1762passed 基线 · live 三 run 双靶点闭合：consumed 命中原 sid · hitl_persist_guard_skip 每次重放 · done{resumed} 语义终态）· CI merge `85058f7` · 归档 done/ · Hub 补登 · CLOSE 文档 `docs/tasks/close/` 落盘 · worktree+分支本 CLOSE 清理 · **T1/T2 上抛偏差正面收口 · 钉案三条照登（resumed 语义 · LLM 盲循环+_collect_decisions 恒 replan 建议后续 task · 仓级 verify 92 缺口基线）**） |
| 2026-10-11 | CLOSE **hitl-auto-resume-claim-race** `#224`（T2 验收 D1 偏差收口 · 方向 A 就绪校验 defer 等下轮 + 台账 `hitl_auto_resume_deferred` · 三闸 approved（维护者授权 · 00 代录 2f91f67）· 20 R1 PASS-WITH-NITS（N-1~N-3 照登核验全过）· 30 红测先行（79b6485 修复前 2 failed 与 live D1 同形 → 51e17ca 实现）· 40 核验七项全 PASS（红测时序 worktree 复跑实证 · TC3 live 零 stranded_checkpoint · deferred×5 挡重复认领 · 恰好一次执行）· merge `11fb7e6` · 归档 done/ · Hub 补登 · CLOSE 文档 `docs/tasks/close/` 落盘 · task+close 分支本 CLOSE 清理 · **T2 live 偏差全收口 · 学习要点四条照登（红测时序证据 · .env PG 闸全进程 · saver.setup() idle-in-transaction · 裸 uvicorn 无台账建议仓级 task）**） || 2026-10-11 | CLOSE **repo-logging-init** `#227`（仓级 logging 初始化 · SPEC §9 序2 · D1=A import 期 basicConfig + D2=A `OPS_LOG_LEVEL` 默认 INFO 非法 fail-closed · 红测先行 445ce28→b329aec · 三闸 approved（维护者授权 · 00 代录 a31d471）· 20 R1 PASS-WITH-NITS（N-1~N-6 照登随 30 回填闭合）· 40 核验 PASS-WITH-NITS（TC2 坑位1 反转实证 · TC3 compose 零 diff · TC4 4请求4行 · TC5 master 基线 4 红逐名吻合 A/B 归因零新增红）· squash merge `e5b5c3d` · CI 修复 2d686f0/5e07040 · 归档 done/ · Hub 补登 · CLOSE 文档 `docs/tasks/close/` 落盘 · worktree+分支移交 00 统一清理 · **N-40-1 import 窗口裸格式 nit 留后续裁定**） |

| 2026-10-11 | CLOSE **specwave-verify-baseline** `#228`（仓级 chore · SPEC §9 序3 · 93 存量豁免 yaml+双址规约 v1 · R1 BLOCKER→B-1 修订→R2 PASS-WITH-NITS · 三闸维护者签（00 代录 m01606/m00255）· 40 复核 PASS 五验全绿（TC3 反向实证亲跑红绿 · 豁免命中 93 invalid 0）· squash merge `5204330` · 归档 done/ · Hub 补登 · CLOSE 文档+50 invoke 落盘 · 审查文 R1/R2 复制落址A 过渡（规约 §二）· **钉案：豁免≠审查通过 · 上游 verify 支持址B 留后续 · 管道吞码坑 D3 复证**） |
| 2026-10-11 | CLOSE **tool-catalog-page B1 capability-mine-endpoint + B2 catalog-manifest-errors-surface**（SPEC v0 signed · HG-SPEC-SIGNOFF approved fb85675 00 代录 m01606 · 状态行 draft→signed 本 CLOSE 回写 · 双 task 同分支同 PR #231 squash `a7d748b` · B1 R1 BLOCKER→f6c041f 修订→R2 PASS · B2 R1 PASS-WITH-NITS（NIT-1/2 消化 · NIT-3 照登）· 三闸 approved（00 代录 m01606/m00255）· 40 双 PASS + live 冒烟双五场景（uvicorn :8070 · viewer⊆maintainer · 坏 manifest 精确点名）· 归档 done/ · Hub 补登 · CLOSE 文档+50 invoke 落盘 · 审查文址A 复制件 30 期先行（826b2ff · 序2 教训前置吸收）· worktree+分支移交 00 统一清理 · **维护者验收 checklist 在 CLOSE 文档第七节**） |
| 2026-10-11 | CLOSE **hitl-approved-replan-quality** `#233`（SPEC §9 序1 · D1=C 混合案：suffix v2 `$preserved_block` 注入去盲 + `_join_subtasks` write 孪生 guard-skip 结构护栏（canonical tool+规范化入参 · 先于签发不派发不消费 · `write_replay_guard_skip`/`replay_of` 台账）· 三闸 approved（维护者授权 m01606/m00255 · 00 代录）· 20 R1 BLOCKED→B-1 修订→R2 PASS · 30 红测先行（9b56343 RED→ebe2a01 绿）· 40 核验 PASS-WITH-NITS（TC3 live 双 run 对照：护栏命中+注入零孪生 · write 执行均=1 · 全量 1769 过/7 红基线零新增 · TC5 台账链可断）· squash merge `be1469d` · 归档 done/ · Hub 补登 · CLOSE 文档+50 invoke 落盘 · 审查文 R1/R2 复制落址A 过渡（规约 §二 · 第三例）· **钉案：N1 locked 空 preserved_block 不注入留另立 task · N2 langfuse 无 GENERATION input · NO_PROXY [::1] 坑位复发 · worktree+分支移交 00 清理**） |
| 2026-10-15 | CLOSE **hitl-resume-async** `#252`（squash `0e5f6b1` · HITL resume 端点异步化 JC-F1 B 方案 · asyncio 派发秒回 200 携 replay cursor · 响应面零改 · 红测先行 · 40 live 8 PASS · web 复验 TC1–TC7 · 三闸 00 代录 · 归档 done/ · CLOSE 文档 `docs/tasks/close/` 落盘 · 分支移交 00 清理）——近两次 CLOSE 漏登本表，本棒按体例补登 |
| 2026-10-16 | CLOSE **demo-agent-host-surface**（三方演示展示面名实分离 · 对外只讲 Agent Host · 三 PR 齐：web #70 `44a77db` + web #71（D4 修正 · `46c8c54`）+ api #255 squash `370cee4` CI 四绿 · TC-1–TC-8 全绿（api 载体 grep 零命中 · display 政策管线 · SPEC 纪律 3 修订 · app/·_tech_graph 零 diff）· 双闸 00 代录 · 归档 done/ · Hub 补登 · CLOSE 文档 `docs/tasks/close/` 落盘 · worktree+分支移交 00 清理 · **钉案：混合脏树切分 worktree 隔离 · graph-compile freeze 副作用须回滚 · web 路由语义先验再挂名（D4 教训）**） |

| 2026-10-30 | CLOSE **specwave-upgrade-3-5-0**（spec-wave 3.3.0→3.5.0 工具链钉版升级 · chore · 维护者令「更新specwave」· 升级类精简形态 · 双闸 00 代录 approved（授权锚 m00236）· 钉位全量对齐：package.json/双 lock/manifest/graph-compile.sh/lint-wiki-delta.yml · app/ 零 diff（S7/S8 env 单源实证）· V1–V8 全绿 · 3.5.0 graph_anchor INFO skip（graph_path_unreachable）与 3.4.0 址B 双址扫描无回归实证 · exempt 扩列四字段 · 无 R1 审查文照登 --allow-no-review 留痕豁免 · FEEDBACK `docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` · **全程本地零 push/PR（维护者令）· 分支 task/specwave-upgrade-3-5-0 移交维护者裁决** · 遗留：prompts sync 与 legacy profile graph_modules_path 修正另案 · task 档 `task_specwave_upgrade_3_5_0.md`） |
| 2026-11-05 | CLOSE **stage-w-write-expand** `#330`（阶段 W 扩写 · Q1=S1 仓内落笔型写 · issue #323 签收链同日全棒：SPEC v0.1 签 → 拆 task+设计闸签 #325 → 20-task-audit R1 PASS+三闸预授权代录 #326 → 30 实现 #327 squash `51030a4`（红测先行 16 枚 · V13 · Q3 新表 `ops_capability_notes` · G-L1 回写）→ 40 复跑 PASS 带偏差登记 #328 squash `3d08529`（live 全链八段实录 · 重复 decide 409 / 写窗 409 live 实证）· CI 4/4 绿 ×2 · lead 双棒终审 APPROVED · 红线零破（registry/policy/lg_rag/gateway/SSE 零 diff）· 归档 done/ · CLOSE 档+50 invoke 落盘 · **40 live 实证既有缺陷 `_worker_state` Send 载荷丢 `run_id`（PR #303 时期潜伏 · 非本 task 回归 · 修复形态已 shim 验证）→ 另立 fix task** · 留转：supervisor prompt `args` 字段文档化 + 既有本地产能红 4 枚清理） |

## 给维护者

`done`、`domain`、`Hub`、`_views`、`freeze_id`、`Epic`
