# Task Audit R1：p0prime-t1-ws-shutdown

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_p0prime_t1_ws_shutdown.md`  
> **日期**：2026-11-13 · 审查人：00 统筹（兼 20）

## 结论摘要

| 维度 | 结论 |
|---|---|
| **内容** | 零阻塞：纯删遗留（未鉴权 demo WS 端点 + 配置开关 + 旧测试），零新增面、零 DDL；负向回归可机断 |
| **依据** | issue #23 R3 实地调研（`ws.py` 未鉴权 + 自述 do not expose publicly）· R4 裁定 P5（直接下线不带闸）/ A3①（安全优先最先行）；workspace `06-kickoff-readiness.md` 任务卡 T1 |
| **范围纪律** | 非范围三条钉死：chat/graph.py、service.py、三表归 T2；410 墓碑不动；iOS WS 资产不落本仓（R4-D2 冻结） |
| **流程闸** | 三闸 approved（HG-TASK-DRAFT / HG-AUDIT-R1 · 维护者 m00177「签收，开始」；HG-GRAPH-MODULES 备注回写已落 `01_modules.md`） |
| **机械闸** | `spec-wave task lint` PASS · 思考轮 R0–R5 齐全 · failure_paths 3 条 · 验收 7 条可机断 |

## 风险核对

- 删除面 grep 锚点齐全（`chat_ws_router` / `ops_chat_ws_enabled` / `app.ops.chat.ws` / `tests/test_chat_ws.py`），残留风险由验收条「grep 为零」兜底。
- `ops_chat_ws_enabled` 随删符合 P5「不带闸保留」裁定；无外部文档引用该 env（仅 tasks/done 历史文档，豁免）。
- 负向回归新测试无 DB 依赖，不引入测试基线波动。

## 签收

**签收**。下一棒：30 按 R2 竖切顺序改码（摘注册 → 删文件 → 删开关 → 测试 → 图谱已在 10 阶段回写）。
