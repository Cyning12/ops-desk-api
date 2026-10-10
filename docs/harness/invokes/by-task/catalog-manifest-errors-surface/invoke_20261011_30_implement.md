# Invoke：catalog-manifest-errors-surface · 30-implement（2026-10-11）

| 字段 | 值 |
|------|-----|
| **hat_id** | 30-implement |
| **task** | \`docs/tasks/active/task_catalog_manifest_errors_surface.md\`（SPEC tool-catalog-page §2 B2） |
| **分支 / worktree** | \`task/tool-catalog-page\`（勿切 · 与兄弟棒 B1 capability-mine-endpoint 并行同树） |
| **基线** | fec3abf（三闸 approved 代录在案） |
| **交付 commit** | 25de9d7（审查档复制 canonical 址）→ 520425f（红测先行）→ 2bf0bd1（闸表归一+NIT 消化）→ 2a2503d（实现+白名单补边） |
| **三闸核验** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved（verify PASS 实证见下） |

## Prompt 快照（钉死契约承接）

七条钉死契约逐条落地：①catalog 既有键逐键零 diff · 只增顶层两键 + hidden visibility_reason 子键 ✅（TC1/TC2 对拍机断）；②get_capability_manifest_metadata 与 /runtime 零 diff ✅（TC4 断言两键集 · tests/test_capability_manifest.py:331/:354 原样绿）；③故障记录=load_capability_manifests failed 集模块级留存 · reload 成功清该文件记录 · 禁无理由自动清零 ✅（_MANIFEST_LOAD_ERRORS path→error · _commit 成功 pop · TC4 生命周期实证）；④visibility_reason 映射表落 visibility.py 词表旁（VISIBILITY_REASON_TEXTS）· 路由零重算 ✅（TC3 钉源+直出对拍）；⑤只读零写 ✅；⑥details 不透 adapter/local_fn: 子串 ✅（TC1 断言）；⑦鉴权不动 ✅（as_admin override 同 observability 先例 · 未触鉴权码面）。

## GATE_VERIFY（开工前实证）

| 核验 | 结果 |
|------|------|
| 人工闸表三行 | approved（fec3abf 在案 · 00 代录） |
| \`npx spec-wave verify --task\` 初跑 | **BLOCKED**——闸表 3 列+状态格内嵌说明，解析器 0 行可读（WARN 提示须 4 列末列说明） |
| 闸表归一（2bf0bd1） | 归一 4 列 canonical（status 纯 approved · 注解移说明列 · 00 裁定 · B1 同病父另行知会）· NIT-1 删「/#6」· NIT-2 B1 表锚 :413-435→:409-435 |
| 归一后复跑 | **BLOCKED · missing R<n> review**——findLatestReview 只扫 docs/harness/reviews/ 且命名须 task_<slug>_audit_R<n>_*.md；20 帽 R1 实落 docs/audits/task-review/ 新址（c3d5e57 内容无误纯落点不命中） |
| 审查档复制（25de9d7 · 00 裁定 m00083 授权超清单） | 复制 → docs/harness/reviews/task_catalog_manifest_errors_surface_audit_R1_20261011.md · 档头注来源 c3d5e57 · 原档保留 · 双址规约待序3钉 |
| 终态复跑 | **VERIFY: PASS**（2a2503d 后实证） |

## 改动文件清单

| 文件 | 性质 | 说明 |
|------|------|------|
| \`tests/test_admin_capability_manifest_errors.py\` | 新增（520425f 红 → 2a2503d 修 TC4 断言形） | TC1–TC4 四用例 · autouse fixture 快照/还原 _MANIFEST_LOAD_ERRORS（FP-1 禁跨用例泄漏） |
| \`app/ops/capability/manifest.py\` | 改（2a2503d） | \`_MANIFEST_LOAD_ERRORS: dict[str, str]\`（path→error · :108 旁）+ \`get_manifest_load_errors()->list[dict]\`（按 path 排序 · 多副本对拍稳定）· load_capability_manifests 失败分支留存 · _commit 成功 pop（load/reload 统一覆盖 · 契约3） |
| \`app/ops/admin/capability.py\` | 改（2a2503d） | catalog 顶层增 manifest_errors(int)+manifest_error_details([{path,error}]) 两键（summary 后）· import get_manifest_load_errors 直引 manifest 子模块（__init__ 不加导出 · 不在清单） |
| \`app/ops/capability/visibility.py\` | 改（2a2503d · **00 裁定 m00056 授权超清单**） | \`VISIBILITY_REASON_TEXTS\` 词表落 REASON_* 旁（单源 · SPEC 纪律 #3）+ evaluate_visibility hidden 条目增 visibility_reason 子键（未知码原样返回不静默吞） |
| \`.importlinter\` | 改（2a2503d · **00 裁定 m00208 授权 · 唯一一处**） | admin 允许清单 :296-305 区间字母序补 \`app.ops.admin.capability -> app.ops.capability.manifest\` 一边 |
| \`docs/harness/reviews/task_catalog_manifest_errors_surface_audit_R1_20261011.md\` | 复制（25de9d7 · 00 裁定 m00083） | 源 docs/audits/task-review/ c3d5e57 保留 · 档头注来源 |
| \`docs/tasks/active/task_catalog_manifest_errors_surface.md\` | 归一+回填（2bf0bd1 / 本 invoke 轮） | 闸表 4 列 canonical · 修订表留痕 · TC1–TC5 勾选 |

## 验收命令结果（TC5 + 基线对照）

| # | 命令 | exit | 结果 |
|---|------|------|------|
| 1 | \`.venv/bin/python -m pytest tests/test_admin_capability_manifest_errors.py\` | 0 | **4 passed**（红测先行时序：520425f 时 ImportError 红 · 实现后全绿） |
| 2 | 受影响面五文件（manifest/manifest_http/admin observability/visibility_receipts/本文件） | 0 | **85 passed** |
| 3 | \`.venv/bin/python -m pytest tests -q\`（全量） | 1 | **1653 passed, 1 skipped, 4 failed**——4 红全基线同现同败：hitl asyncpg + memory_vector_p1（stash 基线复跑同败 · B1 钉案一致）+ multi_replica hitl 两枚（HEAD~1 回退本帽五文件复跑同败 · 共享测试库状态敏感）→ **零新增红成立** |
| 4 | \`ruff check\` 触及四文件 | 1 | 2 errors（I001 import 排序 + 多余括号）**stash 基线复跑同现** → 零新增；format 差异同基线 |
| 5 | \`.venv/bin/lint-imports\` | 0 | **12 kept, 0 broken**（补边后） |
| 6 | \`./scripts/graph-compile.sh\` | 0 | EXIT=0（implementedBy 提示为既有 warning · 不咬 exit） |
| 7 | \`npx spec-wave task lint --file\` | 0 | **LINT: PASS** |
| 8 | \`npx spec-wave verify --task\` | 0 | **VERIFY: PASS** |
| 9 | 多副本 parity（multi_replica -k "catalog or parity"） | 0 | 1 passed（FP-3 新键跨副本一致） |

## TC1–TC5 逐条结论

- **TC1 故障注入可观测** ✅：tmp 坏 manifest（capabilities 非 list）注入 → catalog manifest_errors==1 · details 含 path+error · 无 adapter/local_fn: 子串 · 既有键逐键==注入前基线。
- **TC2 零故障基线** ✅：manifest_errors==0 · details==[] · 键集精确=既有+两新键 · summary 逐键==capability_catalog_snapshot 直出（路由零重算机断）。
- **TC3 visibility_reason 钉源** ✅：department 受限 fixture → hidden entry reason==REASON_DEPARTMENT 且 visibility_reason==VISIBILITY_REASON_TEXTS 词表值 · body==snapshot 直出 · 词表覆盖四码。
- **TC4 失败域隔离与生命周期** ✅：好坏混载 好文件注册/坏文件 failed · 记录只含坏 path · 修好 reload 后记录清除 · meta 两键集=={version, capability_manifest_count} 且 version 确变（钉死契约 2/3）。
- **TC5 工程面** ✅：九命令上表 · 三闸 approved 后才 30（verify PASS 在案）。

## 图谱实判（F5 回写义务）

预判 n/a **实证维持 n/a**：改动面收敛于既有端点响应增键 + capability 包内模块级记录 + visibility 词表——无新一级模块/路由/SSE 事件/表/env，modules.md capability 行既有「观测快照 visibility.py（经 admin 模块端点暴露）」+ admin 行备注覆盖语义；task :18-20 条件回写触发器（新 env 旋钮/新机制面）未命中 → 零回写 · HG-GRAPH-MODULES 无需新签录（既有 approved 在案）。

## 关键裁定与实证记录

1. **visibility.py 超清单授权（00 裁定 m00056）**：task 钉死契约 4 明写映射表落 visibility.py（真值源），父令文件清单遗漏 → 授权照改 · B1 零撞车确认在案。
2. **.importlinter 白名单补边（00 裁定 m00208）**：admin→capability.manifest 新边触发 import-linter 契约 BROKEN（test_splittability_hardening d2 两枚红 · stash 基线实证系我新边）；备选排除——__init__.py 加导出不许（不在清单）/ 函数内挪导入 lint-imports 仍抓 AST · 唯一正解=逐边枚举白名单补一行 · 授权限定唯一一处。
3. **审查档 canonical 址复制（00 裁定 m00083）**：spec-wave findLatestReview 只扫 docs/harness/reviews/ + 命名口径；双址并存规约待序3钉。
4. **基线对照方法学**：全量 4 红逐一实证——stash（未 commit 期）与 HEAD~1 checkout（commit 后）两法互证基线同败；首跑 multi_replica 两枚曾绿、次跑红 → 共享测试库状态敏感，非本帽引入。
5. **并行纪律**：同树兄弟棒 B1（f79fe3f 实现 + 863260c 闸表归一已交织在案）；本帽 git add 仅己文件 · B1 task 档/invoke 零触达。

## 非范围照登

用户态 /capability/mine 端点（B1 兄弟 task · f79fe3f 已交付）· __init__.py 导出面 · 鉴权码面 · 前端页面 · 热加载语义——均不在本 task。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 30 交付：红测先行（520425f ImportError 红）→ 实现（2a2503d 4 绿）· 全量 1653 passed 零新增红（4 红基线两法互证）· 工程面九命令绿 · 图谱实判维持 n/a · 三裁定（visibility/.importlinter/审查档）落地留痕 |
