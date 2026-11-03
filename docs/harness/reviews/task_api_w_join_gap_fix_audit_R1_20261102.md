# 审查文 · task_api_w_join_gap_fix · 20-R1（2026-11-02）

| 字段 | 值 |
|------|-----|
| **审查对象** | `docs/tasks/active/task_api_w_join_gap_fix.md`（分支 `task/api-w-join-gap-fix` · HG-TASK-DRAFT approved · 其余三闸 pending） |
| **审查帽** | 20-task-audit · R1 |
| **日期** | 2026-11-02 |
| **审查基准** | workspace `invoke_20261102_10_c8_evidence_archive.md`（F11/F12/F13 · §2/§5）· workspace 契约 `api-v1-tenant-readonly-context-draft.md`（F1–F6）· api/web 码面锚点亲自抽验 |
| **结论** | **FAIL**（blocker ×1 · minor ×3 · note ×3）→ **退回 10**；内容阻塞未清前禁止指示 30 开工 |

---

## 结论摘要

- **内容面**：1 个 blocker（B1 · A5/FP-5 可达性链条断裂，涉及闸决策点③与验收条款可判定性）+ 3 minor。其余维度（范围/非范围、failure_paths、红测先行、思考轮、证据一致性）核验通过。
- **流程闸**：`HG-AUDIT-R1` = **pending**（本审查 FAIL，不具备签收条件）；`HG-GRAPH-MODULES` / `HG-W-FIX-DESIGN` 均 pending。30 拒开工状态不变。

---

## 码面锚点抽验记录（全部亲自核对 · 非转述）

| task 声称 | 抽验结果 |
|-----------|----------|
| `app/ops/hitl/router.py:473 _preflight_decided_resume` · `:520 resume_request` 零 ttl/过期引用 | ✅ 坐实（`grep -in 'ttl\|过期\|expired' router.py` 零命中；函数行号精确） |
| `app/ops/hitl/store.py:116-117` TTL 闸 · `:22 STATUS_EXPIRED` 死码 | ✅ 坐实（`:116-117` 即 `time.time() - float(decided_at) > ttl_seconds → None`；hitl 域 expired 全仓仅定义无赋值；`memory/service.py:221` 确系另一域） |
| `app/ops/issues.py:29 list_issues` 与 pulls.py / overview.py 零 tenant 谓词 | ✅ 坐实（三文件 `grep -in tenant` 全零命中；`async def list_issues` 正在 `:29`） |
| `app/ops/tenant_context.py` TENANT_HEADER / `current_tenant_or_default():24-26` 回落 TENANT_A | ✅ 坐实 |
| `app/ops/deps.py:43-45` session 真源接线 | ✅ 坐实 |
| `app/ops/lg_rag/multi/nodes.py:307` 旋钮 · `:328` 默认 3600 / [1,86400] | ✅ 坐实 |
| `app/ops/hitl/auto_resume.py:104-108` 引同一 `_approval_consumption_ttl_seconds`（单一旋钮现状） | ✅ 坐实 |
| `app/ops/lg_rag/router.py:376-384` 头/session 不一致 403 | ✅ 坐实 |
| web `HitlApprovalView.vue:111,:153` mapping `/过期|expired/i` | ✅ 坐实，**但发现关键补充事实（→ B1）**：两处 mapping 均位于 `decideErrorText`/`onDecide` catch（**decide 错误路径**）；`onResume` catch（`:173-180`）**无** `/过期|expired/i` mapping——409 走 `续跑失败：${message}` 透传（`:176`），其余状态码走泛化「续跑失败（网络/服务异常），可重试」（`:179`） |
| invoke §5 实验数字（approved 后 +178s > 90s 短窗）· A4② issue `cc227ab1…` · DB 881 行全 A | ✅ 与 invoke 原文一致 |
| lint 自检 `npx spec-wave task lint` PASS | ✅ 20 复跑 PASS（2026-11-02） |

---

## Blocker（blocker > 0 → FAIL 退回 10）

### B1 · A5「web FP-5 行级提示可达」与「web 零改」非范围 + 决策点③建议方案三者不自洽

- **task 行号**：`:41`（HG-W-FIX-DESIGN ③ 建议「decide 不拒超龄 pending，resume/消费环拒超龄 approved」）· `:78`（过期出口钉在手动 resume）· `:94`（非范围：web 业务码「FP-5 渲染已存在 · 只等 api 出口」）· `:111`（failure_path：文案含「过期」→ 命中 FP-5 mapping）· `:124`（A5 验收：web FP-5「审批已过期」行级提示可达）
- **理由**：web 码面实证（本帽抽验）：`HitlApprovalView.vue:111` 的 `/过期|expired/i` mapping **只存在于 `decideErrorText`**，仅被 `onDecide` catch（`:150`）调用；`:153` 同在 decide 失败联动刷新分支。续跑按钮走的是 `onResume`（`:161`），其 catch（`:173-180`）**没有**过期 mapping：409 透传为「续跑失败：{message}」，410 等其他状态码落到泛化「续跑失败（网络/服务异常），可重试」。而 task 钉死语义「批准不过期」（`:77`，与 invoke §4 freeze 语义一致）意味着 decide 永远不会对超龄 pending 报过期——**decide 路径产不出含「过期」的错误**。于是按 task 草案建议（resume-only 出口）+ web 零改，FP-5「审批已过期，请刷新列表」**仍然不可达**，A5 验收条款不可判定（除非把 onResume 409 透传的「续跑失败：…过期…」宽认为达标——但 task 写的是 FP-5 行级提示，非泛化续跑失败）。即 task `:94`「FP-5 渲染已存在 · 只等 api 出口」的前提对 **resume 路径不成立**，`:111` failure_path 的因果链（文案含过期 → FP-5 命中）同样断裂。
- **建议修法（10 回填 · 20 不代改实质）**：
  1. 现状锚点表/闸说明补该码面事实：web 过期 mapping 仅在 decide 错误路径，`onResume` 无 mapping；
  2. HG-W-FIX-DESIGN ③ 决策点补注「选型与 A5 可达性绑定」：若签 resume-only 出口，则 A5 验收口径须改写为「行级过期提示可达（onResume 透传含『过期』文案）」并放宽 FP-5 字面；若坚持 FP-5 原态，则须把 web `onResume` mapping 增补显式列入本 task 范围（破除 :94 非范围条）或另立 web task 并在依赖表挂接；
  3. failure_paths `:111` 的「FP-5 mapping 不命中」判定条件随上述口径同步修订。

---

## Minor（不阻塞 20 结论走向，但建议随 B1 回填同批修订）

### M1 · HG-W-FIX-DESIGN 闸行决策点枚举缺「单据终态 / STATUS_EXPIRED 启用」

- **task 行号**：`:41`（闸行列三点：①状态码文案 ②freeze 增补 ③decide/resume 作用面）vs `:79`（单据终态「二选一由 HG-W-FIX-DESIGN 钉死」）· `:89`（范围：`STATUS_EXPIRED` 启用或移除按设计钉死）
- **理由**：task 正文两处把「单据终态（expired 启用与否）」显式钉给 HG-W-FIX-DESIGN，但闸行枚举只有三点、不含终态——签署人按闸行字面签三点，终态决策可能漏签，30 面临「闸已签但终态未定」的解释缝隙。
- **建议修法**：闸行补第④点「单据终态策略（启用 `STATUS_EXPIRED` 或维持 approved+错误出口）」，与 `:79`/`:89` 对齐。

### M2 · 决策点③「作用于 decide 或仅 resume」与钉死契约「批准不过期」存在选型冲突风险

- **task 行号**：`:41`（③「过期出口作用于 decide 或仅 resume」）vs `:77`（「批准不过期」不变：`adecide` 对超龄 pending 不拒）· `:122`（验收：decide 对超龄 pending 不拒回归测绿）· `:125`（decide 400/404/409/422 既有语义零变化）
- **理由**：③的字面允许「作用于 decide」，但 `:77`/`:122`/`:125` 已把 decide 侧钉成零变化——若签署人按③字面选 decide 面，三处钉死/验收全部失配。③的真实决策空间比字面窄。
- **建议修法**：③收窄表述（如「过期出口仅 resume/消费环；decide 面仅限对已 expired 终态单据的报错文案」）或注明「选 decide 面须联动修订 `:77`/`:122`/`:125`」。

### M3 · 行为变更类 task 缺显式「旧测 grep 影响面」验收项

- **task 行号**：`:126`（仅写「`pytest` 本波 + 既有 hitl/tenant/issues 回归绿」）
- **理由**：本 task 属行为变更类（resume 新增拒绝路径 · 只读面新增过滤谓词），按 20-task-audit checklist 须列「旧测 grep 影响面」——哪些既有测试编码了旧行为（如 resume 无闸正样本、跨租户列表返回全量行的断言、`tenant_id=''` fixture 行）需随修，防 30 静默改测对齐。
- **建议修法**：验收标准补一条「旧测 grep 影响面已列明（tests/ 内编码旧行为的用例清单 · 改测理由逐条注记）」。

---

## Note（核验通过项 · 留档）

- **N1 · F11/F12 覆盖无漏**：W-fix-1 = F11（手动 resume 补 TTL 闸 · 与 `store.py:116-117` 对称）+ F12（过期出口 + `STATUS_EXPIRED` 处置 + freeze 增补路径）合并设计，与 invoke §7 #5「与 F12(a) 合并设计」建议一致；F13 独立 W-fix-2 对齐 `task_tenant_readonly_predicate` 先例不另造框架 ✓。
- **N2 · 「批准不过期，执行权过期」三环自洽**：decide 不拒超龄 pending（`:77`）/ resume 拒超龄 approved（`:78`）/ 消费闸 T1 既有拒（invoke §4 TTL 行佐证兜底有效 · §5 零回执实证）——除 B1 的出口呈现层断点外，语义环本身一致 ✓。
- **N3 · 思考轮控制完备**：R0–R3 表 + 逐轮展开齐全，R3 early_stop 理由（决策面已框死）与残险（`tenant_id=''` 历史行可见性 · 30 实扫回填）均落字；W-fix-2 的 `tenant_id=''` 处置（`:82`）已留 30 回填口（实扫提出 + 回填修订表 · 默认从严）。建议（非阻塞）补一句「偏离默认从严须维护者签」，防 30 把回填口当自主裁量。
- **N4 · 非范围与回接条款**：非范围（web 码 / SSE freeze / freeze 本体 / 联调 CLOSE / 其余发现另行立项）边界清晰；A4②/A5 回接条款（`:124`）锚 invoke §C6 口径与 §5 短窗复现参数（`OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS=90`），可判定 ✓（A5 可达性本身见 B1）。failure_paths 八行覆盖闸、误拒、误伤、freeze 擅改、文案、双旋钮、404 泄漏、回接缺失，完备 ✓。

---

## 回填清单（退回 10 · 修订后重排 20-R2）

1. **B1**：现状锚点表 + HG-W-FIX-DESIGN ③ + A5 验收（`:124`）+ failure_paths（`:111`）+ 非范围（`:94`）五处联动修订，把「web FP-5 mapping 仅在 decide 错误路径」码面事实摆进签决策面，并钉死 A5 达成口径与③选型的绑定关系。
2. **M1**：闸行 `:41` 补第④决策点（单据终态 / STATUS_EXPIRED）。
3. **M2**：③收窄或加联动修订注记。
4. **M3**：验收标准补「旧测 grep 影响面」项。
5. **N3（可选）**：`:82` 补「偏离默认从严须维护者签」。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（FAIL · B1 待 10 回填）
- [ ] 10 回填修订后重排 20-R2 审查
- [ ] R2 PASS 后在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] HG-GRAPH-MODULES / HG-W-FIX-DESIGN 维护者签收
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 `docs/harness/prompts/TEMPLATE_30_gate_stop.md`）。

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-02 | 20-R1：结论 **FAIL**（B1 blocker：FP-5 可达性链条断裂 · A5 与 web 零改非范围及决策点③不自洽）· minor ×3（闸决策点缺终态项 / ③与「批准不过期」选型冲突 / 缺旧测 grep 影响面项）· note ×4 · 码面锚点全抽验坐实 · 退回 10 |
