# SPEC 书面审查：tool-catalog-page · R1（20-spec-audit）

## 元信息

| 字段 | 值 |
|---|---|
| **帽** | 20-spec-audit（SPEC 书面审 · 不实现代码 · 不改 SPEC 实质内容） |
| **日期** | 2026-10-11 |
| **对象 SPEC** | `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（v0 · draft · commit ff3348d · HG-SPEC-SIGNOFF=pending） |
| **轮次** | R1（轻量路径：10-spec 思考轮 R0–R5 已回填充分，单轮书面审） |
| **实证抽查范围** | `app/ops/admin/capability.py` · `app/ops/capability/gateway.py`(:110-169) · `app/ops/capability/visibility.py` · `app/ops/capability/manifest.py`(:140-219) · `app/ops/capability/manifests/builtin.v1.yaml` · `app/ops/capability/manifests/oa.readonly.v1.yaml` · `app/ops/deps.py` · `app/ops/router.py` · `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` · 上游 `docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md`（主仓副本只读 · 见 N5） |

## 核对项表

| # | 核对项 | 结果 | 证据 / 说明 |
|---|---|---|---|
| C1 | 范围可界：B1（用户态工具端点 · 新立） | ✅ | §2 B1 端点语义表齐全（`GET /api/ops/capability/mine` · 字段族九键 · `{items, count}` 外形 · 空集 200 如实）· 只回可见集防探测、复用求值单源、排除 adapter 三纪律落成 |
| C2 | 范围可界：B2（admin 总表原地增键 · 向后兼容） | ✅ | §2 B2 既有键全保留 + 新增 `items` 全在册条目（13 字段族 + `status` 三态 + `visibility_reason`）；纪律 #2 锁「只增不删 · 既有调用方零 diff」 |
| C3 | 范围可界：F1 仅概要 · 前端专项 SPEC 另立 | ✅ | §2 F1 三行概要（表格列 / admin 总表模式 / 空态）+ §6「以前端专项 SPEC 为准」· 与 Q4 裁定一致 |
| C4 | 非范围锁死 | ✅ | §3 七条显式排除（注册/启停 · 执行/编排/委派面 · MCP 挂起 · 前端细节 · SSE · args_schema · 跨用户对比）；freeze_id=「无 · 零 SSE 帧改动」 |
| C5 | D 组边界完整性 | ✅ | §3 行 90「非只读测试 capability 归 D 组 task」· §8 相邻工作面 D 组 · 纪律 #1 manifest 真源零改动；同 commit ff3348d 附 D 组 00 启动 Prompt（`docs/harness/invokes/by-task/_prompts/PROMPT_00_capability-expansion_20261009.md`），观测面（本 SPEC）与注册面（D 组）两轨互不越界 |
| C6 | Q1–Q4 全部作答 · ≥2 案对比 · 维护者原话留痕 · 候选不锁死 | ✅ | Q1「catalog新立」/ Q2「admin是超级管理员可看的总表…扩充返回内容」/ Q4「B2可以先用方案2」（承前批 · 见 N5）与头部立项令行（SPEC :5）逐字一致；Q3 本帽裁定理由成立（需求原话「当前用户权限下所有工具」→ 任意登录用户 · 可见集由 `evaluate_visibility` 按 principal 区分 · 未登录 401）；弃选项均有理由，未锁死未来空间 |
| C7 | failure_paths FP-1~FP-6 可机验 | ✅ | FP-1 401 承 `get_current_user` 既有语义（deps.py:25-27/40-42 实证在仓）；FP-2 空集 200；FP-3 故障可观测；FP-4 既有键对拍；FP-5「响应体不含 `adapter`/`local_fn:` 子串」可 grep 机断；FP-6 走查 + 单测对拍求值函数直出 |
| C8 | 验收标准 B1/B2 全可机断 | ✅ | §6 B1 四条（字段族齐 / 与 `evaluate_visibility` 对拍 / 401 / viewer ⊆ maintainer）· B2 三条（既有键逐键零 diff / items 全覆盖 + 三态可分辨 / 故障注入可观测）· 契约图谱三条（SSE 零 diff / G-L1 行备注 / pytest+lint-imports 绿）均可 pytest 机断 |
| C9 | 契约面（freeze 零动）可 diff 断言 | ✅ | §6「零 SSE 帧 diff」机断可行；本 SPEC 纯 REST 查询面 · 无 SSE 触点 |
| C10 | R0–R5 控制表齐全 · early_stop=no 合理 | ✅ | §7 六轮全 done + early_stop=no；四裁定全作答、无遗留开放项，无提前停止理由 |
| C11 | 实证锚点①：capability 查询面仅 admin 系 · 无用户态端点 | ✅ | `app/ops/router.py:4/:27` 仅注册 `admin_capability_router`；全仓 grep `capability/mine` 零命中；admin 五端点 `/runtime`(:79) · `/catalog`(:163) · `/metrics`(:217) · `/receipts`(:228) · `/idempotency`(:255) 与 SPEC :39 一致 · `AdminSyncAuth` 鉴权（:43 import · :165 用） |
| C12 | 实证锚点②：catalog 现状 `capability.py:163-216` 仅回 `{filter, principal, visible_ids, **summary}` | ✅（nit 见 N1） | catalog 函数实位于 :163-214；返回字典实起 :192（SPEC :40 引 :199-215 未含起始行 · 见 N1）；返回键与 SPEC 描述逐键一致（`filter`:193-203 · `principal`:204-211 · `visible_ids`:212 · `**summary`:213）· 无描述/权限/状态字段 ✓ |
| C13 | 实证锚点③：manifest 字段族在册 `builtin.v1.yaml:7-29` | ✅ | `capabilities:` 于 :7；首条目 :8-26 含 SPEC 列全部字段：`id`/`kind`/`description`/`when_to_use`/`when_not_to_use`(:12)/`tags`/`risk_level`/`side_effect`/`enabled`/`tenant_scoped`/`reversible`(:22)/`execution_type`(:23)；`adapter: local_fn:...`(:26) 实证纪律 #4 排除对象存在 |
| C14 | 实证锚点④：`capability_catalog_snapshot`（gateway.py:133-143）→ `evaluate_visibility` | ✅ | gateway.py:133-143 逐行一致（:143 调 `evaluate_visibility`）；visibility.py:112-135 回 `(kept, summary)` · `visibility_hidden` 各附 `reason`（:126 · 词表 :38-41 department/role/project/classification）——B2 `denied:<原因码>` + `visibility_reason` 数据源实证在仓 |
| C15 | 实证锚点⑤：manifest 故障静默缺条目 | ✅ | manifest.py:200 `logger.error("manifest 加载失败（已跳过该文件）: %s: %s", ...)` 与 SPEC :43 引文逐字一致；`get_capability_manifest_metadata`（:145-147）仅回 version+count —— 失败仅见日志与加载期返回值，端点面不可观测，缺口 #5 成立 |
| C16 | 实证锚点⑥：`deps.py:56-115` 鉴权依赖 | ✅（nit 见 N2） | `CurrentUser = Depends(get_current_user)` :114 ✓ · `request.state.ops_tenant_id` 赋值 :44 ✓ · `AdminSyncAuth` :116 ✓；唯 SPEC §8 引区间 :56-115 未含 `get_current_user` 本体（:18-53 · B1 实际依赖入口，见 N2） |
| C17 | 可见集实证：8 个 tool 全 `side_effect: read` | ✅ | builtin.v1.yaml 5 枚（mock_get_issue_status / mock_get_deploy_info / utc_now_iso / get_issue_by_number / get_pr_by_number）+ oa.readonly.v1.yaml 3 枚（oa.doc.search / oa.org.whois / oa.todo.mine）= 8 枚全 `side_effect: read`；验收记录 :32「可见集 8 个 tool · 全只读」一致 |
| C18 | 与终局文档 A 面定位对齐 | ✅ | `DESIGN_agent_contribution_endgame_v0_zh.md:35`「P0：D 组写面零突破 + A/B 观测面（工具列表页 · 全量过程展示 · SSE 导出）」——本 SPEC 即 A 面「工具列表页」；纯只读零写 + F1 数据源 B1 与观测面定位一致（文档不在本分支 · 见 N5） |
| C19 | 人工闸字段 pending 照实 | ✅ | SPEC :27 `HG-SPEC-SIGNOFF | pending`；本帽不代签 |

**核对计数**：19 项 · 通过 19 · 部分通过（含 nit）0 · 不通过 0（C12/C16 判 ✅ 附非阻塞 nit N1/N2）


## 阻塞清单

无。范围/非范围边界清晰可执行，D 组注册面与本 SPEC 观测面互不越界，Q1–Q4 裁定闭合且维护者三裁定原话与立项令逐字一致，FP-1~FP-6 与验收标准均可机断，19 项实证抽查与代码真值一致。未发现需退回 10-spec 的实质缺口。

## 非阻塞清单（nits · 不阻签收 · 建议 00 拆 task 时顺手处理）

| # | 级别 | 内容 | 建议 |
|---|---|---|---|
| N1 | 文献 nit | SPEC :40 锚点 `capability.py:199-215` 未含返回字典起始行（return 实起 :192，函数体 :163-214） | 实现 task 引用时改为 `:163-214`（或 `:192-214`）；SPEC 本体无需为此升版 |
| N2 | 文献 nit | SPEC §8 锚点 `deps.py:56-115` 未含 `get_current_user` 本体（:18-53 · B1 鉴权实际入口） | 实现 task 引用时改为 `:18-115`；SPEC 本体无需为此升版 |
| N3 | 交付提示 | Q3 `CurrentUser` 口径下 viewer 的 Principal 构造未钉死：`OpsUser.role` 为单值（deps.py:58 实证），映射到 `Principal.roles` 集合的口径属实现细节 | B1 task 钉 roles 映射（如 `roles={user.role}`）并固化 viewer fixture ⊆ maintainer 对拍断言（§6 已要求，机断可行） |
| N4 | 交付提示 | B2 `manifest_errors` 落点 SPEC 留「实现 task 裁定」——现状 `get_capability_manifest_metadata` 仅回 version+count（manifest.py:145-147），故障仅 `logger.error`（:200） | B2 task 在两候选落点（summary 增 `manifest_errors` 键 / 扩既有 meta 面）中裁一，验收以故障注入断言为准（§6 已钉，机断可行） |
| N5 | 观察 | 上游终局文档 `docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md` 不在本 worktree 分支（居 `docs/agent-contribution-roadmap` · 维护者令 D2 收口后合入），C18 对齐核对基于主仓副本只读；另 Q4 引原话「B2可以先用方案2」系承前批选项编号，与本文 Q4 S1/S2 编号不直接对应 | 00 知悉即可；拆 task 时勿将「方案2」误读为本文 Q4 S2（弃选项），其义为承 chat-history-hitl-ux Q4 同款分仓策略（即本文 S1） |

## HG-SPEC-SIGNOFF 建议

建议签收（pass）。本帽不代签 human_gate；维护者签录后可由 00 起草后端 task（B1/B2 可先并行拆 · invoke_slug=`tool-catalog-page`），前端 F1 依 Q4 由前端专项 SPEC 另立（ops-desk-web 仓）。拆 task 时携带 N1–N4 回填。

## 结论：R1 PASS-WITH-NITS

R1 书面审 **PASS-WITH-NITS**：19 项核对全数通过，六组实证锚点与代码真值一致（catalog 简略出站 · manifest 字段族在册 · 可见性求值完备 · 故障静默缺口 · 鉴权依赖 · 8 枚全只读可见集），Q1–Q4 裁定闭合且维护者原话留痕无误，failure_paths 与验收标准均可机断执行，与终局文档 A 面观测面定位对齐；五条非阻塞 nits（两处锚点行号微偏 / viewer principal 映射 / manifest_errors 落点 / 上游文档跨分支与承前批编号）移交 task 阶段处理，不影响 HG-SPEC-SIGNOFF 进入人签。

