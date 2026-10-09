# PROMPT · 新 00 统筹 D 组（capability-expansion）启动

> 用途：复制本文件全文到新窗口首发，启动 D 组两个小 task 的 Harness 链。
> 生成：2026-10-09 · 00（chat-history-hitl-ux 验收窗）· 维护者令「生成新00统筹D的启动Prompt」

---

你是 **00**（delegate-only）：只委派不亲改实现码（闸扫描 → 下一棒 Prompt → 派子 Agent → 短报 → CLOSE）。Open Folder = 本仓根（`ops-desk-api`）。先读 `AGENTS.md` + `docs/tasks/active/` 扫描在途 task。

## 背景（为什么有 D 组）

2026-10-09 本地验收（`docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 偏差登记 #1/#2）：

- **D2 动因**：当前 capability 注册表**全只读**（`side_effect: read` · 可见集 8 个），`LG_RAG_DELEGATION_TOKEN_MODE=enforce` 下按 Q2 裁定「只读自动放行」**永远无真实 HITL 挂起可触发**——「真实图挂起 → decide → resume 解锁」全链无法验收。需注册一枚**非只读测试 capability** 作为可审对象。
- **D1 动因**：`docker-compose.yml` `api.environment` 未透传 `OPS_HITL_PERSISTENCE`，全 docker 形态验不了 HITL db 持久化（checklist 阶段 5）。

## D 组两个 task（免 SPEC · 直走 10-task → 20 → 三闸人签 → 30/40 → PR → CLOSE · 可并行起草、串行合并）

### D1 · compose 透传 OPS_HITL_PERSISTENCE（config 小 task）

- 改动点：`docker-compose.yml` `api.environment` 增 `OPS_HITL_PERSISTENCE: ${OPS_HITL_PERSISTENCE:-}`（空=默认 · 与既有 `LG_RAG_DELEGATION_TOKEN_*` 透传同范式）
- 锚点：`docker-compose.yml:51-70` · `app/ops/hitl/persistence.py:22`（`ENV_PERSISTENCE`）
- 验收：compose config 渲染对拍 · `OPS_HITL_PERSISTENCE=db docker compose up -d api` 后 `/api/ops/hitl/runtime` 显示 db store · 默认值行为零 diff
- 分支建议：`fix/compose-hitl-persistence-env` 或 `task/compose-hitl-persistence`

### D2 · 注册非只读测试 capability（behavior 小 task）

- 改动点：`app/ops/capability/manifests/` 增测试条目（建议独立文件 `testing.v1.yaml` 或并入 builtin · task 裁定）：`side_effect: write`（或 sandbox/cli 类 · 三条件任一不满足即触发 HITL · 真值 `app/ops/capability/delegation.py:488-510` auto_approve_ok）· `enabled` 可默认 true 但建议带 `testing` tag 便于过滤 · adapter 落 `app/ops/capability/defaults.py` 罐头实现（不碰真实写操作 · 语义 mock）
- 锚点：`manifests/builtin.v1.yaml:7-29`（字段族范式）· `app/ops/lg_rag/multi/nodes.py:277-295`（`_delegation_issue_block_reason` 触发链）· `nodes.py:701-715`（hitl_required 落点）
- 关键验收：**enforce 模式下** plans 含该 tool 的 run → `hitl.waiting` 挂起 → `GET /api/ops/hitl/pending` 可见 → decide(approved) → resume → `done{completed}` 全链（补齐 2026-10-09 验收唯一未验项）；**off 模式零 diff**（默认 off 纪律）
- 注意：可见集基线 `deny_write: true`（catalog filter 实证）——若测试 capability 被基线裁掉导致模型不可见，task 须裁定放行口径（测试 tag 白名单或专用 filter · 不可全局松 deny_write）
- 分支建议：`task/testing-write-capability`

## 纪律钉

- 10-task 起草前读 `docs/standards/CODING_BACKEND_L2_v1_zh.md`；task 须含 failure_paths / 验收可机断 / 思考轮 R0–R5
- D2 属**行为变更类**（新 capability 进可见集求值面）→ 20-task-audit 会查「旧测 grep 影响面」（capability catalog/visibility 既有测试断言清点）
- 三闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）维护者人签前 30 拒开工；图谱闸签「在册」备注随交付落盘（2026-09-30 先例）
- 全部 PR + CI 四绿后 merge；merge 后 CLOSE 归档 done/ + Hub 补登 + CLOSE invoke
- 验收链复跑参照 `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md`「操作便签」

## 相邻工作面（不在本窗范围 · 勿越界）

- SPEC `tool-catalog-page`（工具列表页 · 另窗走 20-spec-audit → 人签 → 拆 task）
- B 面（对话过程全量展示 + SSE 导出 + mermaid 拓扑 · SPEC 待起草）
- SPEC-C（tech_graph 读码 · **挂起**待维护者完善 `/Users/cyning/Desktop/Projects/cyning-harness-meta`）

## 首动作

1. `ls docs/tasks/active/` + 分支确认（禁 master 直改 · 各 task 切各自分支）
2. GATE_VERIFY 扫描（如有在途 task）
3. 派 10-task 子 Agent 起草 D1/D2 两 task（可并行）
