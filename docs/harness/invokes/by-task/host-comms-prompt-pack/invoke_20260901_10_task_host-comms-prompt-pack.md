# Invoke：10-task · host-comms-prompt-pack（C2）

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `host-comms-prompt-pack` |
| task_paths | `docs/tasks/active/task_host_comms_prompt_pack.md` |
| related_review_or_none | 无（本帽结束后交 20-task-audit） |
| git_branch | `task/host-comms-prompt-pack` |
| created_utc_or_local | 2026-09-01 |
| notes | 00 已起草 C2 初稿（00 定夺钉死 · invoke_20260901_00 已落盘）；10 补全/审校 + 现网事实核对，**不实现代码** |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：host-comms-prompt-pack  
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1、不改 `app/` / `tests/`、不改人工闸表状态

必读：`docs/harness/prompts/10-task-requirements.md` · 已落盘 task 初稿（00 定夺钉死）· SPEC `06_host_comms_boundary_spec_v0.md`（signed · §3/§4/§6/§8/§9/§10/§15）· C1 关账链（#114/#115）

只做什么：
1. `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_prompt_pack.md`；FAIL 则补结构（验收 / failure_paths / wiki_delta 已有则勿删）
2. 核对 00 定夺与非范围：slug=`host-comms-prompt-pack`；纯函数层 `render_pack("comms", slots)` + `route_intent(text)` → `"comms" | "product"`（**不新增 HTTP 路由**）；槽位链=kit FRAGMENT 真值（`FRAGMENT_00_delegate_only_v1_zh.md` + `FRAGMENT_hat_reanchor_v1_zh.md` · 禁拷贝漂移）+ task 字段清单 + 对话策略 + 禁令条文（永不签发 human_gate · 写盘仅 docs/tasks/+invoke 草稿 · Skills≠verify）；意图路由默认/回退 product · 规则/关键词纯函数（不引入 LLM 判定）；分 session 仅元信息标记 `session_scope="comms"`；product 侧零影响；不新增一级模块
3. 现网事实核对（只读）：`app/ops/prompts/render.py` · `templates.py`（API 形态）· FRAGMENT 两文件存在性 · prompts 在 `docs/_tech_graph/l1/01_modules.md` 归属行；与现网不符才修正并记录
4. 补遗漏验收钩（不改 00 定夺实质）：pack 元信息字段钉死 · `route_intent` 严格二值回退 · product 渲染签名不变
5. 思考轮：本 task 由 SPEC 06 §15「思考轮控制」承载，**不必**强行加 R0–R5（无节仅 W4 · 合法）
6. 补 `### 自检结论`；修订记录追加 10-task 行；回填本 invoke 交付摘要；下一棒 20-task-audit

禁止扩 scope。禁止改 `app/` / `tests/`。禁止改人工闸表状态（HG-AUDIT-R1 保持 pending）。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权（C 轨串行 · C2 波）· 2026-09-01

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_prompt_pack.md` → exit **0** · **PASS**（W4：无思考轮节 · SPEC 06 §15 承载合法）；`npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → exit **0** · **PASS** |
| **变更路径** | `docs/tasks/active/task_host_comms_prompt_pack.md`（graph_delta 开放钉钉死 + 验收钩 +2 + `### 自检结论` + 修订记录 10-task 行）；本 invoke |
| **事实核对** | **现网与 task 陈述全部一致 · 零事实修正**；1 处开放钉（graph_delta「模块归属由 10 核现网钉」）已按现网钉死：`render.py` API=`render(template_id, variables=None, *, slots=None) -> str`（slots 追加 `<!-- slot:name -->` 块）+ `get_template` + `PromptTemplateNotFoundError` ✓ · `templates.py` 仅 `lg_rag.intent.system`/`lg_rag.supervisor.system`（v1 · 后者含 `{catalog_block}`）✓ · `FRAGMENT_00_delegate_only_v1_zh.md` 与 `FRAGMENT_hat_reanchor_v1_zh.md` 均存在 ✓ · `01_modules.md` 模块表无 `app/ops/prompts/**` path glob、模板 id 全部 `lg_rag.*` 且被 lg_rag supervisor/intent 消费 → **归属 `lg_rag` 行（L27）备注**，不新增一级模块 |
| **未改** | `app/` · `tests/` · CI · 图谱正文 · 00 定夺范围实质（slug / 纯函数层无新路由 / 槽位链 / 禁令条文 / 意图路由默认·回退 product / 分 session 元信息 / product 侧零影响 **全部保留**）· `HG-AUDIT-R1`（仍 pending） |
| **内容可交 20** | **是**（结构齐全；00 定夺钉死项保留；现网事实已对齐；无内容阻塞） |
| **需 00 定夺** | **none**（无退回意见；归属钉钉死与验收钩补充属事实对齐/可检验化，非范围变更） |
| **下一棒** | **20-task-audit**（落盘 R1 review 后由 00 代签 `HG-AUDIT-R1`） |
