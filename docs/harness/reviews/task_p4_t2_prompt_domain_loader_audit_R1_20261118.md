# R1 审查文 · task_p4_t2_prompt_domain_loader

> **审查帽**：20-task-audit（R1）
> **task**：docs/tasks/active/task_p4_t2_prompt_domain_loader.md
> **日期**：2026-11-18
> **授权链**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权）· 需求真源 workspace 18-domain-pack-v1.md §2/:94-97 + §10 P4-T2 任务行 · 口径真源 19-p4-contracts.md §3（commit e453a36 钉死）· 委派书 p4-t2-prompt-domain-loader

## 结论

**GO · PASS · 零阻塞** — task 档范围/非范围/验收/failure_paths/思考轮（R0-R5）齐备，与 19 契约 §3.1-§3.4 钉死口径逐条对齐，修法裁定「目录回退 · 白名单薄封装 · contextvar 注入 · 调用点零 churn · 不建 assets/ops/」为契约内最小改动面，可进 30。

## 核对项

| 项 | 结论 | 依据 |
|----|------|------|
| 范围8条 ↔ 委派书/19 §3 | 一致 | loader 目录回退+缓存键扩展（§3.1）· templates 薄封装白名单不动（§3.2）· domain_context.py + worker 注入位（§3.3）· 不建 assets/ops/（§3.4）· 测试九类断言 · 图谱签收 + 过闸落盘 |
| 非范围 | 一致 | manifest domain 键消费 T3 · RAG 域隔离 T4 · oa 域资产 T5 · skill/goal 域回退 R11 · memory domain 列 R4 · 不挂 tenant · 11 份既有模板资产零变更 · 调用点零 churn · 零新依赖 · alembic//scripts//.importlinter 禁入 |
| 验收标准 | 11 条全机判锚 | 域命中 · 缺失回退（按模板独立）· 坏件显式炸 · 词表拒入+路径穿越负例 · 解析回退+warning · OPS_DOMAIN on/off 11 模板逐字节对拍（§3.4）· 白名单 KeyError · get_template 域路由 · worker 注入 · 回归+全量+ruff · 图谱两件 · 过闸四件 |
| failure_paths | 8 条 | 路径穿越双闸 · 坏件静默 · 漏设错域（R-P4-2）· 词表互拼（R5）· import 期漂移 · 并行冲突 · 环境性红对照 · 脏树期 registry 红常态 |
| 思考轮 | R0-R5 齐 · actual_last_round=R5 | 表头 `| 轮 | 结论 | early_stop |` 合规 |
| 人工闸表 | 三行 approved | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · issue #23 授权 |
| 体例 | 照 p2c-t1-planner-tool-awareness done 模板 | registry/invokes/图谱签收承 P2c-T1 先例 |
| 仓规条款一 | 遵守 | 本审查文即 20-R1 路径 · 未用 --allow-no-review |

## 关键决策复核

- **目录回退语义与契约逐字对齐**：命中判定=文件存在（is_file）；存在即走同一 _load_from_path 全量校验（坏件 PromptAssetError 显式炸点名域件路径 · 坏文件不静默）；不存在回退根目录；否半份合并（域件缺字段不拿根件补）——契约「覆盖以模板为单位缺省回退」逐字落实；缓存键 (template_id, domain) 扩展后旧键 (id, None) 与新键 (id, "ops") 并存读同路径零语义差。
- **路径穿越双闸成立**：env 面 resolve_domain 词表 [a-z0-9_]+ fullmatch 非法回退 ops + logger.warning（§5.1）；loader 入参面 domain 词表校验非法抛 PromptAssetError——路径字符（../ · 分隔符）永远进不了目录拼接，纵深防御；词表纪律（§1.2 R5）domain 无点号与 template id 词表（loader.py:20 允许点号）各自独立禁止互拼，测试钉「domain 带点号拒入」。
- **白名单薄封装形态成立**：_TEMPLATE_IDS 11 id 编译期白名单不动（§3.2）；TEMPLATES import 期构建保持 load_asset(template_id) 单参不传 domain（ops 默认面零 diff · 既有 test_prompt_assets EXPECTED_IDS 集合等式+版本钉版断言天然全绿）；get_template_for_domain 置 templates.py 与 _TEMPLATE_IDS 同文件（白名单唯一真源）；render.get_template 为唯一域路由点（ops 走 TEMPLATES 同对象 · 非 ops 委托薄封装 · 未知 id PromptTemplateNotFoundError 保持）——六处调用点（memory/extract.py:31 · lg_rag/multi/nodes.py:76 · lg_rag/query_rewrite.py:35 · lg_rag/nodes.py:27 · strategy/intent.py:13 · session/summary.py:38）零 churn。
- **current_domain env 回落裁定成立（偏差候选 · 已入 task 档 R3 登记）**：19 §3.3 字面「默认 ops」；裁定未注入时回落 resolve_domain_from_env()——OPS_DOMAIN 缺省/非法时与契约字面完全一致（归 ops · ops 部署零行为差 · §3.4 对拍验收不受影响），OPS_DOMAIN=oa 时非 run 通路（session/summary.py 等 HTTP 面）读部署域同值而非静默 ops；契约「注入位 run 启动处」原样实现（worker 显式注入 + finally reset 保 run 内确定性）。理由链完整：OPS_DOMAIN 部署级单值承 QDRANT_COLLECTION 先例（18 :94-97），「漏设无害化」由「读到部署域同值」结构性成立，比「读到 ops 同值」更贴近 R-P4-2 设计意图。
- **worker 注入位成立**：run_worker.py:116-166 _main 内 tenant_token/llm_token 模式（set 于开头 · finally reset）——domain_token 同位同构；.importlinter lg-rag-outbound contract source_modules 含 app.ops.prompts（同族互导允许）· domain_context.py 仅 stdlib——零新边零 contract 改动。
- **零 diff 双保险成立**：不建 assets/ops/（§3.4）→ 域=ops 时域目录不存在恒回退根目录；叠加验收「OPS_DOMAIN on/off 11 模板 body 逐字节对拍」机判锚，ops 面行为漂移结构性不可藏。
- **测试隔离形态成立**：tmp_assets fixture 承 test_prompt_assets.py:146-151（monkeypatch loader._ASSETS_DIR + clear_asset_cache）——域件模拟不触真实 assets/ · 11 份既有模板资产零变更。

## 偏差确认

一项（已入 task 档 R3 + 范围第 3 条登记）：current_domain() 未注入回落 env 解析（R-P4-2 强化裁定 · 对 19 §3.3「默认 ops」字面的语义扩展 · ops 部署行为零差 · 理由见关键决策复核第四条）。其余无偏差：委派书四条全覆盖无裁剪。

## 机读通过词

PASS（spec-wave task lint 命令：`npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t2_prompt_domain_loader.md`）
