# SPEC Audit R1：lg-rag-sse-delta-realtime-spec（T5.1 · 终答 delta 实时投递）

> **hat_id**：20-spec-audit  
> **SPEC 真值**：`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2 · **§10.4.1** · §11.3  
> **task 锚**：`docs/tasks/active/task_lg_rag_sse_delta_realtime_spec.md`  
> **日期**：2026-09-01 · 审查人：20-spec-audit  
> **分支**：`task/lg-rag-sse-delta-realtime-spec`

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10-spec |
| **流程闸** | 审查时 `HG-SPEC-SIGNOFF` 为 pending（正确 · 20 不签发）；本文件落盘后可交 00 代签 |
| **签收建议** | **可交 00 代签 HG-SPEC-SIGNOFF**（维护者令「签收」+ 内容零阻塞 + 审查落盘） |

---

## 审查核对

### A. 00 定夺落入 §10.4.1

| # | 00 定夺项 | SPEC 落点 | 结果 |
|---|---|---|---|
| 1 | SoT = SSE 到达时间线 | §10.4.1 定夺表 SoT | ✅ |
| 2 | 尽快 yield · 禁节点结束批量 flush | 吐出时效 + §4.2 `answer` 旁注 | ✅ |
| 3 | burst 定义（验收用） | 定夺表 burst | ✅ |
| 4 | 降级可观测 · 禁静默攒帧称 T5 成功 | 定夺表降级 | ✅ |
| 5 | 代理 / 部署检查清单 | §10.4.1 部署表（6 项） | ✅ |
| 6 | 框架层默认不攒批 | 框架层与攒批节 | ✅ |
| 7 | freeze 沿用 `lg-rag-sse-v1` · 不新 event_type | T5.1 冻结补充 + 定夺表 | ✅ |
| 8 | progress ≠ 投递失败 · 只评终答阶段 | 与 progress 关系 | ✅ |
| 9 | 红线（假打字机 / progress token / replay / thread_id·cursor） | 非目标表 | ✅ |
| 10 | 实现另 task（建议 `lg-rag-sse-delta-realtime`） | 实现波次行 | ✅ |

### B. 红线与协议边界

| 审查点 | 结论 |
|---|---|
| 无新 `event_type`（如 `answer.delta`） | ✅ 明文多处 |
| 不改 `delta` / `content` / `final` 键语义 | ✅ T5.1 冻结补充 |
| 不把 web 假打字机写成契约 SoT | ✅ SoT + 非目标 + 常见坑 |
| web 同步改码非本波义务 | ✅ 实现波次 api-only 可先合；与维护者裁定一致 |

### C. §11 T5.1 验收可勾选

五条齐全：live 时间线 · mock 慢 chunk · 降级日志 · replay 形状 · 反代检查项文档化。✅

### D. 应然 vs 实然诚实性

缺口候选（persist-before-yield · Vite proxy · provider 极快）已写明且标明「本波不改码」——不构成 SPEC 签收阻塞。✅

### E. 实证

| 项 | 结果 |
|---|---|
| `app/` · `tests/` | `git diff` 空 ✓ |
| 无新 freeze / event_type | 05 正文核对 ✓ |
| invoke | `invokes/by-task/lg-rag-sse-delta-realtime-spec/` 00+10-spec ✓ |
| `task lint` / `lint-wiki-delta` | 10 自检 PASS；本帽不重开实现 |

---

## 阻塞

无。

---

## 签收栏（20 不签发闸）

内容 **pass**。`HG-SPEC-SIGNOFF` 由 **00 代签 · 维护者令「签收」** 回填 task 表（本文件不写 approved 冒充已签）。
