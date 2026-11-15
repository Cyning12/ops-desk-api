# invoke · 10_draft · p2a-t1-panel-list-tools

## 内容

按 issue Cyning12/ops-desk-workspace#23（m03064 夜间授权）+ 设计真源 08-p2a-tools-design.md 终稿 §7 T1 行，落 task 档 docs/tasks/active/task_p2a_t1_panel_list_tools.md + registry.yaml 第 16 entry（base=e0a6734）。

## 勘察定论（R0）

- **ci_status 词表不可钉**：仓内无生产写入方——app/ops/admin/sender/mapper.py:93 恒设 ci_status=None；grep 全仓无其它写入路径；仅测试夹具虚构值（"success"/"pending"）。按 §1.3 走 string 放行 + description 列已知值（GitHub check 惯例 success/failure/pending；现 sync 波恒 null，过滤当前命中空集，防 vacuous pass）。
- **loader 硬约束与 R2 冲突（偏差预登记）**：manifest.py:523-526 when_to_use 必填非空，与 R2「不填」冲突 → 新条目填与 description 一致的简短引导；when_not_to_use 不填（loader 允许缺省）。registry note 已登记。
- **_DEFAULT_SPECS 必须 +2**：test_capability_manifest.py:66-67 钉 set(_BUILTIN_IDS)==硬编码 ids，只加 YAML 不加 defaults 会破对齐测试（回退路径契约不漂移）。
- manifest 真实路径 = app/ops/capability/manifests/builtin.v1.yaml（归 allowed_app_files 非 tree）。
- adapter 白名单 manifest.py:64-66 既有 defaults:/lookups: 两前缀，本波不扩。
- 01_modules.md:34 capability 行存在 → 本波补 P2a-T1 行备注 + HG-GRAPH-MODULES 签收行（splice 于末条后），PR 前跑 graph-compile。
- 测试范式锚点：tests/test_capability_lookups.py（双租户 TENANT_A/B · tool_exec ctx 断言）、test_capability_gateway.py:180-229（span patch / args_schema_invalid 范式）、test_stage_w_write_expand.py:87-103（_DB_MARK + autouse 复位 fixture，须补 budget.reset()/circuit.reset()）。
