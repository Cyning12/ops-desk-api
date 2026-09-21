# Task 书面审查：prompt-asset-roadmap-p1（R1 · 20-task-audit）

> **审查帽**：20-task-audit（Harness V2 · 书面审 task，不改实质内容，不代签人闸）
> **审查日期**：2026-09-22
> **task**：`docs/tasks/active/task_prompt_asset_roadmap_p1.md`（draft · 2026-09-22 10-task 落稿 · commit 77568ed）
> **对照 SPEC**：`docs/spec/prompt-asset-roadmap/SPEC-prompt-asset-roadmap_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · commit 94b2e21）
> **分支核验**：`git branch --show-current` = `task/prompt-asset-roadmap` ✅（审查全程未切分支 · 未 push）

---

## 一、结论摘要

| 维度 | 结论 |
|------|------|
| **内容审查** | **PASS（零阻塞 · 无须返工项）**：范围/非范围/验收/failure_paths/R0–R5/闸表 与 SPEC 逐项核对一致；B1 实扫抽查全部属实；四条 grep 计数断言基线本帽全部复跑吻合；变异检验三条可执行；两处 SPEC 措辞偏差留痕经复核属实且处理合规 |
| **流程闸** | **HG-AUDIT-R1 = pending**（blocks 30 · 待维护者/授权 00 代录签收）；HG-GRAPH-MODULES=approved 经本帽**亲读** `docs/_tech_graph/l1/01_modules.md` 复核成立；HG-TASK-DRAFT=pending；HG-PILOT-OPSDESK-GLAYER=n/a |
| **回炉 10-task** | 无 |
| **非阻塞备注** | 4 条（见第四节），均不阻塞签闸 |

**结论**：task 内容可交维护者签 HG-AUDIT-R1；pending 期间 30 拒开工，本审查文**不附 30 Prompt**。

---

## 二、核对项结果（逐项）

### 2.1 SPEC 对照（范围 / 非范围 / 验收 / failure_paths / 闸表 / 思考轮）

| # | 核对项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 范围 D1–D4 与 SPEC §2 一致 | ✅ | task §范围 D1–D4 逐块映射 SPEC §2 D1–D4：D1 渲染去转义（string.Template.substitute · 方案 S1）· D2 9 模板迁 `assets/*.md`（registry 3 + lg_rag 5 + memory 1 · front-matter template_id/version）· D3 审计形态（README/docstring + version bump 约定）· D4 图谱零变更按实判；竖切结论（D1/D2 强耦合一次提交）理由成立 |
| 2 | 非范围与 SPEC §3 一致 | ✅ | SPEC §3 十一条全收（阶段二三实现 · 文案优化 · 注入防护 · A/B 平台 · grader/answer/packs/chat 四特例 · fallback 话术 · 表结构 · 历史文档/web·ios）；task 增「既有图谱登记缺口回填留痕非义务」一条，属闸表留痕的镜像声明，与 SPEC 非范围同向 |
| 3 | 验收断言化：D1 去转义 | ✅ | D1×3 条 = SPEC §6-D1 一致 + 计数口径细化（`.format(` 3→2 点名 answer.py:107/fallback.py:326 特例保留）；缺键 KeyError 单测点名 `lg_rag.supervisor.system` 少传 `catalog_block`，可执行 |
| 4 | 验收断言化：D2 落盘 | ✅ | D2×5 条 = SPEC §6-D2 一致：9 md 文件逐 id 列名含版本号（v1/v2/v1 + 6×v1）· registry 覆盖 9 模板 · 6 常量删除点名消费点行号 · `你是` 13→4 特例清单计数断言 · 调用方零 diff 白名单（intent.py 整文件 · multi/nodes.py render 两调用行逐字） |
| 5 | 验收断言化：D3 审计形态 | ✅ | D3×2 条 = SPEC §6-D3 一致 + 加载器校验 version 格式与缓存可清单测化（承 SPEC §7 residual ② 禁新重依赖） |
| 6 | 行为零变化与逐字节对拍 | ✅ | 全量 pytest 绿（基线 1176 collected · 无既有用例删除）+ ruff 零新增 + **迁移前后 9 模板渲染输出逐字节 diff 为空**（含变量代入成品串 · 一次性命令入 40 记录 · 不留全文快照）+ 生产路径 diff 白名单；锚点断言（裸 `{"domain"`/`{"route"`/`{"facts"` 且无 `{{` 残留 · 非全文快照）与 SPEC 设计纪律 4 一致 |
| 7 | 变异检验三条 | ✅ | ① 缺键显式（去 `catalog_block` 传参 → 指定单测 KeyError 挂）② 缺文件显式（改名 assets/*.md → 加载即炸非静默空串）③ 转义残留可检（body 写入 `{{"route"` → grep/锚点断言必挂）；各条操作具体、预期明确、恢复后全绿，与 failure_paths「无变异检验却宣称迁移有效 → 40/verify 拒收」闭环 |
| 8 | failure_paths | ✅ | task 15 条 = SPEC §5 十条全收（逐条比对无漏无改义 · 翻四列）+ 过程五条（闸拒开工 / B1 闸前置拒收 / 无变异检验拒收 / 加载器缓存测试语义 / memory→prompts 边误读防歧义），与 R3 声明一致 |
| 9 | R0–R5 思考轮 | ✅ | 控制表 6 行齐（R0–R5 全 done），actual_last_round=R5 · early_stop=no；residual_risks 两条（version 忘 bump 无机械闸承 SPEC §7 residual ① · 既有图谱登记缺口留痕待图谱维护波次）均标明处置轨；各轮子节有实质结论非空转 |
| 10 | graph_change_layer / 图谱裁定 | ✅ | `graph_change_layer=无` + `graph_delta_note` 含**「30 偏离零变更预判（新增一级模块 / prompts 拆独立 module_id / 新增路由/表/事件类型）则回炉补闸 + SPEC 回炉」条款**（另见于闸表行、验收人工闸行、工程项、R1 子节，共 5 处钉死）；与 SPEC §2 D4 裁定一致 |
| 11 | review_hat / test_strategy / 元信息 | ✅ | `review_hat=20` · `test_strategy=required` + note 与 SPEC 元信息一致；`orchestration` 标「总轨三阶段：本 task = 阶段一」承 SPEC §2 波次裁定；freeze_id=无（不动三个 freeze 契约） |
| 12 | 闸表：HG-AUDIT-R1 必须 pending | ✅ | 闸表行 `HG-AUDIT-R1 | pending | 30`，task 状态行同步声明「30 拒开工」，failure_paths 首行兜底；HG-TASK-DRAFT=pending（00 依授权 20 审后代录 · 本帽不签） |
| 13 | 闸表：HG-GRAPH-MODULES 亲读复核 | ✅ | 本帽亲读 `docs/_tech_graph/l1/01_modules.md`：模块表已建置（bootstrap 签 2026-07-16 · 第 55 行）；lg_rag 行 C2 备注（2026-09-01 · 签录第 63 行）确载「prompt 装配层 `app/ops/prompts/**` 归属本行（模板 id 全部 `lg_rag.*` 且被 supervisor/intent 消费）」；memory 行在表（第 28 行 · 出边 `db`, `rag`, `llm`）。task 闸表说明与图谱真值**一致**，零图谱变更裁定成立 |
| 14 | 行为变更类 task 旧测 grep 影响面（K7 checklist） | ✅ | B1 清单 21 行实扫落盘 · 逐条有处置三态（回归/改编/新增 · 删除×0）· 扫描口径真跑写明；验收「工程 · 闸前置」项钉死 30 逐条执行并回填 |

### 2.2 grep 计数断言基线复核（本帽 2026-09-22 真跑）

| 断言 | task 基线 | 本帽复跑 | 结果 |
|------|-----------|----------|------|
| `grep -rn --include='*.py' '\.format(' app/` | **3 处**：render.py:45 · answer.py:107 · fallback.py:326 | 逐行一致（3 处同行号） | ✅ |
| `grep -rn --include='*.py' '你是' app/` | **13 处**（templates ×3 · lg_rag/nodes ×3（:47,:57,:223）· multi/nodes ×2（:85,:94）· memory/extract :47 · grader ×2（:104,:115）· chat/nodes :30 · packs :133） | **13 处**逐行一致 | ✅ |
| 迁移后 `你是` 应剩 4 处特例 | grader :104,:115 · chat/nodes :30 · packs :133 · answer 经 yaml 零 .py 命中 | 13 − 9 迁移源 = 4，落点与清单逐行吻合；answer.py 确零 `.py` 命中 | ✅ |
| 9 模板常量区 `$` 零命中 | 零 | 四文件（templates.py · lg_rag/nodes.py · multi/nodes.py · memory/extract.py）**全文**零命中（强于常量区口径） | ✅ |
| tests 零直引 6 常量名 | 零命中 | `grep -rn -E '_ROUTER_SYSTEM|_DIRECT_SYSTEM|_REWRITE_SYSTEM|_EXTRACT_SYSTEM|_AGGREGATOR_SYSTEM|EXTRACTION_SYSTEM_PROMPT' tests/` = **0** | ✅ |
| pytest 基线 | 1176 collected | 本帽真跑 `python -m pytest tests --collect-only -q` = **1176 tests collected** | ✅ |

### 2.3 B1 旧测影响面 21 行抽查（本帽独立复核 · 抽 9 条）

| B1# | 抽查内容 | 复核结果 |
|-----|----------|----------|
| 1 | `tests/test_prompt_assembly.py` 五用例锚点（:7-8 import · :11-16 v2 version/body · :19-23 intent v1 · :26-32 render 带变量 · :35-42 slots · :45-47 未知模板） | ✅ 逐行亲读全吻合；`:14` version=="v2" 与 `:21` version=="v1" 在，front-matter 承值裁定可落地 |
| 2 | `tests/test_prompt_packs.py:19,176-180` `TEMPLATES` 子集断言 | ✅ `:19` import TEMPLATES 在；`:180` `{"lg_rag.intent.system", "lg_rag.supervisor.system"} <= set(TEMPLATES)` 在且注释自证「加法不挂」语义 |
| 3 | `tests/test_prompt_packs.py:183-193` render 断言 | ✅ supervisor.system v2 + `catalog_block` + slots 三断言在 |
| 4 | `tests/test_prompt_packs.py:196-211` packs 依赖方向 AST 禁令 | ✅ 在（禁 import session/chat） |
| 8 | `app/ops/strategy/intent.py:19,57` | ✅ `:19` `INTENT_SYSTEM_TEMPLATE = "lg_rag.intent.system"` · `:57` `render(INTENT_SYSTEM_TEMPLATE)` · `:13` 既有 `from app.ops.prompts import render` |
| 9 | `app/ops/lg_rag/multi/nodes.py:120-123,130-137` render 两调用 | ✅ 逐行亲读吻合（`:63` import render）；`_build_supervisor_system` / `_build_supervisor_suffix_system` 变量集合 `catalog_block` / 三变量与钉死契约一致 |
| 10–15 | 6 常量定义与消费点行号（nodes.py :46/:56/:222 与 :100/:245/:290 · multi/nodes.py :84/:93 与 :1041/:1512 · extract.py :47 与 :116） | ✅ grep 全吻合（extract.py `:46` docstring 注「不做 str.format」· `:49` 裸 `{"facts"...}` 实证在） |
| 16/17 | templates.py 3 模板内联 body · render.py:45 `.format(` | ✅ templates.py `:11-13`/`:28`/`:40`/`:56` 四处 `{{ }}` 转义实证在 · 变量 `:33`/`:54`/`:62`/`:63` 吻合 · 版本 v1/v2/v1 吻合；render.py `:45` format · `:46-47` KeyError 包装 · `:48-52` slots · `:24-32` get_template 逐行吻合 |
| 20 | tests 全仓 6 常量名零直引 | ✅ 见 2.2 表 |

**B1 裁定**：21 行为实扫所得，抽查 9 条全数属实；处置三态定义清晰，「渲染语法切换 + 9 模板搬 assets + 6 常量删除，对外签名与渲染输出逐字节不变 → 回归为主 · 改编限 6 消费点与 templates/render 本体 · 删除×0」的裁定与钉死契约/非范围一致。

### 2.4 两处 SPEC 措辞偏差留痕属实性复核

| 留痕 | 本帽复核 | 结果 |
|------|----------|------|
| ① SPEC「strategy/intent.py:57」路径省 `app/ops/` 前缀易误读为 lg_rag 内 | 实路径 `app/ops/strategy/intent.py`（**不在** `app/ops/lg_rag/` 下）；该文件 `:13` 已 import `app.ops.prompts` 为既成事实，本 task 对其零 diff | ✅ 属实，留痕准确；范围语义零影响裁定成立 |
| ② SPEC「memory→prompts 依赖边已存在或同包内」实扫不成立 | `grep 'prompts' app/ops/memory/` = **零命中**（memory 侧不成立）；lg_rag 侧成立（multi/nodes.py `:63` import render）；30 改调 render() 将新增 memory→prompts 物理 import，因 prompts 非独立 module_id（C2 裁定归属 lg_rag 行），按 memory 行出边备注级补充处理（对齐 llm-layer-hardening「依赖出边 +db」00 代录先例 · 签录第 88 行） | ✅ 属实，备注级处理与图谱语义自洽，不构成 SPEC 回炉的裁定成立 |
| 附：既有登记缺口两处（非本波义务） | lg_rag 行出边（`lc_evidence_chain, llm, structured_output, capability`）确无 memory，而 `router.py:50` / `sse_stream.py:49` / `continuity.py:218` 已 import `app.ops.memory`（本帽 grep 吻合）；memory 行出边确无 structured_output，而 `extract.py:30` 已 import | ✅ 属实，留痕不回改处理合规 |

---

## 三、阻塞项（回炉 10-task）

**无。** 内容零阻塞；流程闸 pending 属正常待签状态，非内容回炉。

---

## 四、非阻塞备注（不阻签闸 · 供维护者与下游知悉）

1. **20 invoke 快照**：task `required_invoke_hats=10,20,30,40` 含 20，按 Harness 惯例 20 过程 invoke 快照可落 `docs/harness/invokes/by-task/prompt-asset-roadmap-p1/`。本次维护者指令限定「只写 reviews/ 下审查文」，本审查文即 R1 书面真值；若需严格对齐 invoke 留痕，维护者可令 00 在签闸时一并补录 20 invoke 摘要（指向本文件即可）。
2. **验收 20 条 vs SPEC §6 17 条**：task 多出「人工闸行 / 闸前置 B1 / 守护测试就位」三条，属过程化落地增补（task R5 已声明实质差异为零），非范围偏差，无须 SPEC 回炉。
3. **B1 处置统计口径**：R4「回归×11 · 改编×8」为归并计数（#9/#18/#19 为混合处置行），逐行处置以 B1 表为准；本帽抽查以行为单位核验属实，统计口径差异无实质影响。
4. **SPEC 措辞两处偏差不回改 SPEC**：task 选择如实留痕 + 修措辞走 10-spec 修订轨，符合「不改 signed SPEC 实质」纪律；建议随下一波图谱/文档维护顺手修订，非本波义务。

---

## 五、回填清单

无（零阻塞，无回炉回填项）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文件：内容 PASS 零阻塞）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期；或依本窗授权由 00 代录并留痕）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | 20-task-audit R1：对照 SPEC（signed · 94b2e21）逐项核对 14 项全过 · grep 计数断言四条 + pytest 基线 1176 全部真跑吻合 · B1 二十一抽九全属实 · 两处 SPEC 措辞偏差留痕复核属实 · 图谱闸亲读 `01_modules.md` 复核成立 · 内容零阻塞 · HG-AUDIT-R1 仍 pending → 附维护者签闸清单，不附 30 Prompt（结论节措辞参照 memory-embedding-backfill 2026-09-21 机读格式修订写法） |
