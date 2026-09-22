# SPEC：画像记忆（kind=preference · 首期只收显式声明）（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved**（2026-09-22 · 维护者授权 00 本窗签收全部过程文档 · 原话「此spec完成后继续把完成后续spec，一个个进行，每次PR到main通过CI后自动merge」承前令「授权00签收所有过程文档」） · 人签前不出 task / 不改码）
> **track**：`feature`（新 kind + 新召回渲染语义 + **有 alembic 义务**（CHECK 放宽）· 图谱零变更按实判见 §2 D5）
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 §1.2.4 画像记忆 ❌ · §1.3 四问 · §1.8 红线③）
> **格式基准**：`docs/spec/prompt-asset-roadmap/SPEC-prompt-asset-roadmap_v1.md`（signed · 2026-09-22）
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 实现
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `memory-preference-profile` |
| **invoke_slug** | `memory-preference-profile`（单 task · 波次裁定见 §2） |
| **test_strategy** | `required` |
| **test_strategy_note** | 闸判据单测（新原因码按码断言，沿用 gate 先例）· 注入分节结构断言（无偏好 → 偏好节物理不存在）· supersede/revoke 状态机断言（沿用 P0 否定性断言范式）· 幻觉偏好红线离线金样（evals/ · 热路径零 LLM-as-judge）· 变异检验三条（见 §6）· alembic upgrade head + 全量 pytest 绿 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/memory-preference-profile` |
| **graph_change_layer（建议）** | 无（**零图谱变更按实判**：不新增路由/表/事件类型/一级模块；改动面 = `app/ops/memory/**` 模块内 + `lg_rag/continuity.py` 渲染/装配 + `db/models.py` CHECK 常量 + alembic 迁移文件（migrations 既有面）。若 30 形态偏离（新增路由/表/事件/一级模块）→ 回 10-spec 修订并补 HG-GRAPH-MODULES 行） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved** | 2026-09-22 · 维护者授权 00 本窗代录签收（原话留痕头部状态行） |

---

## 1. 背景与目标

### 现状（2026-09-22 实扫 · 锚点逐个核）

**记忆四层中画像层仍空（手册 §1.2.4）。P0/P1 已在 kind 位预留画像入口，但闸、CHECK、召回渲染三面全锁 fact。**

| 锚点 | 实扫结论 |
|---|---|
| `app/ops/memory/gate.py` | `ALLOWED_KIND = "fact"`（:27）；kind ≠ fact → `kind_not_allowed` 拒写（:103-104 · docstring :12「preference 属画像，P1+」）；`FactCandidate.kind` 字段已预留（:89 · 默认 fact）。其余判据（主体/稳定 key/易失前缀/标量值/长度）与 kind 正交可复用 |
| `app/db/models.py` | `kind` 列**已存在**（:501 · String · default 'fact'）；但 `CheckConstraint("kind = 'fact'")`（:470 · `ck_ops_memory_facts_kind`）物理锁死；alembic `20260921_memory_facts.py:37,48` 同 CHECK 落库——**放开 preference 必须改 CHECK（有 alembic 义务）** |
| `app/ops/memory/extract.py` | 抽取 prompt **已资产化**：`render("memory.extract.system")`（:105）→ `app/ops/prompts/assets/memory.extract.system.md`（v1 · 「你是事实抽取器」· 规则只讲稳定事实，零偏好语义）；schema `ExtractedFactItem` 仅 key/value **无 kind 字段**（:47-51）；构造点 `FactCandidate(...)` 默认 kind=fact（:129-131）——**抽取管道物理产不出 preference，首期保持这一形态即"显式-only"的落点之一** |
| `app/ops/memory/service.py` | supersede 同事务（`_write_in_session` :49-76）：查重谓词 `(tenant_id, user_id, key, status=active)` **不含 kind**（:53-58）；`revoke_by_source` 按 source_run_id 一键全撤（:128-157 · 幂等 · 审计日志）——但显式写入 `source_run_id` 为空，**preference 纠错缺定位入口**；来源权重已有雏形 `SOURCE_WEIGHT_EXPLICIT=1.0 > SOURCE_WEIGHT_EXTRACTED=0.8`（:233-234 · `_source_weight` :340-342）；`recall_active`/:187-220 与 `_VECTOR_RECALL_SQL`/:237-245 均**无 kind 谓词** |
| 召回注入点 `app/ops/lg_rag/continuity.py` | `assemble_graph_messages_with_memory`（:187-244）召回 → `render_memory_facts_block`（:149-166）渲成**单一 `[已知事实]` 块**（key=value 一行一条）→ `inject_memory_facts_block` 作**独立 SystemMessage** 插前缀系统消息后（:169-184）；span `memory_facts_injected=N`（:240/:243）；开关 `MEMORY_FACTS_ENABLED` 默认 false（:105-115）；**现状无事实/偏好之分——闸放开后若不染渲染层，preference 会被当事实注入（静默错）** |
| `app/ops/memory/README.md` | key 首段域约定**已列 `pref`**（:21 「project / user / repo / pref …」）；非范围 :144 明示「画像 / preference」待本 SPEC 解锁；env 表、注入格式、故障语义为 P0/P1 真值 |

### 手册纪律合规论证（先事实型后偏好型 · §1.2.4）

手册 §1.2.4 纪律原文：「先做**事实型画像**……而不是**偏好型画像**——因为事实型画像**可验证**（能对着数据源核对），偏好型画像只能靠推断，错了没法发现。」本 SPEC 含偏好型（kind=preference），**合规路径 = 首期只收显式声明**，论证三点：

1. **纪律反对的是"只能靠推断"，不是"偏好"本身**。显式声明的偏好（用户原话："我以后要中文回答"）来源不是推断——它**可归因、可对着用户声明核对**，验证性与事实型等同。闸把推断型偏好**显式拒收**，正是把手册担忧的"错了没法发现"形态物理排除。
2. **先事实后偏好的顺序已被满足**：事实型画像（kind=fact · P0 显式写 + P1 抽取/向量召回）已签收上线，本 SPEC 是在其状态机/supersede/revoke/权重底座上做增量，不是绕过它另起炉灶。
3. **"错了能发现"先于功能上线**：幻觉偏好红线（§2 D4）与「写入→污染→撤销→消失」全链路变异检验（手册 §1.8）随本波一并交付，不留"先上功能后补评测"的窗口。

### 一句话目标

在 memory-facts P0/P1 底座上放开 `kind=preference`：**首期只收显式声明**（闸判据差异化 + 抽取管道物理不产偏好），召回注入**分节区分事实/偏好**，冲突走既有 supersede、纠错补 `revoke_by_key` 一键清除，并以**幻觉偏好红线**（无偏好记忆时不得编造 · 手册 §1.8 红线③扩展）结构断言 + 离线金样 + 变异检验为证。

---

## 2. 范围

**波次裁定：单 task（slug `memory-preference-profile`），四块不拆波。** 理由：① 四块是一个不可拆的语义单元——只放开闸不配注入区分 = 偏好污染事实通路（静默错）；不配红线评测 = 违反手册「先把"坏了能发现"装上，再让功能上线」（§1.8 :193）；② 耦合面小（闸纯函数增量 + 渲染分节 + 一个 service 入口 + 一个迁移），单 PR 不巨型；③ track 同为 feature，无混 track 问题。

### D1 · 闸放开 kind=preference + 判据差异化（必做）

| 项 | 约定 |
|---|---|
| 放开 | `ALLOWED_KINDS = {"fact", "preference"}`（gate.py:27 单常量放开为集合）；kind 不在集合 → `kind_not_allowed` 沿用 |
| 判据差异化 · 双向 key 域绑定 | `kind=preference` ⟺ key 首段 == `pref`（**双向**：preference 必须 `pref.` 前缀；`pref.` 前缀必须 kind=preference）· 违反 → 新原因码 `key_kind_mismatch`（入 `REJECT_REASONS` · 按码断言不按文案 · gate 先例）。域约定 README :21 已预留 `pref` |
| 判据差异化 · 显式-only 落点 | 闸是纯函数不感知来源，"显式-only"落在**写入通路**：preference 仅经显式 service API 调用构造（P0 同款通路）；**抽取管道产物永远 kind=fact**——extract.py 构造点（:129-131）钉死 + 单测断言 `MemoryFactExtraction` schema 无 kind 字段、构造候选 kind==fact。推断型偏好（行为推断）首期**无写入通路**，物理拒收 |
| 其余判据 | 主体/稳定 key/易失前缀/标量值/长度与 kind 正交，原样复用（preference 陈述是自然语言 str，过既有标量判据） |

**显式-only 裁定理由**（R2 层面，连同 §1 合规论证）：显式表达 > 行为推断（占位草案方向）——首期收显式声明的理由是**可验证性**：显式声明可对着用户原话核对（可验证 ⟺ 手册事实型同等级）；行为推断只能由模型/启发式产出，错了无任何核对面，正是 §1.2.4「错了没法发现」的形态。且推断型一旦入库会持续污染后续所有决策（§1.3 问三），纠正成本高。故首期以"无写入通路"物理排除推断型，而非"收了再筛"。

### D2 · 来源分级与权重 + 召回注入区分事实/偏好（必做）

| 项 | 约定 |
|---|---|
| 来源分级 | 沿用 `_source_weight`（service.py:340-342）：显式/人工（source_run_id 空）= 1.0 > 抽取 = 0.8。首期 preference **只有显式来源**（权重恒 1.0）；断言：融合排序中显式 preference 权重 == `SOURCE_WEIGHT_EXPLICIT`；0.8 权重路径对 preference 物理不存在（D1 通路约束的下游不变量） |
| 注入区分（方案 B1 · §4） | `render_memory_facts_block` 按 kind **分节**：`[已知事实]` 节（kind=fact）+ `[用户偏好]` 节（kind=preference · 带引导语「用户显式陈述的偏好，用于调整回应方式；非客观事实」）；仍**单条独立 SystemMessage**（inject_memory_facts_block :169-184 结构不变 · 不掺入任何 prompt 模板）；**无 preference → 偏好节物理不存在**（红线结构断言落点）；无 fact 且无 preference → 空串不注入（现行为沿用） |
| 召回 SQL | 不加 kind 谓词：`recall_active`/向量 SQL 结果集 ≤N（默认 8）小，渲染层按 kind 分节；**不新增索引**（既有 `idx_ops_memory_facts_recall` 覆盖主谓词） |
| 预算 | 统一预算 `MEMORY_FACTS_MAX_ITEMS` 内两节混排截断（融合排序不动）；preference 天然量少，不另切预算不新增 env——挤占风险列残余风险（§7） |
| 观测 | span metadata 增 `memory_preferences_injected=M`（与 `memory_facts_injected` 并列 · update_current_span_metadata 先例 · tracing 未开静默 no-op）；**不新增 SSE 事件类型**；SSE/用户面不输出原始偏好（README :51 纪律沿用） |

### D3 · 冲突与纠正（必做）

| 项 | 约定 |
|---|---|
| 偏好变更 = supersede | 同 `(tenant_id, user_id, key)` 新写 → 复用 `_write_in_session` 同事务 supersede（旧行 `superseded` 留表可审计 · 后写赢）；**查重谓词加 kind**（:53-58 谓词补 `kind == candidate.kind`）——跨 kind 不互相 supersede（D1 双向绑定是第一道，谓词含 kind 是防御第二道，防未来 key 域约定松动静默互冲） |
| 显式偏好一键清除 | 新增 `revoke_by_key(tenant_id, user_id, key)`：按 key 把 active 行置 `revoked`；**必带 tenant+user 谓词**（P0 纪律）；幂等（已 revoked 不动 · 重复调用影响 0 行）；审计日志记影响行数（revoke_by_source :154-156 同款）。存在理由：显式声明 `source_run_id` 为空，`revoke_by_source` 定位不到；合规删除权（手册 §1.3 四问四）要求用户可清除自己的偏好 |
| 推断型清除预留 | 未来若收推断型 preference，**必须带 `source_run_id`** → `revoke_by_source` 一键全撤现成可用；本 SPEC 只立此义务不立实现（推断型本体在非范围） |
| 物理删除 | 不做（P0 纪律：失效走状态机不物理删 · 旧值留表审计） |

### D4 · 幻觉偏好红线评测（必做 · 手册 §1.8 红线③扩展）

| 项 | 约定 |
|---|---|
| 红线语义 | **无偏好记忆时不得编造用户偏好**（§1.8 :240 原句扩展落地：记忆系统的引入本身会提高"编偏好"的先验） |
| 结构断言（deterministic） | 无 preference 行 → 注入块**无 `[用户偏好]` 节**（渲染层单测钉死）；有 preference → 偏好节出现且只含 preference 行 |
| 行为断言（离线金样） | 金样用例：无记忆用户问偏好相关问题 → 回答不得编造偏好；落点 `evals/`（仓内已有 golden/router 先例 · 具体文件 task 阶段定）；**热路径零 LLM-as-judge**（§1.8 :242 纪律） |
| 全链路变异检验 | 写入一条错误偏好 → 断言它**确实污染**回答（证明通路是通的，非空规则）→ `revoke_by_key` → 断言污染**消失**（§1.8 :241 范式 · 与「撤销成功可能是假通过」对偶） |
| prompt 侧防线 | 偏好节引导语明示「无偏好时不要假设/编造」；渲染常量（`MEMORY_FACTS_HEADER` 同款模块内常量先例），锚点断言（含「偏好」字样）而非全文快照（prompt-asset 先例：保证改文案不挂 CI） |

### D5 · 表结构 / alembic / 图谱（必做 · 按实判）

- **alembic 义务：有**。迁移放宽 CHECK：`ck_ops_memory_facts_kind` 从 `kind = 'fact'` 改 `kind IN ('fact','preference')`（drop + add constraint；存量行全 fact 零数据迁移；回滚须先清 preference 行——写入迁移文件注释）。models.py:470 同步。**不新增列、不新增索引**（kind 列与召回索引已存在 · D2 裁定 SQL 不加 kind 谓词）。
- **图谱零变更按实判**：不新增路由/表/事件类型/一级模块；改动面 = memory 模块内 + continuity 渲染 + models CHECK 常量 + alembic 迁移文件。若 30 形态偏离 → 回 10-spec 修订并补 HG-GRAPH-MODULES 行。`./scripts/graph-compile.sh` 绿（回归保险，非新增义务）。
- README 同步：`app/ops/memory/README.md` 非范围 :144 移除「画像 / preference」、env 表（无新 env · 如实记）、注入格式补偏好节样例、故障语义补新原因码；不回改 done/归档历史文档。

---

## 3. 非范围

- ❌ **推断型偏好**（行为推断 / LLM 抽取产 preference 候选）——首期物理拒收；未来另案 SPEC（届时自带 source_run_id + 低权重 + 新判据义务）
- ❌ 跨用户画像聚合；推荐系统（占位原文保留）
- ❌ 改事实型记忆语义（kind=fact 判据/召回/注入行为零变化 · 占位原文保留；注入块事实节渲染与现网逐字节一致）
- ❌ 对外 HTTP 写端点（沿用 P0/P1 非范围 · README :144；preference 写入同走内部 service API）
- ❌ 热路径/流中抽取（沿用 P1 非范围）；抽取 prompt 文案改动（memory.extract.system 保持事实抽取器语义 · 碰它是 prompt 资产化轨的事）
- ❌ 向量召回算法/权重调参（沿用 P1 初值与 R5 residual · 本 SPEC 只在渲染层分 kind）
- ❌ 物理删除（P0 纪律）；偏好管理 UI（web / ios 另案）
- ❌ 热度淘汰 / TTL 新机制（沿用既有 expires_at 双保险 · 手册四问四的另两层另案）
- ❌ 历史文档回改

---

## 4. 方案对比（R2）

### 召回注入区分事实/偏好（D2）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **B1 · 单 SystemMessage 双节（本 SPEC）** | 渲染函数按 kind 分 `[已知事实]` / `[用户偏好]` 两节，仍一条独立 SystemMessage 注入 | 注入点结构零变化（inject_memory_facts_block 单块先例原样复用）；无偏好 → 偏好节物理不存在 = 红线结构断言天然落点；引导语与数据同块，模型端边界强；消息序不增 | 渲染函数从单循环变分节（小改 · 单测可钉） | **推荐** |
| B2 · 两条独立 SystemMessage（事实块 + 偏好块） | 渲染两块、注入两条消息 | 隔离最彻底 | 每请求多一条消息；注入点要改双块逻辑（空块组合 4 态）；消息序更复杂收益不成比例 | 弃 |
| B3 · 单块行级标注（`[偏好] pref.x=y` 混排） | 现渲染循环内加行前缀 | 改动最小 | 事实/偏好边界只剩行级 token，模型把偏好当事实读的风险最高 = 偏好污染事实通路防不住；红线「无偏好节」断言无从落 | 弃 |

### 显式-only 的落点（D1）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **E1 · 通路约束 + 双向 key 域绑定（本 SPEC）** | 闸加 `key_kind_mismatch` 双向绑定；显式-only 由"抽取管道无 kind 字段 + 构造点钉死 fact + 无其他写入通路"保证 | 闸保持纯函数（不感知来源 · P0 设计哲学不动）；拒收是**物理**的（无通路）而非配置的；单测可钉 | "显式-only"不是闸内一条规则，纪律靠构造点单测 + 非范围共同维持（变异检验 ③ 补） | **推荐** |
| E2 · 闸内来源判据 | FactCandidate 加 `source` 字段，should_write 判 preference+推断 → 拒 | 闸内单点可见 | 纯函数被拖入来源语义；调用方照传不误则形同虚设；P0「判据在写入时判」的对象是候选内在属性，来源是通路属性 | 弃 |
| E3 · 首期就收推断型 + 低权重 | preference 放行推断来源，权重 0.5 压制 | 功能面大 | **直接违反 §1.2.4**（推断错了没法发现）；权重压制不了"错了不知道"，只会让它更难发现 | 弃 |

---

## 5. 边界 / 失败路径 / 安全（failure_paths）

| 触发 | 行为 | 可重试 |
|---|---|---|
| **幻觉偏好注入**（无 preference 行却渲染出偏好节） | **静默错**（模型看到空/编造偏好语义）；渲染层「空 preference 集 → 偏好节物理不存在」单测钉死 + 金样行为断言 + 引导语「无偏好不要假设」双保险 | Y（修渲染） |
| **偏好污染事实通路**（preference 行进 `[已知事实]` 节被当客观事实） | **静默错**；分节渲染单测钉死（含向量通路召回的 preference 也进偏好节断言）；引导语明示「非客观事实」 | Y（修渲染） |
| **清除后仍召回**（revoke_by_key 后该 key 仍注入） | **静默错**；召回只认 active 双保险（查询路径自带过滤）+ 全链路变异检验「写入→污染→撤销→消失」钉死；span/log 可对账 | Y（修查询） |
| CHECK 未迁移写 preference（migration 未跑） | insert 违反 `ck_ops_memory_facts_kind` → IntegrityError **显式炸**（非静默）；验收含 `alembic upgrade head` + 写 preference 通路冒烟 | Y（跑迁移） |
| 跨 kind 静默互冲（同 key fact 与 preference 互相 supersede） | **静默错**；第一道：双向 key 域绑定（`key_kind_mismatch`）；第二道：supersede 查重谓词加 kind——双保险，断言跨 kind 同 key 两行各自 active 互不影响 | Y（修谓词） |
| 抽取管道误产 preference（未来改动给抽取候选传 kind） | 闸双向绑定兜（非 pref. key + preference → 拒）；构造点单测钉死 kind==fact；schema 无 kind 字段 = 结构化输出层面也产不出 | Y（改回） |
| key 域漂移（fact 用 `pref.` 前缀 / preference 用非 pref 前缀） | `key_kind_mismatch` 拒写不落库 + GateRejectedError 原因码（调用方不得静默吞 · P0 纪律） | Y（改调用方） |
| 偏好挤占事实预算（统一预算下 preference 多致 fact 被截） | 首期 preference 量少 + span 双计数（facts/preferences injected）可观测；列残余风险不列验收（§7 ①） | — |
| revoke_by_key 跨 tenant / 幂等 | 必带 tenant+user 谓词（跨 tenant = 0 行）；重复调用影响 0 行幂等返回，审计日志仍记 `affected=0`（revoke_by_source 同款） | Y |
| 引导语/节名被改坏（偏好节文案失去「偏好/非事实」语义） | 锚点断言（注入块含「用户偏好」节名与「非客观事实」级锚点）必挂 CI；非全文快照（改文案不挂） | Y（改文案） |
| 召回 DB 故障 / 向量通路故障 | 沿用现行为：`memory_degraded` / `memory_vector_degraded` 降级不注入/回退确定性，不拖垮 chat（continuity :235-238 · service :450-457）——本 SPEC 零改动 | Y |

安全：无新凭证面/网络面；不新增对外端点；偏好内容经同一 SystemMessage 结构隔离注入（不掺入 prompt 模板 · 注入面与现状同构）；身份（tenant/user）取自请求上下文纪律不变，模型产出不得参与（README :50 沿用）。

---

## 6. 验收标准（单 task 直接可用）

### D1 · 闸放开与判据差异化

- [ ] `ALLOWED_KINDS = {"fact", "preference"}`；kind 集合外 → `kind_not_allowed`（按码断言）
- [ ] 双向绑定单测：preference+非 pref. key / fact+pref. key / 非 pref. key+缺省 kind → `key_kind_mismatch`；preference+`pref.*` key → 放行
- [ ] 新原因码入 `REJECT_REASONS`；闸拒 = 不落库 + `GateRejectedError`（沿用）
- [ ] 抽取管道单测：`MemoryFactExtraction` schema 无 kind 字段；构造候选 kind==`fact`（extract.py 构造点钉死）
- [ ] kind=fact 全部既有判据回归绿（P0/P1 闸单测零变化通过）

### D2 · 来源分级与注入区分

- [ ] 融合排序断言：显式 preference 来源权重 == `SOURCE_WEIGHT_EXPLICIT`（1.0）
- [ ] 分节渲染单测：fact 行进 `[已知事实]` 节、preference 行（含向量通路召回者）进 `[用户偏好]` 节、互不串节
- [ ] **无 preference → 注入块无 `[用户偏好]` 节**（红线结构断言）；空集 → 空串不注入（现行为）
- [ ] 注入仍单条独立 SystemMessage，位置语义不变；kind=fact 节渲染与现网**逐字节一致**（对拍断言）
- [ ] span metadata `memory_preferences_injected` 与 `memory_facts_injected` 分别计数；SSE 零新事件类型
- [ ] 锚点断言：偏好节含「用户偏好」「非客观事实」级锚点（非全文快照）

### D3 · 冲突与纠正

- [ ] supersede 谓词含 kind：跨 kind 同 key 两行各自 active 互不影响（双保险断言）；同 kind 同 key 新写 → 旧行 superseded + 召回零命中（沿用 P0 否定性断言范式）
- [ ] `revoke_by_key`：active → revoked；必带 tenant+user 谓词；幂等 0 行；审计日志记 affected；**清除后召回零命中 + 注入块无该 key**
- [ ] 物理删除零发生（状态机断言沿用）

### D4 · 幻觉偏好红线

- [ ] 结构断言（见 D2 无偏好无节）
- [ ] 离线金样：无记忆用户偏好类提问 → 回答无编造偏好（evals/ 落点 · 热路径零 LLM-as-judge）
- [ ] **全链路变异检验**：写入错误偏好 → 断言污染出现 → `revoke_by_key` → 断言污染消失（三态全断言，缺第一态不算过）

### D5 · 表结构 / alembic / 图谱 / 文档

- [ ] alembic 迁移：CHECK 放宽 `kind IN ('fact','preference')`；`alembic upgrade head` 后 preference 写入通路冒烟过；回滚注释含"先清 preference 行"
- [ ] 无新增列/索引；`./scripts/graph-compile.sh` 绿；图谱零变更裁定与实现形态一致（偏离 → 本 SPEC 回炉）
- [ ] `app/ops/memory/README.md`：非范围移除「画像 / preference」、注入格式补偏好节样例、故障语义补 `key_kind_mismatch` 与 `revoke_by_key`

### 变异检验（不验收空真规则）

- [ ] ① 污染可检：临时让渲染把 preference 行渲进 `[已知事实]` 节 → 分节单测必挂；恢复后全绿
- [ ] ② 清除可检：全链路「写入→污染→撤销→消失」三态（见 D4）
- [ ] ③ 显式-only 可检：临时给抽取构造点传 `kind="preference"` → 构造点单测必挂；恢复后全绿

### 工程

- [ ] 全量 `pytest tests` 绿；`ruff check app tests` 绿；生产路径 diff 只含：gate/service/extract 构造点断言/continuity 渲染/models CHECK/alembic/README/测试/evals

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游手册 §1.2.4（画像 ❌ · 先事实后偏好因可验证性）+ §1.3 四问 + §1.8 红线③；实扫纠正/确认占位：kind 列**已存在**但 CHECK 物理锁 fact（models.py:470 · alembic :48 → 有 alembic 义务）；抽取 prompt 已资产化至 `assets/memory.extract.system.md`（prompt 资产化阶段一已迁移 · extract.py:105 实扫为准）；schema 无 kind 字段 = 抽取物理产不出 preference；`_source_weight` 显式 1.0 > 抽取 0.8 已有雏形；注入现状单 `[已知事实]` 块无 kind 之分 | done |
| R1 | 范围 = D1 闸放开+判据差异化 / D2 来源分级+注入区分 / D3 supersede+revoke_by_key / D4 幻觉偏好红线 / D5 alembic+图谱+README；非范围 = 推断型偏好（物理拒收）· 跨用户聚合 · 推荐 · 改 fact 语义 · 对外端点 · 热路径抽取 · 权重调参 · 物理删除 · UI（占位原文全保留并据实扫扩列） | done |
| R2 | 两组对比各 ≥2：注入区分选 B1 单消息双节（弃 B2 双消息：注入点复杂化收益不成比例；弃 B3 行级标注：边界弱防不住污染事实通路）；显式-only 落点选 E1 通路约束+双向绑定（弃 E2 闸内来源判据：破坏纯函数哲学且形同虚设；弃 E3 首期收推断型：直接违反 §1.2.4） | done |
| R3 | failure_paths 11 条，三静默错（幻觉偏好注入 / 偏好污染事实通路 / 清除后仍召回）各有断言+变异检验兜底；跨 kind 互冲双保险（双向绑定 + supersede 谓词含 kind）；CHECK 未迁移显式炸非静默；偏好挤占预算列残余风险 | done |
| R4 | 验收全为可执行断言：闸按码断言 · 分节/无节结构断言 · fact 节逐字节对拍 · revoke 后零召回 · 金样+三态全链路变异检验 · 锚点断言替代全文快照（prompt-asset 先例）· 热路径零 LLM-as-judge（§1.8 纪律） | done |
| R5 | SPEC draft-complete 可交人签 HG-SPEC-SIGNOFF；签后 00 出单 task（slug `memory-preference-profile` · 波次裁定四块不拆 · failure_paths 沿用 §5） | done |
| early_stop | no | — |
| residual_risks | ① 统一预算下 preference 挤占 fact 召回预算（首期量少 + span 双计数可观测；真出现再切分预算另案）；② 显式-only 靠构造点单测+非范围维持而非闸内单规则（变异检验 ③ 补 · 未来新增写入通路时必须复判本约束）；③ 金样「编造偏好」判定在 evals 层的确定性程度需 task 阶段细化落点 | 签收时知悉 |

---

## 8. 下一棒

1. **维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`
2. **00**：起草 `docs/tasks/active/task_memory_preference_profile.md`（范围 §2 D1–D5 · failure_paths 沿用 SPEC §5 · 人工闸表按实判：无 HG-GRAPH-MODULES 义务除非形态偏离 · 变异检验三条入验收）
3. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1`
4. **30**：`task/memory-preference-profile` 分支实现（D1 闸 → D5 迁移 → D3 service → D2 渲染 → D4 评测 · fact 语义零变化）
5. **40**：验收（含逐字节对拍 fact 节 + 变异检验三条 + alembic upgrade）→ PR（与 memory-facts-p0/p1 · prompt-asset-roadmap 同模式）

### 下一棒可复制 Prompt（20-spec-audit 预审 / 00 起草 task）

```text
你是 ops-desk-api 仓（/Users/cyning/Desktop/Ops-desk/ops-desk-api）的 <20-spec-audit ｜ 00>。
SPEC：docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md（draft-complete · HG-SPEC-SIGNOFF=pending）。
<20-spec-audit>：书面审范围/非范围/验收/failure_paths 与 R0–R5 思考轮，结论落盘 docs/harness/reviews/，不代签人闸。
<00>：待维护者签 HG-SPEC-SIGNOFF=approved 后，按 SPEC §8 起草 docs/tasks/active/task_memory_preference_profile.md（D1–D5 · failure_paths 沿用 SPEC §5 · 图谱闸按实判零变更 · 变异检验三条入验收 · alembic 义务：CHECK 放宽）。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 占位稿（范围草案 + 锚点 + 验收方向 + 接续指引） |
| 2026-09-22 | 10-spec 补全：锚点逐个实扫（gate/extract/service/continuity/models/alembic/README/assets）——确认 kind 列已存在但 CHECK 物理锁 fact（**有 alembic 义务**）、抽取 prompt 已资产化（assets/memory.extract.system.md · schema 无 kind 字段）、来源权重雏形已存在（显式 1.0 > 抽取 0.8）、注入现状单块无 kind 之分；范围断言化四块 + D5；**显式-only 裁定**（§1 合规论证三点 + §4 E1/E2/E3 对比 · 推断型物理拒收）；注入区分方案对比 B1/B2/B3 选单消息双节；supersede 谓词加 kind 双保险 + 新增 revoke_by_key（显式声明 source_run_id 空定位不到）；幻觉偏好红线结构断言 + 金样 + 三态全链路变异检验；track 裁定 `feature`（新 kind + 新渲染语义 + alembic）；failure_paths 11 条；R0–R5 回填；HG-SPEC-SIGNOFF 保持 pending 待人签 |
