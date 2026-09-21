# Task：画像记忆 kind=preference 首期「显式-only」（闸放开 + 分节注入 + revoke_by_key + 幻觉偏好红线 + CHECK 放宽 · memory-preference-profile）

> **状态**：`draft`（2026-09-22 · 10-task 落稿 · 待 20-task-audit → HG-AUDIT-R1 人签 → 30）  
> **类型**：feature（新 kind + 新召回渲染语义 + **有 alembic 义务**（CHECK 放宽 · 无新列无新索引）· 图谱零变更按实判，偏离回炉条款见闸表与 graph_delta_note）  
> **上游 SPEC**：`docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · commit 4a2f4d9）  
> **分支**：`task/memory-preference-profile`（**禁止 master/main 直改 · 禁止 push**）  
> **10 注**：2026-09-22 · 本棒由 00 委派 10-task 帽 Agent 执行；HG-TASK-DRAFT / HG-AUDIT-R1 均 **pending**（20 审后由人签/授权代录），**本帽不签**

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-preference-profile` |
| **git_branch** | `task/memory-preference-profile` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 闸判据单测（新原因码 `key_kind_mismatch` 按码断言不按文案 · gate 先例）；注入**分节结构断言**（无 preference → 偏好节**物理不存在** · 有 preference → 偏好节只含 preference 行互不串节）+ 单 SystemMessage 双节注入断言 + fact 节与现网**逐字节对拍**；显式 preference 权重 == `SOURCE_WEIGHT_EXPLICIT`（1.0）断言；span `memory_preferences_injected` 计数断言；supersede 谓词含 kind 双保险断言 + `revoke_by_key`（幂等 · 审计 affected · 清除后零召回 + 注入块无该 key · 沿用 P0 否定性断言范式）；幻觉偏好红线离线金样（evals/ · 热路径零 LLM-as-judge）；**变异检验三条**（污染可检 / 清除可检三态 / 显式-only 可检 · 见验收「变异检验」）；alembic CHECK 放宽迁移**可逆往返**（upgrade head + downgrade 回滚注释含「先清 preference 行」）；全量 pytest 绿（基线 1210 collected 真跑）+ ruff 零新增 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | 无（**零图谱变更按实判** · SPEC `2 D5 裁定：不新增路由/表/事件类型/一级模块；改动面 = `app/ops/memory/**` 模块内 + `lg_rag/continuity.py` 渲染/装配 + `db/models.py` CHECK 常量 + alembic 迁移文件（migrations 既有面）+ `app/ops/memory/README.md` + 测试 + evals；**本帽真读复核**见闸表 HG-GRAPH-MODULES 行与 R0） |
| **graph_delta** | 无 |
| **graph_delta_note** | **回炉补闸条款**：若 30 阶段实现形态偏离零变更预判（新增一级模块 · 新增任何路由/表/事件类型 · 新增列/索引），**不得沿用本裁定**——退回 10-spec 修订 SPEC + 10-task 补 HG-GRAPH-MODULES 新行义务 + `docs/_tech_graph/` 如实登记后方可续 30；30 交付时 `01_modules.md` memory 行备注补「kind=preference 放开（闸 `ALLOWED_KINDS` + CHECK 放宽 `IN ('fact','preference')` + `revoke_by_key` + 注入分节）」属**备注级顺手更新**（对齐 prompt-asset-roadmap-p1「依赖出边 +prompts」/ llm-layer-hardening「+db」00 代录先例），非 SPEC 回炉 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `memory-preference-profile`；`app/ops/memory/README.md` 同步属 D5 范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | **单 task 四块不拆波**（SPEC `2 波次裁定：闸/注入/纠错/红线是一个不可拆语义单元——只放开闸不配注入区分 = 偏好污染事实通路静默错；不配红线评测 = 违反手册 `1.8「先把坏了能发现装上再让功能上线」）；本 task：10 落稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30（承 SPEC `8 序：D1 闸 → D5 迁移 → D3 service → D2 渲染 → D4 评测 · fact 语义零变化）→ 40（fact 节逐字节对拍 + 变异检验三条 + alembic 往返）→ CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1` / `lc-evidence-http-v1`；SSE 零新事件类型） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **pending** | 20-R1, 30 | 待 00 验收 10-task 稿后代录/人签（**本帽不签**） |
| HG-AUDIT-R1 | **pending** | **30** | 待 20-task-audit 书面审 R1 PASS 后人签/授权代录（`docs/harness/reviews/` 落盘）；**30 拒开工** |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-22 本帽**真读** `docs/_tech_graph/l1/01_modules.md`：模块表已建置；memory 行在表（:28 · 路径 glob `app/ops/memory/**` · 出边 `db, rag（embedder）, llm（抽取）, prompts（extract 模板加载）` · P0/P1/prompt-asset 三级备注留痕）；`lg_rag/continuity.py` 在 lg_rag 行路径覆盖内；models/alembic 在 db 行（`app/db/**`, `alembic/**`）覆盖内。SPEC `2 D5 判本 task **零图谱变更**（不新增路由/表/事件类型/一级模块；CHECK 放宽是既有表既有约束的迁移文件，db 行 migrations 既有面）→ **无新签义务**。memory 行**备注级更新预期**：30 交付后备注补 kind=preference 放开（00 代录先例见 graph_delta_note）。**若 30 形态偏离（新增一级模块 / 新增路由/表/事件类型 / 新增列/索引）→ 回炉补闸**（见 graph_delta_note，不得沿用本裁定） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点 |

---

## 背景与目标

现状（SPEC `1 实扫锁死 · 2026-09-22 本帽复核一致）：记忆四层中**画像层仍空**（手册 `1.2.4）；P0/P1 已在 kind 位预留画像入口，但**闸、CHECK、召回渲染三面全锁 fact**——`gate.py:27` `ALLOWED_KIND = "fact"`；`models.py:470` `CheckConstraint("kind = 'fact'")` 物理锁死（alembic `20260921_memory_facts.py:37,48` 同 CHECK 落库）；注入现状单 `[已知事实]` 块无事实/偏好之分。

一句话目标（SPEC 锁死）：在 memory-facts P0/P1 底座上放开 `kind=preference`——**首期只收显式声明**（闸判据差异化双向 key 域绑定 + 抽取管道物理不产偏好），召回注入**分节区分事实/偏好**（方案 B1 单 SystemMessage 双节），冲突走既有 supersede（谓词加 kind 双保险）、纠错补 `revoke_by_key` 一键清除，并以**幻觉偏好红线**（无偏好记忆时不得编造 · 手册 `1.8 红线③扩展）结构断言 + 离线金样 + 三态全链路变异检验为证；CHECK 放宽走 alembic（可逆往返），fact 语义**零变化**。

设计纪律（30 不得违反 · 承 SPEC `1/`2 签收锁死）：

1. **显式-only 物理拒收推断型**：闸是纯函数不感知来源；preference 仅经显式 service API 通路构造；抽取管道产物永远 kind=fact（extract.py 构造点钉死 + schema 无 kind 字段 + 单测断言）。推断型偏好首期**无写入通路**（非「收了再筛」）。
2. **fact 语义零变化**：kind=fact 判据/召回/注入行为零变化；注入块**事实节渲染与现网逐字节一致**（对拍断言 · prompt-asset 先例）。
3. **双向 key 域绑定**：`kind=preference` ⟺ key 首段 == `pref`（双向）；违反 → 新原因码 `key_kind_mismatch`（入 `REJECT_REASONS` · 按码断言）。
4. **无偏好 → 偏好节物理不存在**：红线结构断言天然落点；空集 → 空串不注入（现行为沿用）。
5. **锚点断言替代全文快照**：偏好节引导语断言含「用户偏好」「非客观事实」级锚点（改文案不挂 CI · 改变量语义必挂）。

---

## 现状锚点（只读 · 30 必读 · 10 已扫 · 承 SPEC `1 并复核）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 写入闸（改造对象 D1） | `app/ops/memory/gate.py` | `ALLOWED_KIND = "fact"`（:27）；kind ≠ fact → `kind_not_allowed`（:103-104 · docstring :12「preference 属画像，P1+」）；`REJECT_REASONS` frozenset 7 码（:39-49）；`FactCandidate.kind` 字段已预留（:89 · 默认 fact）；其余判据（主体 :106-107 / key 正则 :110 / 易失前缀 :112-113 / 标量值 :115-124 / 长度 :125-127）与 kind 正交可复用 |
| CHECK 物理锁（改造对象 D5） | `app/db/models.py:470` · `alembic/versions/20260921_memory_facts.py:37,48` | `CheckConstraint("kind = 'fact'", name="ck_ops_memory_facts_kind")`（:470）；`kind` 列**已存在**（:501 · String · default 'fact'）；alembic 同 CHECK 落库——**放开必须迁移（有 alembic 义务）** |
| alembic 链 | `alembic heads` 真跑 | head = `20260921_llm_usage`；链序 … → `20260921_memory_facts` → `20260921_memory_facts_embedding` → `20260921_llm_usage`；新迁移挂 head 后（建议 slug `20260922_memory_facts_kind_preference`） |
| 抽取管道（显式-only 落点） | `app/ops/memory/extract.py` | prompt 已资产化 `render("memory.extract.system")`（:105）；schema `ExtractedFactItem` 仅 key/value **无 kind 字段**（:47-51）· `MemoryFactExtraction`（:54-57）；构造点 `FactCandidate(...)`（:129-131）默认 kind=fact——**抽取物理产不出 preference，首期保持即显式-only 落点之一** |
| 状态机与权重（改造对象 D3/D2） | `app/ops/memory/service.py` | `_write_in_session` 同事务 supersede（:49-76）：查重谓词 `(tenant_id, user_id, key, status=active)` **不含 kind**（:53-58）；`revoke_by_source`（:128-157 · 幂等 · 审计日志 :154-156 记 affected）——显式写入 `source_run_id` 为空，**preference 纠错缺定位入口**（→ `revoke_by_key`）；权重雏形 `SOURCE_WEIGHT_EXPLICIT=1.0`（:233）> `SOURCE_WEIGHT_EXTRACTED=0.8`（:234）· `_source_weight`（:340-342）；`recall_active`（:187-220）与 `_VECTOR_RECALL_SQL`（:237-245）均**无 kind 谓词**（D2 裁定：不加 · 渲染层分节） |
| 注入点（改造对象 D2） | `app/ops/lg_rag/continuity.py` | `MEMORY_FACTS_HEADER = "[已知事实]"`（:98）；`render_memory_facts_block`（:149-166）单循环渲单块（key=value 一行一条 · 空集 → 空串）；`inject_memory_facts_block`（:169-184）作**独立 SystemMessage** 插前缀系统消息后（空块 no-op）；`assemble_graph_messages_with_memory`（:187-244）开关 `MEMORY_FACTS_ENABLED` 默认 false（:105-115）· span `memory_facts_injected=N`（:240/:243）· 召回故障降级不注入——**现状无 kind 之分，闸放开后不染渲染层 = 偏好被当事实注入（静默错）** |
| key 域约定 | `app/ops/memory/README.md:21` | 首段域约定**已列 `pref`**（project / user / repo / pref …）；非范围 :144 明示「画像 / preference」待本波解锁（D5 移除该条 + 注入格式补偏好节样例 + 故障语义补新原因码） |
| evals 基线 | `ls evals/` 真跑 | `evals/memory/` 现仅 `__init__.py` + `run_eval.py`（**无金样 yaml**）；红线金样为**新增**（落点 30 定 · `evals/agent/redlines/capability_v1.yaml` 为先例形态）；热路径零 LLM-as-judge（手册 `1.8 纪律） |
| 测试基线 | `python -m pytest tests --collect-only -q` | **1210 collected**（2026-09-22 本帽真跑）；memory 面既有用例：gate 12 / injection 15 / service_db 7 / extract_p1 12 / vector_p1 8 / time_decay_tz 6 / embedding_backfill 15；本波新增守护测试 → collected 增加数入 40 验收记录，**无既有用例删除** |

---

## 钉死契约（自 SPEC `2/`4 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **闸放开** | `ALLOWED_KINDS = {"fact", "preference"}`（gate.py:27 单常量放开为集合）；kind 不在集合 → `kind_not_allowed` 沿用 |
| **双向 key 域绑定** | `kind=preference` ⟺ key 首段 == `pref`；违反 → `key_kind_mismatch` 新原因码（入 `REJECT_REASONS` · 按码断言不按文案）；README :21 域约定已预留 `pref` |
| **显式-only 通路约束** | 闸保持纯函数（不感知来源 · P0 设计哲学不动）；preference 仅经显式 service API 构造；**抽取管道产物永远 kind=fact**——extract.py 构造点（:129-131）钉死 + 单测断言 `MemoryFactExtraction` schema 无 kind 字段、构造候选 kind==fact（变异检验 ③ 补） |
| **来源权重** | 沿用 `_source_weight`：显式/人工（source_run_id 空）= **1.0** > 抽取 = 0.8；首期 preference **只有显式来源**（权重恒 1.0）；融合排序断言显式 preference 权重 == `SOURCE_WEIGHT_EXPLICIT`；0.8 路径对 preference 物理不存在（D1 通路约束的下游不变量） |
| **注入区分（方案 B1）** | `render_memory_facts_block` 按 kind **分节**：`[已知事实]` 节（kind=fact · 与现网**逐字节一致**）+ `[用户偏好]` 节（kind=preference · 带引导语「用户显式陈述的偏好，用于调整回应方式；非客观事实」+「无偏好时不要假设/编造」语义）；仍**单条独立 SystemMessage**（`inject_memory_facts_block` :169-184 结构不变 · 不掺入任何 prompt 模板）；**无 preference → 偏好节物理不存在**；无 fact 且无 preference → 空串不注入（现行为沿用） |
| **召回 SQL** | **不加 kind 谓词**（recall_active / _VECTOR_RECALL_SQL 结果集 ≤N 小 · 渲染层分节）；**不新增索引**（既有 `idx_ops_memory_facts_recall` 覆盖主谓词）；统一预算 `MEMORY_FACTS_MAX_ITEMS` 内两节混排截断（融合排序不动 · 不新增 env） |
| **观测** | span metadata 增 `memory_preferences_injected=M`（与 `memory_facts_injected` 并列 · `update_current_span_metadata` 先例 · tracing 未开静默 no-op）；**不新增 SSE 事件类型**；SSE/用户面不输出原始偏好（README :51 纪律沿用） |
| **supersede 双保险** | 偏好变更 = supersede：同 `(tenant_id, user_id, key)` 同 kind 新写 → 复用 `_write_in_session` 同事务（旧行 superseded 留表可审计 · 后写赢）；**查重谓词加 kind**（:53-58 补 `kind == candidate.kind`）——跨 kind 不互相 supersede（双向绑定第一道 · 谓词含 kind 第二道防御） |
| **revoke_by_key** | 新增 `revoke_by_key(tenant_id, user_id, key)`：按 key 把 active 行置 `revoked`；**必带 tenant+user 谓词**（P0 纪律 · 跨 tenant = 0 行）；幂等（已 revoked 不动 · 重复调用影响 0 行）；审计日志记影响行数（revoke_by_source :154-156 同款 · 含 affected=0）；**清除后召回零命中 + 注入块无该 key** |
| **物理删除** | 不做（P0 纪律：失效走状态机不物理删 · 旧值留表审计） |
| **alembic** | 迁移放宽 CHECK：`ck_ops_memory_facts_kind` 从 `kind = 'fact'` 改 `kind IN ('fact','preference')`（drop + add constraint；存量行全 fact 零数据迁移；**回滚须先清 preference 行**——写入迁移文件注释）；`models.py:470` 同步；**不新增列、不新增索引**；迁移须**可逆往返**（upgrade → downgrade → upgrade 冒烟） |
| **图谱** | 零变更按实判（闸表 HG-GRAPH-MODULES 行留痕 · memory 行备注级更新预期）；`./scripts/graph-compile.sh` 绿为回归保险；不回改 done/归档历史文档 |
| **README 同步** | `app/ops/memory/README.md`：非范围 :144 移除「画像 / preference」、env 表（无新 env · 如实记）、注入格式补偏好节样例、故障语义补 `key_kind_mismatch` 与 `revoke_by_key` |
| **安全** | 无新凭证面/网络面；不新增对外端点（preference 写入同走内部 service API）；偏好内容经同一 SystemMessage 结构隔离注入（不掺入 prompt 模板）；身份（tenant/user）取自请求上下文纪律不变，模型产出不得参与（README :50 沿用） |

---

## 范围（同 task 竖切 · 四块不拆波 · SPEC `2 波次裁定）

- [ ] **D1 · 闸放开 kind=preference + 判据差异化（必做）**：`ALLOWED_KINDS` 集合放开；双向 key 域绑定 + `key_kind_mismatch` 入 `REJECT_REASONS`；显式-only 通路约束（extract 构造点钉死 + schema 断言单测）；其余判据原样复用
- [ ] **D2 · 来源分级与召回注入区分（必做）**：显式 1.0 权重断言；`render_memory_facts_block` 分节渲染（双节单 SystemMessage · 无偏好节物理不存在 · fact 节逐字节不变）；召回 SQL 不加 kind 谓词；span `memory_preferences_injected`；锚点断言引导语
- [ ] **D3 · 冲突与纠正（必做）**：supersede 查重谓词加 kind；新增 `revoke_by_key`（tenant+user 谓词 · 幂等 · 审计 · 清除后零召回）；物理删除零发生
- [ ] **D4 · 幻觉偏好红线评测（必做）**：结构断言（无偏好无节）+ evals 离线金样（无记忆用户偏好类提问 → 回答无编造偏好 · 热路径零 LLM-as-judge）+ 三态全链路变异检验（写入→污染→撤销→消失）+ prompt 侧引导语锚点断言
- [ ] **D5 · 表结构 / alembic / 图谱 / 文档（必做）**：CHECK 放宽迁移（可逆往返 · 回滚注释含「先清 preference 行」）+ models.py 同步 + README 同步 + graph-compile 绿（图谱零变更按实判）

**竖切结论**：D1–D5 同 task 一次提交（SPEC `2：只放开闸不配注入区分 = 偏好污染事实通路静默错；不配红线评测 = 违反手册 `1.8；耦合面小单 PR 不巨型）；承 SPEC `8 实现序 D1 闸 → D5 迁移 → D3 service → D2 渲染 → D4 评测。

### 非范围

- ❌ **推断型偏好**（行为推断 / LLM 抽取产 preference 候选）——首期物理拒收；未来另案 SPEC（届时自带 source_run_id + 低权重 + 新判据义务 · 推断型清除预留：`revoke_by_source` 现成可用 · 本 task 只立义务不立实现）
- ❌ 跨用户画像聚合；推荐系统
- ❌ 改事实型记忆语义（kind=fact 判据/召回/注入行为零变化；注入块事实节渲染与现网逐字节一致）
- ❌ 对外 HTTP 写端点（沿用 P0/P1 非范围；preference 写入同走内部 service API）
- ❌ 热路径/流中抽取（沿用 P1 非范围）；抽取 prompt 文案改动（`memory.extract.system` 保持事实抽取器语义 · 碰它是 prompt 资产化轨的事）
- ❌ 向量召回算法/权重调参（沿用 P1 初值；本 task 只在渲染层分 kind）
- ❌ 物理删除（P0 纪律）；偏好管理 UI（web / ios 另案）
- ❌ 热度淘汰 / TTL 新机制（沿用既有 expires_at 双保险）
- ❌ 新增 env / 新增 SSE 事件类型 / 新增列 / 新增索引
- ❌ 历史文档回改；web / ios

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| **幻觉偏好注入**（无 preference 行却渲染出偏好节） | **静默错**（模型看到空/编造偏好语义）；渲染层「空 preference 集 → 偏好节物理不存在」单测钉死 + 金样行为断言 + 引导语「无偏好不要假设」双保险 | Y（修渲染） | 否 |
| **偏好污染事实通路**（preference 行进 `[已知事实]` 节被当客观事实） | **静默错**；分节渲染单测钉死（含向量通路召回的 preference 也进偏好节断言）；引导语明示「非客观事实」；**变异检验 ① 钉死** | Y（修渲染） | 否 |
| **清除后仍召回**（revoke_by_key 后该 key 仍注入） | **静默错**；召回只认 active 双保险（查询路径自带过滤）+ 全链路变异检验「写入→污染→撤销→消失」钉死（**缺第一态不算过**）；span/log 可对账 | Y（修查询） | 否 |
| CHECK 未迁移写 preference（migration 未跑） | insert 违反 `ck_ops_memory_facts_kind` → IntegrityError **显式炸**（非静默）；验收含 `alembic upgrade head` + 写 preference 通路冒烟 | Y（跑迁移） | 是（CI 红） |
| 跨 kind 静默互冲（同 key fact 与 preference 互相 supersede） | **静默错**；第一道：双向 key 域绑定（`key_kind_mismatch`）；第二道：supersede 查重谓词加 kind——双保险，断言跨 kind 同 key 两行各自 active 互不影响 | Y（修谓词） | 否 |
| 抽取管道误产 preference（未来改动给抽取候选传 kind） | 闸双向绑定兜（非 pref. key + preference → 拒）；构造点单测钉死 kind==fact；schema 无 kind 字段 = 结构化输出层面也产不出；**变异检验 ③ 钉死** | Y（改回） | 否 |
| key 域漂移（fact 用 `pref.` 前缀 / preference 用非 pref 前缀） | `key_kind_mismatch` 拒写不落库 + `GateRejectedError` 原因码（调用方不得静默吞 · P0 纪律） | Y（改调用方） | 否 |
| 偏好挤占事实预算（统一预算下 preference 多致 fact 被截） | 首期 preference 量少 + span 双计数（facts/preferences injected）可观测；列残余风险不列验收（SPEC `7 ①） | — | 否 |
| revoke_by_key 跨 tenant / 幂等 | 必带 tenant+user 谓词（跨 tenant = 0 行）；重复调用影响 0 行幂等返回，审计日志仍记 `affected=0`（revoke_by_source 同款） | Y | 否 |
| 引导语/节名被改坏（偏好节文案失去「偏好/非事实」语义） | 锚点断言（注入块含「用户偏好」节名与「非客观事实」级锚点）必挂 CI；非全文快照（改文案不挂 · prompt-asset 先例） | Y（改文案） | 否 |
| 召回 DB 故障 / 向量通路故障 | 沿用现行为：`memory_degraded` / `memory_vector_degraded` 降级不注入/回退确定性，不拖垮 chat——本 task 零改动 | Y | 否 |
| 回滚卡死（downgrade 时库内有 preference 行违反旧 CHECK） | 迁移文件注释写明「回滚须先清 preference 行」；downgrade 前清行后往返冒烟通过（验收 D5 钉死） | Y（清行后回滚） | 是（CI 红） |
| 30 开工前旧测影响面清单未落盘或逐条无处置 | 验收「工程 · 闸前置」项不满足 → **拒收**（B1） | 是 | 否 |
| 无变异检验三条却宣称红线有效 | 40/verify **拒收**（不验收空真规则） | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：`HG-AUDIT-R1` approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved · 本 task 零图谱变更无新签义务；**若 30 偏离零变更预判（新增一级模块 / 新增路由/表/事件类型 / 新增列/索引）→ 回炉补闸**，见闸表与 graph_delta_note）

### D1 · 闸放开与判据差异化（映射 SPEC `6-D1）

- [ ] `ALLOWED_KINDS = {"fact", "preference"}`；kind 集合外（如 `"profile"`）→ `kind_not_allowed`（按码断言）
- [ ] 双向绑定单测：preference+非 pref. key / fact+pref. key / 非 pref. key+缺省 kind → `key_kind_mismatch`；preference+`pref.*` key → 放行
- [ ] 新原因码入 `REJECT_REASONS`（enumerable 覆盖断言同步改编 · B1 #2）；闸拒 = 不落库 + `GateRejectedError`（沿用）
- [ ] 抽取管道单测：`MemoryFactExtraction` schema 无 kind 字段；构造候选 kind==`fact`（extract.py :129-131 构造点钉死）
- [ ] kind=fact 全部既有判据回归绿（P0/P1 闸单测零变化通过 · B1 #1/#2 改编两例外如实落盘）

### D2 · 来源分级与注入区分（映射 SPEC `6-D2）

- [ ] 融合排序断言：显式 preference 来源权重 == `SOURCE_WEIGHT_EXPLICIT`（**1.0** 显式断言 · 0.8 路径对 preference 物理不存在）
- [ ] 分节渲染单测：fact 行进 `[已知事实]` 节、preference 行（含向量通路召回者）进 `[用户偏好]` 节、互不串节
- [ ] **无 preference → 注入块无 `[用户偏好]` 节**（红线结构断言 · 节物理不存在非空节）；空集 → 空串不注入（现行为）
- [ ] 注入仍**单条独立 SystemMessage** 双节，位置语义不变（`inject_memory_facts_block` 结构不变）；kind=fact 节渲染与现网**逐字节一致**（对拍断言 · 一次性命令输出入 40 验收记录）
- [ ] span metadata `memory_preferences_injected` 与 `memory_facts_injected` 分别计数（tracing 未开静默 no-op）；SSE 零新事件类型
- [ ] 锚点断言：偏好节含「用户偏好」「非客观事实」级锚点（非全文快照）

### D3 · 冲突与纠正（映射 SPEC `6-D3）

- [ ] supersede 谓词含 kind：跨 kind 同 key 两行各自 active 互不影响（双保险断言）；同 kind 同 key 新写 → 旧行 superseded + 召回零命中（沿用 P0 否定性断言范式）
- [ ] `revoke_by_key`：active → revoked；必带 tenant+user 谓词（跨 tenant = 0 行）；幂等 0 行；审计日志记 affected（含 affected=0）；**清除后召回零命中 + 注入块无该 key**
- [ ] 物理删除零发生（状态机断言沿用）

### D4 · 幻觉偏好红线（映射 SPEC `6-D4）

- [ ] 结构断言（见 D2 无偏好无节 · 渲染层单测钉死）
- [ ] 离线金样：无记忆用户偏好类提问 → 回答无编造偏好（`evals/` 落点 · 30 定具体文件 · `evals/agent/redlines/capability_v1.yaml` 先例形态 · 热路径零 LLM-as-judge）
- [ ] **全链路变异检验**：写入错误偏好 → 断言污染出现 → `revoke_by_key` → 断言污染消失（**三态全断言，缺第一态不算过**）

### D5 · 表结构 / alembic / 图谱 / 文档（映射 SPEC `6-D5）

- [ ] alembic 迁移：CHECK 放宽 `kind IN ('fact','preference')`（drop + add · 挂 head `20260921_llm_usage` 后）；`alembic upgrade head` 后 preference 写入通路冒烟过；**可逆往返**（upgrade → downgrade → upgrade）；回滚注释含「先清 preference 行」
- [ ] 无新增列/索引；`./scripts/graph-compile.sh` 绿；图谱零变更裁定与实现形态一致（偏离 → 回炉补闸 + SPEC 回炉）
- [ ] `app/ops/memory/README.md`：非范围移除「画像 / preference」、注入格式补偏好节样例、故障语义补 `key_kind_mismatch` 与 `revoke_by_key`、env 表如实记（无新 env）

### 变异检验（不验收空真规则 · 映射 SPEC `6-变异检验）

- [ ] ① **污染可检**：临时让渲染把 preference 行渲进 `[已知事实]` 节 → 分节单测必挂；恢复后全绿
- [ ] ② **清除可检**：全链路「写入→污染→撤销→消失」三态（见 D4 · 缺第一态不算过）
- [ ] ③ **显式-only 可检**：临时给抽取构造点传 `kind="preference"` → 构造点单测必挂；恢复后全绿

### 工程（映射 SPEC `6-工程）

- [ ] **闸前置**：30 开工前旧测影响面清单已落盘且逐条有处置（回归/改编理由）——清单见下「旧测影响面清单（B1）」，30 逐条执行处置并在提交说明逐条回填
- [ ] 全量 `pytest tests` 绿（基线 **1210 collected** · 2026-09-22 本帽真跑；**无既有用例删除**，新增守护用例数如实入 40 记录）；`ruff check app tests` 绿（零新增告警口径）
- [ ] 生产路径 diff 白名单：`git diff master -- app/ alembic/` 只含 gate / service（谓词 + revoke_by_key）/ extract 构造点断言 / continuity 渲染 / models CHECK / alembic 迁移 / memory README + 测试 + evals

### 旧测影响面清单（B1 · 2026-09-22 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'memory|continuity'` · `grep -rln 'should_write|ALLOWED_KIND|kind_not_allowed|render_memory_facts_block|inject_memory_facts_block|memory_facts_injected|revoke_by_source|recall_active|assemble_graph_messages_with_memory|MEMORY_FACTS_ENABLED' tests/`（命中 5 文件：test_memory_gate / test_memory_injection / test_memory_service_db / test_memory_extract_p1 / test_memory_vector_p1）· 各文件 `def test_` 计数（gate 12 / injection 15 / service_db 7 / extract_p1 12 / vector_p1 8 / time_decay_tz 6 / embedding_backfill 15 / session_continuity 2 / lg_rag_session_continuity 15）· `grep -n 'kind' tests/test_memory_*.py`（kind 直引仅 3 处：gate :37-40/:103-106 · service_db :93-96）· `python -m pytest tests --collect-only -q`（=**1210**）。本波行为变更源裁定：**闸放开 + 分节渲染 + supersede 谓词加 kind + revoke_by_key 新增 + CHECK 放宽**；fact 语义零变化（fact 节逐字节对拍钉死），故影响面以**回归**为主、**改编**集中在三处 kind 直引断言（preference 从拒变放行的语义反转 + enumerable 覆盖），**无测试删除**。处置三态：**回归**（不受影响，全波次重跑确认）/ **改编**（随本波更新）/ **删除**（本清单无）。

| # | 锚点 | 旧测/调用点现状 | 本波影响 | 处置 |
|---|------|----------------|----------|------|
| 1 | `tests/test_memory_gate.py:37-40` `test_kind_not_allowed` | 用 `_candidate(kind="preference")` 断言拒 + `kind_not_allowed` | **语义反转**：preference 放开后该候选不再天然被拒（pref.* key 将放行）→ 必挂 | 改编（断言对象换 kind 集合外值如 `"profile"`；preference 放行面由新双向绑定单测覆盖 · SPEC `6-D1） |
| 2 | `tests/test_memory_gate.py:103-106` enumerable 覆盖断言 | `REJECT_REASONS` 7 码可枚举 + 覆盖全拒径 | 增 `key_kind_mismatch` → 8 码；覆盖断言须补新码拒径 | 改编（随 D1 同步 · 钉死契约「双向 key 域绑定」） |
| 3 | `tests/test_memory_gate.py` 其余 10 用例 | 标量/主体/key/易失/长度判据 | 判据与 kind 正交原样复用 → 零改动全绿 | 回归（零改动） |
| 4 | `tests/test_memory_service_db.py:93-96` `test_gate_rejection_writes_nothing` | 用 `_candidate(kind="preference")` 触发闸拒断言不落库 | preference 放开后该候选不再天然被拒 → 触发方式失效 | 改编（换触发原因码：非 pref. key + preference → `key_kind_mismatch` 或 kind 集合外值；「闸拒不落库」语义不变） |
| 5 | `tests/test_memory_service_db.py:108` `test_same_key_supersedes_old_value` | 同 key 新写 → 旧行 superseded | 谓词加 kind 后同 kind 行为不变（双保险第二道只影响跨 kind）→ 零改动全绿 | 回归（零改动）+ 新增跨 kind 互不影响断言（新增义务 · 见 #12） |
| 6 | `tests/test_memory_service_db.py:125` revoke 幂等 · `:202` 三态变异先例 | `revoke_by_source` 幂等 affected=0 · 「写入→污染→revoke_by_source→消失」 | revoke_by_source 本体不动 → 零改动；三态范式被本波 revoke_by_key 沿用（D4 变异检验 ②） | 回归（零改动 · 范式承先例） |
| 7 | `tests/test_memory_service_db.py` 其余（过期不可见 :148 · 截断 :174 · 跨租户 :239） | 召回谓词/过期/租户面 | 召回 SQL 不加 kind 谓词 → 零改动 | 回归（零改动） |
| 8 | `tests/test_memory_injection.py` 15 用例（渲染格式 :80-96 · 注入位置 :99-126 · 开关/env :32-64,:132 · 降级 :148,:233 · span :197-248） | 单块渲染/注入/观测守护 | **fact-only 输入渲染须逐字节不变**（D2 对拍钉死）→ 既有用例零改动全绿；分节/无偏好无节/span 双计数为新增断言 | 回归（零改动守护）+ 新增分节断言（新增义务 · 见 #12） |
| 9 | `tests/test_memory_extract_p1.py` 12 用例 | 抽取开关/调度/闸拒/零写入面 | 抽取管道形态不变（显式-only 落点即「保持不动」）→ 零改动；schema 无 kind + 构造点 kind==fact 断言为新增 | 回归（零改动）+ 新增 schema/构造点断言（新增义务 · 变异检验 ③ 落点） |
| 10 | `tests/test_memory_vector_p1.py` 8 用例 | 向量召回/融合/降级/跨租户 | SQL 不加 kind 谓词、融合排序不动 → 零改动；「向量召回 preference 进偏好节」为新增断言 | 回归（零改动）+ 新增向量通路分节断言（新增义务 · SPEC `6-D2） |
| 11 | 辅扫：`test_memory_time_decay_tz.py`（6）· `test_memory_embedding_backfill.py`（15）· `test_session_continuity.py`（2）· `test_lg_rag_session_continuity.py`（15） | 时区/embedding/continuity 窗口装配面 | 与 kind 正交、不触渲染块语义 → 零改动 | 回归（零改动 · 全波次重跑确认） |
| 12 | 新增义务：分节渲染断言 / 无偏好无节结构断言 / fact 节逐字节对拍 / span 双计数 / 权重 1.0 断言 / supersede 跨 kind 双保险 / revoke_by_key（幂等 · 审计 · 清除后零召回）/ 金样 + 三态变异检验 / alembic 往返冒烟 | 当前不存在 | 本波新增守护测试 + evals 金样（工程验收项）；collected 自 1210 增加，新增数入 40 记录 | 新增（30 实现 · 40 核验） |
| 13 | alembic 链 | head=`20260921_llm_usage`（真跑 `alembic heads`）· 链序 memory_facts → embedding → llm_usage | 新迁移挂 head 后；既有迁移零改动 | 新增迁移文件（D5 · 可逆往返钉死） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 4a2f4d9） |
| 上游手册 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（`1.2.4 画像 ❌ · `1.3 四问 · `1.8 红线③） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 2026-09-22 真读核验 · memory 行 :28） |
| 改造对象 | `app/ops/memory/gate.py`（:27 ALLOWED_KIND · :39-49 REJECT_REASONS）· `app/ops/memory/service.py`（:53-58 谓词 · :128-157 revoke 先例 · :233-234/:340-342 权重）· `app/ops/lg_rag/continuity.py`（:98 header · :149-166 渲染 · :169-184 注入 · :240/:243 span）· `app/db/models.py:470`（CHECK） |
| 显式-only 落点 | `app/ops/memory/extract.py`（:47-57 schema · :129-131 构造点钉死） |
| 迁移链 | `alembic/versions/20260921_memory_facts.py:37,48`（CHECK 落库）· head `20260921_llm_usage` |
| P0/P1 底座 | `docs/tasks/done/task_memory_facts_p0.md` · `docs/tasks/done/task_memory_facts_p1.md`（状态机/闸/向量召回/抽取先例） |
| 变异检验先例 | `tests/test_memory_service_db.py:202`（写入→污染→revoke_by_source→消失三态 · P0）· `tests/test_memory_vector_p1.py:202`（向量通路同款） |
| 锚点断言先例 | `docs/tasks/done/task_prompt_asset_roadmap_p1.md`（锚点断言替代全文快照 · 显式炸模式 · PR #155） |
| 测试锚点 | `tests/test_memory_gate.py` · `tests/test_memory_injection.py` · `tests/test_memory_service_db.py` · `tests/test_memory_extract_p1.py` · `tests/test_memory_vector_p1.py` |
| evals 先例 | `evals/agent/redlines/capability_v1.yaml`（红线金样形态）· `evals/memory/run_eval.py` |
| 格式基准 | `docs/tasks/done/task_prompt_asset_roadmap_p1.md`（signed → done 五棒全通 · PR #155） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（`1 合规论证 / `2 D1–D5 / `4 方案裁决 B1+E1 / `5 failure_paths / `6 验收 / `7 residual）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/memory/gate.py` · `app/ops/memory/service.py`（:49-76 · :128-157 · :233-245 · :340-342）· `app/ops/memory/extract.py`（:47-57 · :129-131）· `app/ops/lg_rag/continuity.py`（:98-244）· `app/db/models.py`（:466-505）· `app/ops/memory/README.md`
6. 先例：`tests/test_memory_service_db.py:202`（三态变异检验范式）· `app/ops/prompts/packs.py:119-127`（显式炸模式）· `evals/agent/redlines/capability_v1.yaml`
7. 测试：`tests/test_memory_gate.py` · `tests/test_memory_injection.py` · `tests/test_memory_service_db.py` · `tests/test_memory_extract_p1.py` · `tests/test_memory_vector_p1.py`
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-22 · 4a2f4d9）；范围 D1–D5 承 SPEC `2 不重开辩论；本帽实扫复核：分支正确（`task/memory-preference-profile`）· gate.py:27/:103-104 · models.py:470/:501 · alembic :37,:48 与 head=20260921_llm_usage · extract schema 无 kind（:47-57）· service 谓词 :53-58 不含 kind · continuity :98/:149-244 单块无 kind 之分 · README :21 pref 域已预留 · evals/memory 无金样 · pytest 基线 **1210 collected**（真跑）——SPEC `1 锚点全部复核一致，零措辞偏差 | no | — | none |
| R1 | 开工闸：HG-TASK-DRAFT=pending（本帽不签）· HG-AUDIT-R1=pending（blocks 30 · 本帽不签）· HG-GRAPH-MODULES=approved（真读 `01_modules.md` · memory 行 :28 在表 · 零图谱变更 + memory 行备注级更新预期 + 偏离回炉补闸条款）· HG-PILOT-OPSDESK-GLAYER=n/a | no | — | 无 |
| R2 | 竖切：D1–D5 同 task 一次提交（承 SPEC `2 波次裁定 · 四块不可拆语义单元）；实现序承 SPEC `8（D1 闸 → D5 迁移 → D3 service → D2 渲染 → D4 评测）；方案对比继承 SPEC `4 两组裁决（B1 单消息双节弃 B2/B3 · E1 通路约束+双向绑定弃 E2/E3），不重演 | no | — | 无 |
| R3 | failure_paths **15 条** = SPEC `5 十一条翻四列 + 过程四（闸未签拒开工 · B1 闸前置拒收 · 无变异检验拒收 · 回滚卡死先清 preference 行）；三静默错（幻觉偏好注入 / 偏好污染事实通路 / 清除后仍召回）各有断言+变异检验兜底 | no | — | 无 |
| R4 | 验收 **27 条**全否定性断言化逐块映射 SPEC `6（人工闸 1 / D1×5 / D2×6 / D3×3 / D4×3 / D5×3 / 变异检验×3 / 工程×3）；B1 实扫 **13 行**落盘（回归×7 · 改编×3 · 新增×2 · 迁移×1 · 删除×0）；kind 直引断言仅 3 处需改编（gate :37-40/:103-106 · service_db :93-96）——实扫钉死 | no | — | 统一预算下 preference 挤占 fact 召回（承 SPEC residual ① · span 双计数可观测 · 真出现再切预算另案） |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（B1 / 闸行留痕 / 基线数 / 扫描口径细化均为过程化落地）；HG-AUDIT-R1 待人签 | no | — | ① 显式-only 靠构造点单测+非范围维持而非闸内单规则（变异检验 ③ 补 · 承 SPEC residual ②）；② 金样「编造偏好」判定的确定性程度由 30 在 evals 落点细化（承 SPEC residual ③）；③ 偏好挤占预算（承 SPEC residual ①） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

SPEC 已签收，本 task 只做可执行化拆解：记忆四层画像层仍空（手册 `1.2.4）· 闸/CHECK/召回渲染三面锁 fact · 首期显式-only 合规路径（SPEC `1 论证三点）。本帽实扫复核：分支 `task/memory-preference-profile` 正确；`ALLOWED_KIND = "fact"`（gate.py:27 · 与 SPEC 一致）；`CheckConstraint("kind = 'fact'")`（models.py:470）+ alembic `20260921_memory_facts.py:37,48` 同 CHECK 落库（有 alembic 义务复核成立）；`alembic heads` 真跑 = `20260921_llm_usage`（链序 memory_facts → embedding → llm_usage）；extract schema `ExtractedFactItem` 仅 key/value 无 kind（:47-51）· 构造点 :129-131 默认 kind=fact（显式-only 落点复核成立）；service 查重谓词 :53-58 不含 kind · `revoke_by_source` :128-157 幂等审计先例在位；continuity `MEMORY_FACTS_HEADER` :98 · 渲染 :149-166 单循环 · 注入 :169-184 独立 SystemMessage · span :240/:243；README :21 域约定已列 `pref` · :144 非范围「画像 / preference」；`evals/memory/` 无金样（新增义务）；pytest 基线 **1210 collected**（真跑）。SPEC `1 锚点全部复核一致，**零措辞偏差**。

### R1 · 开工闸

HG-TASK-DRAFT / HG-AUDIT-R1 均 pending（20 审后人签/授权代录，本帽不签）；HG-GRAPH-MODULES **真读** `docs/_tech_graph/l1/01_modules.md` 核验：模块表已建置；memory 行在表（:28 · 路径 glob `app/ops/memory/**` · 出边 db/rag/llm/prompts · P0/P1/prompt-asset 三级备注）；`lg_rag/continuity.py` 在 lg_rag 行路径覆盖内；models/alembic 在 db 行覆盖内。本 task 按 SPEC `2 D5 判零图谱变更（不新增路由/表/事件类型/一级模块；CHECK 放宽 = 既有表既有约束迁移文件 · db 行 migrations 既有面）→ 无新签义务；memory 行**备注级更新预期**（30 交付后备注补 kind=preference 放开 · 00 代录先例对齐 prompt-asset-roadmap-p1/llm-layer-hardening）；**回炉补闸条款**钉死：30 新增一级模块 / 新增路由/表/事件类型 / 新增列/索引 → 退 10-spec 修订 SPEC + 补闸 + 图谱如实登记，不得沿用本裁定。HG-PILOT-OPSDESK-GLAYER=n/a。

### R2 · 竖切

承 SPEC `2 波次裁定：四块（闸放开 / 注入区分 / 冲突纠正 / 红线评测）是一个不可拆语义单元——只放开闸不配注入区分 = 偏好污染事实通路（静默错）；不配红线评测 = 违反手册 `1.8「先把坏了能发现装上再让功能上线」；耦合面小（闸纯函数增量 + 渲染分节 + 一个 service 入口 + 一个迁移），单 PR 不巨型。实现序承 SPEC `8：D1 闸 → D5 迁移（CHECK 先行 · 未迁移写 preference 显式炸而非静默）→ D3 service（谓词 + revoke_by_key）→ D2 渲染（分节 + span）→ D4 评测（金样 + 三态变异检验收口）。方案对比不重演，直接继承 SPEC `4 两组裁决（B1 单 SystemMessage 双节弃 B2 双消息/B3 行级标注 · E1 通路约束+双向绑定弃 E2 闸内来源判据/E3 首期收推断型）。

### R3 · 失败语义

SPEC `5 十一条失败面全收并翻四列：三静默错（幻觉偏好注入 / 偏好污染事实通路 / 清除后仍召回）各有断言 + 变异检验兜底；CHECK 未迁移显式炸非静默；跨 kind 互冲双保险（双向绑定 + supersede 谓词含 kind）；key 域漂移按码拒；偏好挤占预算列残余风险；revoke 跨 tenant/幂等；引导语锚点断言；召回故障降级沿用零改动。补过程四行：闸未签拒开工 · B1 未落盘拒收 · 无变异检验拒收（防空真规则）· 回滚卡死（downgrade 时库内有 preference 行违反旧 CHECK → 迁移注释「先清 preference 行」+ 往返冒烟钉死）。

### R4 · 可测性

验收 **27 条**全部可执行断言：闸按码断言（`kind_not_allowed` 集合外 · `key_kind_mismatch` 双向三态）· enumerable 覆盖断言同步改编 · 显式 1.0 权重断言 · 分节/无节结构断言（无偏好 → 偏好节物理不存在）· fact 节逐字节对拍 · span 双计数 · supersede 跨 kind 双保险 · revoke_by_key 幂等审计 + 清除后零召回 · 金样 + 三态全链路变异检验（缺第一态不算过）· 锚点断言替代全文快照（prompt-asset 先例）· alembic 可逆往返 + 回滚注释 · ruff 零新增 + graph-compile 绿 + diff 白名单。B1 实扫落盘 **13 行**：回归×7（gate 其余 · service_db 召回面 · injection 15 全回归守护 · extract/vector 本体 · 辅扫 4 文件 38 用例）· 改编×3（gate :37-40 语义反转 · gate :103-106 enumerable · service_db :93-96 触发方式）· 新增×2（守护测试义务 · evals 金样含于 #12）· 迁移×1（alembic 新文件）· **删除×0**。kind 直引断言全仓 tests 仅 3 处（grep 实证）——改编面钉死无遗漏。

### R5 · 交接就绪

思考充分可交 20-task-audit；与 SPEC 逐条核对**实质差异为零**（验收 27 条 = SPEC `6 各块 + 人工闸行 + 闸前置 B1，均过程化落地；SPEC `1 锚点复核零偏差）。残余风险三条全承 SPEC `7：统一预算下 preference 挤占 fact（首期量少 + span 双计数可观测）；显式-only 靠构造点单测+非范围维持（变异检验 ③ 补 · 未来新增写入通路时必须复判）；金样「编造偏好」判定确定性由 30 在 evals 落点细化。

---

### 自检结论（40 核验 · 待回填）

（待 40 核验后回填 · 当前 10-task 落稿态 · HG-AUDIT-R1 pending → 30 拒开工）

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | 10-task 落稿 · R0–R5 全轮无 early_stop · 验收 **27 条**逐块映射 SPEC `6 实质零差异（人工闸 1 / D1×5 / D2×6 / D3×3 / D4×3 / D5×3 / 变异检验×3 / 工程×3）· B1 旧测影响面 **13 行**实扫落盘（口径：tests grep 5 文件命中 · kind 直引仅 3 处 · 用例计数 9 文件 · pytest 基线 **1210 collected** 真跑 · `alembic heads` = 20260921_llm_usage 真跑）· SPEC `1 锚点复核零偏差 · HG-TASK-DRAFT=pending · HG-AUDIT-R1=pending → 30 拒开工 · HG-GRAPH-MODULES=approved（真读 `01_modules.md` · 零图谱变更 + memory 行备注级更新预期 + 偏离回炉补闸条款）· HG-PILOT-OPSDESK-GLAYER=n/a |
