# task_p2b_t3_mcp_translator · R1 审查文（20 帽）

- 时刻：2026-11-16
- 审查人：exec-p2b-t3（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03216 · 00 代签体系）
- 对象：`docs/tasks/active/task_p2b_t3_mcp_translator.md` v1

## 审查项

1. **范围对账**：task 范围 10 条与 11-p2b-mcp-skill-design.md 终稿 §8 T3 行
   （ALLOWED_KINDS+mcp · 翻译快照单测 · M1 缺省拒载 · write 缺幂等键拒 ·
   毒 description/inputSchema 递归拒载 · 闸链 e2e · P2a 四样例不误选）+
   §0.1 R1-R10 硬约束（R1 side_effect 缺省翻转 · R2 递归清洗 · R3 catalog
   引导语+（外部工具）前缀 · R4 when_to_use 强制合成+_commit mcp:// 伪 source
   · R5 shutdown unregister）+ §3 字段映射（capability_id/args_schema/
   output_fields/annotations 保守向/_meta 丢弃/enabled=false 不注册）+
   §4 安全防线（配置缺失降级/单 server 隔离/条目拒载 fail-closed）1:1 落入；
   委派书 m00002 内联面（命名 mcp__{server}__{tool} · 冲突整批拒+span ·
   M1/M2/M3 · 重试 1 次 · exclude/overrides 翻译层生效）全部锚定。GO。
2. **非范围**：transport/session 本体（T2 · 仅 manager _connect_one 重试 1 次为
   委派 §4-B 显式要求）· skill 面（T4 已闭环）· 真社区 server 冒烟（T5b）·
   MCP SDK（裁定 A 零新依赖）· strategy 候选集（L1 限制登记）· output_schema
   契约合成（D3 偏差登记）· alembic/ · scripts/ · skill_registry/ 均明示排除。GO。
3. **R5b 同源**：翻译产物直调 `_entry_from_raw`（manifest.py:513）——V1-V13
   校验链对 kind=mcp 全生效，零旁路构造；`_build_adapter` 增 mcp 分支经
   `raw["mcp"]` 块取 server_key/tool_name + lazy import 防环；`_commit`
   target 宽化 Path|str 承 `mcp://<key>` 伪 source（_FILE_IDS 记账 · reload
   注销继承）。同源纪律成立。GO。
4. **节号漂移处理**：委派书引用的 §4-A/B/D/F · §5-⑦ · §9.2 MCP (d)(e) 在
   终稿 grep 零命中（幻影节 · 承 T2 先例）；task 档 R0 节与偏差 D1 如实登记，
   以委派书内联技术细节为操作真源——符合「最小改动 + 如实登记偏差」授权口径。GO。
5. **D2 命名形态**：设计 R-D1' 点分 vs 委派双下划线——从委派（唯一范围真源），
   双段净化（lower+非法字符收 _+折叠+截 64）+ `^[a-z][a-z0-9_]{0,63}$` 段校验
   + 折叠保证段内无 `__`（§4-F 切分唯一解防相互注入），理由成立。GO。
6. **D4 annotations 两稿并集**：委派 destructiveHint→irreversible 与设计 §7-④
   risk 抬 high 并存——取并集（irreversible 且 high）保守向不丢防护；
   readOnlyHint=false+声明 read 冲突拒载（§7-④）有锚。GO。
7. **安全防线落地**：M2 清洗白名单 21 键 + 剥壳 8 键记 notes + 每层 properties
   过 manifest 同源 `_reject_secret_keys`（ManifestError 包成 McpEntryRejectedError
   单条拒载不炸批）+ 字符串毒扫（指令性词表 + slots 伪造标记字面本地复制——
   capability→prompts 禁引以复制规避，注释注明同源）+ 截 500 + 节级引导语写入
   description（R2/R3 如实不静默）。GO。
8. **冲突整批拒**：批内 dup / registry 冲突 → 整批拒 + span
   `mcp_translator_batch_rejected` + warn（不静默跳过）；自身 `mcp://<key>`
   批次豁免保幂等重注册（replace 先摘旧批再 _commit 照 reload 先例）。GO。
9. **执行面 fail-closed**：sync invoke raise McpSessionUnavailableError（gateway
   同步路径转 ok=False）；ainvoke 经模块级 manager 槽位（lifespan 注入/清除 ·
   duck-typed 防环）get_session None → mcp_session_unavailable（§10）；R-G12
   structuredContent 优先/文本拼接/64KB 截断 truncated:true/isError→upstream_error
   稳定码。GO。
10. **验收可机判**：13 条验收逐条锚到 tests/test_capability_mcp_translator.py
    36 例或文件证据；锚点跟随两处（manifest 未知 kind fixture mcp→bogus ·
    observability allow_tags_any 断言 ["mcp","oa"]）如实登记；预算锚
    capability ≤6000 扩 mcp 条目（9+8）后仍绿；脏树期 wave_gate 两红为在途面
    咬禁改面常态（commit 后转绿 · CI 终裁）。GO。
11. **思考轮**：R0-R5 表 + actual_last_round=R5 + 六小节齐备；R3 记录命名/
    冲突整批拒/两稿并集/域放行入口/manager 槽位五决策。GO。
12. **registry N3 entry**：base=b3bc3d6f · allowed_app_files 七件精确列举 ·
    allowed_tree_files 八件 · allowed_tree_prefixes=invokes 目录 ·
    banned_prefixes=[alembic/, scripts/, app/ops/skill_registry/]（lg_rag 不 ban
    ——catalog 分节需 nodes.py 且在 allowed_app_files 精确列举）· yaml safe_load
    验证通过。GO。
13. **人工闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三行 approved，
    依据 issue #23 m03064/m03216 夜间授权；01_modules.md 签收承 :139 先例。GO。

## 结论

**GO · 通过（零阻塞项）** —— task v1 可进 30 实施（夜间授权窗口 · 30 台账见 invoke_20261116_30_impl.md · 40 验收台账见 invoke_20261116_40_acceptance.md）。
