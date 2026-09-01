# SPEC Audit R1：host-comms-boundary-spec（Host C0 · 沟通边界 comms vs product）

> **hat_id**：20-spec-audit  
> **SPEC**：`docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`（draft · C0 · docs-only · **不授权 30**）  
> **task 锚**：`docs/tasks/active/task_host_comms_boundary_spec.md`（active · 00 定夺 + 验收标准）  
> **对照素材**：`docs/discussions/2026-08-31_host_comms_agent_kit_nesting_plan_draft.md`（素材 · 随本 PR 合入）· `docs/spec/agent-infra/02_agent_host_plan_v0.md`（H1–H5 CLOSE · 确认无重开）  
> **日期**：2026-09-01 · 审查人：20-spec-audit  
> **分支**：`task/host-comms-boundary-spec`（实证 ✓ · 审查全程未切换 · 未 push）

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10-spec · 无「必须退回 00 改钉」级问题 |
| **流程闸** | `HG-SPEC-SIGNOFF` **仍 pending**（正确 · 20 不签发）· `HG-TASK-DRAFT` 已 approved（00 代签 · 维护者 Prompt 授权） |
| **签收建议** | **可交 00 代签 HG-SPEC-SIGNOFF**（docs-only SPEC 波代签授权两前提均满足：**内容零阻塞** + **审查落盘**=本文件）；本帽不签发、不附任何实现 Prompt |

---

## 审查核对

### A. 00 定夺 11 项逐项落入 SPEC（对照 task「00 定夺」表 L50–60 · 无软化）

| # | 00 定夺项 | SPEC 落点 | 结果 |
|---|---|---|---|
| 1 | slug=`host-comms-boundary-spec` | 头部 L7 + Harness 元信息 L15 | ✅ 一致 |
| 2 | SPEC 落点 `06_host_comms_boundary_spec_v0.md`（接 02/05 编号序列） | 文件实证存在；`docs/spec/agent-infra/` 目录 00–06 编号连续无冲突 | ✅ |
| 3 | 草稿为素材随本 PR 合入 master · 语义冲突**以 SPEC 为准** | §1 L34 · §2.2 L42 · §12 风险表 L150；git diff 实证草稿以 `A` 在本分支 | ✅ |
| 4 | 意图路由：默认 **product** · 显式意图进 **comms** · 误判**回退 product**（写清判定与回退） | §4 L62–66 | ✅ **无软化且收紧**：不确定亦回退 product（「宁可漏进 comms，不可把业务答误入立项流程」L64）；误判跨 session 交还不就地混答（L65）；判定器形态明留 C2（L66）不越权预冻 |
| 5 | 产物路径：comms 写盘**仅** `docs/tasks/`（active/draft）+ invoke 草稿 · **禁写 `app/`** · C3 边界在 C0 钉死 | §5 L72–75 | ✅ 禁写 `app/` 标「**永久**」（L73）；C3 受控写盘 allowlist/dry-run/人确认三要素边界钉在 C0（L74） |
| 6 | 禁代签 · 闸真值在 task 表 · 与「00 过程代签」区分写明 | §3 永久禁令 B（L53）· §6 L81–83 | ✅ 区分无混淆：「00 代签 = 人工授权流程（维护者人聊显式授权 + 00 回填留痕）**不是模型自签**；无维护者 Prompt 授权 → 00 也不得签；comms Pack 模型无任何签闸权限」（L83）；违规字样判定具体（L81「已签收/approved/已代签 → 违规」） |
| 7 | Capability 白名单**仅 `harness.*`** · 禁通用 shell · Policy **默认关** · kit 版本 env 钉 `DSH_CODING_KIT_VERSION`（C1 落地） | §7 L90–100 · §3 永久禁令 A（L52） | ✅ 三条 Capability（verify/task_lint/status）均「默认关 → `policy_blocked`」；「仅 harness.* · 新增须 SPEC 修订」（L96）；通用 shell 禁令含「可传任意命令的 npx 封装」封堵绕过（L97）；无 env 时「Capability 不可用而非静默漂版」（L98） |
| 8 | Skills≠verify 明文 · C1 CLI Capability **必做** · 不得以 Skill 替代 | §8 L104–106 | ✅ 「Skill = 提示层纪律，不是机械闸」「任何波次不得以『已加载 Skill』宣称 verify 已完成」（L106） |
| 9 | comms/product **分 thread/session** · 共用 CapabilityGateway · **不共用** system prompt | §9 L112–114 | ✅ 三项全钉 |
| 10 | C1–C4 波次表（slug/形态/依赖）· 顺序钉死 **C1→C2→C3** · C4 可与 C3 尾并行**仅 web 侧** | §10 L118–130 | ✅ 「不可颠倒、不可合并开工」（L128）；并行例外收窄到 web 侧且 api 侧仍串行（L129）；每波依赖列 CLOSE/签收前置（L130） |
| 11 | 待拍板建议钉：写盘落点=**api 仓 `docs/tasks/`** · `/obs` 作 comms UI 主入口（C4 跨仓）· 随 HG-SPEC-SIGNOFF 一并签收 · 异议走 SPEC 修订 | §11 L134–139 | ✅ 两条建议钉 + 签收方式 +「不口头漂移」（L139） |

### B. 非范围与两条永久禁令

| 审查点 | 结论 |
|---|---|
| §3 含**永久禁令 A**（通用 shell Capability） | ✅ L52：「任何波次不得以通用 shell/任意 npx 执行 Capability 代替白名单 · 本禁令不随版本解除 · 修订须经维护者显式改本行」——与 §7 L97 互钩 |
| §3 含**永久禁令 B**（模型代签 human_gate） | ✅ L53：「Host 沟通 Agent **永不**签发任何 human_gate（含现列与未来新增）· 不随版本解除」——覆盖未来新增闸，无枚举逃逸口 |
| 非范围与 task 非范围一致 | ✅ C1–C4 实现码 · 05 freeze 字段 · Chat/lg-rag 行为 · 重开 H1–H5 · web `/obs` 实现逐条对应（SPEC L48–54 ↔ task L73–77）；task 非范围仅列禁令 A、禁令 B 由其 00 定夺行承载，SPEC 双列属收紧非冲突 |
| 02 非目标承接 | ✅ 「动态 StateGraph compile · 以兼容 chat 为验收条件」继续沿用（SPEC L54 ↔ 02 L48/L52） |

### C. 思考轮 R0–R5 控制节合法性（§15）

| 审查点 | 结论 |
|---|---|
| R0–R5 六轮回填 | ✅ L181–186 全填；R2 方案对比含被弃项及理由（B 业务每轮跑完整 10→30 弃 · C 通用 shell 弃→禁令 A）；R3 边界/失败分析逐条对应正文；R5 指明下一棒（20-spec-audit → 00 代签 → C1 task） |
| early_stop 判定 | ✅ L190 `early_stop=no`：未提前停轮，六轮全跑与判定一致，无「停轮却缺轮」矛盾 |
| residual_risks 非空诚实 | ✅ L191 列三项真实残余（C2 意图判定器形态未冻留 C2 task · `/obs` 主入口建议钉依赖本次签收 · kit FRAGMENT_00_delegate 依赖 kit ≥1.10 同步）——均为如实留白且正确指向后续波次/本次签收口，不构成 C0 边界签收阻塞 |

### D. freeze 声明与 05 不回写（§16）

| 审查点 | 结论 |
|---|---|
| 不改 `lg-rag-sse-v1` 任何字段 · 05 各节不回写 | ✅ L195 明文；freeze id 在 05 实证存在（05 L138/L152/L225）；与 task 非范围 L74 一致；git diff 实证 05 零改动 |
| 自身无新 freeze · 不预冻 C1+ 契约 | ✅ L196：Capability 入参/出参 JSON 由实现 task 各自定义 freeze——避免在边界 SPEC 预冻未实现契约，合理 |

### E. 与 02 H1–H5 边界无重叠/重开 · C 轨定位

| 审查点 | 结论 |
|---|---|
| H1–H5 状态 | 02 实证：状态 `completed` · H1–H5 全轨 CLOSE（02 L4/L96–102/L166） |
| SPEC 不重开声明 | ✅ 头部 L5 + §1 L33「不重开 H1–H5 任何结论」；§10 依赖列仅把 H2/H4 作 **CLOSE 前置**引用（C1←H2 · C2←H4），不重定义 H 模块内容，无重叠解释空间 |
| C 轨定位=沟通嵌套 kit | ✅ §1 L35「一套 Process Kernel + 多 Pack；沟通 Agent 全嵌套闸/task/verify；业务 lg-rag/Chat 只借鉴」——与草稿 §0 一致；草稿「暂缓 C0」前提（T6 #108 · web T5 #109）经 commit 实证（`bde05a4` #108 合入 · `3cc1804` #109 合入 · `d03708b` T6 归档 done/） |

### F. failure_paths 与风险表可执行性（§12/§13）

| 审查点 | 结论 |
|---|---|
| failure_paths 非套话 | ✅ 七行均「具体触发 → 具体期望行为」：`policy_blocked` 错误语义 · dry-run diff 未确认不落盘 · env 未钉「Capability 报不可用而非静默跑漂版」 · C0 波 `app/` diff 由 PR 检查拦截；「可重试/用户可见」列填具体去向（C1/C3 验收 · C2 联调），可执行可验收 |
| 风险表映射条文 | ✅ 七行风险每行缓解指向具体章节/机制（禁令 A/B · §6–§9 · env 钉 · 默认 product 回退），无「加强管理」式空转 |

### G. 验收标准客观可判定（§14）

七条全部可客观判定：章节齐全（可数 · 本帽逐节核对 ✓）· 00 定夺落入（本核对表 A 区逐条可查）· 草稿在 master（git 可证 · 本分支已 `A`）· 审查文落盘 pass（=本文件）· HG-SPEC-SIGNOFF=approved（task 人工闸表可查）· `lint-wiki-delta` PASS（命令可跑 · **本帽复跑 exit 0 · scanned=99 · issues=0**）· `app/`/`tests/` 零改动（`git diff master...HEAD` 实证仅 docs 文件）。

### H. 实证核查（本帽独立复核 · 非转述 10 自检）

| 项 | 结果 |
|---|---|
| 分支 | `task/host-comms-boundary-spec` ✓（未切换 · 未 push） |
| `git diff --name-status master...HEAD` | 仅 6 个 docs 文件（草稿 A · 00/10 invoke A · SPEC 06 A · task A · tasks/active/README M）；`app/` · `tests/` **零改动** ✓ |
| 编号序列 | `docs/spec/agent-infra/` 00–06 连续，06 无冲突 ✓ |
| invoke 留档 | `docs/harness/invokes/by-task/host-comms-boundary-spec/` 00 + 10-spec 双落盘 ✓ |
| `lint-wiki-delta` 复跑 | PASS（exit 0 · scope=all · scanned=99 · issues=0）✓ |
| 人工闸表状态 | SPEC 表（L22–27）与 task 表（L38–42）一致：HG-SPEC-SIGNOFF=pending · HG-AUDIT-R1=n/a（无 30）· HG-GRAPH-MODULES=n/a ✓ |
| T6/web T5 前提 | `docs/tasks/done/task_lg_rag_deprecate_chat_stream.md` 存在 ✓ · #108/#109 merge commit 实证 ✓ |

---

## 阻塞

无。

---

## 非阻塞观察（不退回 10-spec · 00/后续波知情即可）

1. **§14 验收条 2 的钉死项列举为代表性非穷举**：该条列 8 项（未单列 Policy 默认关 / env 钉 / C4 并行条件字样），但三者作子项在 §7/§10 正文钉死（L90–98/L129），且本审查 A 区已按 11 项全量核对——勾选时以「正文全量落入」为准即可，不改条文。
2. **§13「意图误判」行「用户可见=C2 联调」为压缩写法**：语义是「可见性验证点留 C2 联调」，可解读无歧义，不阻塞。
3. **签收后的文档回填提醒**：HG-SPEC-SIGNOFF 代签时，SPEC 头部状态行（L4 `draft`）与两处人工闸表需同步回填 + 修订记录追行——属签收留痕动作、非改钉，由 00/10-spec 按既有惯例处理。

---

## 回填清单

无（内容零阻塞 · **不改 SPEC 实质** · **不改**人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-SPEC-SIGNOFF` 仍 **pending**（本帽不签发）——**可交 00 代签 HG-SPEC-SIGNOFF**（维护者 Prompt 授权 docs-only SPEC 波代签：内容零阻塞 + 审查落盘，两前提均满足）。签收后下一棒：00 起草 C1 task（`host-harness-cli-capability` · 依赖 H2 ✓ + 本 SPEC 签收）。

---

## 维护者签闸（20 后 · C1 task 起草前）

- [ ] 已读 R1 审查结论
- [ ] 跑机械闸 `npx dsh-coding-kit verify --spec docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`（审查文存在性）
- [ ] 在 task 人工闸表 + SPEC 人工闸表将 HG-SPEC-SIGNOFF 改为 approved（00 代签 · 维护者 Prompt 授权 · 日期）
- [ ] SPEC 状态行 draft → 签收态 + 修订记录回填 · commit
- [ ] PR 合入（本 PR 携带 discussions 草稿入 master · 语义冲突以 SPEC 为准）
- [ ] 00 起草 C1 task（HG-AUDIT-R1 按实现波各自走）
