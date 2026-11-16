# invoke_40 · acceptance（p2b-t3-mcp-translator）

## 内容

40 验收：提交前全量测试复跑 + 提交后闸测试复绿 + 验收标准逐条核对 + CI 四绿终裁。

## 验证台账

| 项 | 结果 |
|---|---|
| `pytest tests` 全量（五键 blank 前缀 · CI 无 .env 等效） | **2308 passed, 2 skipped**（75s）· 2 failed 为脏树期结构性红（test_tc8_diff_whitelist / test_wave_gate_registry · 承 T1/T2/T4 钉案 · 提交后复绿） |
| `test_tc8_diff_whitelist` + `test_wave_gate_registry`（提交后复跑） | 22 passed（提交后复绿实证 · 首轮与 amend 后各复验一次） |
| `ruff check app tests` | All checks passed（CI 首轮抓出 F401/I001×2/N818/F841 四处 → 修复 amend 402e5bb 后本地+CI 双绿） |
| `pytest tests/test_capability_mcp_translator.py` | 36 passed（快照/拒载矩阵/清洗/冲突整批拒/exclude+overrides/shutdown unregister/ainvoke 过闸链 e2e/baseline/catalog/预算锚） |
| import-linter（.importlinter） | CI pass（mcp 子包零新 forbidden 出边 · adapter duck-typed 槽位不 import manager 防环） |
| lint-wiki-delta | CI pass |
| check（仓前检） | CI pass |
| **CI 终裁（PR #414 · amend 402e5bb）** | **四绿：pytest 2m44s · check 16s · import-linter 9s · lint-wiki-delta 10s · mergeable=CLEAN** |
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（W1 状态 token 分词 warn · W6 思考轮表头 warn-only 过渡 —— 与 T2 draft 同型） |
| registry.yaml N3 entry | yaml.safe_load PASS · waves=22 · 末 entry=p2b-t3-mcp-translator · base=b3bc3d6f |
| catalog 预算锚（capability ≤6000 扩 mcp 条目） | PASS（默认 9 条 + 8 mcp 条目渲染断言绿 · tests/test_capability_mcp_translator.py 预算用例） |

## 验收标准逐条（对账 task 档 13 条）

- [x] ALLOWED_KINDS+mcp 生效；V1-V13 全校验链对 kind=mcp 生效（R5b 同源：翻译产物直调 `_entry_from_raw` · 未知 kind/坏 id/缺 side_effect 拒载矩阵锚）
- [x] 命名 `mcp__{server_key}__{tool_name}` · 段校验 `^[a-z][a-z0-9_]{0,63}$` · 折叠保证 `__` 切分唯一解（§4-F 注入防护用例）
- [x] 命名冲突即拒该 server 整批 + span `mcp_translator_batch_rejected` + warn（批内 dup / registry 冲突两锚）
- [x] M1 side_effect 缺省拒载（readOnlyHint=true 可按 read 上架 · readOnlyHint=false+read 冲突拒 §7-④）
- [x] M2 inputSchema 递归清洗（白名单 21 键 · $ref/$defs/anyOf/oneOf/allOf 剥壳记 notes · 每层 properties 同源密钥形扫描 · 字符串毒扫截 500 · 节级引导语写入 description）—— $defs+$ref+anyOf 样本断言锚
- [x] M3 when_to_use 强制合成（description_override > description 截 200 > 名称兜底 · R4 · manifest.py:537-539 缺口同源解法）
- [x] annotations 保守向映射（readOnlyHint→read 缺省 · destructiveHint→irreversible+high 两稿并集 D4）
- [x] tool_overrides（description_override/risk）+ exclude_tools 翻译层生效断言锚
- [x] 连接失败 server 整批跳过 + 重试 1 次（§4-B · 重试成功/重试尽跳过两锚）· tools/list 空 → info 跳过不炸启动
- [x] 执行面：sync invoke fail-closed · ainvoke get_session→tools/call · session 未建立 mcp_session_unavailable fail-closed（§10）· R-G12 结果整型（structuredContent 优先/文本拼接/64KB 截断/isError→upstream_error）· args_schema_invalid 过闸链负例 e2e
- [x] R5c：lifespan shutdown unregister（manager aclose → unregister_server_safely 摘除断言锚）· 启动期内存注册不落盘（裁定 D）
- [x] catalog mcp 分节（（外部工具）前缀+不可信描述引导语 R3 · 非 mcp 行逐字节不变）· baseline 域放行（DOMAIN_ALLOW_TAGS+mcp · high/irreversible 恒被裁）
- [x] pytest 全量绿（闸测试提交后复绿）· CI 四绿为终裁 · ruff 绿 · import-linter 绿

## 偏差终录

1. **D1（节号漂移）**：委派书 §4-A/B/D/F · §5-⑦ · §9.2 MCP (d)(e) 在设计终稿 grep 零命中（幻影节 · 承 T2 先例）→ 以委派书内联技术细节为操作真源。
2. **D2（命名形态）**：`mcp__…__…` 从委派（设计 R-D1' 为点分 `mcp.<server>.<tool>`）。
3. **D3（outputSchema）**：只取 `output_fields` ≤16 键名 · 不合成 output_schema 契约（设计 R-D3' vs 委派「output_schema 声明面」→ 取最小安全读法）。
4. **D4（destructiveHint）**：两稿并集（irreversible 且 high · 委派 irreversible vs 设计 §7-④ risk 抬 high）。
5. **L1（限制 · 非偏差）**：strategy 候选集不碰 —— supervisor 真实流需运维 allowlist 注入 mcp id；plan-JSON 选择锚以 ainvoke 过闸链 e2e（含 args_schema_invalid 负例）替代。
6. **CI 首轮 lint 红（流程教训）**：invoke_30 台账先写 ruff PASS 但本地未真跑 → CI 终裁抓出 F401/I001×2/N818/F841 → McpEntryRejected 改名 McpEntryRejectedError（新内部符号改名优于 noqa）+ 删行 + --fix → amend 402e5bb 双绿。此后流程改为「写台账前本地 ruff 实证」。

## 结果

40 验收 GO · PR #414 CI 四绿 · 进 squash merge。
