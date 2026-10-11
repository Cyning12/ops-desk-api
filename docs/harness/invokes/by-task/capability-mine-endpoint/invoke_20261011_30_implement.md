# Invoke：capability-mine-endpoint · 30-implement（2026-10-11）

| 字段 | 值 |
|------|-----|
| **hat_id** | 30-implement |
| **task** | `docs/tasks/active/task_capability_mine_endpoint.md`（SPEC tool-catalog-page §2 B1） |
| **分支 / worktree** | `task/tool-catalog-page`（勿切 · 与兄弟棒 B2 catalog-manifest-errors-surface 并行同树） |
| **基线** | fec3abf（三闸 approved 代录在案 · 授权 m01606/m00255） |
| **交付 commit** | e30b7ca（红测先行）→ 826b2ff（审查档复制）→ 863260c（闸表归一）→ f79fe3f（实现+modules.md 回写） |
| **三闸核验** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved（闸表 + fec3abf 在案 · verify PASS 实证见下） |

## Prompt 快照（钉死契约承接）

八条钉死契约逐条落地：①GET /api/ops/capability/mine · CurrentUser 任意登录用户 ✅；②Principal 由会话构造（user_id=str(user.id) · tenant_id=request.state.ops_tenant_id 缺省 ops-desk-pilot · roles=frozenset({user.role}) · departments/projects 空 · classification_max 缺省 · 禁取自请求参数）✅；③可见性单源 evaluate_visibility（经 capability_catalog_snapshot · 路由层零过滤零排序）✅；④出站白名单九键 + status="available" 常量 · adapter/args_schema/when_not_to_use/tenant_scoped/reversible/execution_type 排除 ✅；⑤只回可见集防探测 · 空集 200 ✅；⑥只读零写零迁移零新 env ✅；⑦落点 app/ops/capability_mine.py 包外 + lint-imports 绿 ✅；⑧baseline_filter 不叠加（裁定依据见下）✅。

## GATE_VERIFY（开工前实证）

| 核验 | 结果 |
|------|------|
| 人工闸表三行 | approved（fec3abf 在案 · 00 代录） |
| `npx spec-wave verify --task` 初跑 | **BLOCKED（HG-AUDIT-R1 pending）**——与闸表 approved 自相矛盾 |
| 根因实证（探针 m00044） | spec-wave 解析器不吃「粗体+中文括注」status 单元格；归一为纯 approved 后同内容判 PASS |
| 00 裁定（m00056 / m00068） | 闸表归一 4 列 canonical（注解移说明列 · 修订表留痕）+ 审查档复制至 `docs/harness/reviews/` 机读口径（命名 task_capability_mine_endpoint_audit_R1/R2_20261011.md · 源 daa6871 保留） |
| 处置后复跑 | **VERIFY: PASS**（863260c 后） |

## 改动文件清单

| 文件 | 性质 | 说明 |
|------|------|------|
| `tests/test_capability_mine.py` | 新增（e30b7ca 红 → f79fe3f 修） | TC1–TC6 六用例 · fixture manifest 自控在册集（clear→register→恢复默认承 gateway 先例） |
| `app/ops/capability_mine.py` | 新增（f79fe3f） | `router=APIRouter(tags=["ops-capability"])` + `GET /capability/mine` + 公开投影函数 `project_capability(spec)` 九键 + `_principal_from_request` 会话构造 |
| `app/ops/router.py` | 注册一行（f79fe3f） | import（字母序 auth 后）+ `router.include_router(capability_mine_router)`（admin_capability_router 后） |
| `docs/_tech_graph/l1/01_modules.md` | 备注（f79fe3f） | `api` 行增 2026-10-11 注册备注 + HG-GRAPH-MODULES 签录行（00 代录 · 不新增一级模块 · 零新跨模块边 · 不增 implementedBy） |
| `docs/tasks/active/task_capability_mine_endpoint.md` | 归一+回填（863260c / 本 invoke 轮） | 闸表 status 纯 approved · 修订表留痕 · TC1–TC7 勾选 + 自检结论（30 实施者） |
| `docs/harness/reviews/task_capability_mine_endpoint_audit_R1/R2_20261011.md` | 复制（826b2ff） | 00 裁定 m00068 · 档头注来源 daa6871 · 原档保留 · 双址规约待序3钉 |

## 验收命令结果（TC7 五命令 + 基线对照）

| # | 命令 | exit | 结果 |
|---|------|------|------|
| 1 | `.venv/bin/python -m pytest tests/test_capability_mine.py` | 0 | **6 passed**（红测先行时序：e30b7ca 时 6 failed · 实现后全绿） |
| 2 | `.venv/bin/python -m pytest -q`（全量） | 1 | **1652 passed, 1 skipped, 1 failed**——failed 为 `test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker`（SILICONFLOW_API_KEY 缺失环境性存量）；**基线对照**：临时 worktree checkout fec3abf 同命令复跑**同现同败** → 零新增红成立 |
| 3 | `.venv/bin/ruff check app/ops/capability_mine.py app/ops/router.py tests/test_capability_mine.py` | 0 | All checks passed |
| 4 | `.venv/bin/lint-imports` | 0 | **12 kept, 0 broken** |
| 5 | `./scripts/graph-compile.sh` | 0 | EXIT=0（implementedBy 提示为既有 warning · 不咬 exit） |
| 6 | `npx spec-wave verify --task docs/tasks/active/task_capability_mine_endpoint.md` | 0 | **VERIFY: PASS**（三闸 approved · ✅可30） |

## TC1–TC7 逐条结论

- **TC1 鉴权** ✅ `test_mine_requires_auth_401`：无 cookie → 401（真路径 · 未挂 override）。
- **TC2 maintainer 字段族+对拍** ✅：九键齐 · count==len(items) · status="available" · id 集与 capability_catalog_snapshot 直出完全一致。
- **TC3 viewer⊆maintainer** ✅：真子集机断（viewer 无 fixture_maintainer_only · 有 fixture_visible_all · ⊆ 且 ≠）。
- **TC4 空集如实** ✅：全裁 → 200 `{"items": [], "count": 0}`。
- **TC5 出站白名单** ✅：resp.text grep "adapter"/"local_fn:" 零命中 · 键集精确九键（fixture 故意带 args_schema/when_not_to_use/tenant_scoped/reversible/execution_type 证不泄露）。
- **TC6 单源对拍** ✅：路由返回 == capability_catalog_snapshot 直出经 project_capability 投影（含顺序）——路由层零过滤机断。
- **TC7 工程面** ✅：五命令上表 + G-L1 行备注 + HG-GRAPH-MODULES 签录。

## 关键裁定与实证记录

1. **baseline_filter 不叠加（钉死契约 8 · FP-8 裁定）**：baseline_filter（baseline.py:33-44 · kinds={local_fn}+allow_tags_any={oa}+deny_high_risk+deny_write）是 admin catalog 的**场景收窄预设**；用户面语义是**身份求值**（evaluate_visibility 对 principal 的 fail-closed 判定）。叠加会产生第二裁剪真源，与钉死契约 3（可见性单源）/TC6（对拍直出）冲突；实证 builtin.v1.yaml 在册 5 枚 local_fn read 全低风险，叠加与否对本仓现状输出无差，但语义上叠加即双真源 → **不叠加**，裁定依据留此。
2. **dependency_overrides 签名陷阱（教训）**：override 函数禁 `*args/**kwargs`——FastAPI 按 override 自身签名解析，`*a, **k` 被当 required query 参数报 422。修正为零参签名（tests/test_capability_mine.py `_override_user` 注释在案）。
3. **spec-wave verify 审查档口径墙（00 裁定 m00068 处置）**：verify 只扫 `docs/harness/reviews/` 且命名须 `task_<slug>_audit_R<N>_<date>.md`；本 task R1/R2 原档在 `docs/audits/task-review/` 新址 → 复制双址（档头注来源 · 原档保留 · 双址规约待序3钉）。
4. **并行纪律**：同树兄弟棒 B2（520425f 红测 commit 已交织在案）；本帽 git add 仅己文件 · B2 task 档（M 态）零触达；router.py/modules.md 无撞车。

## 非范围照登

admin 面字段族端点 / manifest_errors 面（B2 兄弟 task）· capability 包内改动 · 执行语义 · 前端页面——均不在本 task。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 30 交付：红测先行（e30b7ca 6 红）→ 实现（f79fe3f 6 绿）· 全量 1652 passed 零新增红（基线对照实证）· 工程面五命令绿 · modules.md 行备注+签录 · 闸表归一/审查档复制（00 两裁定落地） |
