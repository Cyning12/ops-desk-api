# Invoke · 00 · demo_agent_host_surface · task 壳起草（2026-10-16）

- **帽**：00（总调度 · delegate-only）
- **动作**：闸扫描 + 锚点扫描 + 起草 task 壳；**未改实现码**（app/、ops-desk-web/src、单测、freeze、路由、表名零触碰）
- **授权句**（用户 2026-10-16 本窗 prompt）：「授权签收后续过程文档，直接完成此短链任务」→ 00 起草壳 + 落本 invoke；**无**「00 本窗亲自 30」授权
- **闸扫描**：本需求无既有 SPEC/task 初稿（`docs/tasks/active/` 7 个 active task 均无关：hitl_*×3、lg_rag_sse_*×2、n40_1、verify-upstream；一律不改不关不并入）
- **分支**：当前 `task/arch-browser-eng-graph-mermaid`（**非** main/master · 有 arch-browser 未提交改动属他 task）→ 建议 30 开工前切 `task/demo-agent-host-surface` 并厘清与 eng-graph-mermaid 脏树的合入顺序（build_site.py / web/app.js / dist 同文件）
- **锚点扫描（2026-10-16 快照）**：
  - `docs/arch-browser/catalog/home_narrative.json:6,10`（lg-rag 叙事）
  - `docs/arch-browser/catalog/host_outline.json:34-35,74`（E1 入口层 / N0）
  - `docs/arch-browser/scripts/build_site.py:35-52,243-255`（Chat/LC Evidence 演示标签 · class 行）
  - `docs/arch-browser/web/app.js:549-553`（node→route map）
  - `docs/arch-browser/catalog/crosswalk.yaml:374-387`（chat / lc_evidence_chain 真值行 · **只读不删**）
  - SPEC 冲突：`docs/spec/arch-browser/SPEC-arch-browser_v0.md:44` §1 纪律 3「传输壳可仍叫 lg-rag（首页文案须保持）」→ D3 显式修订
- **交付**：`docs/tasks/active/task_demo_agent_host_surface.md`（壳：验收 TC-1–TC-8 · failure_paths FP-1–FP-7 · 非范围 · D1–D3 · HG pending · R 轮待 10）
- **下一棒**：**10-task**（落稿：填 R0–R5、校锚点行号、拟 SPEC 修订文 D3、补验收证据位）→ 20 R1 → 维护者签 HG-TASK-DRAFT + HG-AUDIT-R1 → 30
- **展示名裁定（锁）**：侧栏「LG RAG」→「Agent 工作台」；arch-browser 入口层「Agent 工作台（SSE 流式运行）」；对照展示不出现 lg-rag 等歧义命名。**10 不得重开 D1**
