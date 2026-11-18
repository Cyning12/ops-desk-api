# invoke · 10 · P4-T4 RAG 域配置面 task 落卡（draft）

> 2026-11-18 · task_slug=p4-t4-rag-domain-config · hat=10 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03796（夜间授权）· 委派书 p4-t4-rag-domain-config 为唯一范围真源

## 内容编号清单

1. **task 档**：docs/tasks/active/task_p4_t4_rag_domain_config.md——Harness 元信息（base=370a137a · graph_change_layer=G-L1 · review_hat=20 · wiki_delta=n/a）· 人工闸表三行（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES approved 2026-11-18 · 授权 issue #23 m03064/m03796）· 背景 · 范围 8 条 · 非范围 6 条 · 失败路径 8 条 · 验收标准 10 条 · 必读列表（需求真源 18 文 §2.3/§10 P4-T4 行/§13 + 19 契约 §4 commit e453a36 · 代码锚 · 契约锚 · 测试锚 · 体例先例）· 思考轮 R0-R5（actual_last_round=R5）· 实现备忘（偏差登记/限制登记占位 · 30/40 波回填）· 测试策略 · 修订记录。
2. **registry entry**：docs/harness/audit_gates/registry.yaml 追加 p4-t4-rag-domain-config（status=active · base="370a137a" · note 含修法裁定 · allowed_app_files 四件=[app/ops/rag/backend.py, app/ops/rag/glossary.py, app/ops/rag/shadow_write.py, app/ops/lg_rag/multi/nodes.py] · allowed_tree_files 六件 · allowed_tree_prefixes=invokes by-task/p4-t4-rag-domain-config/ · banned_prefixes=[alembic/, scripts/]）。
3. **R1 审查文**：docs/harness/reviews/task_p4_t4_rag_domain_config_audit_R1_20261118.md——结论 GO · PASS · 零阻塞（仓规条款一：走 20-R1 审查文非 --allow-no-review）。
4. **本 invoke**：10 波过程件。

## 验证台账

| 项 | 命令/方式 | 结果 |
|----|-----------|------|
| 委派书范围对账 | 逐条对照 19 §4.1/§4.2/§4.3 + 18 §2.3/§10 P4-T4 行/§13 vs 代码锚（backend.py:39-40 · glossary.py:18-29 · shadow_write.py:111-147 · nodes.py:1921-1998 · qdrant_retriever.py:38 · retrieve.py:95/171-178 · domain_context.py） | 全格锚定 · 无悬空 |
| 静态边界核对 | .importlinter rag-outbound（:100-125）/ lg-rag-outbound（:207-247）逐 forbidden 对改造点 | rag→prompts 与 lg_rag→rag.backend 判为 importlib 运行期解析（承 continuity.py 先例 · .importlinter 零改动）；lg_rag→prompts 静态合法（nodes.py:76 既有边实证） |
| task lint | `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t4_rag_domain_config.md` | PASS（exit 0 · W3 自检结论占位符 draft 期合法警告 · close 前须回填） |
| gate verify | `npx --yes spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_p4_t4_rag_domain_config.md`（GATE_VERIFY 闸扫描） | PASS（exit 0 · HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 三闸 approved · 可 30 · INFO 图谱锚点检查跳过 vocabulary_empty=01_struct.md 缺失仓内常态） |

## 偏差

- 无（10 波纯文档面 · 零 app 代码改动）。

## 结果

- task 档 + registry entry（active）+ R1 审查文（GO）+ 本 invoke 落盘；task lint PASS 后转 30 实现波（四件 app 文件 + tests/test_rag_domain_config.py）。
