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

## 给维护者

`done`、`domain`、`Hub`、`_views`、`freeze_id`、`Epic`
