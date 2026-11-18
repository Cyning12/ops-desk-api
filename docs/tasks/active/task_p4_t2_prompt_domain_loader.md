---
title: task · P4-T2 · prompt 模板域机制（domain-pack-v1 · 目录回退 + 白名单薄封装 + contextvar 注入）
---

# task · P4-T2 · prompt 模板域机制（domain-pack-v1 · 目录回退 + 白名单薄封装 + contextvar 注入）

> **状态**：`active`（2026-11-18 落卡 · 夜间自动执行波）
> **来源**：domain-pack-v1 设计 18 文 §10 P4-T2 任务行 + 19 契约 §3（钉死口径真源 · commit e453a36）· 授权 issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权 · 委派书 p4-t2-prompt-domain-loader）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p4-t2-prompt-domain-loader |
| base | cfe76b23 |
| 关联 issue | issue Cyning12/ops-desk-workspace#23（授权真源）· 18 设计文 §2/:94-97 + 19 契约 §3（需求与口径真源） |
| 关联 PR | feat 本 PR · close chore PR（收口登记） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 prompts 域机制 G-L1 面 + 图谱登记 |
| graph_change_layer | G-L1（01_modules.md lg_rag 行 p4-t2 备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-18 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03796（夜间授权）+ 委派书 p4-t2-prompt-domain-loader 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-18 · 同上授权 + R1 审查文 docs/harness/reviews/task_p4_t2_prompt_domain_loader_audit_R1_20261118.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-18 · 同上授权（lg_rag 行 p4-t2 备注属图谱登记义务 · 随 30 交付回填） |

## 背景

domain-pack-v1 为 ops-desk 引入「部署级领域」概念：同一后端按部署服务不同领域（ops 默认 · oa 办公域后继），prompt 模板需按域覆盖且 ops 面逐字节零 diff。19 契约 §3（commit e453a36 钉死）定稿三件套口径：§3.1 loader 目录回退（assets/<domain>/<id>.md 命中用域件、缺失回退根目录、坏域件显式炸、缓存键=(template_id, domain)）· §3.2 编译期白名单 11 id 不动 + TEMPLATES 保持 ops 默认面（import 期零 diff）+ 新增 get_template_for_domain 薄封装 · §3.3 新增 domain_context.py（contextvar 默认 ops · 注入位 start_run_worker 与 set_current_tenant 同位）· §3.4 不建 assets/ops/（零 diff 双保险）。词表纪律（19 §1.2 R5）：domain 词表 [a-z0-9_]+ 无点号、与 template id 词表（loader.py:20 允许点号）各自独立禁止互拼——domain 只拼目录名不进 template_id。OPS_DOMAIN 部署级 env（承 QDRANT_COLLECTION 先例 · 不挂 tenant），默认/缺省/非法 → ops + logger.warning（§5.1 防 env 注入路径穿越）。本波依赖 P4-T1（capability manifest · 已 merge）。

## 范围

1. **loader 目录回退**（19 §3.1）：`app/ops/prompts/loader.py`——`load_asset(template_id, domain=None)` 增 domain 形参；domain 非空先读 `assets/<domain>/<id>.md`，文件不存在回退根目录（覆盖以模板为单位 · 否半份合并）；缓存键扩展为 (template_id, domain)；domain 词表校验（[a-z0-9_]+ fullmatch · 非法拒入 loader 抛 PromptAssetError 点名 · 路径穿越负例）；域文件存在但形态非法 → PromptAssetError 显式炸点名路径（坏文件不静默 · 缺文件才回退）；读取主体抽 `_load_from_path` 复用（根/域同校验面）；域集合运行时发现在 assets/ 子目录不硬编码。
2. **templates 薄封装**（19 §3.2）：`app/ops/prompts/templates.py`——`_TEMPLATE_IDS` 11 id 白名单不动；`TEMPLATES` import 期构建保持 ops 默认面（load_asset(template_id) 不传 domain · 零 diff）；新增 `get_template_for_domain(template_id, domain)` 薄封装（白名单查 KeyError 原样 · 委托 load_asset 带 domain）；docstring 「10 模板」陈旧注释修正为 11（18 文已点名）。
3. **domain_context 注入面**（19 §3.3）：新增 `app/ops/prompts/domain_context.py`（仿 tenant_context.py · stdlib only）——`DEFAULT_DOMAIN="ops"` · `_DOMAIN_RE` · `resolve_domain(raw)`（缺省/空白/非法 → ops + logger.warning 一次一值 @cache · 值返回型纯函数）· `resolve_domain_from_env()`（读 OPS_DOMAIN）· `current_domain()`（contextvar 已注入用注入值 · 未注入回落 env 解析=R-P4-2 漏设无害化强化裁定）· `set_current_domain(domain)`（词表校验 · 非法 ValueError 编程错误面）· `reset_current_domain(token)`。
4. **render 域路由**（19 §3.3 调用点零 churn）：`app/ops/prompts/render.py`——`get_template(template_id)` 内部读 `current_domain()`：域=ops 走 TEMPLATES（现状同路径零 diff）· 非 ops 走 `get_template_for_domain`（未知 id KeyError → PromptTemplateNotFoundError 保持）；`render()` 本体零改。
5. **worker 注入位**：`app/ops/lg_rag/run_worker.py`——`_main()` 内 `domain_token = set_current_domain(resolve_domain_from_env())`（与 set_current_tenant 同位 · finally reset_current_domain）。
6. **测试**（新增 `tests/test_prompt_domain_assets.py` · tmp_assets 形态承 test_prompt_assets.py:146-151 先例）：域文件命中 / 缺失回退（按模板独立）/ 坏域件显式炸点名路径 / 非法 domain 词表拒入（含 ../ 路径穿越负例）/ resolve_domain 缺省·空白·非法回退 ops + warning / OPS_DOMAIN on/off 全量 11 模板 body 逐字节对拍一致（19 §3.4 验收）/ 白名单越界 KeyError / get_template 域路由（ops=TEMPLATES 同对象 · 非 ops 走域件）/ worker 注入后 contextvar 可见性。真 PG 绿（postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀）· 目标回归（test_prompt_assets / test_prompt_render / test_prompt_packs / run_worker 相关）零红 · 全量 pytest 绿（环境性红与 base cfe76b23 同路径基线逐签对照 · CI 终裁）· `ruff check app tests` 绿。
7. **图谱**：`docs/_tech_graph/l1/01_modules.md` lg_rag 行（:35）补 p4-t2 备注 + HG-GRAPH-MODULES 签收行（承 P2c-T1 先例）。
8. **落盘**：registry entry（status=active → close 波 closed 钉 wave_tip）· invokes by-task/p4-t2-prompt-domain-loader/{10,30,40,50} · R1 审查文 · task 档 active→done。

## 非范围

- 不消费 manifest domain 键（P4-T3 范围）；不动 RAG 检索域隔离（P4-T4）；不做 oa 域资产落地（P4-T5 · oa 覆盖 7 份与 4 份刻意不覆盖均为 T5）。
- skill 目录/goal 注入属部署级资产不进域回退（19 §1.2 R11）；memory 不加 domain 列（R4）；domain 不挂 tenant（部署级进程单值 · 承 QDRANT_COLLECTION 先例）。
- 不建 `assets/ops/` 目录（19 §3.4 零 diff 双保险）；不动 11 份既有模板资产（零 bump 零内容变更）。
- 调用点零 churn：六处 render 调用点（memory/extract.py:31 · lg_rag/multi/nodes.py:76 · lg_rag/query_rewrite.py:35 · lg_rag/nodes.py:27 · strategy/intent.py:13 · session/summary.py:38）不改一行。
- 不引新依赖；不碰 alembic/ · scripts/ · .importlinter（lg-rag-outbound contract 同族互导已允许 · 零新边）。

## 失败路径

- 路径穿越：domain 经 env/入参带 `../` 或分隔符拼出 assets/ 外路径 → _DOMAIN_RE fullmatch 双重拒入（env 解析回退 ops + warning · loader 入参 PromptAssetError）· 负例测试守。
- 坏域件静默回退掩盖资产错误：域文件存在但形态非法必须显式炸（PromptAssetError 点名路径）——由坏件负例测试守；仅「文件不存在」才回退。
- contextvar 漏设读到错误域（R-P4-2）：current_domain() 未注入时回落 env 解析（默认/非法均归 ops · 与现状同值无害化 + oa 部署非 run 通路亦正确）· worker 注入位 finally reset 防跨 run 泄漏。
- 词表互拼（R5）：domain 只拼目录名不进 template_id——resolve_domain 词表无点号 · loader 只对 domain 段单独校验 · 测试钉「domain 带点号拒入」。
- import 期行为漂移：TEMPLATES 构建保持 load_asset(template_id) 单参（domain 默认 None）· test_prompt_assets EXPECTED_IDS 集合等式 + 版本钉版断言零 diff 回归。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → rebase origin/master 保留双方 entry 手动解，冲突块如实登记。
- 仓根 .env 渗入收集期致全量 pytest 环境性红 → 与 base cfe76b23 同路径基线逐签对照登记，CI 终裁。
- 脏树期 wave_gate_registry 红为结构性常态（委派书钉明）。

## 验收标准

- [ ] 域文件命中：assets/<domain>/<id>.md 存在时 load_asset(template_id, domain) 返回域件 (version, body)（新断言）
- [ ] 缺失回退：域件不存在回退根目录件；同 domain 下不同模板各自独立命中/回退（否半份合并 · 新断言）
- [ ] 坏件显式炸：域文件存在但形态非法 → PromptAssetError 点名域件路径（新断言）
- [ ] 非法 domain 拒入：词表外值（含 ../ 路径穿越 · 带点号）loader 抛 PromptAssetError（新断言）；resolve_domain 缺省/空白/非法 → ops + logger.warning（新断言）
- [ ] ops 零 diff 对拍：OPS_DOMAIN on/off 双跑全量 11 模板 body 逐字节一致（19 §3.4 · 新断言）
- [ ] 白名单不动：get_template_for_domain 白名单外 id → KeyError；TEMPLATES import 期 ops 默认面零 diff（既有 test_prompt_assets 全绿）
- [ ] get_template 域路由：ops 域返回 TEMPLATES 同对象；非 ops 域走域件；未知 id PromptTemplateNotFoundError 保持（新断言）
- [ ] worker 注入：start_run_worker _main 内 set_current_domain(resolve_domain_from_env()) 与 set_current_tenant 同位 + finally reset（新断言）
- [ ] 目标回归零红；全量 pytest 绿（环境性红逐签对照 base cfe76b23 · CI 终裁）；`ruff check app tests` 绿
- [ ] 01_modules.md lg_rag 行 p4-t2 备注 + HG-GRAPH-MODULES 签收行
- [ ] registry entry active · invokes 四件 · R1 审查文 · spec-wave task lint PASS

### 自检结论

（40 收口时回填 · 验收 11 条逐条锚定）

## 必读列表

- 需求真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/18-domain-pack-v1.md` §2/:94-97（OPS_DOMAIN env 解析 · 词表拒穿越 · 不挂 tenant）+ §10 P4-T2 任务行 · `19-p4-contracts.md` §3（commit e453a36 钉死口径 · §3.1-§3.4）+ §1.2 R5/R11 + §5.1
- 代码锚：`app/ops/prompts/loader.py:20`（_ID_RE 允许点号）· `:51-80`（load_asset 读取校验主体 → _load_from_path）· `app/ops/prompts/templates.py:11-30`（_TEMPLATE_IDS 白名单 + TEMPLATES 构建）· `app/ops/prompts/render.py:25-54`（get_template/render）· `app/ops/tenant_context.py`（contextvar 先例）· `app/ops/lg_rag/run_worker.py:116-166`（_main token 模式 · 注入同位）
- 图谱/契约锚：`.importlinter` lg-rag-outbound（prompts 属 lg_rag 同族 · 零新边）· `docs/_tech_graph/l1/01_modules.md:35`（lg_rag 行 · prompts 归此 C2 裁定）
- 测试先例：`tests/test_prompt_assets.py:146-151`（tmp_assets fixture · monkeypatch _ASSETS_DIR + clear_asset_cache）· `tests/test_prompt_render.py`
- 体例先例：`docs/tasks/done/task_p2c_t1_planner_tool_awareness.md` · registry `docs/harness/audit_gates/registry.yaml`

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs 19 契约 §3 vs 18 §10 P4-T2 行 vs 代码锚）done | false |
| R1 | 失败路径推演（路径穿越 · 坏件静默 · 漏设错域 · 词表互拼 · import 漂移 · 并行冲突 · 环境性红）done | false |
| R2 | 非范围边界（T3 manifest 消费 · T4 RAG · T5 oa 资产 · R11 skill/goal · R4 memory 列 · 不挂 tenant）done | false |
| R3 | 关键决策记录（目录回退语义 · current_domain env 回落裁定 · 白名单薄封装形态 · worker 注入位）done | false |
| R4 | 体例对账（p2c-t1 模板 · registry/invokes/审查文/图谱登记 · 仓规条款一）done | false |
| R5 | 收尾复核（验收 11 条全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书四条与 19 契约 §3 + 18 §10 P4-T2 行逐条对齐：loader 目录回退+缓存键扩展（§3.1）· templates get_template_for_domain 薄封装白名单不动（§3.2）· domain_context.py contextvar 默认 ops + OPS_DOMAIN env 解析非法回退 ops+warning + start_run_worker 注入位（§3.3）· 不建 assets/ops/（§3.4）。勘察已定位全部锚点（loader.py:20/:51-80 · templates.py:11-30 · render.py:25-54 · run_worker.py:116-166 · tenant_context.py 先例 · test_prompt_assets.py:146-151 隔离形态）。importlinter 核对：prompts 属 lg-rag-outbound 同族（source_modules 含 app.ops.prompts），run_worker.py import domain_context 零新边；domain_context.py 仅 stdlib。

### R1 · 失败路径推演

见「失败路径」节。推演增补：OPS_DOMAIN env 值经 resolve_domain 解析后只可能为词表内值或 ops（路径字符永远进不了 loader 目录拼接）——env 面与 loader 入参面双重词表闸，纵深防御；@cache 的 load_asset 键扩为 (template_id, domain) 后 ops 面旧键 (id, None) 与新键 (id, "ops") 并存，两者读同一路径零语义差（双份内存可忽略）；clear_asset_cache() 保持全清语义，测试隔离形态不变。

### R2 · 非范围边界

T3 消费 manifest domain 键（prompt 选择面与本波「部署级单域」正交 · 19 §4 真源）；T4 RAG 检索域隔离；T5 oa 域资产 7+4 份落地（含 4 份刻意不覆盖裁定——本波机制须支持「不覆盖=回退」天然成立）；R11 skill 目录/goal 注入为部署级资产不进域回退；R4 memory 不加 domain 列（部署级单域无需存储面）；不挂 tenant（部署级进程单值 · 承 QDRANT_COLLECTION 先例 · 18 :94-97）。

### R3 · 关键决策记录

- **目录回退语义（19 §3.1 钉死）**：命中判定=文件存在；存在即全量校验（坏件显式炸）· 不存在即回退。否「半份合并」（域件缺 front-matter 字段时拿根件字段补）——合并语义使资产错误静默化且版本归属混乱，契约明确拒绝。
- **current_domain() 未注入回落 env 解析（R-P4-2 强化裁定 · 偏差候选登记）**：19 §3.3 字面为「默认 ops」；本波裁定未注入时回落 resolve_domain_from_env()（缓存按原始值 keyed）——OPS_DOMAIN 缺省/非法时行为与契约字面完全一致（归 ops），OPS_DOMAIN=oa 时非 run 通路（session/summary.py 等 HTTP 面）亦读到正确部署域而非静默 ops。契约「注入位 run 启动处」仍原样实现（worker 显式注入+finally reset 保 run 内确定性）。理由：OPS_DOMAIN 是部署级单值（承 QDRANT_COLLECTION），「漏设无害化」由「读到部署域同值」结构性成立，比「读到 ops 同值」更贴近设计意图；ops 部署零行为差（验收对拍不受影响）。
- **白名单薄封装形态**：get_template_for_domain 置于 templates.py（与 _TEMPLATE_IDS 同文件 · 白名单唯一真源）；render.get_template 为唯一域路由点（ops 走 TEMPLATES 同对象 · 非 ops 委托薄封装），六处调用点零 churn。
- **set_current_domain 词表校验 ValueError**：编程错误面显式炸（仅 env 解析面 fail-closed）——worker 注入值恒为 resolve 产物（合法），测试注入非法值应即炸而非静默。
- **TEMPLATES import 期零 diff**：构建调用保持 load_asset(template_id) 不传 domain（缓存键 (id, None) · 根目录路径）——既有 EXPECTED_IDS 集合等式与版本钉版断言天然全绿。
- **docstring 修正**：templates.py:3「10 模板」→ 11（18 文点名陈旧 · 顺手修正零行为面）。

### R4 · 体例对账

照 task_p2c_t1_planner_tool_awareness：task 档结构/人工闸表/registry entry（base=cfe76b23 · allowed_app_files 五件 · allowed_tree_files 含图谱/registry/task/review · allowed_tree_prefixes invokes 目录 · banned_prefixes=[alembic/, scripts/]）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave@3.5.0 task lint PASS 为闸；图谱签收承 01_modules.md P2c-T1 先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 11 条逐条锚：域命中/回退/坏件/词表拒入/解析回退/零 diff 对拍/白名单/域路由/worker 注入（全新断言）+ 目标回归+全量+ruff + 图谱两件 + 过闸四件。回退 = revert 五件 app 文件 + 新测试文件删除（零存量测试迁移面）。

## 实现备忘

### 偏差登记

（30 交付时回填）

### 限制登记

1. oa 域资产落地归 P4-T5（委派书钉明 · 本波仅机制面 · 验收以测试 tmp 域件模拟）。
2. manifest domain 键消费归 P4-T3；RAG 域隔离归 P4-T4（19 契约 §4/§5 真源）。
3. 全量 pytest 环境性红与 base 同路径一致（若有）非本波引入；CI 终裁。

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；新增 tests/test_prompt_domain_assets.py 全绿；目标回归 tests/test_prompt_assets.py / tests/test_prompt_render.py / tests/test_prompt_packs.py / run_worker 相关全绿；全量回归环境性红与 base cfe76b23 同路径基线逐签对照；ruff check app tests 绿；allowed_app_files 五件机判。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-18 | 落卡（夜间自动执行波 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03796 · 来源 18 设计文 §10 P4-T2 行 + 19 契约 §3） |
