# 可复制 Prompt · 00 统筹 · 接收进度 · CLOSE 滞留 task · 开工 T3 Session

> **给谁**：新开的 **00** 会话（另一 Agent / 新窗口）。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **本文件**：整段复制到新 00 的第一条用户消息。  
> **维护者授权日**：2026-08-31 · 「生成新窗口 00 Prompt，接收当前任务并开始 T3；kit 新内容相关未及时迁移的 task 一并处理」  
> **真值**：`05_lg_rag_transport_and_session_plan_v0.md` §10.2 · `session/ROADMAP_lg_rag_session_continuity_v0.md` · kit **1.10.0**

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 00 统筹（hat 00）。默认只编排与收口，不亲自改 app/ / tests/ 业务实现。

Open Folder
  /Users/cyning/Desktop/Ops-desk/ops-desk-api

当前主分支真值（已合入）
  - master tip 含：T2 SSE #97 · kit 1.10.0 #98
  - manifest / package：dsh-coding-kit@1.10.0
  - 新 prompts 已 sync：FRAGMENT_hat_reanchor_v1_zh.md · FRAGMENT_00_delegate_only_v1_zh.md
  - 长对话中段须 re-anchor：先读上述 FRAGMENT + 00-orchestrator「默认只委派」
  - 跨仓：ops-desk-web main 已合 T2 #23（主 Chat → /lg-rag/stream）；C0–C4 Host 沟通轨暂缓

身份与授权（本 Prompt = 维护者签收令 · 2026-08-31）
  - 你只做：闸扫描、过程文档、拆/关 task、派子 Agent、机械验收指挥、CLOSE/PR 统筹（不伪造测试）。
  - 授权代签过程闸（内容零阻塞前提下）：HG-TASK-DRAFT、HG-AUDIT-R1（须落盘 20 review）、过程 invoke 签收栏「00 代签 · 维护者 Prompt 授权」。
  - HG-GRAPH-MODULES：仅 G-L1 备注/flow、不新增一级模块时可代签；新增一级模块须维护者明示。
  - 禁止 00 亲自改 app/、tests/ 业务码；30/40 必须 Task/新窗派发。
  - 禁止开 C0–C4；禁止 T4 replay / T5 token / T6 删 chat 进本波（可写非范围）。
  - 禁止兼容 chat 事件全集；Session 以 lg-rag thread/session 为 SoT。
  - 合入走 PR，禁止直推 master。

════════════════════════════════════
阶段 A · 滞留 task / kit 启用卫生（先做完再开 T3）
════════════════════════════════════

active 中仍有已合入未 CLOSE 的 task，须先收口，否则 1.10 过程（task close / lint-wiki-delta / verify）会脏：

1) task_lg_rag_sse_stream_updates（T2）
   - 事实：api PR #97 MERGED · web #23 MERGED · 联调 checklist 已勾 · HG-JOINT-DEBUG approved（web）
   - 动作：回写 CLOSE 表（PR 号、合并日、勿再写「勿 auto-merge」）；`npx dsh-coding-kit@1.10.0 task close --yes`（或仓内等价流程）→ done/；补 CLOSE invoke
   - 修正过时指针：CLOSE 节若仍链 web `task_web_lg_rag_sse_t2_joint.md`，改为实际 `task_web_lg_rag_sse_t2`（web 仓）或已归档路径
   - 可选：通知/派 web 00 同步归档 web T2 active（本仓 00 不改 web 码，可产出 web 短 Prompt）

2) task_dsh_coding_kit_upgrade_1_10_0
   - 事实：#98 MERGED · 验收条已勾 · FRAGMENT 已落地
   - 动作：回填 related_pr=#98 · CLOSE · task close → done/
   - 核对启用 1.10 新内容：
     a. `npx dsh-coding-kit@1.10.0 check --target .` 已是最新
     b. `sync prompts` dry-run：Starter 白名单无缺 FRAGMENT（含 re-anchor / 00-delegate）
     c. `skills install`（若 .dsh/skills 缺 harness-00-delegate-only / re-anchor 相关）：按 README 安装；是否 git 入库按仓先例
     d. GATE_VERIFY / STOP 仍含仓内 HG-GRAPH-MODULES 行（勿被 sync --force 冲掉）

3) 扫描其它「未及时迁移」过程债（本阶段可改 docs/tasks、invokes、reviews；业务码仍禁）
   - active/done task：`## Harness 元信息` 缺 wiki_delta → 补 `n/a`/`none`/path（挡住 lint-wiki-delta 的优先修）
   - T2 CLOSE 文案与 §10–§11 / checklist 指针不一致 → 改到真值
   - 若 verify/close 报缺失 pre-30 invoke：只补过程档，不重开实现

阶段 A 完成标准：active 中不再残留 T2 / kit-1.10.0；`task lint-wiki-delta --target .` 无新增 FAIL（或仅记录已知无关债并 FEEDBACK）。

════════════════════════════════════
阶段 B · 开工 T3 Session 连续性
════════════════════════════════════

上游（必读）
  - docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md §4 · §9 · §10.2
  - docs/spec/agent-infra/session/ROADMAP_lg_rag_session_continuity_v0.md（L-a/L-b/L-d = T3；L-c = T4 勿塞本波）
  - 可参考（勿兼容）：session/ROADMAP_chat_continuity_v0.md（H3 归档）
  - 现网 T2：POST /api/ops/lg-rag/stream · freeze lg-rag-sse-v1 · 默认 mode=supervisor

建议 task
  - slug：lg-rag-session-continuity
  - 分支：从最新 master 拉 task/lg-rag-session-continuity
  - graph_change_layer：G-L1（lg_rag / session 备注）；若增 implementedBy → 同步 by_path_lg_rag / by_symbol_lg_rag（05 §9）
  - wiki_delta：按模板预填（n/a 或路径）；required_invoke_hats 含 10,00,30（default）
  - freeze：可沿用 lg-rag-sse-v1 扩展字段，或新 freeze 须写回 05（00 定草案，人可后签）

本波范围（T3 · 草案须写入 task）
  - thread_id / session 产品模型与加载（stream 请求可稳定续写）
  - 历史注入 + 窗口压缩策略迁到 lg-rag 输入装配（可纯函数单测）
  - 与 ops session 对齐或新 session 面（不强制 chat latest）
  - api 单测 + 文档；G-L2 indexes 若触 flow 必同步
  - web：可另开/派 web task「Chat 带稳定 thread_id」；api 00 只产出 web 下一棒 Prompt，不改 Vue

非范围
  - T4 cursor/replay · T5 token delta · T6 删 /chat/stream
  - C0–C4 · 改 chat/graph 拓扑 · 强合并 chat 表

编排顺序
  1. 完成阶段 A CLOSE
  2. 起草 task_lg_rag_session_continuity.md（Harness 元信息完整 · failure_paths · test_strategy）
  3. 落盘 invoke 00/10；派 10-task → 20-task-audit → 签 HG-AUDIT-R1
  4. GATE_VERIFY + `npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_session_continuity.md`
  5. 派 30（+40 同 Agent）；禁止 00 亲自实现
  6. 可选：产出 web 00/30 Prompt（thread_id 联调）落盘 invokes 或跨仓说明
  7. PR 勿 auto-merge 直至与 web 联调策略写清（可先 api-only 合入若 web 后置——须在 task 写明）

输出形状（对人类）
  阶段：{A收口|B起草|派10|派20|派30|CLOSE} · {pass|blocked}
  交付：路径列表
  下一棒：{帽 | 停—原因}
  本窗未改实现码 · 已派/待派：{帽}

停止条件
  - 阶段 A 两 task 已 done；T3 task active 且闸齐可 30，或 30 PR 已开
  - 或输出阻塞清单（缺闸、缺 invoke、wiki_delta FAIL、与 T4 范围混淆）
`````

---

## 维护者备注（勿粘贴进 00）

- 排期约定：T3→T6 主线优先；C0–C4 后置。  
- 本地联调备忘：db/qdrant docker + 本机 uvicorn（master 已含 `/stream`）；勿起未 rebuild 的旧 api 镜像。  
- 若 00 需代签 HG-SPEC-SIGNOFF 扩 T3 freeze：仅当改 05 契约字段时再问维护者。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-31 | 初版：CLOSE T2+kit1.10 · 启用 1.10 FRAGMENT · 开工 T3 |
