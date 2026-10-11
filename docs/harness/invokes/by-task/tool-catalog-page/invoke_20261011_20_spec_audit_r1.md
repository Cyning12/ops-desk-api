# Invoke：20-spec-audit · tool-catalog-page（SPEC v0 书面审 R1）

| 字段 | 值 |
|---|---|
| hat_id | 20-spec-audit |
| task_slug | `tool-catalog-page` |
| task_paths | `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（审查对象 · v0 · draft · commit ff3348d） |
| related_review_or_none | `docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（R1 **PASS-WITH-NITS** · 携带 N1–N5） |
| git_branch | `task/tool-catalog-page` |
| created_utc_or_local | 2026-10-11 |
| notes | 20-spec-audit 不实现代码、不改 SPEC 实质内容、不签 HG-SPEC-SIGNOFF（保持 pending 待人签）；上游 handoff：PROMPT_00 hitl-consumption-loop-handoff 20261009 第二棒 · 维护者令启动 |

---

## 可复制 Prompt 快照

hat_id：20-spec-audit  
task_slug：tool-catalog-page  
本帽禁区：不实现代码、不改 SPEC、不签人工闸、不动 `app/`/`tests/`

必读：SPEC `tool-catalog-page_v0.md`（commit ff3348d）· 上游 `docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md`（A 面定位 · 主仓副本只读）· 审查先例 `docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md` · 实证源 `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` · 码面真值 `app/ops/admin/capability.py` · `app/ops/capability/gateway.py` · `visibility.py` · `manifest.py` · `manifests/*.yaml` · `app/ops/deps.py` · `app/ops/router.py`

只做什么：
1. 逐节亲读 SPEC · 结论先行（通过词落 `## 结论` 节内）
2. 码面锚点逐一亲读核真（SPEC 引用的每个 file:line）
3. D 块范围完整性 · 开放裁定 Q 全部作答且候选不锁死 · failure_paths/验收可机验性 · A 面定位对齐 · 人工闸 pending 照实
4. 发现分 BLOCKER / NIT；审查文落 `docs/harness/reviews/`；回填本 invoke 交付摘要

禁止扩 scope。禁止改 `app/` / `tests/` / SPEC 本体。

## 签收栏

20 帽产出（未经人签）· 2026-10-11

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（R1 **PASS-WITH-NITS** · 核对 19/19 通过 · 阻塞 0 · nit 5） |
| **验证** | SPEC 全部码面锚点亲读核真：`capability.py:163-216` catalog 现状（返回字典实起 :192）· `gateway.py:133-143` → `visibility.py:112-135` · `builtin.v1.yaml:7-29` 字段族 · `manifest.py:200` 故障日志逐字一致 · `deps.py`（`CurrentUser`:114 · `ops_tenant_id`:44）· `router.py:4/:27` 仅 admin 系 · 8 枚 capability 全 `side_effect: read`（builtin 5 + oa 3）· 验收记录 :32 一致 |
| **已定夺** | Q1–Q4 闭合核验通过（维护者三裁定原话与 SPEC :5 逐字一致 · Q3 本帽裁定理由成立）· D 组边界完整（§3 行 90 + 同 commit D 组 Prompt）· A 面定位对齐（终局文档 :35「工具列表页」） |
| **未改** | `app/` · `tests/` · SPEC 本体 · 图谱 YAML · 未签任何 human_gate（HG-SPEC-SIGNOFF 保持 pending） |
| **携带回填** | N1（:199-215→:163-214）· N2（deps :56-115→:18-115）· N3（viewer Principal.roles 映射待 B1 task 钉）· N4（manifest_errors 落点待 B2 task 裁）· N5（终局文档跨分支 + Q4 承前批编号口径） |
| **下一棒** | HG-SPEC-SIGNOFF 人签 → 00 拆后端 B1/B2 task（invoke_slug=`tool-catalog-page`）· 前端 F1 专项 SPEC 另立（ops-desk-web 仓） |
