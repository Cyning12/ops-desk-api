# invoke · 10 起草 · p4-t2-prompt-domain-loader

> **task_slug**：p4-t2-prompt-domain-loader
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权 · 委派书 p4-t2-prompt-domain-loader）

## 内容

1. 落卡 docs/tasks/active/task_p4_t2_prompt_domain_loader.md（体例照 docs/tasks/done/task_p2c_t1_planner_tool_awareness.md）：Harness 元信息表（task_slug/base=cfe76b23/关联 issue/wiki_delta n/a/graph_change_layer G-L1/review_hat 20）· 人工闸表三行 approved · 背景（domain-pack-v1 部署级领域 · 19 契约 §3 钉死口径）· 范围 8 条 · 非范围 5 条 · 失败路径 8 条 · 验收标准 11 条 · 必读列表 · 思考轮 R0-R5（actual_last_round=R5）。
2. 勘察结论入档：loader.py:20 _ID_RE 允许点号 · :51-80 load_asset 读取校验主体；templates.py:11-30 白名单 11 id + TEMPLATES import 期构建；render.py:25-54 get_template/render；tenant_context.py contextvar 先例；run_worker.py:116-166 _main token 模式（注入同位）；.importlinter lg-rag-outbound 同族互导允许（零新边）；六处 render 调用点零 churn 面确认。
3. 口径定稿（19 §3.1-§3.4 · commit e453a36）：目录回退（命中=文件存在 · 存在即全量校验坏件显式炸 · 缺失回退根目录 · 否半份合并 · 缓存键=(template_id, domain)）；白名单 11 id 不动 + TEMPLATES ops 默认面零 diff + get_template_for_domain 薄封装；domain_context.py（resolve_domain 非法回退 ops+warning · worker 注入位）；不建 assets/ops/。
4. 裁定登记（偏差候选）：current_domain() 未注入时回落 resolve_domain_from_env() 而非恒 ops——OPS_DOMAIN 缺省/非法时与契约字面一致（归 ops），OPS_DOMAIN=oa 时非 run 通路读部署域同值（R-P4-2 漏设无害化强化 · ops 部署零行为差）。
5. registry entry（status=active · base=cfe76b23 · allowed_app_files 五件=[prompts/{loader,templates,render,domain_context}.py, lg_rag/run_worker.py] · banned_prefixes=[alembic/, scripts/]）。

## 验证台账

| 检查 | 结果 |
|------|------|
| npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t2_prompt_domain_loader.md | PASS |
| npx spec-wave verify --target . --task docs/tasks/active/task_p4_t2_prompt_domain_loader.md | 人工闸三行 approved（30 放行依据） |

## 偏差

无。

## 结果

10 起草完成 · 进 20-R1 审查文。
