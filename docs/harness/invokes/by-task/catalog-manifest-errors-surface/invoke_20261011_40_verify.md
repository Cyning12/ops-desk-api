# Invoke：catalog-manifest-errors-surface · 40-verify（2026-10-11）

| 字段 | 值 |
|------|-----|
| **hat_id** | 40-verify |
| **task** | `docs/tasks/active/task_catalog_manifest_errors_surface.md`（SPEC tool-catalog-page §2 B2） |
| **分支 / HEAD** | `task/tool-catalog-page` @ 42803fc（B2 完工 42803fc · 与 B1 同树共存已复验） |
| **基线** | fec3abf（对拍用临时 worktree /tmp/base-fec3abf） |
| **核验范围** | diff 逐条复核（归 B2：manifest.py + visibility.py + admin/capability.py + .importlinter + tests）· 全量工程面复跑 · live 冒烟（坏 manifest + 限定 manifest 双注入 curl 实证） |

## 钉死契约逐条复核（diff 对拍）

| # | 契约 | verdict | 证据 |
|---|------|---------|------|
| 1 | catalog 顶层增 `manifest_errors:int` + `manifest_error_details:[{path,error}]`（details 按 path 排序） | ✅ | admin/capability.py 两键插于 summary 之后；get_manifest_load_errors() 返回 `sorted(...)` list of {path,error}（manifest.py） |
| 2 | 既有响应键逐字节不动（顶层键序/visible_ids/summary/hidden 序） | ✅ | git diff 纯增两键，既有键零 diff；live /runtime manifest meta 仍精确两键 {version, capability_manifest_count} |
| 3 | 错误态留存：模块级 _MANIFEST_LOAD_ERRORS dict(path→error) · 首次加载失败也计 · 成功修复后 pop（load/reload 统一） | ✅ | load_capability_manifests 失败分支 `_MANIFEST_LOAD_ERRORS[path]=error`；`_commit` 成功路径 pop；reload 复用同函数 |
| 4 | hidden 条目增 `visibility_reason:str` 键（reason 中文映射 · 未知码原样返回） | ✅ | visibility.py `VISIBILITY_REASON_TEXTS` 四码词表 + `.get(reason, reason)` 兜底；hidden append 处增子键 |
| 5 | 四码词表精确（department_mismatch=部门不在该能力的可见范围内 等） | ✅ | 词表逐条对拍 SPEC §2 B2 词表一致；live 实证 department_mismatch → 「部门不在该能力的可见范围内」 |
| 6 | .importlinter 补边 admin.capability→capability.manifest（00 裁定授权 · 无环） | ✅ | diff 增一行 allowed import；lint-imports 12 kept 0 broken 亲跑 |
| 7 | 零 schema/迁移/env · 零运行时行为变化（仅观测面） | ✅ | diff 无 db/alembic/env；catalog 计算路径仅增读取 |

## 工程面复跑（40 亲跑 · 与 B1 同轮共享环境）

| # | 命令 | exit | 结果 |
|---|------|------|------|
| 1 | `.venv/bin/python -m pytest tests -q` 全量 | 1 | 1653 passed, 1 skipped, 4 failed——4 红基线（/tmp/base-fec3abf）复跑逐枚同败 → 零新增红；test_admin_capability_manifest_errors.py 4 passed 含其中 |
| 2 | ruff check 触及七文件 | 1 | 2 errors（I001 · UP034）与 fec3abf 基线同 2 枚同码区（行号平移）→ 零新增；UP038 口径订正注见 B1 invoke（ruff 0.15.21 已移除该规则） |
| 3 | lint-imports | 0 | 12 kept, 0 broken |
| 4 | graph-compile.sh | 0 | EXIT=0（npm ci 钉版 3.0.1 后；3.2.0 漂移照录 · 不 merge master） |
| 5 | spec-wave verify / task lint | 0 | 双 PASS（三闸 approved） |

## live 冒烟（uvicorn :8070 · OPS_DESK_SECRET=verify40-secret · OPS_CAPABILITY_EXTRA_MANIFESTS=/tmp/verify40_bad_manifest.yaml,/tmp/verify40_restricted_manifest.yaml 双注入）

| 场景 | 实证 |
|------|------|
| 坏 manifest（capabilities 非 list）注入 → admin GET /admin/capability/catalog | **manifest_errors=1** · details=[{path:/tmp/verify40_bad_manifest.yaml, error:"manifest.capabilities 必须是 list: ..."}] · 坏 path 精确点名 · 响应体无 adapter/local_fn: 泄漏 ✅ |
| 限定 manifest（departments:[finance]）注入 | visibility_hidden=[{capability_id:verify40.finance.only, reason:department_mismatch, **visibility_reason:"部门不在该能力的可见范围内"**}] ✅ |
| /runtime manifest meta 回归 | 仍精确两键 {version, capability_manifest_count} · 契约2 零 diff ✅ |
| 鉴权面回归 | viewer→admin catalog **403** · 匿名 **401** ✅ |
| B1/B2 共存 | 同进程 mine 端点不受 manifest 错误影响（count=5 正常投影）· 零互扰 ✅ |

## 结论

**PASS**——七条钉死契约逐条落地有 diff+live 双重证据；TC1–TC5 对应测试全绿；工程面零新增红（40 独立基线对拍）；live 冒烟全场景如契约（含词表中文映射真实出站）。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 40 核验：契约七条 diff 复核 + 工程面五命令亲跑（基线 /tmp/base-fec3abf 独立对拍）+ live 冒烟五场景（坏 manifest 点名 / visibility_reason 中文映射 / runtime 两键回归 / 403·401 / B1 共存）· graph-compile 3.2.0 漂移照录 |
