---
title: 审查门禁双址规约（review-gate dual-address convention）
version: v1
date: 2026-10-11
source_task: specwave-verify-baseline
---

# 审查门禁双址规约 v1（docs/harness/reviews/ ↔ docs/audits/task-review/）

> **性质**：仓级规约档（CONVENTION）· 钉死审查文落址与 verify 门禁消费口径。  
> **立项**：task_specwave_verify_baseline D2 裁定（三闸 approved 2026-10-11 · 00 代录 · 授权 m01606/m00255）。  
> **原则**：**只钉规约，不挪存量**——docs/harness/reviews/ 133 档与 docs/audits/task-review/ 既有档零挪零改。

## 一、工具口径实证（spec-wave 3.2.0 · 源码在案）

仓级 `npx spec-wave verify` 的审查门禁消费面（`src/checks/review-gates.ts` `findLatestReview`）：

| 维度 | 实证真值 |
|------|----------|
| 扫描目录 | **仅** `docs/harness/reviews/` 与 `reviews/` 两址（仓内只用前者） |
| 命名口径 | `task_<slug>_audit_R<n>_*.md`（RE `^(task_.+?)_audit_R(\d+)_.*\.md$` · 按最高 R 轮取最新） |
| 结论机读口径 | 审查文须含以「结论/签收」起首的 ##/### 节 · 节内含通过词（PASS/ACCEPT/签收/通过/零阻塞）· 无否定结论词 · 去通过词后实质 ≥20 字符 · 含审查行为陈述（SUBJ · 审查/评审/核对/复核/审计/验收/检查/audit/review） |
| 豁免机制 | `docs/harness/legacy-gate-exempt.yaml`（failClosed · 四字段 slug/reason/date/authorized_by · authorized_by 过 A1 三元判「身份（YYYY-MM-DD …授权出处词…）」） |

**关键限制（钉死）**：`docs/audits/task-review/` **完全不入 verify 扫描面**。审查文只落该址时，对应 done 任务 verify 仍报 `missing R<n> review` BLOCKED。

**误报实证（两起在案）**：
1. `task_hitl_auto_resume_claim_race.md`（done）——20 R1 审查文落 `docs/audits/task-review/20261010_hitl-auto-resume-claim-race_r1.md`，verify 消费址无档 → 列入本 task 基线 93 缺口（missing R<n> review）。
2. B1/B2 两 task（00 调度 2026-10-11 实证）——审查文只落新规约址 → verify 误报 missing R<n> review BLOCKED · 已裁定各棒复制审查文回旧址过渡。

## 二、双址分工裁定（D2 落钉）

| 址 | 定位 | 命名规约 | verify 消费？ |
|----|------|----------|----------------|
| **址A · `docs/harness/reviews/`** | **verify 门禁消费址（唯一真值面）** | `task_<slug>_audit_R<n>_YYYYMMDD.md` | ✅ 扫描 |
| **址B · `docs/audits/task-review/`** | 20 书面审存档址 | `YYYYMMDD_<slug>_r<n>.md` | ❌ 不扫描 |

**过渡期口径（当前生效）**：
1. 新增审查文**必须落址A**（供 verify 门禁消费 · 命名与机读口径从上表）；**可同时落址B** 存档（双址各落一份 · 同文或互参）。
2. 只落址B = verify 红（预期行为 · 非误伤 · 补落址A 即复绿）。
3. 存量档零挪零改：址A 133 档与址B 既有档保持原址原内容（钉死契约 4/5）。

**根治方向（照登非范围）**：verify 上游支持址B 扫描——属 spec-wave 上游改动，本 task 非范围已钉（不改上游 verify 规则）；上游若日后支持，本规约届时修订。

## 三、存量豁免清单规约（legacy-gate-exempt.yaml）

1. **清单档**：`docs/harness/legacy-gate-exempt.yaml`（本 task 新建 · 基线 93 档逐枚列入 · 提取自 verify 实跑输出 · 禁手敲）。
2. **条目语义**：`reason: 存量基线豁免 · 未审` 中「未审」= **未在址A落可机读通过审查档**——覆盖「根本无审查文」与「审查文存在但未达机读口径/未落消费址」两类；豁免 **≠** 审查通过（诚实口径 · 禁伪造审查）。
3. **增量零豁免**：新增 task/spec 档不得入清单；新增不合规档 verify 必须红（TC3 反向实证在案）。
4. **扩列纪律**：每行四字段齐（slug/reason/date/authorized_by · authorized_by 过 A1 形态判）+ PR 人审拦截滥用。

## 四、EXIT 码自证口径（D3）

凡验收/文档引 verify EXIT 码：**重定向后取 `$?`** 或 `set -o pipefail`——`verify | tail` 类管道吞码报 0 为已知坑（T1 30 棒前科 · 本 task 实证复现：管道 0 vs 真值 2）。

```bash
npx spec-wave verify --target . > /tmp/verify.txt 2>&1; echo "EXIT=$?"   # ✅ 正解
npx spec-wave verify --target . | tail -5                                # ❌ 吞码
```

## 五、TC1 基线全表（93 档逐档分类落账 · 与实跑输出 1:1 对账）

> 来源：`/tmp/verify_baseline_30.txt`（2026-10-11 30 棒实跑 · EXIT=2 · 尾行 `VERIFY: BLOCKED · 仓级 reviews 缺口 93`）逐行 parse · 处置全部落地后 verify EXIT=0 PASS（93 豁免命中留痕 · 0 invalid）。

| # | done 档 | 缺口类型 | 处置 |
|---|---------|----------|------|
| 1 | `docs/tasks/done/task_admin_github_sync_2026-07-17.md` | 零审查档（missing R<n> review） | 豁免 |
| 2 | `docs/tasks/done/task_agent_host_framework_alignment.md` | 零审查档（missing R<n> review） | 豁免 |
| 3 | `docs/tasks/done/task_agent_infra_spec_hierarchy.md` | 审查文无结论/签收节 | 豁免 |
| 4 | `docs/tasks/done/task_auth_session_db_cookie.md` | 零审查档（missing R<n> review） | 豁免 |
| 5 | `docs/tasks/done/task_cap_mcp_real.md` | 审查文无结论/签收节 | 豁免 |
| 6 | `docs/tasks/done/task_cap_portable_core.md` | 审查文无结论/签收节 | 豁免 |
| 7 | `docs/tasks/done/task_capability_gateway_p0.md` | 审查文无结论/签收节 | 豁免 |
| 8 | `docs/tasks/done/task_capability_gateway_p1.md` | 审查文无结论/签收节 | 豁免 |
| 9 | `docs/tasks/done/task_capability_gateway_p2.md` | 审查文无结论/签收节 | 豁免 |
| 10 | `docs/tasks/done/task_capability_gateway_p3.md` | 审查文无结论/签收节 | 豁免 |
| 11 | `docs/tasks/done/task_capability_policy_sandbox.md` | 审查文无结论/签收节 | 豁免 |
| 12 | `docs/tasks/done/task_catalog_manifest_yaml.md` | 审查文无结论/签收节 | 豁免 |
| 13 | `docs/tasks/done/task_chat_session_continuity.md` | 审查文无结论/签收节 | 豁免 |
| 14 | `docs/tasks/done/task_chat_websocket_v1_2026-07-18.md` | 零审查档（missing R<n> review） | 豁免 |
| 15 | `docs/tasks/done/task_critic_rebind.md` | 审查文无结论/签收节 | 豁免 |
| 16 | `docs/tasks/done/task_dsh_coding_kit_upgrade_1_5_1.md` | 零审查档（missing R<n> review） | 豁免 |
| 17 | `docs/tasks/done/task_dsh_coding_kit_upgrade_1_5_2.md` | 零审查档（missing R<n> review） | 豁免 |
| 18 | `docs/tasks/done/task_dsh_coding_kit_upgrade_1_6_1.md` | 零审查档（missing R<n> review） | 豁免 |
| 19 | `docs/tasks/done/task_dsh_coding_kit_upgrade_1_8_0.md` | 零审查档（missing R<n> review） | 豁免 |
| 20 | `docs/tasks/done/task_dsh_kit_graph_command_switch.md` | 零审查档（missing R<n> review） | 豁免 |
| 21 | `docs/tasks/done/task_dsh_kit_graph_migrate_probe.md` | 零审查档（missing R<n> review） | 豁免 |
| 22 | `docs/tasks/done/task_eval_e0_e1.md` | 审查文无结论/签收节 | 豁免 |
| 23 | `docs/tasks/done/task_eval_goldenset_lg_rag.md` | 审查文无结论/签收节 | 豁免 |
| 24 | `docs/tasks/done/task_eval_langfuse_experiment_ci.md` | 审查文无结论/签收节 | 豁免 |
| 25 | `docs/tasks/done/task_eval_online_sample_scores.md` | 审查文无结论/签收节 | 豁免 |
| 26 | `docs/tasks/done/task_eval_token_cost_ledger.md` | 审查文无结论/签收节 | 豁免 |
| 27 | `docs/tasks/done/task_fix_deploy_cpu_torch.md` | 零审查档（missing R<n> review） | 豁免 |
| 28 | `docs/tasks/done/task_fix_deploy_ssh_keepalive.md` | 零审查档（missing R<n> review） | 豁免 |
| 29 | `docs/tasks/done/task_golden-query-set-v1.md` | 审查文无结论/签收节 | 豁免 |
| 30 | `docs/tasks/done/task_graph_bootstrap.md` | 零审查档（missing R<n> review） | 豁免 |
| 31 | `docs/tasks/done/task_harness_upgrade_2-18-migrate.md` | 结论节缺审查行为陈述（SUBJ） | 豁免 |
| 32 | `docs/tasks/done/task_harness_upgrade_2.17.0.md` | 结论节缺审查行为陈述（SUBJ） | 豁免 |
| 33 | `docs/tasks/done/task_harness_upgrade_2.19.0.md` | 结论节缺审查行为陈述（SUBJ） | 豁免 |
| 34 | `docs/tasks/done/task_hitl_auto_resume_claim_race.md` | 零审查档（missing R<n> review） | 豁免 |
| 35 | `docs/tasks/done/task_host_comms_boundary_spec.md` | 结论节含否定结论词 | 豁免 |
| 36 | `docs/tasks/done/task_host_comms_prompt_pack.md` | 结论节含否定结论词 | 豁免 |
| 37 | `docs/tasks/done/task_host_comms_task_writer.md` | 结论节含否定结论词 | 豁免 |
| 38 | `docs/tasks/done/task_host_harness_cli_capability.md` | 结论节含否定结论词 | 豁免 |
| 39 | `docs/tasks/done/task_host_obs_comms_ui.md` | 结论节含否定结论词 | 豁免 |
| 40 | `docs/tasks/done/task_import_null_sync_type.md` | 零审查档（missing R<n> review） | 豁免 |
| 41 | `docs/tasks/done/task_inform_graph_backfill_w2_bypass_flows.md` | 零审查档（missing R<n> review） | 豁免 |
| 42 | `docs/tasks/done/task_inform_graph_backfill_w3_chat_g2.md` | 零审查档（missing R<n> review） | 豁免 |
| 43 | `docs/tasks/done/task_inform_graph_backfill_w4_rag_flow.md` | 零审查档（missing R<n> review） | 豁免 |
| 44 | `docs/tasks/done/task_inform_graph_backfill_w5_coverage.md` | 零审查档（missing R<n> review） | 豁免 |
| 45 | `docs/tasks/done/task_inform_graph_backfill_w6_modules_trim.md` | 零审查档（missing R<n> review） | 豁免 |
| 46 | `docs/tasks/done/task_intent_schema_v1.md` | 审查文无结论/签收节 | 豁免 |
| 47 | `docs/tasks/done/task_langfuse_cached_input_tokens.md` | 审查文无结论/签收节 | 豁免 |
| 48 | `docs/tasks/done/task_lc_evidence_chain_hardening.md` | 结论节含否定结论词 | 豁免 |
| 49 | `docs/tasks/done/task_lc_evidence_http.md` | 审查文无结论/签收节 | 豁免 |
| 50 | `docs/tasks/done/task_lc_evidence_langfuse_tracing.md` | 审查文无结论/签收节 | 豁免 |
| 51 | `docs/tasks/done/task_lc_evidence_retrieve_langfuse.md` | 审查文无结论/签收节 | 豁免 |
| 52 | `docs/tasks/done/task_lg_rag_deprecate_chat_stream.md` | 结论节含否定结论词 | 豁免 |
| 53 | `docs/tasks/done/task_lg_rag_http.md` | 零审查档（missing R<n> review） | 豁免 |
| 54 | `docs/tasks/done/task_lg_rag_phase1.md` | 零审查档（missing R<n> review） | 豁免 |
| 55 | `docs/tasks/done/task_lg_rag_phase2.md` | 零审查档（missing R<n> review） | 豁免 |
| 56 | `docs/tasks/done/task_lg_rag_phase3.md` | 零审查档（missing R<n> review） | 豁免 |
| 57 | `docs/tasks/done/task_lg_rag_phase4.md` | 零审查档（missing R<n> review） | 豁免 |
| 58 | `docs/tasks/done/task_lg_rag_sse_idle_keepalive.md` | 零审查档（missing R<n> review） | 豁免 |
| 59 | `docs/tasks/done/task_lg_rag_sse_stream_updates.md` | 审查文无结论/签收节 | 豁免 |
| 60 | `docs/tasks/done/task_lg_rag_sse_subtask_live.md` | 零审查档（missing R<n> review） | 豁免 |
| 61 | `docs/tasks/done/task_lg_rag_sse_subtask_message.md` | 审查文无结论/签收节 | 豁免 |
| 62 | `docs/tasks/done/task_lg_rag_sse_subtask_steps.md` | 审查文无结论/签收节 | 豁免 |
| 63 | `docs/tasks/done/task_lg_rag_sse_t0_t1_spec.md` | 零审查档（missing R<n> review） | 豁免 |
| 64 | `docs/tasks/done/task_lg_rag_sse_token_stream.md` | 结论节含否定结论词 | 豁免 |
| 65 | `docs/tasks/done/task_lg_rag_supervisor_capability_catalog.md` | 审查文无结论/签收节 | 豁免 |
| 66 | `docs/tasks/done/task_llm_provider_v1.md` | 零审查档（missing R<n> review） | 豁免 |
| 67 | `docs/tasks/done/task_ops_pg_lookup_capabilities.md` | 审查文无结论/签收节 | 豁免 |
| 68 | `docs/tasks/done/task_ops_sync_sender_migration.md` | 审查文无结论/签收节 | 豁免 |
| 69 | `docs/tasks/done/task_overview_metrics.md` | 零审查档（missing R<n> review） | 豁免 |
| 70 | `docs/tasks/done/task_prompt_assembly_p1.md` | 零审查档（missing R<n> review） | 豁免 |
| 71 | `docs/tasks/done/task_qdrant_migration.md` | 结论节含否定结论词 | 豁免 |
| 72 | `docs/tasks/done/task_qdrant_server_upgrade.md` | 审查文无结论/签收节 | 豁免 |
| 73 | `docs/tasks/done/task_rag_embed_api_backend.md` | 结论节含否定结论词 | 豁免 |
| 74 | `docs/tasks/done/task_rag_reranker_p0.md` | 审查文无结论/签收节 | 豁免 |
| 75 | `docs/tasks/done/task_rag_sparse_arm_c.md` | 审查文无结论/签收节 | 豁免 |
| 76 | `docs/tasks/done/task_rag_zhparser_arm_a.md` | 审查文无结论/签收节 | 豁免 |
| 77 | `docs/tasks/done/task_siliconflow_default_catalog_cost.md` | 审查文无结论/签收节 | 豁免 |
| 78 | `docs/tasks/done/task_siliconflow_rerank_api.md` | 结论节含否定结论词 | 豁免 |
| 79 | `docs/tasks/done/task_skill_registry_p0.md` | 审查文无结论/签收节 | 豁免 |
| 80 | `docs/tasks/done/task_so_schema_hygiene.md` | 审查文无结论/签收节 | 豁免 |
| 81 | `docs/tasks/done/task_strategy_builder_allowlist.md` | 审查文无结论/签收节 | 豁免 |
| 82 | `docs/tasks/done/task_strategy_builder_spec.md` | 零审查档（missing R<n> review） | 豁免 |
| 83 | `docs/tasks/done/task_structured_output_gateway_p0.md` | 结论节含否定结论词 | 豁免 |
| 84 | `docs/tasks/done/task_structured_output_gateway_p1.md` | 结论节含否定结论词 | 豁免 |
| 85 | `docs/tasks/done/task_structured_output_gateway_p2.md` | 审查文无结论/签收节 | 豁免 |
| 86 | `docs/tasks/done/task_structured_output_gateway_p3.md` | 审查文无结论/签收节 | 豁免 |
| 87 | `docs/tasks/done/task_supabase_initial_import.md` | 零审查档（missing R<n> review） | 豁免 |
| 88 | `docs/tasks/done/task_task_closeout_hygiene.md` | 零审查档（missing R<n> review） | 豁免 |
| 89 | `docs/tasks/done/task_tech_graph_legacy_cleanup.md` | 审查文无结论/签收节 | 豁免 |
| 90 | `docs/tasks/done/task_tech_graph_recent_sync.md` | 零审查档（missing R<n> review） | 豁免 |
| 91 | `docs/tasks/done/task_tenant_readonly_predicate.md` | 零审查档（missing R<n> review） | 豁免 |
| 92 | `docs/tasks/done/task_upgrade_harness_2_20_runbook_feedback.md` | 结论节缺审查行为陈述（SUBJ） | 豁免 |
| 93 | `docs/tasks/done/task_wikitrack_enable_p0.md` | 结论节缺审查行为陈述（SUBJ） | 豁免 |

**分账合计**：零审查档 36 + 无结论/签收节 39 + 否定结论词 13 + 缺 SUBJ 5 = **93**（与 R1 复核口径一致 · N-1 修正后 done/ 154 档）。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 30 落钉（task_specwave_verify_baseline D2）：工具口径实证（址B 不入扫描面 · 误报两起在案）· 双址分工裁定（址A 消费址 · 址B 存档址 · 过渡双落）· 豁免清单规约（四字段 · 未审语义 · 增量零豁免）· EXIT 自证口径 · TC1 基线全表 93 档 |
