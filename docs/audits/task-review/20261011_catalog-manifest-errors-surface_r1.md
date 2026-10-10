# catalog-manifest-errors-surface 审查（R1 · 20-task-audit）

> **对象**：docs/tasks/active/task_catalog_manifest_errors_surface.md（commit a778c13 · B2 故障可见性 A 面下游）· **帽**：20-task-audit R1 书面审（未改 task · 未代签 human_gate · 未 30 · 未切分支 · 仅 add 本帽两文件）· 2026-10-11 · 分支 task/tool-catalog-page（勿切令遵守）

## 结论
**裁定：PASS-WITH-NITS**——锚点 14 组全亲读核真（逐字在案）· N4 落点 A 裁定理由链闭合 · 钉死契约七条 + TC1-TC5 全可机断 · spec-wave task lint 复跑 PASS · NIT-1~3 照登（末节）· 三闸（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES）pending 照实 · 本帽未代签。

## 锚点核真（全亲读 · 逐字在案）

manifest.py:200 `logger.error("manifest 加载失败（已跳过该文件）: %s: %s")` 逐字 ✓ · :102-105 `_LAST_META`={version,count} ✓ · :145-147 getter ✓ · :182-201 failed 逐文件 try ✓ · :127-136 MultiManifestLoadResult ✓ · :14-15 失败域隔离注释 ✓ · :17-19 禁热加载 ✓ · __init__.py:110 返回值即弃 ✓
admin/capability.py:99 meta 被 /runtime 消费（弃 B 证据）✓ · :163-214 catalog（return 实起 :192 · R1 N1 携带正确）✓ · :165 AdminSyncAuth ✓ · visibility.py:126 hidden append reason ✓ · :38-41 四码词表 ✓ · :112-135 evaluate_visibility ✓ · gateway.py:133-143 snapshot 直出 ✓
测试面：test_capability_manifest.py:331/:354 meta 断言 ✓ · test_admin_capability_observability.py:54/:113/:149/:173/:185 五测试 ✓ · test_capability_manifest_http.py:409-428 隔离/重复 id ✓ · test_multi_replica_dualproc.py:674-721 parity ✓ · test_capability_visibility_and_receipts.py:135 ✓
文献面：SPEC :78「在响应 summary 增 manifest_errors 计数键（或沿用既有 meta 面 · 实现 task 裁定落点）」首选语序逐字 ✓ · 纪律 #2/:52 #3/:53 #4/:54 ✓ · FP-3/:138 FP-4/:139 FP-6/:141 ✓ · R1 N1/:48 N4/:51 N5/:52 携带无误 ✓

## N4 裁定（理由成立）
①SPEC :78 语序 summary 首选；②弃 B 主证据亲读在案——meta 被 /runtime（admin/capability.py:99）同步消费，扩键 = 双端点响应面同动；③落点 A 收敛 catalog 单端点 diff、与 visibility_* 平铺外形一致；④故障注入断言单点机断。共同前提（manifest.py 模块级故障记录 · failed 集 __init__.py:110 即弃）钉法正确。

## 契约七条与 TC1-TC5 可机断性
契约：1 只增不删（纪律 #2）✓ 2 meta 与 /runtime 零 diff 有机断锚 ✓ 3 故障记录生命周期（最近 failed 集 + reload 成功清该文件 · 禁自动清零）TC4 可断言 · 结构细节留 30 钉系刻意开放且 residual 已注 ✓ 4 reason→文本单源 visibility.py · 路由零重算 ✓ 5 只读零写 ✓ 6 error 透出限 ManifestError 消息（_reject_secret_keys manifest.py:470 加载期拦）✓ 7 鉴权不动 ✓
TC：TC1 故障注入红测先行双钉（orchestration :27 + test_strategy_note :16）· manifest_errors≥1 + details 含 path/error + 拒 adapter/local_fn: 三断言机断 ✓ TC2 零故障基线逐键对拍 ✓ TC3 钉源对拍 + 路由零重算走查 ✓ TC4 生命周期 + 失败域隔离存续 ✓ TC5 工程面五件（pytest/ruff/graph-compile/lint/三闸）✓

## NIT（照登 · 非阻塞）与 lint 复跑
**NIT-1**：契约 4 引「SPEC 纪律 #3/#6」——设计纪律仅 5 条（SPEC :49-55）无 #6，实指 #3（可见性单源）+ FP-6；建议 10 修订删「/#6」。 **NIT-2**：B1 表锚 test_capability_manifest_http.py:413-435——失败域隔离用例实起 :409（def test_multi_file_failure_isolation），:413 系 load 调用行；建议 :409-435。 **NIT-3**（观察）：弃 B 理由「:331/:354 钉键集」表述略溢——该两处为逐键值断言（meta["version"]/["capability_manifest_count"]）非键集相等断言，加键不机械破；惟 /runtime 双端点面主理由独立成立，裁定不受影响。
`npx spec-wave task lint --file docs/tasks/active/task_catalog_manifest_errors_surface.md` → **PASS**（本帽亲跑 2026-10-11）。