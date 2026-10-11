# Invoke · 10 · capability-mine-endpoint

- **hat**：10-task
- **task_slug**：`capability-mine-endpoint`
- **日期**：2026-10-11
- **对象**：SPEC tool-catalog-page §2 B1（`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md` · HG-SPEC-SIGNOFF approved 2026-10-11）· R1 审 PASS-WITH-NITS（`docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`）
- **结论**：落稿 `docs/tasks/active/task_capability_mine_endpoint.md` —— 新立用户态 `GET /api/ops/capability/mine`（CurrentUser · Q1/Q3 裁定存续）；钉死契约八条（Principal 构造 roles=frozenset({user.role}) N3 钉死 · 可见性单源 · 出站白名单九键排除 adapter/args_schema · 只回可见集防探测 · 空集 200 · 只读零写 · 禁落 capability 包内 · baseline 默认不叠加）；TC1–TC7 全可机断；三闸 pending 不代签。
- **N 回填**：N1 锚点改引 `app/ops/admin/capability.py:163-214`（返回字典实起 :192）· N2 deps 改引 `app/ops/deps.py:18-115`（含 get_current_user 本体 :18-53）· N3 viewer Principal.roles 映射钉死并固化 TC3 viewer⊆maintainer 对拍。
- **候选倾向（开放留 30 实证 · 不锁死）**：落点 `app/ops/capability_mine.py` 新模块（倾向）；baseline_filter 默认不叠加（倾向不加）。
- **verify**：`npx spec-wave verify --target . --task docs/tasks/active/task_capability_mine_endpoint.md` → BLOCKED（三闸 pending · 符合预期 · 30 拒开工）；闸表 4 列契约已对齐（首稿 3 列触发空解析告警 · 已收口）。
- **产物**：`docs/tasks/active/task_capability_mine_endpoint.md`（骨架 ba4a078 → 填肉 7c47ecd → 闸表修正）
- **必读**：SPEC v0 §1/§2 B1/§4/§5/§6 B1 · R1 审 N1–N3 · deps.py:18-115 · visibility.py:112-135 · gateway.py:133-143 · admin/capability.py:163-214（外形对齐源 · 零改动）· router.py:19-34。

| 2026-10-11 | 10 |
