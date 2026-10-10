# Task Audit R1：capability-mine-endpoint · 退回 10-task（BLOCKER）

> **复制说明**：原档 `docs/audits/task-review/20261011_capability-mine-endpoint_r1.md`（在案 commit daa6871）· spec-wave verify 仅扫 `docs/harness/reviews/` 且命名须 `task_capability_mine_endpoint_audit_R<N>_*.md`，00 裁定复制至此（2026-10-11）· 内容零改动 · 双址规约待序3钉

> **hat_id**：20-task-audit
> **task**：`docs/tasks/active/task_capability_mine_endpoint.md`（commit fc9885e 链 · 审查时 HEAD fc9885e）
> **上游**：SPEC `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（HG-SPEC-SIGNOFF approved 2026-10-11）+ R1 审 `docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（PASS-WITH-NITS · N1–N3 归本 task）
> **日期**：2026-10-11 · 分支：`task/tool-catalog-page`（本帽 `git branch --show-current` 核实 · 勿切 · 只 add 自己两文件）
> **task lint**：本帽复跑 `npx spec-wave task lint --file docs/tasks/active/task_capability_mine_endpoint.md` → **LINT: FAIL · EXIT=2 · [E5] 缺 ### 自检结论 节**（兄弟 task_catalog_manifest_errors_surface.md 同命令 PASS，自检结论节在其 :190）
> **task 回填**：有阻塞 · **未改** task 正文 / 人工闸表 / `app/` / `tests/`

## 结论

**BLOCKER · 退回 10 修订**：内容面全数通过（锚点 13 行全核真 · N1–N3 回填到位 · 钉死契约八条与 SPEC 纪律对齐 · TC1–TC7 可机断 · 两候选倾向合理），唯机械闸不过——`spec-wave task lint` E5「缺 ### 自检结论 节」。task 卡自身过不了 lint，HG-AUDIT-R1 不具备提请人签条件，退回 10 补节后本帽复核。三人工闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）均 **pending 照实 · 本帽不代签 · 30 拒开工**。

## 阻塞清单（退 10 修订）

| # | 内容 | 证据 | 处置 |
|---|------|------|------|
| B-1 | task 缺 `### 自检结论` 节，lint E5 FAIL（EXIT=2） | 本帽复跑 `npx spec-wave task lint --file` 输出 `[E5] 缺 ### 自检结论 节 / LINT: FAIL`；兄弟 task `task_catalog_manifest_errors_surface.md:190` 有 `### 自检结论（10 起草者）` 且 PASS | 10 补 `### 自检结论` 节（对齐兄弟 task 形态）→ lint PASS 后回本帽复核 |

## 核对表（内容面 · 全通过 · 不阻之外的实证记录）

| # | 核对项 | 结果 | 证据 |
|---|--------|------|------|
| C1 | 鉴权锚点 deps.py:18-115（N2 回填） | ✅ | `get_current_user` 本体 :18-53（401 三分支 :25-27/:40-42/:49-51 逐行核）· tenant_id 注入 :44（`"ops-desk-pilot"` 缺省逐字一致）· `CurrentUser = Depends(get_current_user)` :114 · N2 修正锚点 :18-115 取代 SPEC :56-115，到位 |
| C2 | models.py:40 role 单值 | ✅ | `role: Mapped[str] = mapped_column(String, nullable=False, default="viewer")` 单值 str；deps.py:58 `user.role != "maintainer"` 旁证成立 |
| C3 | visibility.py:112-135 求值单源 | ✅ | `evaluate_visibility(specs, principal) -> (kept, summary)` 逐行一致；被裁附 reason :126；词表 :38-41 四键；`principal_from_ctx` 主体由代码构造纪律 :54-72 在仓 |
| C4 | admin/capability.py:163-214（N1 修正锚点） | ✅ | catalog 函数体 :163-214；返回字典实起 :192（`filter`:193-203 · `principal`:204-211 · `visible_ids`:212 · `**summary`:213）——task 现状锚点表与依赖节均用 :163-214/:192-214，N1 回填到位 |
| C5 | hitl/router.py {items,count} 外形先例 | ✅ | :94 `return {"items": rows, "count": len(rows)}` · :172 同形 · 空集 :164 `{"items": [], "count": 0}` 三处逐字核 |
| C6 | 挂载点与包内禁令 | ✅ | router.py:19 `prefix="/api/ops"` · :27 仅注册 `admin_capability_router`；admin/capability.py:1-6 docstring「`app/ops/capability/` 内禁止挂 APIRouter（有测试守着）」逐字在仓 → 落点纪律（钉死契约 7）有据 |
| C7 | 次级锚点 | ✅ | gateway.py:133-143 `capability_catalog_snapshot` → :143 调 `evaluate_visibility`；conftest.py:414 viewer fixture；test_hitl_pending_decide.py:50 `role="viewer"`；builtin.v1.yaml:7-29 字段族 + `adapter` :26（排除对象实证）；全仓 grep `capability/mine` 码面零命中（仅文档命中） |
| C8 | N3 回填（roles 映射钉死 + ⊆ 对拍） | ✅ | 钉死契约 2：`roles=frozenset({user.role})`（单值→集合 · 禁取自请求参数/模型产出 · 与 visibility.py:54-72 纪律同源）；TC3 viewer fixture ⊆ maintainer 对拍机断 + FP-4 漂移处置——R1 N3 要求逐条落成 |
| C9 | SPEC 承接完整性 | ✅ | §2 B1 端点形态/字段族九键/`{items,count}`/空集 200/防探测 · §4 Q1（catalog新立）/Q3（CurrentUser）裁定存续 · §5 FP-1/FP-2/FP-5/FP-6 承接为 task FP 表 · 设计纪律 #1/#3/#4/#5 落成钉死契约 6/3/4/（freeze_id 无）；N4/N5 正确不在本 task（N4 归兄弟 task manifest-errors · N5 00 知悉项） |
| C10 | 钉死契约与 TC 可机断 | ✅ | 契约 1–8 条各有锚点/禁令出处；TC1（401）· TC2（九键+对拍）· TC3（⊆+roles 断言）· TC4（空集 200）· TC5（grep `adapter`/`local_fn:` 零命中）· TC6（单测对拍求值直出）· TC7（pytest/ruff/lint-imports/graph-compile/spec-wave verify 五命令）均可 pytest/grep 机断，无人工判断残留（TC6 走查为附属人工项，主体机断） |
| C11 | 候选倾向合理性 | ✅ | ①落点 `app/ops/capability_mine.py` 新模块：避开包内 APIRouter 禁令（C6）· 与 issues.py/pulls.py 同级用户态模块 · 不锁死留 30，合理；②baseline_filter 默认不叠加：admin catalog 现状默认 `baseline=True`（capability.py:166/:178-180 实证），用户面语义=身份求值而非场景裁剪，对拍以 `evaluate_visibility` 直出为准——倾向成立且 FP-8 留 30 实证 registry 后裁定，开放性显式，合理 |
| C12 | 流程面 | ✅ | 三闸 pending 不代签（闸表 4 列契约 · 389e0d5 已收口解析告警）· orchestration 10→20→维护者签→30 与 required_invoke_hats `10,20,30,40` 一致 · 思考轮 R0–R5 闭合 early_stop at R5 · 修订记录两行在案 · 10 invoke 已留档 |

## 非阻塞清单（nits · 照登 · 不阻修订后复核）

| # | 级别 | 内容 | 建议 |
|---|------|------|------|
| n-1 | 文献 nit | 钉死契约 1 / FP-1 引 401 分支仅 :25-27/:40-42，漏第三分支 :49-51（user not found）；现状锚点表 :51 行已含三分支 | 10 补节时顺手统一为三分支（或维持「承 get_current_user 既有语义」概括句）；不阻 |
| n-2 | 文献 nit | R1 思考轮称「锚点 12 行全亲读」，现状锚点表实 13 行 | 顺手改计数；不阻 |

## 复核入口

10 补 `### 自检结论` 节 → `npx spec-wave task lint --file` PASS → 回本帽复核（仅重核 E5 + diff 触碰面）→ HG-AUDIT-R1 提请维护者签。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 20 R1：骨架先行 commit（e87d85f）→ 填肉：锚点 13 行+N1–N3+SPEC 承接全核真（C1–C12 ✅）· 唯 lint E5 缺自检结论节 → **BLOCKER 退 10 修订** · nits n-1/n-2 照登 |
