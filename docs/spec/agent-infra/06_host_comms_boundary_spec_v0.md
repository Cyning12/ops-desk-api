# SPEC：Host C0 · 沟通边界（comms vs product）

> **层级**：L0 SPEC（agent-infra 轨 · 接 02/05 编号序列）  
> **状态**：`draft`（2026-09-01 10-spec 起草；待 20-spec-audit + HG-SPEC-SIGNOFF；**不**授权 30）  
> **上游**：[`00_architecture_and_boundaries.md`](./00_architecture_and_boundaries.md) · [`02_agent_host_plan_v0.md`](./02_agent_host_plan_v0.md)（H1–H5 已 **CLOSE** · 本 SPEC **不重开**）· 草稿 [`../../discussions/2026-08-31_host_comms_agent_kit_nesting_plan_draft.md`](../../discussions/2026-08-31_host_comms_agent_kit_nesting_plan_draft.md)（素材 · **真值以本 SPEC 为准**）  
> **本波 task**：[`task_host_comms_boundary_spec`](../../tasks/active/task_host_comms_boundary_spec.md)（active · docs-only · 无 30）  
> **spec_slug**：`host-comms-boundary-spec`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `host-comms-boundary-spec` |
| **test_strategy** | docs-only；无代码改动；验收 = 章节齐全 + 20-spec-audit pass + HG-SPEC-SIGNOFF |
| **graph_change_layer** | `none`（docs-only SPEC；不动图谱 · C1 实现波再同步） |
| **分支** | `task/host-comms-boundary-spec` |

### 人工闸（SPEC 波）

| human_gate_id | status | 说明 |
|---|---|---|
| HG-TASK-DRAFT | approved | 2026-09-01 · 00 代签 · 维护者 Prompt 授权（见 task 表） |
| **HG-SPEC-SIGNOFF** | **pending** | 待 **20-spec-audit** 落盘后 00 代签（docs-only SPEC 波代签授权：内容零阻塞 + 审查落盘） |
| HG-AUDIT-R1 | n/a | 本波 **无 30**（docs-only） |
| HG-GRAPH-MODULES | n/a | 无图谱变更 |

---

## 1. 背景

- **H1–H5 已 CLOSE**：[`02_agent_host_plan_v0.md`](./02_agent_host_plan_v0.md) 的 Host 计划（H1 Capability Gateway · H2 Policy · H3 Session · H4 PromptAssembly · H5 SkillRegistry）已收口；本 SPEC 是 C 轨 **沟通嵌套 coding-kit** 的边界签收，**不重开** H1–H5 任何结论。
- **草稿暂缓前提已达成**：上游草稿（2026-08-31）曾钉「暂缓开 C0（先 chat 废弃 + lg-rag 迁移联调）」。该前提已完成：T6 CLOSE（api [#108](https://github.com/Cyning12/ops-desk-api/pull/108) · chat/stream → 410 · 任务 [`task_lg_rag_deprecate_chat_stream`](../../tasks/done/task_lg_rag_deprecate_chat_stream.md)）；web T5 已 CLOSE（web #109）。维护者 Prompt 授权开 C 轨（串行波次 3）。
- **一句话**：一套 Process Kernel（coding-kit）+ Host PromptAssembly 多 Pack；沟通 Agent **全嵌套** 闸/task/verify；业务 lg-rag/Chat 只借鉴角色与策略，不全嵌套。C0 只签边界，**不写实现码**。

---

## 2. 范围

1. 本 SPEC 签收 C 轨边界：意图路由 · 产物路径 · 闸纪律 · Capability 白名单 · Skills≠verify · session 隔离 · C1–C4 波次表 · 风险 · failure_paths · 验收。
2. 上游草稿随本 PR 合入 master（作素材；语义冲突处 **以本 SPEC 为准**）。
3. 20-spec-audit 审查文落盘 + HG-SPEC-SIGNOFF 签收（00 代签 · 维护者 Prompt 授权）。
4. `lint-wiki-delta` PASS；`app/` · `tests/` 零改动。

## 3. 非范围

- C1–C4 **任何实现码**（Capability / PromptAssembly / 受控写盘 / UI）。
- 改 05 freeze 契约 `lg-rag-sse-v1` **任何字段**；不回写 05（见 §16 freeze 声明）。
- 改产品 Chat / lg-rag 行为；重开 H1–H5。
- web `/obs` 实现（C4 另 task · 跨仓）。
- **永久禁令 A：通用 shell Capability**——任何波次不得以「通用 shell / 任意 npx 执行」Capability 代替白名单；本禁令不随版本解除，修订须经维护者显式改本行。
- **永久禁令 B：模型代签 human_gate**——Host 沟通 Agent **永不** 签发任何 human_gate（含 `HG-SPEC-SIGNOFF` / `HG-AUDIT-R1` / `HG-GRAPH-MODULES` 等现列与未来新增）；本禁令不随版本解除。
- 动态 StateGraph compile、以兼容 chat 为验收条件等 00 已钉非目标，继续沿用。

---

## 4. 意图路由（comms vs product）

| 项 | 钉死 |
|---|---|
| **默认** | **product**（业务答 / lg-rag 路径）。无显式信号时一律 product。 |
| **comms 判定** | 显式意图信号（如「立项 / 开 task / 写 SPEC / 拆波次 / 走 harness 流程」类措辞，或等价的结构化 UI 入口）→ 路由到 **comms Pack**。 |
| **回退** | 判定不确定或 **误判** → **回退 product**；宁可漏进 comms，不可把业务答误入立项流程。 |
| **误判处理** | 用户在 comms 会话内表明为业务问题 → 交还 product 路径（**跨 session**，不就地混答）；在 product 会话内表明为立项意图 → 提示切到 comms 入口（C4 UI 前的过渡形态：提示文案即可）。 |
| **实现波** | 具体判定器（关键词 / 分类节点 / UI 入口）随 C2 task 定；本 SPEC 只钉 **默认 product + 显式进 comms + 误判回退 product** 三条。 |

## 5. 产物路径

| 项 | 钉死 |
|---|---|
| comms 写盘 | **仅** `docs/tasks/`（active/draft）+ invoke 草稿（`docs/harness/invokes/by-task/`） |
| 禁写 | `app/`（**永久**）；`tests/`；图谱 yaml；05/02 等 SPEC 正文（SPEC 修订走 10-spec 流程，非 comms 写盘） |
| C3 边界 | 受控写盘：写盘 allowlist 仅上述两目录；dry-run 默认；人确认后落盘——C3 task 细化，**边界在本 SPEC（C0）钉死** |
| product Pack | 不写 harness 文档（不动 task/invoke/SPEC） |

## 6. 闸纪律

| 项 | 钉死 |
|---|---|
| 禁代签 | 沟通 Agent 输出现「已签收 / approved / 已代签」字样 → 违规；可输出「待人签」提示与缺失闸清单。 |
| 闸真值 | human_gate 状态 **SoT 在 task 表**（`docs/tasks/active/task_*.md` 人工闸节）；非聊天字面、非 invoke 字面、非模型记忆。 |
| 与 00 过程代签区分 | 「00 代签（维护者 Prompt 授权）」是 **人工授权流程**：维护者在人聊显式授权、00 按授权回填 task 表并留痕（日期 + 授权来源）。这 **不是模型自签**：无维护者 Prompt 授权 → 00 也不得签。comms Pack 模型 **无任何** 签闸权限，两事不得混淆。 |
| C3 前置 | 任何 task 文件落盘前必须 **人确认**（dry-run diff + 显式 yes）；落盘后 `task lint` 可跑。 |

## 7. Capability 白名单

| Capability | 语义 | Policy 默认 |
|---|---|---|
| `harness.verify` | `npx dsh-coding-kit@<pin> verify --target . --task <path> --json` | **默认关**（block → `policy_blocked`） |
| `harness.task_lint` | `task lint` / `lint-wiki-delta` | 默认关 |
| `harness.status` | （可选）status/timeline JSON → obs 投影 | 默认关 |

| 钉死项 | 内容 |
|---|---|
| 白名单 | **仅 `harness.*`** 上述三条；新增须 SPEC 修订 |
| 通用 shell | **禁止**（§3 永久禁令 A）；含「可传任意命令的 npx 封装」 |
| kit 版本钉 | env 钉 `DSH_CODING_KIT_VERSION`（C1 落地；无 env 时 Capability 不可用而非静默漂版） |
| 测试 | mock subprocess + fixture JSON；CI 不断网装 npm |
| 实现波 | C1（`host-harness-cli-capability`）**必做**；不得以 Skill 替代（见 §8） |

## 8. Skills ≠ verify（明文）

- Skill（`docs/skills/` 人读短提示，如 delegate-only / re-anchor）是 **提示层纪律**，**不是机械闸**。  
- 机械闸 = CLI Capability（`harness.verify` / `task_lint`）+ task 表真值 + CI。  
- **C1 CLI Capability 必做**；任何波次不得以「已加载 Skill」宣称 verify 已完成，Skill 输出不得当作闸状态来源。

## 9. session 隔离

| 项 | 钉死 |
|---|---|
| 分 session | comms 与 product **分 thread/session**；互不注入对方历史 |
| 共用 | 可共用 **CapabilityGateway**（同一内核） |
| 不共用 | **不共用** system prompt / Pack；业务答与立项流不混线 |

## 10. C1–C4 波次表

| 波 | slug（建议） | 形态 | 内容 | 依赖 |
|---|---|---|---|---|
| **C0** | `host-comms-boundary-spec` | docs-only SPEC | 本文件 | T6 CLOSE ✓ · 草稿 ✓ |
| **C1** | `host-harness-cli-capability` | 实现 task | `harness.verify` / `task_lint`（+ 可选 `status`）；Policy 默认关；env 钉 `DSH_CODING_KIT_VERSION` | H2 ✓ · 本 SPEC 签收 |
| **C2** | `host-comms-prompt-pack` | 实现 task | PromptAssembly `pack=comms`：槽位 = kit FRAGMENT_00_delegate + task 模板字段清单 + 对话策略；意图路由判定器 | H4 + kit ≥1.10 FRAGMENT · C1 |
| **C3** | `host-comms-task-writer` | 实现 task | 受控写盘：allowlist 仅 `docs/tasks/active|draft` + invoke 草稿；dry-run 默认；人确认落盘 | C1 + C2 |
| **C4** | `host-obs-comms-ui` | web task（跨仓） | `/obs`：fixture → 真 status +「发起沟通」入口 | C1 status · 可与 C3 尾并行（**仅 web 侧**） |

| 顺序钉 | 内容 |
|---|---|
| 串行 | **C1 → C2 → C3** 顺序钉死，不可颠倒、不可合并开工 |
| 并行例外 | **C4 可与 C3 尾并行**，**仅 web 侧**（ops-desk-web 另 task）；api 侧仍 C1→C2→C3 串行 |
| 依赖 | 每波开工前其「依赖」列全部 CLOSE/签收；HG-AUDIT-R1 按实现波各自走 |

## 11. 待拍板（建议钉 · 随 HG-SPEC-SIGNOFF 一并签收）

| 草稿条目 | 本 SPEC 建议钉 |
|---|---|
| 草稿 §8.2 写盘落点 | **api 仓 `docs/tasks/`**（不迁 workspace 统筹） |
| 草稿 §8.3 `/obs` | **`/obs` 作 comms UI 主入口**（C4 跨仓 web task；不另开独立路由） |

签收方式：随 **HG-SPEC-SIGNOFF** 一并签收；维护者异议 → 走 **SPEC 修订**（10-spec 流程），不口头漂移。

## 12. 风险表

| 风险 | 缓解 |
|---|---|
| 模型代签 approved | §3 永久禁令 B + §6 闸纪律 + C3 写盘前人确认；闸真值在 task 表 |
| 任意 npx / shell | §3 永久禁令 A + §7 白名单 + Policy 默认关 |
| Skills 误以为够用 | §8 明文：Skills≠verify；C1 必做 |
| 00 亲自改 `app/` | Host comms **无** 写 `app/` 工具；写盘 allowlist 仅 docs/tasks + invoke |
| 意图误判 | §4 默认 product + 显式进 comms + 回退 product |
| 上游草稿漂移 | 真值以本 SPEC（master 版）为准；草稿仅素材 |
| kit 版本漂移 | `DSH_CODING_KIT_VERSION` env 钉；无 env 不可用而非静默漂 |

## 13. failure_paths

| 触发 | 期望行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 模型试图代签 human_gate | SPEC 禁令；comms 输出「待人签」；闸真值在 task 表 | — | SPEC 条文 |
| 范围蔓延到实现（C0 波出现 `app/` diff） | PR 检查拦截；非范围钉死 | — | PR 检查 |
| 上游草稿与本 SPEC 冲突 | 以本 SPEC 为准；草稿不回写 | — | — |
| 意图误判 comms/product | 回退 product；跨 session 交还 | 是 | C2 联调 |
| kit env 未钉 / 版本不符 | Capability 报不可用；不静默跑漂版 CLI | 是（补 env 后） | C1 验收 |
| Policy 默认关时调用 harness.* | `policy_blocked`；显式开后方可执行 | 是 | C1 验收 |
| C3 写盘未经人确认 | 不落盘；仅 dry-run diff | 是 | C3 验收 |

## 14. 验收

- [ ] 本 SPEC 存在且章节齐全（背景 / 范围 / 非范围 / 意图路由 / 产物路径 / 闸纪律 / Capability 白名单 / Skills≠verify / session 隔离 / C1–C4 波次表 / 待拍板建议钉 / 风险 / failure_paths / 验收 / 思考轮 / freeze 声明 / 修订记录）
- [ ] 00 定夺全部钉死项落入正文（意图路由默认 product · 产物路径仅 docs/tasks+invoke · 禁代签 · 白名单仅 harness.* · Skills≠verify · 分 session · C1→C2→C3 顺序 · 待拍板建议钉）
- [ ] 草稿 `2026-08-31_host_comms_agent_kit_nesting_plan_draft.md` 在 master（本 PR 携带）
- [ ] `docs/harness/reviews/` 落 20-spec-audit 审查文且结论 **pass**
- [ ] HG-SPEC-SIGNOFF=approved（00 代签 · 维护者 Prompt 授权 · 审查落盘后）
- [ ] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` PASS
- [ ] `app/` · `tests/` 零改动（diff 为空）

---

## 15. 思考轮控制（10-spec 回填）

| 轮 | 结论 |
|---|---|
| **R0** | 读 task（00 定夺钉死）+ 上游草稿 + 02（H1–H5 CLOSE）+ 00/05 风格；C 轨授权来自维护者 Prompt；草稿「暂缓 C0」前提已达成（T6 #108 · web T5 #109） |
| **R1** | 范围 = 边界签收六项 + 波次表；非范围 = C1–C4 实现码、05 freeze、Chat/lg-rag 行为、web `/obs` 实现、两条永久禁令单列 |
| **R2** | 方案对比：A 全嵌套 kit（comms Pack · 选）vs B 业务 Chat 每轮跑完整 10→30（弃 · 与草稿一致 · 不挡产品主线）；C 通用 shell 代替白名单（弃 · 永久禁令 A） |
| **R3** | 边界/失败路径：默认 product 防业务答误入立项；代签为永久禁令；写盘 allowlist 收窄到两目录；kit env 钉防漂版；session 隔离防混线；依赖 H1–H5 CLOSE 不回退 |
| **R4** | 验收 = 文档级（章节齐全 + 定夺落入 + audit pass + 人签 + lint + app/tests 零 diff）；实现可测性（policy_blocked / dry-run / mock subprocess）留给 C1–C3 task |
| **R5** | SPEC 可交 20-spec-audit 书面审；通过后 00 代签 HG-SPEC-SIGNOFF；下一棒 00 起草 C1 task |

| 项 | 值 |
|---|---|
| early_stop | no |
| residual_risks | C2 意图判定器形态未冻（C2 task 定）；`/obs` 主入口建议钉依赖 HG-SPEC-SIGNOFF 一并签收；kit FRAGMENT_00_delegate 落地依赖 kit ≥1.10 版本同步 |

## 16. freeze 声明

- **本 SPEC 不改 freeze `lg-rag-sse-v1` 任何字段**；05 各节（含 §4.2 / §9 / §10）**不回写**。  
- 本 SPEC 自身无新 freeze_id；C1 起若出现新契约（Capability 入参/出参 JSON），由对应实现 task 定义 freeze，不在本 SPEC 预冻。

## 17. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **10-spec 初稿**：背景（H1–H5 CLOSE · 暂缓前提达成）· 00 定夺逐项落入（意图路由默认 product · 产物路径 · 禁代签 · 白名单仅 harness.* · Skills≠verify · 分 session · C1→C2→C3 顺序 · C4 并行仅 web · 待拍板建议钉）· 永久禁令 A/B · R0–R5 回填 · freeze 声明（05 不回写） |
