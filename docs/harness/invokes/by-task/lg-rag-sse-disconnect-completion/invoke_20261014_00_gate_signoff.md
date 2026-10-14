# invoke · 00 · lg-rag-sse-disconnect-completion · 人签代录（三闸 + D1–D3）

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 本窗未改实现码 · 仅代录人签 + 派 30） |
| **维护者令** | 「统筹此任务，授权签收后续过程文档」（明示授权 00 代录过程文档 · **不含**亲自改码例外句） |
| **task** | `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`（分支 `task/lg-rag-sse-disconnect-completion`） |
| **审查前置** | 20 R1 **PASS-WITH-NITS** · `docs/harness/reviews/task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md` |

## 授权原话

> 1、统筹此任务，授权签收后续过程文档  
> `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`  
> 2、（附）web 联调 TC4 409 活样本作参照  

## 三闸签署（00 代录 · 落 task 人工闸表）

| human_gate_id | 落录 | 备注 |
|---|---|---|
| HG-TASK-DRAFT | pending → **approved** | signer=维护者（Cyning）· 代录=00 · 2026-10-14 · 10 落稿 + 20 R1 内容零阻塞 |
| HG-AUDIT-R1 | pending → **approved** | signer=维护者（Cyning）· 代录=00 · 2026-10-14 · 审查文 PASS-WITH-NITS · 零内容阻塞 |
| HG-GRAPH-MODULES | pending → **approved** | signer=维护者（Cyning）· 代录=00 · 2026-10-14 · G-L1 备注在册（Wave A 无新一级模块）；若后续另立 Wave B 新模块须该 task 再签 |

## D1 / D2 / D3 裁定（阻塞 30 · 已签）

| 裁定 | 已签值 | 依据 |
|------|--------|------|
| **D1** | **A-only** | 同意 10/20 默认；先消孤儿永久 409 + 诚实收尾；Wave B 另立 |
| **D2** | **`done{status:'disconnected'}`** | 同意 20 优先建议；禁 silent 新 `event_type`；须回写 05 §10.3 + History `terminal_status` 变体 |
| **D3** | **api-only** | 假续看文案另 web task；本棒 FP-5 报回 |

## 联调参照（409 活样本 · 非本仓产物）

挂载于 task 依赖节；30/40 验收对照用：

| 附件 | 路径 | 机读要点 |
|------|------|----------|
| network | `ops-desk-web/docs/harness/invokes/by-task/web-api-joint-check/attachments/jc_tc4_network.json` | mid-stream reload 后 `POST /api/ops/lg-rag/replay` → **409**；`console_errors` 含 409 Conflict；`inflight_error_text` 含 `Run is still in flight` |
| UI 截图 | 同目录 `jc_tc4_inflight_409.png` | ErrorBar：「Run is still in flight; retry after it settles.」+「连接中断…」+「续看」——与 F-OBS-DISCONNECT / FP-5 假续看同构 |

**机理对齐**：客户端断/刷新 → generator close → 无 `done`/`error` → `run_stream_closed==False` → replay `refuse_in_flight` → **永久 409**（真在飞 409 语义须零 diff 保留，见 TC3）。

## 验证命令（机跑实证）

```text
npx --yes spec-wave@3.3.0 verify --target . --task docs/tasks/active/task_lg_rag_sse_disconnect_completion.md
# 2026-10-14 机跑实证：VERIFY: PASS（三闸 approved · 审查文结论节软修后机读通过 · pre-30 10/20/00 齐）
```

## 纪律

- 本 invoke 仅代录人签与裁定；闸真值在 task 人工闸表。
- 代签 ≠ 亲自实现；无「00 本窗亲自 30」例外句 → **派子 Agent 30**。
- 禁卷入 `uv.lock`（task 非范围）。
- 30 仍须首输出 GATE_VERIFY；红测先行（TC1）。

## 下一棒

- **已派 / 待派**：Harness **30**（Wave A · 红测先行 · D2=`disconnected`）

| 日期 | 说明 |
|------|------|
| 2026-10-14 | 00 代录三闸 + D1/D2/D3 · 挂联调 TC4 409 参照 · 交 30 |
