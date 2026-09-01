# Task Audit R1：host-comms-prompt-pack

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_host_comms_prompt_pack.md`（C2 · comms Prompt Pack：`render_pack("comms")` 纯函数 + `route_intent` 规则判定器 + pack 元信息 · 无新路由）  
> **上游 SPEC**：`docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`（**signed**）§4（意图路由）· §6（闸纪律）· §8（Skills≠verify）· §9（session 隔离）· §10（C2 行）· §15（思考轮承载）  
> **先例**：`docs/harness/reviews/task_host_harness_cli_capability_audit_R1_20260901.md`（C1 · 同款 W4 豁免处理 · 同款「00 代签待 R1 落盘」流程）  
> **日期**：2026-09-01 · 审查人：20-task-audit  
> **10 lint**：PASS（W4 无思考轮节 · SPEC 06 §15 承载合法）· 本帽复跑 `dsh-coding-kit@1.10.0 task lint` → **PASS（exit 0 · W4 warn）** 核实

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10 · **无「必须退回 00 改钉」级问题** |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（正确 · 20 不代签）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 已 approved（00 代签 · 维护者 Prompt 授权留痕） |
| **30 授权** | **未签发** · pending 时禁止附 30 Prompt；真值仍在 task 人工闸表；**可交 00 代签 HG-AUDIT-R1** |

---

## 审查核对（对照 SPEC 06 §4/§6/§8/§9/§10/§15 · 现网代码只读核实）

| 审查点 | 结论 |
|--------|------|
| SPEC 06 §4 意图路由三条（默认 product · 显式进 comms · 不确定/误判回退 product） | **一致 · 不退回 00**。00 定夺「意图路由」行逐条对齐：默认 **product** ✓；显式「立项 / 开 task / 写 SPEC」类意图 → comms ✓（§4 例示措辞子集）；**不确定回退 product（宁可漏进 comms）** ✓ 与 §4「宁可漏进 comms，不可把业务答误入立项流程」逐字同向。验收条 3（参数化用例三档：立项关键词→comms · 普通业务问句→product · 空/模糊→product）+ 验收条 5（异常/None 输入 → product）双钩可验收 |
| 规则/关键词判定器（不引入 LLM 判定）是否在范围 | **在范围 · SPEC 显式授权**。§4「实现波」行钉「具体判定器（关键词 / 分类节点 / UI 入口）随 C2 task 定」，§15 residual_risks 同钉「C2 意图判定器形态未冻（C2 task 定）」——task 钉「规则/关键词纯函数 · 本波不引入 LLM 判定」是 §4 授权区间内的收窄落地；非范围明列「LLM 驱动的意图判定（升级另议）」，未越权、未漂移 |
| §6 禁代签入 pack 的验收可判定性 | **可判定**。00 定夺「禁令条文入 pack」行 = 永不签发 human_gate（§3 禁令 B）· 写盘仅 `docs/tasks/`+invoke 草稿（§5/C3 边界预告）· Skills≠verify（§8）三条；验收条 1 钉「『永不签发 human_gate』禁令条文（断言）」——**子串断言机械可判**；failure_paths 行 4「模型输出『已代签』字样 → pack 禁令条文压制 + C3 人确认兜底（§6）」补运行时失效路径。与 §6「可输出『待人签』提示与缺失闸清单」语义相容 |
| FRAGMENT 防拷贝漂移钩 | **成立**。00 定夺槽位链钉「仓内 kit FRAGMENT 真值文件 · 运行时读文件或构建期内嵌由 30 定 · **禁止拷贝后漂移失同步**」；验收条 2 钉「测试读真值文件对比（防拷贝漂移）」；非范围明列「拷贝 FRAGMENT 后双写漂移」。现网核实两真值文件存在：`docs/harness/prompts/FRAGMENT_00_delegate_only_v1_zh.md` ✓ · `FRAGMENT_hat_reanchor_v1_zh.md` ✓（task 前置「kit ≥1.10 FRAGMENT 已 sync 仓内」属实）。真值文件为 SoT、测试对比为钩、拷贝漂移为非范围——三层闭合 |
| 纯函数层无新路由 · product 侧零影响的互斥性 | **互斥成立 · 现网可检验**。范围 1/2 全为纯函数（`render_pack` / `route_intent` / pack 元信息）；非范围明列「新增 HTTP 路由 / 接线到 chat 端点」「改 product pack 或业务 Chat / lg-rag 任何行为」；验收条 6「既有 `render()`/`get_template()` 签名与行为不变 · 旧测绿」+ 验收条 6b「`router.py` 零 diff · 不 import `app.ops.session`/chat 流路径」。现网核实：`render.py` 现签名 `render(template_id, variables=None, *, slots=None) -> str`（slots 以 `<!-- slot:name -->` 块追加）· `get_template` · `PromptTemplateNotFoundError(KeyError)` ——与 10 自检陈述逐字相符；`TEMPLATES` 仅 `lg_rag.intent.system` v1 · `lg_rag.supervisor.system` v1 两枚（含 `{catalog_block}` 变量）✓；既有消费方 `app/ops/strategy/intent.py`（render `lg_rag.intent.system`）· `app/ops/lg_rag/multi/nodes.py`（render supervisor）· 旧测 `tests/test_prompt_assembly.py` 在——「旧测绿」有具体可跑对象 |
| 分 session 本波仅元信息标记 · 与 SPEC §9 的关系 | **表述准确**。§9 钉「分 thread/session · 互不注入历史 · 不共用 system prompt/Pack」为**边界条文**；§10 C2 行内容仅「PromptAssembly pack=comms 槽位 + 意图路由判定器」——session 管理实现不在 C2 行。task 钉「本波交付判定器 + pack 渲染，session 管理接线不在本波；§9 条文落地到 pack 元信息 `session_scope="comms"` 标记」+ 非范围「session 管理实现」+ 验收条 4「pack 元信息含 `name="comms"` · `session_scope="comms"` · `version"`」——元信息标记是 C2 波对 §9 的**最小可验收落地**，接线留 C3/C4 或另议与 §10 波次表不冲突。「不共用 system」由「product/comms system 不混断言」（test_strategy_note）侧钩 |
| failure_paths 完备性 | **完备**（四行）：意图误判 → 回退 product（默认态 · comms 入口须显式）✓（§4 回退条 + §13「意图误判 → 回退 product」对齐）；FRAGMENT 真值文件缺失 → 渲染报错 · **不静默降级为空槽位** ✓；pack 槽位缺字段 → 渲染报错（明确缺哪个槽位）✓（与现网 render 缺变量抛 KeyError 风格一致）；模型输出「已代签」字样 → 禁令条文压制 + C3 人确认兜底 ✓（§6/§12 风险表对齐）。覆盖 SPEC §13 中 C2 相关行并补齐实现侧两条 |
| graph_delta 钉 lg_rag 行备注 · 不新增一级模块 | **合理 · 现网核实**。10 自检已将开放钉钉死：现网 `01_modules.md` 模块表无 `app/ops/prompts/**` path glob；模板 id 全部 `lg_rag.*` 且被 lg_rag supervisor/intent 消费（`strategy/intent.py` import `lg_rag.state`/`lg_rag.schemas` · `multi/nodes.py` 在 `lg_rag/` 内）→ 归属 **`lg_rag` 行 L27** 成立（现网核实 L27 确为 lg_rag 行）；graph_delta 钉「仅该行备注 · 不新增一级模块」与 C1 先例（capability 行备注）同款；「若增 `implementedBy` → 同步 G-L2 indexes」为条件钩不预加义务；graph_change_layer=`G-L1` 合理；HG-GRAPH-MODULES=approved（00 代签 · 仅备注）成立 |
| wiki_delta=`n/a` | **合理**。行为真值在 SPEC 06 §4/§9 + 本 task；不晋升 coding_wiki；验收条 9 `lint-wiki-delta` 钩在 |
| 思考轮 W4 豁免（SPEC 06 §15 承载） | **合法 · 不退回**。本帽复跑 `task lint` → PASS · W4 warn「无思考轮节（SPEC 承载 / bugfix 轨合法豁免）」；SPEC 06 §15 R0–R5 回填完整（R3 已覆盖「默认 product 防业务答误入立项 · 代签为永久禁令 · session 隔离防混线」——即本 task 验收条即 SPEC 思考轮的执行层落地）；与 C1/T5/T6 先例同款处理，20 不把缺节当内容阻塞 |
| 人工闸表与 invoke 留档 | **合规**。required_invoke_hats=`10,00,30`；00/10 invoke 已落盘 `docs/harness/invokes/by-task/host-comms-prompt-pack/`（两文件 glob 核实 ✓）；HG-TASK-DRAFT approved（00 代签 · 维护者 Prompt 授权 · 2026-09-01）· HG-GRAPH-MODULES approved · HG-AUDIT-R1=pending 待本审查落盘后 00 代签——符合 §6 闸纪律「00 代签 ≠ 模型自签」区分；§3 永久禁令 B 未被触碰（本帽亦不签发） |
| 行为变更类 task「旧测 grep 影响面」（K7 checklist） | **已钩 · 本 task 实为新增**。comms 为新增 pack（不改既有默认值/校验/fallback 语义），但验收条 6「product 侧渲染零变化 · 旧测绿」+ 验收条 6b「router.py 零 diff」已覆盖影响面；现网旧测锚点 `tests/test_prompt_assembly.py` 存在；30 自检时建议附 `tests/` 内 prompts 相关测试文件清单逐一点名 |
| Capability 声明与 C1 一致性 | **一致**。00 定夺「pack 元信息可声明可用 `harness.verify`/`harness.task_lint`（C1 已交付）；不在本波调用（Policy 默认关保持）」——与 §7「默认关」+ C1 task 已交付的 `policy_blocked` 语义相容；非范围明列「真调 `harness.*` Capability · 改 Policy 默认」 |
| freeze / 05 契约 | **无冲突**。freeze_id=`n/a` 且注明「不改 lg-rag-sse-v1 · pack 契约由本 task 30 自检记录」——与 SPEC §16「C1 起若出现新契约由对应实现 task 定义 freeze，不在本 SPEC 预冻」对齐 |

其余可执行性：验收含 ruff/pytest/graph-compile/lint-wiki-delta 全绿；必读列表含 SPEC §4/§6/§8/§9 + 现网四文件只读参考 + L2 规范；`close_pr_policy=required`、`kpi_aggregator=CLOSE`、orchestration「C1 ✓ → C2 → C3 串行」与 §10 波次表顺序钉一致；10 自检结论五项现网核对本帽抽样复核（render 签名 ✓ · TEMPLATES 两枚 ✓ · FRAGMENT 两文件 ✓ · L27 lg_rag 行 ✓ · SPEC §15 在 ✓）全部属实。

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 30 知情即可）

1. **FRAGMENT 读取路径的部署形态**：00 定夺允许「运行时读文件或构建期内嵌由 30 定」——若选运行时读 `docs/harness/prompts/`，须注意该目录不在 `app/` 包内，部署/打包环境下相对路径可能失效（failure_paths 行 2「渲染报错不静默降级」可兜底，但 30 须在自检记录写明所选形态与路径解析基准）；选构建期内嵌则验收条 2 的真值对比测试须在内嵌生成步骤之后跑。task 未钉死、属实现自由度。
2. **关键词词表未钉死**：task 验收给了三类用例档位（立项关键词 → comms · 业务问句 → product · 空/模糊 → product），但具体关键词清单（哪些措辞算「显式立项意图」）由 30 落地定；SPEC §4 例示「立项 / 开 task / 写 SPEC / 拆波次 / 走 harness 流程」可作词表种子。建议 30 把最终词表写进自检记录，并保证词表外的业务措辞一律回退 product（验收条 3/5 已钩住方向）。
3. **误判处理的跨 session 交还不在本波**：SPEC §4「误判处理」行钉「用户在 comms 会话内表明为业务问题 → 跨 session 交还 product」——该行为依赖 session 接线，本波仅交付判定器 + pack 渲染（failure_paths 行 1 用户可见「无（C2 无 UI）」已如实标注）；30 不得在本波顺手做交还逻辑，留 C3/C4 或另议，避免范围蔓延。
4. **`render_pack` 与既有 `render()` 的关系未钉**：00 定夺写「扩展 pack 概念（如 `packs.py`）」——是复用 `render()` 加 slots 注入还是独立装配函数，由 30 定；无论何种形态，验收条 6「既有签名与行为不变」已钩住 product 侧零影响，非阻塞。

---

## 回填清单

无（内容零阻塞 · 不改 task 实质 · **不改**人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-AUDIT-R1` 仍 **pending**（本帽不签发）——**可交 00 代签 HG-AUDIT-R1**；pending 期间禁止下发 30 Prompt。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（00 代签 · 维护者 Prompt 授权 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
