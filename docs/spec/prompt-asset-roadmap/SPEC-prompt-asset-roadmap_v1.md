# SPEC：Prompt 资产化三阶段（改得动→看得见→分得开）（v1）

> **状态**：`draft-complete`（HG-SPEC-SIGNOFF=**pending** · 人签前不出 task / 不改码）
> **track**：`refactor`（本波 = 阶段一 · 行为零变化 · **无 alembic 义务** · 图谱零变更按实判见 §2 D4；阶段二/三各自动 task 时重裁 track）
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 §2.1.1 痛点 · §2.4 三阶段）
> **格式基准**：`docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md`（signed · PR #153 已合）
> **下游**：人签 SPEC → 00 出阶段一 task → 20-task-audit → HG-AUDIT-R1 → 30 实现
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `prompt-asset-roadmap` |
| **invoke_slug** | `prompt-asset-roadmap-p1`（task 阶段 · 总轨三阶段按波拆 task，参照 capability-gateway-p0~p3） |
| **test_strategy** | `required` |
| **test_strategy_note** | 阶段一行为零变化以**全量 pytest 绿 + 迁移前后渲染输出逐字节 diff 为空**为证；新增守护：assets 加载器（缺失/格式错显式炸）· 渲染键缺失 KeyError · body 零 `{{` 转义残留 grep 断言 · 锚点断言（JSON 示例裸花括号存在 · 非全文快照，保证非开发改文案不挂测试）；变异检验三条（见 §6） |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/prompt-asset-roadmap` |
| **graph_change_layer（建议）** | 无（**零图谱变更按实判**：不新增路由/表/事件类型；render() 渲染语法与 assets 落盘是 `app/ops/prompts/**` 模块内重构，`01_modules.md` prompts 行路径覆盖不变；lg_rag/memory 侧仅常量删除改调加载器，不新增模块间依赖边——加载器本就在 `app.ops.prompts` 包内，lg_rag→prompts 边已存在（multi/nodes.py:120-137 已 import render）。若 30 形态偏离（新增一级模块 / 新增跨模块依赖边）→ 回 10-spec 修订并补 HG-GRAPH-MODULES 行） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 维护者签收本 SPEC 后方可 00 出 task / 30 改码（人签，不由 10-spec 代签） |

---

## 1. 背景与目标

### 现状（2026-09-22 实扫 · 锚点逐个核）

**registry 覆盖面：3 模板 / 消费点仅 2 处；产品面 prompt 文案 ≥10 处散在 6 个文件。**

| 锚点 | 实扫结论 |
|---|---|
| `app/ops/prompts/templates.py` | registry 仅 3 模板（`lg_rag.intent.system` v1 · `lg_rag.supervisor.system` v2 · `lg_rag.supervisor.suffix.system` v1）；supervisor 两模板 body 内含 `{{"domain":...}}` 双花括号 JSON 示例（:11-13 · :28 · :40 · :56）——**str.format 与 JSON 花括号打架的实证** |
| `app/ops/prompts/render.py` | 唯一渲染口 `render()`（:35-53）：`tmpl.body.format(**vars_map)`，缺键 KeyError 显式炸（:46-47 · 好先例保留）；slots 块拼接注入（:48-52） |
| `app/ops/prompts/packs.py` | comms pack：**「prompt 内容落盘文件 · 运行时读取 · 缺失即 PromptPackError 显式炸不静默降级」先例**（:119-127 读 `docs/harness/prompts/FRAGMENT_*.md`）；其 SoT 是 harness 纪律片段，非产品 prompt——本 SPEC 复用其**模式**不复用其路径 |
| `app/ops/rag/grader.py` | **env 切版本先例**：`RAG_GRADER_PROMPT` 切 v1/v2（:143-155 · 未知值回退 v1 + warning）；GRADER_SYSTEM_V1/V2 内联常量（:104-137）；logger.info 已记 `prompt=%s` 版本（:218-222）——**阶段二「看得见」的雏形已存在于此** |
| `.format(` 全仓 grep（`app/**/*.py`） | **仅 3 处**：render.py:45（registry 渲染口）· lc_evidence_chain/answer.py:107（外置 yaml 模板）· capability/fallback.py:326（降级话术进工具输出 · 非 LLM prompt）。**str.format 面远小于占位暗示，但散布面在「内联常量」** |

### registry 外散布面（2026-09-22 grep `你是 ` / `*_SYSTEM` 实扫）

| 位置 | prompt | 形态 |
|---|---|---|
| `app/ops/lg_rag/nodes.py:46,56,222` | _ROUTER_SYSTEM / _DIRECT_SYSTEM / _REWRITE_SYSTEM | 模块内联常量 · 含 JSON 示例裸花括号（无 format 故无转义，但**改文案必须改 .py**） |
| `app/ops/lg_rag/multi/nodes.py:84,93` | _EXTRACT_SYSTEM / _AGGREGATOR_SYSTEM | 同上 |
| `app/ops/memory/extract.py:47` | EXTRACTION_SYSTEM_PROMPT | 同上 |
| `app/ops/rag/grader.py:104,115` | GRADER_SYSTEM_V1/V2 | 内联常量 + env 切版自有机制（**特例 · 本波不动**） |
| `app/ops/lc_evidence_chain/answer.py:20` | `answer_system_prompt.yaml` 外置 + `RAG_LC_ANSWER_PROMPT` env 切版 | **已资产化的先例**（单 yaml 多版本 · lru_cache · 缺失回退+warning）；仍用 `.format(`（:107）故其 user 模板若含 JSON 示例仍踩转义坑（**特例 · 本波不动**） |
| `app/ops/chat/nodes.py:28` | _SYSTEM_PROMPT | legacy chat 轨（stream 已 410 · `01_modules.md:22`）——**非范围** |
| `app/ops/prompts/packs.py:42-70` | _TASK_FIELD_CHECKLIST / _DIALOG_POLICY / _PROHIBITIONS | comms pack 自身机制文案（harness 纪律 · 非产品问答 prompt）——**特例 · 本波不动** |

### 痛点

1. **改 prompt 必须找开发**（手册 §2.1.1 真痛点）：≥7 处产品面 prompt 是 `.py` 内联常量，改一句文案 = 改代码文件 + 走开发全流程。
2. **str.format 转义税**：registry 内写 JSON 示例必须 `{{ }}` 双写（templates.py 实证），非开发照抄 JSON 必踩 KeyError/ValueError；answer.py yaml 先例虽外置但渲染仍 `.format(`，坑没填。
3. **版本可归因性残缺**：grader 有 env 切版 + 日志版本，registry 有 version 字段但**无渲染日志**，其余散布点连版本都没有——阶段二/三无资产化底座无从谈起。

### 一句话目标

按手册 §2.4 三阶段推进（**顺序不可跳**：先改得动 → 再看得见 → 后分得开），本 SPEC 定三阶段全景；**本波 task 只做阶段一**——去 str.format 转义 + 产品面 prompt 从代码搬数据文件 + 变更审计形态落地，使**非开发同学改一句文案只动 `app/ops/prompts/assets/*.md` 一个文件、PR diff 即审计、CI 锚点断言兜底**，以全量 pytest 绿 + 迁移前后渲染输出逐字节 diff 为空 + 变异检验为证。

设计纪律（签收时锁死）：

1. **行为零变化**：阶段一不改任何 prompt 文案内容与变量集合；迁移前后每个模板渲染输出逐字节一致（一次性 diff 命令验证，不留全文快照——快照会让非开发改文案挂测试，违背目标）。
2. **缺键/缺文件显式炸，不静默降级**：沿用 render.py:46 与 packs.py:119-127 先例；assets 文件缺失/格式错 → 明确异常点名 template_id 与路径，禁止 fallback 空串。
3. **特例不强行收敛**：grader（env 切版实验面）· answer.py（已外置 yaml）· packs.py（harness 纪律 SoT）本波原样保留；统一收敛是后续波次单独裁定，不在本波「顺手」。
4. **锚点断言替代全文快照**：测试断言「渲染输出含裸 `{"domain"` 且无 `{{` 残留」级结构锚点，使「改一句文案」diff 不挂 CI，「改变量名/留转义」必挂 CI。

---

## 2. 范围

### 三阶段全景（总轨 · 顺序不可跳 · 本 SPEC 签收即锁阶段语义）

| 阶段 | 内容 | 到位判据 | 本波 |
|---|---|---|---|
| 一 · **改得动** | 去 str.format 转义；产品面 prompt 从代码搬数据文件；变更审计形态 | 非开发同学能改一句文案并上线（只动 assets/*.md） | ✅ 本波 task |
| 二 · **看得见** | 每次调用记 template_id+version+渲染 hash；效果指标按 version 聚合（接 grader:218 日志先例 · langfuse span metadata） | 改动可归因「哪版 · 变好还是变差」 | ❌ 后续 task（依赖阶段一 version 全量覆盖） |
| 三 · **分得开** | 按 user/thread 打标分流；灰度；一键回退到具体人群（接 grader env 切版先例泛化） | 新用户试新版、老用户不动 | ❌ 后续 task（依赖阶段二归因数据） |

**波次裁定（参照 `docs/tasks/done/task_capability_gateway_p0~p3.md` 总轨四子 task 先例）**：一个总轨 SPEC + 每阶段一个 task，`orchestration` 字段标「总轨三阶段：本 task = 阶段一」。取舍理由：① 顺序不可跳且阶段一是二三的物理前置（无资产化无 version 可归因 · 无归因无灰度依据）；② 耦合面递增——阶段一纯模块内重构（行为零变化 · 图谱零变更），阶段二动观测聚合面，阶段三动分流基础设施，一口吃下 = 单 PR 混 refactor+feature 两 track 且巨型化；③ 阶段一独立交付即直解手册 §2.1.1 痛点，无需等二三。

### 阶段一细化（本波 task 范围）

#### D1 · 渲染去转义（必做）

| 项 | 约定 |
|---|---|
| 渲染语法 | `render()` 从 `str.format` 改 `string.Template.substitute`（方案 S1 · §4）；变量 `{catalog_block}` → `$catalog_block`，JSON 示例 `{{...}}` → 裸 `{...}` |
| 缺键行为 | `substitute` 缺键抛 KeyError（与现行为一致）· 包装点名 template_id 沿用 render.py:46 模式 |
| 变量集合 | 一字不改：supervisor.system=`catalog_block` · supervisor.suffix.system=`catalog_block, prefix_block, suffix_cap` · intent=无变量 |
| 调用方 | strategy/intent.py:57 · lg_rag/multi/nodes.py:120-137 零改动（render 签名不变） |

#### D2 · prompt 资产落盘（必做）

| 项 | 约定 |
|---|---|
| 落盘位置 | `app/ops/prompts/assets/`（**包内数据文件** · 与 answer.py `with_name("answer_system_prompt.yaml")` 先例同侧 · 方案 A1）；**不复用** `docs/harness/prompts/`（那是 harness 纪律片段 SoT · packs.py:24） |
| 文件形态 | 每模板一个 `.md` 文件，front-matter 载 `template_id` / `version`，正文即 body（方案 A1-a · §4） |
| 迁移清单 | registry 3 模板 + lg_rag/nodes.py ×3（router/direct/rewrite · 命名 `lg_rag.router.system` 等进 registry）+ lg_rag/multi/nodes.py ×2（extract/aggregator）+ memory/extract.py ×1（`memory.extract.system`）= **9 个模板** |
| 代码侧 | 上述 .py 内联常量删除，改调 `render()`/`get_template()`（lg_rag/memory → prompts 依赖边已存在或同包内 · 图谱零变更按实判） |
| 加载器 | 运行时读文件 · 缺失/front-matter 缺字段/空 body → 明确异常点名路径与 template_id（packs.py:119-127 模式 · 设计纪律 2） |

#### D3 · 变更审计形态（必做）

| 项 | 约定 |
|---|---|
| 审计单元 | 文件即资产：PR diff 到 `assets/<id>.md` 即文案变更的机械证据；body 变更须同 PR bump front-matter `version`（约定写入 assets README/模块 docstring；加载器校验 version 存在且格式 `v<N>`） |
| 版本可得性 | `get_template()` 已返回 `PromptTemplate.version`（render.py:24-32 · 零改动）；9 模板全部有 version = 阶段二「看得见」的接入底座 |
| CI 兜底 | 锚点断言 + 零转义 grep 断言（设计纪律 4）；不做全文快照 |

#### D4 · 图谱与文档（必做 · 按实判零图谱变更）

- 不新增路由/表/事件类型；`assets/` 是 prompts 模块内数据目录，`01_modules.md` prompts 行 `app/ops/prompts/**` 路径覆盖不变；lg_rag/memory 侧无新增跨模块边。若 30 形态偏离 → 回 10-spec 修订并补 HG-GRAPH-MODULES 行。
- `./scripts/graph-compile.sh` 绿（回归保险，非新增义务）。
- assets README 或模块 docstring 写明「非开发改文案操作路径 + version bump 约定」（D3 审计形态的文字落点）。
- 不回改 done/归档历史文档。

---

## 3. 非范围

- ❌ 阶段二「看得见」/ 阶段三「分得开」任何实现（观测埋点 · 指标聚合 · 打标分流 · 灰度回退——各自后续 task · 占位草案语义保留）
- ❌ 改 prompt 文案内容本身（文案优化另案 · 阶段一迁移逐字节一致）
- ❌ 注入防护（security-hardening 占位 SPEC 的事 · 占位原文保留）
- ❌ A/B 统计平台（占位原文保留）
- ❌ grader.py env 切版机制与 GRADER_SYSTEM_V1/V2 内联常量（实验面特例 · 设计纪律 3）
- ❌ lc_evidence_chain answer_system_prompt.yaml 与其 `.format(`（已外置特例 · 去转义顺手它 = 范围蔓延）
- ❌ packs.py 内联 checklist/policy/prohibitions 与 FRAGMENT 机制（harness 纪律 SoT）
- ❌ `app/ops/chat/**` 含 _SYSTEM_PROMPT（已 410 · chat 轨清退另一波 · 沿用 `01_modules.md:22` 裁定）
- ❌ capability/fallback.py 降级话术（进工具输出 · 非 LLM prompt）
- ❌ 表结构变更（无 alembic 义务 · 本 SPEC 不触 DB）
- ❌ 历史文档回改；web / ios

---

## 4. 方案对比（R2）

### 去 str.format 转义（D1）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · string.Template（本 SPEC）** | `Template(body).substitute(**vars)`；变量 `$` 前缀；花括号不再是元字符，JSON 示例裸写 | stdlib 零依赖；缺键 KeyError 与现行为逐点一致（render.py:46 包装可原样留）；`{{ }}` 转义税物理清零——非开发照抄 JSON 不再踩坑；迁移后渲染输出可与迁移前逐字节对拍 | 存量 3 模板变量改写 `$` 前缀（grep 可机械核）；文案若含 `$` 需 `$$`——实扫 9 模板零 `$` 字符（迁移验收含 grep 断言） | **推荐** |
| S2 · 独立块拼接（packs.py:130-149 模式） | 模板拆 parts 列表，变量位置整块 `"\n\n".join`，零渲染语法 | 转义问题同样清零；comms pack 已有先例 | 变量语义退化为块级拼接，`{suffix_cap}` 这类句内嵌变量表达不了；每模板一段装配代码 = prompt 又被拖回代码，与 D2 搬数据目标自相矛盾 | 弃 |
| S3 · 保留 str.format + 只搬数据（answer.py yaml 先例） | body 搬文件但渲染仍 `.format(` | 改动最小 | **转义坑原样保留**——非开发在 md 里写 JSON 示例仍要 `{{ }}`，痛点 2 没解；answer.py 本身就是这个形态的活例，不能当目标态 | 弃 |

### prompt 落盘形态（D2）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **A1-a · 包内 assets/ 每模板一 md + front-matter（本 SPEC）** | `app/ops/prompts/assets/lg_rag.supervisor.system.md`，front-matter `template_id/version`，正文裸 markdown | 非开发最友好（无 yaml 缩进/引号税）；单文件 diff = 单模板审计单元（D3 直接成立）；随包分发测试可定位；packs.py 已证「运行时读 md 文件」模式可行 | 9 个小文件；加载器需解析 front-matter（手写 ≤30 行或复用既有依赖，30 阶段定 · 禁引重依赖） | **推荐** |
| A1-b · 包内单 yaml 汇总（answer.py 完全同构） | `assets/templates.yaml` 一文件全量 | 与 answer.py 先例一字不差；一次读取 | yaml 多行块缩进/引号对非开发是税；单文件多模板 diff 审计粒度粗；answer.py 先例自身还带着 `.format(` 转义坑，「同构」不是优点 | 弃 |
| A2 · 仓根 `prompts/` 或 `docs/` 下 | 复用 packs.py 的 docs 路径感 | 非开发「找得到」感更强 | `docs/harness/prompts/` 是 harness 纪律 SoT 不可混居；产品 prompt 随代码分发/测试定位/部署打包都以包内为正；docs 路径在部署镜像里可能不在 | 弃 |

---

## 5. 边界 / 失败路径 / 安全（failure_paths）

| 触发 | 行为 | 可重试 |
|---|---|---|
| 渲染键缺失（调用方少传变量 / 模板新增变量调用方未跟上） | `substitute` KeyError → render() 包装点名 template_id 与缺键（沿用 render.py:46 模式）；**变异检验 ① 钉死** | Y（补变量） |
| 转义残留（迁移后 body 仍留 `{{ }}`） | Template 语法下 `{{ }}` 原样输出进 prompt → **静默错**（模型看到双花括号）；验收含 assets/*.md grep `{{` 零命中断言 + 锚点断言裸 `{"domain"` 存在——双保险 | Y（改 assets） |
| 双写漂移（assets 已落盘但 .py 旧常量残留未删） | 代码侧常量与 assets 文件两份真值 → 静默错；验收含 grep 断言：`app/**/*.py` 搜 `你是 ` 仅剩 grader/answer/chat/packs 四处特例清单内命中；删常量是 D2 必做项非「顺手」 | Y（删残留） |
| assets 文件缺失 / front-matter 缺 version / body 空 | 加载器明确异常点名路径与 template_id（packs.py:119-127 模式 · 设计纪律 2）；**变异检验 ②：临时改名一个 assets 文件 → 加载即炸不静默** | Y（恢复文件） |
| 文案含 `$`（Template 元字符误伤） | 实扫 9 模板零 `$`；迁移验收含 grep 断言；若未来文案引入 `$` → substitute 可能 KeyError/ValueError 显式炸（非静默），CI 锚点断言兜 | Y（`$$` 转义） |
| 变量集合漂移（模板改 `$xxx` 调用方没传 / 反之） | 缺键向：KeyError 显式；多传向：substitute 忽略多余键（与 format 一致）——多传无害，缺键显式，无静默路径 | Y |
| 改文案忘 bump version（D3 约定破坏） | 阶段一不机械强制（无 git 历史感知）；由 PR 审查 + assets README 约定 + 阶段二「看得见」上线后归因错位倒逼；列为残余风险而非验收项 | — |
| lg_rag/memory 改调加载器后 import 顺序问题 | 加载器纯文件读取无服务依赖；全量 pytest + 启动冒烟（`import app.main`）兜底；模块常量删除若留引用残留 → ImportError/NameError 显式炸 | Y |
| 误改文案（30 手滑改动 body 内容） | 验收含**迁移前后渲染输出逐字节 diff 为空**断言（一次性命令 · 9 模板全量对拍） | Y（revert） |
| 图谱编译断裂 | `graph-compile.sh` 绿为验收项；模块内重构不触发索引失配 | Y |

安全：纯重构无新凭证面/网络面/DB 面；prompt 内容零变化故无注入面变化；assets 文件读取限定包内目录，无路径穿越面（template_id 白名单来自 registry 键，不接受外部路径入参）。

---

## 6. 验收标准（阶段一 · 本波 task 直接可用）

### D1 · 渲染去转义

- [ ] `render()` 使用 `string.Template.substitute`；`str.format` 在 `app/ops/prompts/` 下零残留（grep 断言）；全仓 `.format(` 命中从 3 处降为 2 处（answer.py:107 与 fallback.py:326 特例保留）
- [ ] 缺键 KeyError 包装点名 template_id（单测钉死）
- [ ] assets/*.md grep `{{` / `}}` 零命中；9 模板 grep `$` 零命中（`$` 变量前缀除外）

### D2 · 资产落盘

- [ ] `app/ops/prompts/assets/` 9 个 md 文件，front-matter `template_id` + `version`（`v<N>` 格式）齐全，正文非空
- [ ] registry `TEMPLATES` 覆盖 9 模板（原 3 + lg_rag 5 + memory 1）；`templates.py` 内联 body 清零
- [ ] 代码侧旧常量全删：lg_rag/nodes.py _ROUTER_SYSTEM/_DIRECT_SYSTEM/_REWRITE_SYSTEM · multi/nodes.py _EXTRACT_SYSTEM/_AGGREGATOR_SYSTEM · memory/extract.py EXTRACTION_SYSTEM_PROMPT，改调 render/get_template
- [ ] grep 断言：`app/**/*.py` 搜 `你是 ` 命中仅落 grader.py / answer.py(经 yaml) / chat/nodes.py / packs.py 特例清单
- [ ] strategy/intent.py:57 · multi/nodes.py:120-137 调用方零 diff

### D3 · 审计形态

- [ ] assets README（或 prompts 模块 docstring）写明非开发操作路径（改 body → bump version → PR → CI 锚点断言 → 合入上线）与 version bump 约定
- [ ] 加载器校验 front-matter 缺字段/空 body 明确报错（单测钉死）

### 行为零变化

- [ ] 全量 `pytest tests` 绿；`ruff check app tests` 绿
- [ ] **逐字节对拍**：迁移前后 9 模板渲染输出 diff 为空（含变量代入后成品串 · 一次性命令输出入 40 验收记录，不留全文快照）
- [ ] 生产路径 diff 只含：prompts/ 模块内改动 + 上述 6 个常量删除点 + assets/ 新增 + 测试

### 变异检验（不验收空真规则）

- [ ] ① 缺键显式：临时从 supervisor.system 调用去掉 `catalog_block` 传参 → 指定单测 KeyError 挂；恢复后全绿
- [ ] ② 缺文件显式：临时改名一个 assets/*.md → 加载/首渲染明确异常挂（非静默空串）；恢复后全绿
- [ ] ③ 转义残留可检：临时在某 assets body 写入 `{{"route"` → grep 断言/锚点断言必须挂；恢复后全绿

### 工程

- [ ] `./scripts/graph-compile.sh` 绿；图谱零变更裁定与实现形态一致（新增一级模块/跨模块边 → 本 SPEC 回炉）

### 阶段二/三（方向性判据 · 后续 task 细化，非本波验收）

- 阶段二：每次 LLM 调用日志/span 可见 template_id+version+渲染 hash；同 template 两版本指标可分聚合（grader:218 日志先例泛化）
- 阶段三：按 user/thread 打标可指定版本；一键回退；grader env 切版先例泛化为统一分流面

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游手册 §2.1.1 痛点（改 prompt 找开发）+ §2.4 三阶段；实扫纠正占位暗示：`.format(` 全仓仅 3 处（转义面小），真散布面是 ≥7 处 .py 内联常量（registry 只覆盖 3/10）；发现两处自有机制特例（grader env 切版 · answer yaml 外置）与两处模式先例（packs 运行时读 md 显式炸 · render 缺键 KeyError） | done |
| R1 | 范围 = 三阶段全景签收 + 本波只做阶段一（D1 去转义 / D2 落盘 9 模板 / D3 审计形态 / D4 图谱零变更按实判）；非范围 = 阶段二三实现 · 文案优化 · 注入防护 · A/B 平台（占位原文全保留）+ grader/answer/packs/chat 四特例 + fallback 话术 | done |
| R2 | 两组对比各 ≥2：去转义选 string.Template（弃块拼接：句内变量表达不了且拖回代码；弃保留 format 只搬文件：转义坑原样 = answer.py 现状不能当目标态）；落盘选包内 assets 每模板一 md（弃单 yaml：非开发缩进税 + 审计粒度粗；弃 docs 路径：SoT 混居 + 部署面） | done |
| R3 | failure_paths 10 条，核心：转义残留与双写漂移是**静默错**（grep 断言 + 锚点断言 + 删常量入必做项三保险）；缺键/缺文件显式炸由变异检验①②钉死；version 忘 bump 阶段一不机械强制列残余风险 | done |
| R4 | 验收全为可执行断言：grep 计数（.format 3→2 · `你是 ` 特例清单 · `{{` 零命中）· 9 模板逐字节对拍 · 锚点断言替代全文快照（保证非开发改文案不挂 CI）· 变异检验三条 | done |
| R5 | SPEC draft-complete 可交人签 HG-SPEC-SIGNOFF；签后 00 出阶段一 task（slug 建议 `prompt-asset-roadmap-p1` · orchestration 标总轨三阶段 · 参照 capability-gateway-p0~p3） | done |
| early_stop | no | — |
| residual_risks | ① version 忘 bump 无机械闸（PR 审查 + README 约定 + 阶段二倒逼）；② front-matter 解析若引依赖须 30 阶段从轻（禁 yaml 全家桶顺手进 requirements 之外的新重依赖）；③ lg_rag/nodes.py 的 rewrite 等 prompt 未来若加变量，调用方改造属彼时 task 的事 | 签收时知悉 |

---

## 8. 下一棒

1. **维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`
2. **00**：起草 `docs/tasks/active/task_prompt_asset_roadmap_p1.md`（范围 §2 D1–D4 · failure_paths 沿用 SPEC §5 · 人工闸表按实判：无 HG-GRAPH-MODULES 义务除非形态偏离 · `orchestration: 总轨三阶段：本 task = 阶段一` · 变异检验三条入验收）
3. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1`
4. **30**：`task/prompt-asset-roadmap` 分支实现阶段一（D1 渲染语法 → D2 落盘迁移 → D3 审计文字 · 文案零改动）
5. **40**：验收（含逐字节对拍 + 变异检验三条）→ PR（与 memory-facts-p0/p1 · continuity-dedup 同模式）
6. 阶段二/三各自回 10-spec/10-task 拆波（本 SPEC §2 全景即依据 · 顺序不可跳）

### 下一棒可复制 Prompt（20-spec-audit 预审 / 00 起草 task）

```text
你是 ops-desk-api 仓（/Users/cyning/Desktop/Ops-desk/ops-desk-api）的 <20-spec-audit ｜ 00>。
SPEC：docs/spec/prompt-asset-roadmap/SPEC-prompt-asset-roadmap_v1.md（draft-complete · HG-SPEC-SIGNOFF=pending）。
<20-spec-audit>：书面审范围/非范围/验收/failure_paths 与 R0–R5 思考轮，结论落盘 docs/harness/reviews/，不代签人闸。
<00>：待维护者签 HG-SPEC-SIGNOFF=approved 后，按 SPEC §8 起草 docs/tasks/active/task_prompt_asset_roadmap_p1.md（D1–D4 · failure_paths 沿用 SPEC §5 · 图谱闸按实判零变更 · orchestration 总轨三阶段本 task=阶段一 · 变异检验三条入验收）。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 占位稿（范围草案 + 锚点 + 验收方向 + 接续指引） |
| 2026-09-22 | 10-spec 补全：锚点逐个实扫（templates/render/packs/grader）+ 全仓 `.format(` grep（**仅 3 处 · 纠正占位暗示的大转义面**）+ `你是 `/`*_SYSTEM` 散布面 grep（≥7 处 .py 内联常量 · registry 只覆盖 3/10）；波次裁定：SPEC 覆盖三阶段全景 + 本波只做阶段一（参照 capability-gateway-p0~p3 · 四理由见 §2）；方案对比两组（string.Template vs 块拼接 vs 保留 format · 包内 md vs 单 yaml vs docs 路径）；特例裁定四例（grader env 切版 / answer yaml / packs FRAGMENT / chat legacy 均本波不动）；failure_paths 10 条（转义残留与双写漂移两静默错三保险 · 缺键缺文件显式炸）；验收断言化 + 变异检验三条 + 锚点断言替代全文快照；track 裁定 `refactor`（本波行为零变化 · 无 alembic · 图谱零变更按实判）；R0–R5 回填；HG-SPEC-SIGNOFF 保持 pending 待人签 |
