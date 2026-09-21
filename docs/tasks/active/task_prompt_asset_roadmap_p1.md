# Task：Prompt 资产化阶段一「改得动」（去 str.format 转义 + 9 模板落盘 assets + 审计形态 · prompt-asset-roadmap-p1）

> **状态**：`signed`（2026-09-22 · R1 PASS 零阻塞 · HG-TASK-DRAFT/HG-AUDIT-R1=approved（维护者授权 00 代录）· 可 30）  
> **类型**：refactor（**行为零变化 · 无 alembic 义务**；图谱零变更按实判，偏离回炉条款见闸表与 D4）  
> **上游 SPEC**：`docs/spec/prompt-asset-roadmap/SPEC-prompt-asset-roadmap_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · commit 94b2e21）  
> **分支**：`task/prompt-asset-roadmap`（**禁止 master/main 直改 · 禁止 push**）  
> **10 注**：2026-09-22 · 维护者授权 00 本窗签收全部过程文档（原话「此spec完成后继续把完成后续spec，一个个进行，每次PR到main通过CI后自动merge」承前令「授权00签收所有过程文档」，留痕于 SPEC 状态行）· HG-TASK-DRAFT / HG-AUDIT-R1 由 00 在该授权下于 20 审后代录，**本帽不签**

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `prompt-asset-roadmap-p1` |
| **git_branch** | `task/prompt-asset-roadmap` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 行为零变化以**全量 pytest 绿 + 迁移前后 9 模板渲染输出逐字节 diff 为空**为证（一次性对拍命令输出入 40 验收记录，**不留全文快照**——快照会让非开发改文案挂 CI，违背 SPEC 目标）；新增守护：assets 加载器（缺文件/缺 front-matter 字段/空 body 显式炸）· 渲染缺键 KeyError 包装点名 template_id · assets body 零 `{{` 转义残留 grep 断言 · 锚点断言（渲染输出含裸 `{"domain"` / `{"route"` 等 JSON 示例结构锚点 · 非全文快照）；变异检验三条（缺键 / 缺文件 / 转义残留 · 见验收「变异检验」） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | 无（**零图谱变更按实判** · SPEC §2 D4 裁定：不新增路由/表/事件类型；`assets/` 是 `app/ops/prompts/**` 模块内数据目录，`01_modules.md` lg_rag 行 C2 备注「prompt 装配层 `app/ops/prompts/**` 归属本行」路径覆盖不变；**本帽真读复核留痕一处 SPEC 措辞偏差与一处既有登记缺口**，均备注级处理 · 见闸表 HG-GRAPH-MODULES 行与 R0） |
| **graph_delta** | 无 |
| **graph_delta_note** | **回炉补闸条款**：若 30 阶段实现形态偏离零变更预判（新增一级模块 · 把 prompts 拆为独立 module_id · 新增任何路由/表/事件类型），**不得沿用本裁定**——退回 10-spec 修订 SPEC + 10-task 补 HG-GRAPH-MODULES 新行义务 + `docs/_tech_graph/` 如实登记后方可续 30；30 交付时 `01_modules.md` memory 行备注补「extract 改调 prompts 加载器」属备注级顺手更新（对齐 llm-layer-hardening 「依赖出边 +db」先例 · 00 代录人签行），非 SPEC 回炉 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `prompt-asset-roadmap` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | **总轨三阶段：本 task = 阶段一「改得动」**（参照 capability-gateway-p0~p3 总轨四子 task 先例 · 阶段二「看得见」/阶段三「分得开」各自后续 task · SPEC §2 全景即依据 · 顺序不可跳）；本 task：10 落稿 → 20-task-audit → 维护者授权 00 代录闸 → 30（D1 渲染语法 → D2 落盘迁移 → D3 审计文字一次提交 · 文案零改动）→ 40（逐字节对拍 + 变异检验三条）→ CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1` / `lc-evidence-http-v1`） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-22 · 00 验收 10-task 稿通过（维护者本窗授权 00 签收过程文档 · 原话留痕 SPEC 状态行） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-22 · 20-task-audit R1 PASS 零阻塞零返工（`docs/harness/reviews/task_prompt_asset_roadmap_p1_audit_R1_20260922.md` · 计数断言亲跑全吻合）· 维护者本窗授权 00 代录签收 |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-22 本帽**真读** `docs/_tech_graph/l1/01_modules.md`：模块表已建置；lg_rag 行 C2 备注（2026-09-01）已裁定「prompt 装配层 `app/ops/prompts/**` 归属本行（模板 id 全部 `lg_rag.*` 且被 supervisor/intent 消费）」；memory 行在表（出边 `db, rag, llm`）。SPEC §2 D4 判本 task **零图谱变更**（不新增路由/表/事件类型 · `assets/` 为 prompts 模块内数据目录 · 无新增一级模块）→ **无新签义务**。**如实留痕两点**：① SPEC「memory→prompts 依赖边已存在」与实扫不符——`app/ops/memory/` 对 `prompts` **零 import**（2026-09-22 本帽 grep），30 改调 `render()` 将新增 memory→prompts 物理 import；因 prompts 非独立 module_id（C2 裁定归属 lg_rag 行内部路径），该边在模块表语义下为 memory 行出边备注级补充（对齐 llm-layer-hardening 「依赖出边 +db」00 代录先例），**不构成 SPEC 回炉**；② 既有登记缺口（非本波义务 · 不回改）：lg_rag 行出边未列 memory（`router.py:50` / `sse_stream.py:49` / `continuity.py:218` 已 import `app.ops.memory`）· memory 行出边未列 structured_output（`extract.py:30` 已 import）。**若 30 形态进一步偏离（新增一级模块 / prompts 拆独立 module_id / 新增路由/表/事件类型）→ 回炉补闸**（见 graph_delta_note，不得沿用本裁定） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点 |

---

## 背景与目标

现状（SPEC §1 实扫锁死 · 2026-09-22 本帽复核一致）：registry 仅覆盖 **3 模板**（`templates.py` · supervisor 两模板 body 内含 `{{"domain"...}}` 双花括号 JSON 示例 · str.format 转义税实证），消费点仅 2 处；产品面 prompt 文案 **≥10 处散在 6 个文件**，其中 **6 处是 registry 外 `.py` 内联常量**（lg_rag/nodes.py ×3 · multi/nodes.py ×2 · memory/extract.py ×1）——改一句文案 = 改代码文件 + 走开发全流程（手册 §2.1.1 真痛点）。全仓 `.format(` 仅 3 处（render.py:45 · answer.py:107 · fallback.py:326），真散布面在内联常量而非 format 调用。

一句话目标（SPEC 锁死）：阶段一「改得动」——`render()` 从 `str.format` 改 `string.Template.substitute`（去转义）+ 9 模板（registry 3 + lg_rag 5 + memory 1）从代码搬 `app/ops/prompts/assets/*.md`（front-matter 载 `template_id`/`version`）+ 变更审计形态落地，使**非开发同学改一句文案只动 `assets/*.md` 一个文件、PR diff 即审计、CI 锚点断言兜底**，以全量 pytest 绿 + 迁移前后渲染输出逐字节 diff 为空 + 变异检验三条为证。

设计纪律（30 不得违反 · 承 SPEC §1 签收锁死四条）：

1. **行为零变化**：不改任何 prompt 文案内容与变量集合；迁移前后每个模板渲染输出逐字节一致（一次性 diff 命令验证 · 9 模板全量对拍含变量代入后成品串）。
2. **缺键/缺文件显式炸，不静默降级**：沿用 render.py:46-47 与 packs.py:119-127 先例；assets 文件缺失/front-matter 缺字段/空 body → 明确异常点名路径与 template_id，**禁止 fallback 空串**。
3. **特例不强行收敛**：grader.py（env 切版实验面 · GRADER_SYSTEM_V1/V2 内联常量）· answer.py（已外置 yaml + 其 `.format(`）· packs.py（harness 纪律 SoT · FRAGMENT 机制）· chat/nodes.py（legacy 已 410）**本波原样保留**；capability/fallback.py 降级话术（进工具输出 · 非 LLM prompt）不动；统一收敛是后续波次单独裁定，不在本波「顺手」。
4. **锚点断言替代全文快照**：测试断言「渲染输出含裸 `{"domain"` 且无 `{{` 残留」级结构锚点，使「改一句文案」diff 不挂 CI，「改变量名/留转义」必挂 CI。

---

## 现状锚点（只读 · 30 必读 · 10 已扫 · 承 SPEC §1 并复核）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 唯一渲染口（改造对象） | `app/ops/prompts/render.py:35-53` | `render()`：`:45` `tmpl.body.format(**vars_map)`；`:46-47` 缺键 KeyError 包装点名 template_id（**好先例保留**）；`:48-52` slots 块拼接注入（`<!-- slot:name -->` · 保持不动）；`get_template()` `:24-32` 返回 `PromptTemplate.version`（零改动 · 阶段二底座） |
| registry（迁移源 3 模板） | `app/ops/prompts/templates.py` | `TEMPLATES` 3 键：`lg_rag.intent.system` v1（无变量 · `:11-13` `{{"domain"...}}` 转义）· `lg_rag.supervisor.system` v2（变量 `{catalog_block}` `:33` · `:28`/`:40` 转义）· `lg_rag.supervisor.suffix.system` v1（变量 `{prefix_block}` `:54` / `{catalog_block}` `:62` / `{suffix_cap}` `:63` · `:56` 转义）；全文 **0 个 `$`**（本帽实扫） |
| 内联常量 ×3（迁移源） | `app/ops/lg_rag/nodes.py:46-54,56-60,222-229` | `_ROUTER_SYSTEM`（无变量 · 裸 `{"route"...}` JSON 示例）· `_DIRECT_SYSTEM`（无变量）· `_REWRITE_SYSTEM`（无变量）；消费点 `:100` / `:290` / `:245` `LlmMessage(role="system", ...)`；常量区 **0 个 `$`** |
| 内联常量 ×2（迁移源） | `app/ops/lg_rag/multi/nodes.py:84-91,93-106` | `_EXTRACT_SYSTEM`（无变量 · 裸 `{"dates"...}`）· `_AGGREGATOR_SYSTEM`（无变量）；消费点 `:1041` / `:1512`；常量区 **0 个 `$`** |
| 内联常量 ×1（迁移源） | `app/ops/memory/extract.py:47-55` | `EXTRACTION_SYSTEM_PROMPT`（无变量 · docstring 注「不做 str.format」· 裸 `{"facts"...}`）；消费点 `:116` `system=EXTRACTION_SYSTEM_PROMPT`；常量区 **0 个 `$`** |
| render 调用方（零 diff 钉死） | `app/ops/strategy/intent.py:57` · `app/ops/lg_rag/multi/nodes.py:120-123,130-137` | `render(INTENT_SYSTEM_TEMPLATE)`（`:19` 常量 = `lg_rag.intent.system`）· `_build_supervisor_system` / `_build_supervisor_suffix_system`；**render 签名不变故调用方零改动**（SPEC §2 D1） |
| 特例四例（本波不动） | `app/ops/rag/grader.py:104-137` · `app/ops/lc_evidence_chain/answer.py:20,107` · `app/ops/prompts/packs.py:42-70,119-127,133` · `app/ops/chat/nodes.py:28-34` | grader env `RAG_GRADER_PROMPT` 切 v1/v2 + `:218-222` 日志记版本（阶段二雏形）；answer 外置 yaml + `RAG_LC_ANSWER_PROMPT` env + `.format(`；packs comms 机制文案 + FRAGMENT 运行时读 md 显式炸先例；chat legacy（stream 已 410 · `01_modules.md:22` 裁定沿用） |
| `.format(` 全仓面 | `grep -rn --include='*.py' '\.format(' app/` | **3 处**：render.py:45 · answer.py:107 · fallback.py:326（本帽 2026-09-22 真跑 · 与 SPEC 一致）；迁移后应为 **2 处**（answer/fallback 特例保留） |
| `你是` 全仓面 | `grep -rn --include='*.py' '你是' app/` | **13 处**：templates.py ×3 · lg_rag/nodes.py ×3（:47,:57,:223）· multi/nodes.py ×2（:85,:94）· memory/extract.py:47 · grader.py ×2（:104,:115）· chat/nodes.py:30 · packs.py:133；迁移后应剩 **4 处特例命中**（grader ×2 · chat ×1 · packs ×1 · answer 经 yaml 零 .py 命中） |
| prompts 包内容 | `ls app/ops/prompts/` | `__init__.py` / `packs.py` / `render.py` / `templates.py`（**无 assets/ 目录** · 本波新增） |
| 图谱登记 | `docs/_tech_graph/l1/01_modules.md` lg_rag 行 C2 备注 | 「prompt 装配层 `app/ops/prompts/**` 归属本行」（2026-09-01 HG-GRAPH-MODULES approved）；`assets/` 落盘后路径覆盖不变 |
| 测试基线 | `python -m pytest tests --collect-only -q` | **1176 collected**（2026-09-22 本帽真跑 · 与 continuity-dedup 40 核验后基线一致）；本波新增守护测试（加载器/缺键/锚点/变异）→ collected 增加数入 40 验收记录，**无既有用例删除** |

---

## 钉死契约（自 SPEC §1/§2 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **渲染语法** | `render()` 从 `str.format` 改 `string.Template.substitute`（方案 S1 · SPEC §4）；变量 `{catalog_block}` → `$catalog_block`；JSON 示例 `{{...}}` → 裸 `{...}`；缺键 `substitute` 抛 KeyError → render() 包装点名 template_id 沿用 render.py:46-47 模式；`render()` 签名与 slots 语义（`<!-- slot:name -->` 拼接）**一字不动** |
| **变量集合** | 一字不改：supervisor.system=`catalog_block` · supervisor.suffix.system=`catalog_block, prefix_block, suffix_cap` · 其余 7 模板**无变量** |
| **迁移清单** | **9 模板**：registry 3（`lg_rag.intent.system` v1 / `lg_rag.supervisor.system` v2 / `lg_rag.supervisor.suffix.system` v1）+ lg_rag 5（`lg_rag.router.system` / `lg_rag.direct.system` / `lg_rag.rewrite.system` / `lg_rag.extract.system` / `lg_rag.aggregator.system` · 各 v1 进 registry）+ memory 1（`memory.extract.system` v1）——**版本号承 registry 原值，新增 6 枚从 v1 起；文案逐字节搬运，连标点都不改** |
| **落盘形态** | `app/ops/prompts/assets/<template_id>.md` 每模板一文件；front-matter 载 `template_id` / `version`（`v<N>` 格式），正文即 body；**不复用** `docs/harness/prompts/`（harness 纪律 SoT · packs.py:24） |
| **加载器** | 运行时读文件；缺失/front-matter 缺字段/空 body/version 非 `v<N>` → 明确异常点名路径与 template_id（packs.py:119-127 模式 · 设计纪律 2）；front-matter 解析手写 ≤30 行或复用既有依赖，**禁引 requirements 之外新重依赖**（SPEC §7 residual ②）；加载结果可缓存（lru_cache 级 · answer.py 先例），缓存不影响「缺文件即炸」语义（测试可清缓存） |
| **代码侧删除面** | `templates.py` 内联 body 清零（`TEMPLATES` 改由加载器喂或整体重构为加载器查表 · 30 定形态但须满足：`get_template()` / `render()` 对外签名与 `TEMPLATES` 键集合语义不变——`test_prompt_packs.py:180` 子集断言与 `set(TEMPLATES)` 消费存续）；6 处内联常量全删：lg_rag/nodes.py `_ROUTER_SYSTEM`/`_DIRECT_SYSTEM`/`_REWRITE_SYSTEM` · multi/nodes.py `_EXTRACT_SYSTEM`/`_AGGREGATOR_SYSTEM` · memory/extract.py `EXTRACTION_SYSTEM_PROMPT`，各消费点改调 `render()`/`get_template()` |
| **调用方零 diff** | `app/ops/strategy/intent.py:57` · `app/ops/lg_rag/multi/nodes.py:120-137` **零改动**（render 签名不变的直接推论；`git diff` 白名单核验） |
| **审计形态** | assets README（或 prompts 模块 docstring）写明非开发操作路径（改 body → bump front-matter `version` → PR → CI 锚点断言 → 合入上线）与 version bump 约定；body 变更须同 PR bump version |
| **图谱** | 零变更按实判（闸表 HG-GRAPH-MODULES 行留痕两点如实记录）；`./scripts/graph-compile.sh` 绿为回归保险；不回改 done/归档历史文档 |
| **安全** | 纯重构：无新凭证面/网络面/DB 面（无 alembic 义务）；prompt 内容零变化故无注入面变化；assets 文件读取限定包内目录，template_id 白名单来自 registry 键，**不接受外部路径入参**（无路径穿越面） |

---

## 范围（同 task 竖切）

- [ ] **D1 · 渲染去转义（必做）**：`render()` 改 `string.Template.substitute`；缺键 KeyError 包装点名 template_id 沿用；slots 语义不动；`app/ops/prompts/` 下 `.format(` 零残留
- [ ] **D2 · prompt 资产落盘（必做）**：新建 `app/ops/prompts/assets/` + 9 个 md（front-matter `template_id`/`version` 齐全 · 正文非空）；加载器实现（显式炸模式）；registry 覆盖 9 模板；6 处内联常量删除并改调 render/get_template；templates.py 内联 body 清零
- [ ] **D3 · 变更审计形态（必做）**：assets README 或模块 docstring 写明非开发操作路径 + version bump 约定；加载器校验 front-matter 缺字段/空 body/version 格式（单测钉死）
- [ ] **D4 · 图谱与文档（必做 · 按实判零图谱变更）**：`./scripts/graph-compile.sh` 绿；memory 行备注顺手更新（00 代录人签行 · 非义务但建议 · 见 graph_delta_note）；不回改 done/归档历史文档

**竖切结论**：D1–D4 同 task 一次提交（D1 改渲染语法与 D2 模板变量改写 `$` 前缀强耦合——只改 render 不改模板即 KeyError 全炸的中间态；D3 文字落点依赖 D2 的 assets/ 存在）；无「先行提交」切分空间（对照 memory-embedding-backfill 的 D3 先行模式不适用于渲染语法切换）。

### 非范围

- ❌ 阶段二「看得见」/ 阶段三「分得开」任何实现（观测埋点 · 指标聚合 · 打标分流 · 灰度回退——各自后续 task）
- ❌ 改 prompt 文案内容本身（文案优化另案 · 迁移逐字节一致）
- ❌ 注入防护（security-hardening 占位 SPEC 的事）· A/B 统计平台
- ❌ grader.py env 切版机制与 GRADER_SYSTEM_V1/V2 内联常量（实验面特例 · 设计纪律 3）
- ❌ lc_evidence_chain `answer_system_prompt.yaml` 与其 `.format(`（已外置特例 · 去转义顺手它 = 范围蔓延）
- ❌ packs.py 内联 checklist/policy/prohibitions 与 FRAGMENT 机制（harness 纪律 SoT）
- ❌ `app/ops/chat/**` 含 `_SYSTEM_PROMPT`（已 410 · chat 轨清退另一波 · `01_modules.md:22` 裁定沿用）
- ❌ capability/fallback.py 降级话术（进工具输出 · 非 LLM prompt）
- ❌ lg_rag 行出边补 memory / memory 行出边补 structured_output 的**既有登记缺口回填**（留痕非义务 · 可随图谱维护波次处理）
- ❌ 表结构变更（无 alembic 义务 · 本 task 不触 DB）
- ❌ 历史文档回改；web / ios

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| 渲染键缺失（调用方少传变量 / 模板新增变量调用方未跟上） | `substitute` KeyError → render() 包装点名 template_id 与缺键（沿用 render.py:46-47 模式）；**变异检验 ① 钉死** | Y（补变量） | 是（CI 红） |
| 转义残留（迁移后 body 仍留 `{{ }}`） | Template 语法下 `{{ }}` 原样输出进 prompt → **静默错**（模型看到双花括号）；验收含 assets/*.md grep `{{` 零命中断言 + 锚点断言裸 `{"domain"` 存在——双保险；**变异检验 ③ 钉死** | Y（改 assets） | 否 |
| 双写漂移（assets 已落盘但 .py 旧常量残留未删） | 代码侧常量与 assets 文件两份真值 → 静默错；验收含 grep 断言：`app/**/*.py` 搜 `你是` 仅剩 grader/chat/packs 特例清单 4 处命中；删常量是 D2 必做项非「顺手」 | Y（删残留） | 否 |
| assets 文件缺失 / front-matter 缺 version / body 空 / version 非 `v<N>` | 加载器明确异常点名路径与 template_id（packs.py:119-127 模式 · 设计纪律 2）；**变异检验 ②：临时改名一个 assets 文件 → 加载即炸不静默** | Y（恢复文件） | 是（CI 红） |
| 文案含 `$`（Template 元字符误伤） | 本帽实扫 9 模板常量区**零 `$`**；迁移验收含 grep 断言；未来文案引入 `$` → substitute 显式炸（非静默），CI 锚点断言兜 | Y（`$$` 转义） | 否 |
| 变量集合漂移（模板改 `$xxx` 调用方没传 / 反之） | 缺键向：KeyError 显式；多传向：substitute 忽略多余键（与 format 一致）——多传无害，缺键显式，无静默路径 | Y | 否 |
| 改文案忘 bump version（D3 约定破坏） | 阶段一不机械强制（无 git 历史感知）；由 PR 审查 + assets README 约定 + 阶段二「看得见」上线后归因错位倒逼；列为残余风险而非验收项 | — | 否 |
| lg_rag/memory 改调加载器后 import 顺序问题 | 加载器纯文件读取无服务依赖；全量 pytest + 启动冒烟（`import app.main`）兜底；模块常量删除若留引用残留 → ImportError/NameError 显式炸 | Y | 是（CI 红） |
| memory→prompts 新 import 边被误读为 SPEC 回炉 | 闸表已留痕：prompts 非独立 module_id（C2 裁定归属 lg_rag 行内部路径），该边为 memory 行出边备注级补充（llm-layer-hardening 先例 · 00 代录）；**若 30 把 prompts 拆为独立一级模块或新增路由/表/事件 → 回炉** | — | 否 |
| 误改文案（30 手滑改动 body 内容） | 验收含**迁移前后渲染输出逐字节 diff 为空**断言（一次性命令 · 9 模板全量对拍含变量代入成品串 · 输出入 40 验收记录） | Y（revert） | 否 |
| 加载器缓存导致测试期改 assets 不生效 | 加载器缓存须暴露清缓存口（`functools.lru_cache.cache_clear` 级）供测试/future reload；单测钉死「清缓存后重读」 | Y | 否 |
| 图谱编译断裂 | `graph-compile.sh` 绿为验收项；模块内重构不触发索引失配 | Y | 是（CI 红） |
| 30 开工前旧测影响面清单未落盘或逐条无处置 | 验收「工程 · 闸前置」项不满足 → **拒收**（B1） | 是 | 否 |
| 无变异检验三条却宣称迁移有效 | 40/verify **拒收**（不验收空真规则） | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：`HG-AUDIT-R1` approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved · 本 task 零图谱变更无新签义务；**若 30 偏离零变更预判（新增一级模块 / prompts 拆独立 module_id / 新增路由/表/事件类型）→ 回炉补闸**，见闸表与 graph_delta_note）

### D1 · 渲染去转义（映射 SPEC §6-D1）

- [ ] `render()` 使用 `string.Template.substitute`；`str.format` 在 `app/ops/prompts/` 下零残留（grep 断言）；全仓 `.format(` 命中从 3 处降为 **2 处**（answer.py:107 与 fallback.py:326 特例保留 · `grep -rn --include='*.py' '\.format(' app/` 计数断言）
- [ ] 缺键 KeyError 包装点名 template_id（单测钉死：`render("lg_rag.supervisor.system", {})` 少传 `catalog_block` → KeyError 且消息含 template_id）
- [ ] `assets/*.md` grep `{{` / `}}` 零命中；9 模板 grep `$` 零命中（`$` 变量前缀除外 · 本帽基线实扫 9 常量区已零 `$`）

### D2 · 资产落盘（映射 SPEC §6-D2）

- [ ] `app/ops/prompts/assets/` 9 个 md 文件，front-matter `template_id` + `version`（`v<N>` 格式）齐全，正文非空（`lg_rag.intent.system` v1 / `lg_rag.supervisor.system` v2 / `lg_rag.supervisor.suffix.system` v1 / `lg_rag.router.system` v1 / `lg_rag.direct.system` v1 / `lg_rag.rewrite.system` v1 / `lg_rag.extract.system` v1 / `lg_rag.aggregator.system` v1 / `memory.extract.system` v1）
- [ ] registry 覆盖 9 模板（原 3 + lg_rag 5 + memory 1 · `set(TEMPLATES)` 或等价加载器查表语义）；`templates.py` 内联 body 清零
- [ ] 代码侧旧常量全删：lg_rag/nodes.py `_ROUTER_SYSTEM`/`_DIRECT_SYSTEM`/`_REWRITE_SYSTEM` · multi/nodes.py `_EXTRACT_SYSTEM`/`_AGGREGATOR_SYSTEM` · memory/extract.py `EXTRACTION_SYSTEM_PROMPT`，6 处消费点（nodes.py:100/:245/:290 · multi/nodes.py:1041/:1512 · extract.py:116）改调 render/get_template
- [ ] grep 断言：`grep -rn --include='*.py' '你是' app/` 命中从 13 处降为 **4 处**且仅落特例清单（grader.py:104,115 · chat/nodes.py:30 · packs.py:133 · answer.py 经 yaml 零 .py 命中）
- [ ] `app/ops/strategy/intent.py:57` · `app/ops/lg_rag/multi/nodes.py:120-137` 调用方**零 diff**（`git diff master -- app/ops/strategy/intent.py` 为空 · multi/nodes.py diff 仅含常量删除与 import 调整，render 两调用行逐字不动）

### D3 · 审计形态（映射 SPEC §6-D3）

- [ ] assets README（或 prompts 模块 docstring）写明非开发操作路径（改 body → bump version → PR → CI 锚点断言 → 合入上线）与 version bump 约定
- [ ] 加载器校验 front-matter 缺字段/空 body/version 非 `v<N>` 明确报错点名路径与 template_id（单测钉死）；缓存可清（测试钉死清缓存后重读生效）

### 行为零变化（映射 SPEC §6-行为零变化）

- [ ] 全量 `pytest tests` 绿（基线 1176 collected · 2026-09-22 本帽真跑；**无既有用例删除**，新增守护用例数如实入 40 记录）；`ruff check app tests` 绿（零新增告警口径 · 明细 diff 为空）
- [ ] **逐字节对拍**：迁移前后 9 模板渲染输出 diff 为空（含变量代入后成品串：supervisor.system 带 `catalog_block` · suffix 带三变量 · 其余 7 模板无变量直渲；一次性命令输出入 40 验收记录，不留全文快照）
- [ ] 生产路径 diff 白名单：`git diff master -- app/` 只含 `app/ops/prompts/` 模块内改动 + 上述 6 个常量删除点（含各文件 import 行调整）+ `assets/` 新增 + 测试

### 变异检验（不验收空真规则 · 映射 SPEC §6-变异检验）

- [ ] ① **缺键显式**：临时从 supervisor.system 调用去掉 `catalog_block` 传参 → 指定单测 KeyError 挂；恢复后全绿
- [ ] ② **缺文件显式**：临时改名一个 assets/*.md → 加载/首渲染明确异常挂（非静默空串）；恢复后全绿
- [ ] ③ **转义残留可检**：临时在某 assets body 写入 `{{"route"` → grep 断言/锚点断言必须挂；恢复后全绿

### 工程（映射 SPEC §6-工程）

- [ ] **闸前置**：30 开工前旧测影响面清单已落盘且逐条有处置（回归/改编理由）——清单见下「旧测影响面清单（B1）」，30 逐条执行处置并在提交说明逐条回填
- [ ] `./scripts/graph-compile.sh` 绿；图谱零变更裁定与实现形态一致（若 30 新增一级模块/把 prompts 拆独立 module_id/新增路由/表/事件类型 → 回炉补闸 + SPEC 回炉）
- [ ] 新增守护测试就位且全绿：assets 加载器（缺文件/缺字段/空 body/version 格式）· 缺键 KeyError · 锚点断言（渲染输出含裸 `{"domain"` / `{"route"` / `{"facts"` 结构锚点且无 `{{` 残留 · **非全文快照**）

### 旧测影响面清单（B1 · 2026-09-22 10-task 实扫落盘）

> 扫描口径（真跑）：`grep -rn -E 'get_template|render\(|TEMPLATES' app/ tests/ --include='*.py'`（prompts 包外消费面）· `grep -rn --include='*.py' '\.format(' app/`（=3）· `grep -rn --include='*.py' '你是' app/`（=13）· `grep -rn -E '_ROUTER_SYSTEM|_DIRECT_SYSTEM|_REWRITE_SYSTEM|_EXTRACT_SYSTEM|_AGGREGATOR_SYSTEM|EXTRACTION_SYSTEM_PROMPT' tests/ app/ --include='*.py'`（消费点全在 app/ · **tests 零直引**）· `python -m pytest tests --collect-only -q`（=**1176**）。本波行为变更源裁定：**render() 渲染语法切换 + 9 模板搬 assets + 6 常量删除**，对外签名与渲染输出逐字节不变；故影响面以**回归**（既有 prompt 测试零改动）与**改编**（6 常量消费点 + templates/render 本体）为主，**无测试删除**。处置三态：**回归**（不受影响，全波次重跑确认）/ **改编**（随本波更新）/ **删除**（本清单无）。

| # | 锚点 | 旧测/调用点现状 | 本波影响 | 处置 |
|---|------|----------------|----------|------|
| 1 | `tests/test_prompt_assembly.py` 全文件 5 用例（`:7-8` import · `:11-16` version/body 断言 · `:19-23` intent body 断言 · `:26-32` render 带变量 · `:35-42` slots · `:45-47` 未知模板） | registry 渲染口唯一直测 | 渲染输出逐字节不变 + `get_template`/`render` 签名不变 → 零改动全绿；`:14` version=="v2" 与 `:21` version=="v1" 由 front-matter 承值 | 回归（零改动 · 全波次重跑确认） |
| 2 | `tests/test_prompt_packs.py:19,176-180` `TEMPLATES` 子集断言 | `{"lg_rag.intent.system", "lg_rag.supervisor.system"} <= set(TEMPLATES)` | 9 模板是**加法** → 子集断言仍真；`set(TEMPLATES)` 消费语义存续（钉死契约「代码侧删除面」） | 回归（零改动） |
| 3 | `tests/test_prompt_packs.py:183-193` render 断言 | supervisor.system v2 + render 带 `catalog_block` + slots | 同 #1 · 渲染逐字节不变 | 回归（零改动） |
| 4 | `tests/test_prompt_packs.py:196-211` 依赖方向禁令（AST 扫 packs 不 import chat/session） | packs.py 禁令闸 | 本 task 不动 packs.py（特例）→ 闸语义不受触 | 回归（零改动） |
| 5 | `tests/test_skill_registry.py:22-33` slot 集成 | render + `slots={"skill": ...}` | slots 语义钉死不动 → 零改动 | 回归（零改动） |
| 6 | `tests/test_rag_grader_prompt.py` 全文件 | grader env 切版 + V1/V2 常量断言 | grader 特例本波不动 → 零改动 | 回归（零改动 · 设计纪律 3） |
| 7 | `tests/test_chat_nodes.py`（chat legacy prompt 消费面） | chat `_SYSTEM_PROMPT` 相关 | chat 非范围 · 零改动 | 回归（零改动 · 非范围） |
| 8 | `app/ops/strategy/intent.py:19,57` | `INTENT_SYSTEM_TEMPLATE` 常量 + `render()` 调用 | render 签名不变 → **零 diff 钉死**（验收 D2 白名单核验） | 回归（零 diff） |
| 9 | `app/ops/lg_rag/multi/nodes.py:120-123,130-137` | `_build_supervisor_system` / `_build_supervisor_suffix_system` render 两调用 | render 调用行**逐字不动**；文件 diff 仅含 `_EXTRACT_SYSTEM`/`_AGGREGATOR_SYSTEM` 常量删除与 import 调整 | 回归（调用行零 diff）+ 改编（常量删除 · 见 #12/#13） |
| 10 | `app/ops/lg_rag/nodes.py:46,100` `_ROUTER_SYSTEM` | 内联常量 + `LlmMessage(role="system", ...)` 消费 | 常量删除 → 改调 `render("lg_rag.router.system")`；渲染输出逐字节不变（无变量模板） | 改编（删常量改调 render · SPEC §2 D2） |
| 11 | `app/ops/lg_rag/nodes.py:56,290` `_DIRECT_SYSTEM` | 同上 | 同上（`lg_rag.direct.system`） | 改编（同 #10） |
| 12 | `app/ops/lg_rag/nodes.py:222,245` `_REWRITE_SYSTEM` | 同上 | 同上（`lg_rag.rewrite.system`） | 改编（同 #10） |
| 13 | `app/ops/lg_rag/multi/nodes.py:84,1041` `_EXTRACT_SYSTEM` | 内联常量 + `LlmMessage` 消费 | 同上（`lg_rag.extract.system`） | 改编（同 #10） |
| 14 | `app/ops/lg_rag/multi/nodes.py:93,1512` `_AGGREGATOR_SYSTEM` | 同上 | 同上（`lg_rag.aggregator.system`） | 改编（同 #10） |
| 15 | `app/ops/memory/extract.py:47,116` `EXTRACTION_SYSTEM_PROMPT` | 内联常量 + `system=` 消费 | 同上（`memory.extract.system`）· **新增 memory→prompts 物理 import**（闸表留痕 · 备注级图谱补充非回炉） | 改编（删常量改调 render/get_template） |
| 16 | `app/ops/prompts/templates.py` 3 模板内联 body | registry 真值 | body 搬 assets/*.md（逐字节 · 版本承原值）；`TEMPLATES` 键集合语义存续 | 改编（内联 body 清零 · SPEC §2 D2） |
| 17 | `app/ops/prompts/render.py:45` `.format(` | 唯一渲染口 | 改 `string.Template.substitute`；`:46-47` KeyError 包装模式沿用；slots `:48-52` 不动 | 改编（SPEC §2 D1） |
| 18 | 辅扫：`.format(` 全仓 3 处 | render.py:45 · answer.py:107 · fallback.py:326 | render.py 改编；answer/fallback 特例保留 → 3→2 | 改编 ×1 + 回归 ×2（特例 · 验收 D1 计数断言） |
| 19 | 辅扫：`你是` 全仓 13 处 | 9 处随迁移消失（templates ×3 · lg_rag ×3 · multi ×2 · memory ×1）+ 4 处特例留存 | 特例四例本波不动 → 13→4 | 改编 ×9 + 回归 ×4（特例 · 验收 D2 计数断言） |
| 20 | 辅扫：tests 全仓 grep 6 常量名 | **零命中**（无任何测试直引内联常量） | 删常量不挂任何直引测试；守护由回归测试 + 逐字节对拍 + 变异检验兜 | 回归（无处置） |
| 21 | 新增义务：加载器单测 / 缺键 KeyError / 锚点断言 / 变异三条 | 当前不存在 | 本波新增守护测试（工程验收项）；collected 自 1176 增加，新增数入 40 记录 | 新增（30 实现 · 40 核验） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/prompt-asset-roadmap/SPEC-prompt-asset-roadmap_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 94b2e21） |
| 上游设计 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 §2.1.1 痛点 · §2.4 三阶段） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 2026-09-22 真读核验 · lg_rag 行 C2 备注 / memory 行） |
| 改造对象 | `app/ops/prompts/render.py`（`:45` 渲染语法）· `app/ops/prompts/templates.py`（内联 body 清零） |
| 迁移源 | `app/ops/lg_rag/nodes.py:46,56,222` · `app/ops/lg_rag/multi/nodes.py:84,93` · `app/ops/memory/extract.py:47`（6 内联常量） |
| 零 diff 调用方 | `app/ops/strategy/intent.py:57` · `app/ops/lg_rag/multi/nodes.py:120-137` |
| 显式炸先例 | `app/ops/prompts/packs.py:119-127`（运行时读 md 缺失即炸）· `app/ops/prompts/render.py:46-47`（缺键 KeyError 包装） |
| 已资产化先例 | `app/ops/lc_evidence_chain/answer.py:20`（包内数据文件 `with_name` 同侧模式） |
| 测试锚点 | `tests/test_prompt_assembly.py` · `tests/test_prompt_packs.py:176-211` · `tests/test_skill_registry.py:22-33`（全回归 · 零改动守护） |
| 格式基准 | `docs/tasks/done/task_continuity_dedup.md`（signed → done 五棒全通 · PR #153） |
| 总轨先例 | `docs/tasks/done/task_capability_gateway_p0~p3.md`（一总轨 SPEC + 每阶段一 task） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/prompt-asset-roadmap/SPEC-prompt-asset-roadmap_v1.md`（§2 D1–D4 / §4 方案裁决 / §5 failure_paths / §6 验收）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/prompts/render.py`（`:35-53`）· `app/ops/prompts/templates.py` · `app/ops/lg_rag/nodes.py`（`:46-60,:222-229` 与消费 `:100,:245,:290`）· `app/ops/lg_rag/multi/nodes.py`（`:84-106` 与消费 `:1041,:1512` 与 render 调用 `:120-137`）· `app/ops/memory/extract.py`（`:47-55` 与消费 `:116`）· `app/ops/strategy/intent.py`（`:19,:57` 零 diff）
6. 先例：`app/ops/prompts/packs.py`（`:119-127` 显式炸）· `app/ops/lc_evidence_chain/answer.py`（`:20` 包内数据文件 · 特例本体不动）
7. 测试：`tests/test_prompt_assembly.py` · `tests/test_prompt_packs.py` · `tests/test_skill_registry.py`
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-22 · 94b2e21）；范围 D1–D4 承 SPEC §2 不重开辩论；本帽实扫复核：分支正确（`task/prompt-asset-roadmap`）· `.format(` 3 处 · `你是` 13 处 · 9 常量区零 `$` · pytest 基线 1176 collected；**SPEC 措辞偏差留痕两处**（「strategy/intent.py:57」实路径 `app/ops/strategy/intent.py` 不在 lg_rag/ 下 · 「memory→prompts 边已存在」实扫不成立）——范围语义零影响 · 如实写不改 SPEC | no | — | none |
| R1 | 开工闸：HG-TASK-DRAFT=pending（00 代录）· HG-AUDIT-R1=pending（blocks 30 · 本帽不签）· HG-GRAPH-MODULES=approved（真读 `01_modules.md` · lg_rag 行 C2 备注覆盖 prompts · 零图谱变更 + 回炉补闸条款 + 两点如实留痕）· HG-PILOT-OPSDESK-GLAYER=n/a | no | — | 无 |
| R2 | 竖切：D1–D4 同 task 一次提交（渲染语法与模板变量 `$` 改写强耦合 · 拆开即 KeyError 全炸中间态）；方案对比继承 SPEC §4 两组裁决（S1 string.Template · A1-a 包内 md），不重演 | no | — | 无 |
| R3 | failure_paths 15 条 = SPEC §5 十条翻四列 + 过程五（闸 / B1 闸前置 / 变异检验 / 加载器缓存测试语义 / memory→prompts 边误读防歧义）；核心纪律：逐字节对拍防手滑 · 变异检验三条钉死显式炸 · 双写漂移 grep 计数断言 | no | — | 无 |
| R4 | 验收 **20 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×3 / D2×5 / D3×2 / 行为零变化×3 / 变异检验×3 / 工程×3）；B1 实扫 21 行落盘（回归×11 · 改编×6 消费点+2 本体 · 辅扫×3 · 新增×1 · 删除×0）；grep 计数断言四条（`.format(` 3→2 · `你是` 13→4 · `{{` 零命中 · `$` 零命中） | no | — | 加载器缓存形态（lru_cache 级）与 front-matter 解析手写/复用为 30 设计自由（SPEC §7 residual ② · 禁新重依赖已钉） |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（B1 / 闸行留痕 / 基线数 / grep 口径细化均为过程化落地；两处 SPEC 措辞偏差如实留痕非范围偏差）；HG-AUDIT-R1 待人签（00 依授权代录） | no | — | ① version 忘 bump 无机械闸（承 SPEC residual ① · PR 审查 + README 约定 + 阶段二倒逼）；② 既有图谱登记缺口（lg_rag 出边缺 memory · memory 出边缺 structured_output）留痕待图谱维护波次 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

SPEC 已签收，本 task 只做可执行化拆解：registry 3/10 覆盖缺口 + str.format 转义税 + 6 处 registry 外内联常量 · 手册 §2.1.1 痛点与 §2.4 三阶段（本波 = 阶段一）。本帽实扫复核：分支 `task/prompt-asset-roadmap` 正确；`.format(` 全仓 3 处（render.py:45 · answer.py:107 · fallback.py:326 · 与 SPEC 一致）；`你是` 全仓 13 处（9 迁移源 + 4 特例）；9 个迁移源常量区 `$` 字符零命中（Template 元字符面清零 · SPEC「实扫零 `$`」复核成立）；`app/ops/prompts/` 现仅 4 文件无 assets/；pytest 基线 1176 collected（真跑）。**SPEC 措辞偏差留痕两处**：① SPEC「strategy/intent.py:57」实际路径为 `app/ops/strategy/intent.py:57`（**不在** `app/ops/lg_rag/` 下 · SPEC 省 `app/ops/` 前缀的写法易误读为 lg_rag 内）；该文件 `import app.ops.prompts` 为既成事实，本 task 对其零 diff，图谱零变更裁定不受影响。② SPEC「lg_rag/memory → prompts 依赖边已存在或同包内」——lg_rag 侧成立（multi/nodes.py:120-137 已 import render）· **memory 侧不成立**（`app/ops/memory/` 对 prompts 零 import · 本帽 grep 实证）；处理见闸表 HG-GRAPH-MODULES 行与 failure_paths 专行，备注级补充非 SPEC 回炉。两处均范围语义零影响，本 task 按实测如实写，不改 SPEC（修措辞走 10-spec 修订轨）。

### R1 · 开工闸

HG-TASK-DRAFT / HG-AUDIT-R1 均 pending（00 在维护者「授权00签收所有过程文档」令下于 20 审后代录，本帽不签）；HG-GRAPH-MODULES **真读** `docs/_tech_graph/l1/01_modules.md` 核验：模块表已建置；lg_rag 行 C2 备注（2026-09-01 人签 approved）已裁定「prompt 装配层 `app/ops/prompts/**` 归属本行」→ assets/ 落盘是 lg_rag 行内部路径延展，路径覆盖不变；memory 行在表（出边 `db, rag, llm`）。本 task 按 SPEC §2 D4 判零图谱变更（不新增路由/表/事件类型 · 不新增一级模块）→ 无新签义务；**回炉补闸条款**钉死：30 新增一级模块 / 把 prompts 拆独立 module_id / 新增任何路由/表/事件类型 → 退 10-spec 修订 SPEC + 补闸 + 图谱如实登记，不得沿用本裁定。既有登记缺口两处（lg_rag 出边缺 memory · memory 出边缺 structured_output）如实留痕，非本波义务不回改。

### R2 · 竖切

D1（render 改 Template）与 D2（模板变量 `{x}` → `$x` 改写 + 搬 assets）强耦合：只改 render 不改模板即全部渲染 KeyError 炸中间态，只搬模板不改 render 则 `$` 前缀变量对 format 是字面文本 = 静默错；D3 审计文字落点（assets README）依赖 D2 目录存在；故 D1–D4 同 task 一次提交，无 memory-embedding-backfill「D3 纯测先行」式切分空间。方案对比不重演，直接继承 SPEC §4 两组裁决（S1 string.Template 弃块拼接/保留 format · A1-a 包内 md 弃单 yaml/docs 路径）。

### R3 · 失败语义

SPEC §5 十条失败面全收并翻四列：缺键 KeyError（变异①）· 转义残留静默错（grep+锚点双保险 · 变异③）· 双写漂移静默错（`你是` 13→4 计数断言 + 删常量入必做项）· 缺文件/缺字段/空 body 显式炸（变异②）· `$` 误伤（基线零命中 + grep 断言）· 变量集合漂移（多传无害缺键显式）· version 忘 bump（列残余风险非验收项 · 承 SPEC）· import 顺序（全量 pytest + 启动冒烟兜）· 误改文案（逐字节对拍）· 图谱编译（回归保险）。补过程五行：闸未签拒开工 · B1 未落盘拒收 · 无变异检验拒收（防空真规则）· 加载器缓存须可清（否则测试期改 assets 不生效 = 假绿/假红）· memory→prompts 新边误读防歧义（闸表留痕 + 回炉边界钉死）。

### R4 · 可测性

验收 20 条全部可执行断言：grep 计数四条（`.format(` 3→2 · `你是` 13→4 特例清单 · assets `{{`/`}}` 零命中 · `$` 零命中——基线数全部本帽真跑）· 9 模板逐字节对拍（含变量代入成品串 · 一次性命令入 40 记录）· 锚点断言替代全文快照（裸 `{"domain"`/`{"route"`/`{"facts"` 结构锚点 · 保证非开发改文案不挂 CI）· 调用方零 diff 白名单（strategy/intent.py 整文件 · multi/nodes.py render 两调用行逐字）· 变异检验三条（各致指定测试挂）· ruff 零新增 + graph-compile 绿。B1 实扫落盘 21 行：回归×11（既有 prompt 测试五组 + 调用方两处 + 特例测试 + 辅扫）· 改编×8（6 常量消费点 + templates/render 本体 · 含 #18/#19 计数行）· 新增×1（守护测试义务）· 删除×0。

### R5 · 交接就绪

思考充分可交 20-task-audit；与 SPEC 逐条核对**实质差异为零**（验收 20 条 = SPEC §6 各块 + 人工闸行 + 闸前置 B1，均过程化落地；两处措辞偏差为如实留痕 · R0 记录，非范围偏差）。残余风险两条：version 忘 bump 无机械闸（承 SPEC §7 residual ① 签收知悉）；既有图谱登记缺口两处留痕待图谱维护波次（不影响本 task 零变更裁定）。

---

### 自检结论（40 核验 · 待回填）

（本节由 40 核验后回填 · 对齐 continuity-dedup 先例：总判定 / 逐条计数 / 变异检验复做记录 / 基线对照 / B1 处置核验 / ruff / graph-compile / WARN 清单 / 证据 invoke 指针）

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | 10-task 落稿 · R0–R5 全轮无 early_stop · 验收 **20 条**逐块映射 SPEC §6 实质零差异（人工闸 1 / D1×3 / D2×5 / D3×2 / 行为零变化×3 / 变异检验×3 / 工程×3）· B1 旧测影响面 21 行实扫落盘（口径 `.format(`=3 · `你是`=13 · 常量消费点 tests 零直引 · pytest 基线 1176 collected 真跑 · 9 常量区 `$` 零命中）· SPEC 措辞偏差留痕两处（strategy/intent.py 实路径 `app/ops/strategy/` · memory→prompts 边实扫不成立 → 备注级处理非回炉）· HG-TASK-DRAFT=pending · HG-AUDIT-R1=pending → 30 拒开工 · HG-GRAPH-MODULES=approved（真读 `01_modules.md` · 零图谱变更 + 回炉补闸条款 + 既有登记缺口两处留痕）· HG-PILOT-OPSDESK-GLAYER=n/a |
