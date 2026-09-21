# app/ops/memory — 事实型记忆 P0（memory-facts-p0）

> 上游 SPEC：`docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`（signed）  
> 设计纪律：**只记事实，不记对话**；**判据在写入时判，不在检索时筛**；**不能自证的机制等于没装**。

## 模块职责

| 文件 | 职责 |
|------|------|
| `gate.py` | `should_write(candidate)` 写入闸**纯函数**；三判据落成显式规则，拒绝返回稳定原因码（`REJECT_REASONS`）。**闸拒 = 不落库**。 |
| `service.py` | 状态机：`write_fact`（过闸 → 落库；同 `(tenant_id,user_id,key)` 有 active 则**同一事务**内置旧 `superseded` + 新行 `supersedes` 指旧 id）· `revoke_by_source`（按源头批量 `revoked`，幂等，审计日志记影响行数）· `sweep_expired`（过期置 `expired`）· `recall_active`（仅 active 且未过期，`updated_at desc` top-N）。 |
| `../lg_rag/continuity.py`（注入点） | `assemble_graph_messages_with_memory`：装配 + 可选记忆注入；渲染/插入助手 `render_memory_facts_block` / `inject_memory_facts_block`。 |

存储：`ops_memory_facts`（`app/db/models.py::OpsMemoryFact`；migration `alembic/versions/20260921_memory_facts.py`）。失效一律走状态机，**不物理删**（旧值留表供审计对账）。

## key 命名约定

- **小写点分层，至少两段**：`^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`，如 `project.primary_repo`、`user.display_tz`。
- 首段为**域**（project / user / repo / pref …），其后逐级收窄；禁止大写、连字符、单段键。
- **易失前缀拒写**：`tmp.` / `session.` / `ephemeral.` / `draft.` —— 一次性上下文不是稳定事实。
- key 是冲突消解粒度：同 `(tenant_id, user_id, key)` 写新值 = 旧值逻辑失效（supersede）。

## env 表

| env | 默认 | 非法值行为 | 作用 |
|-----|------|-----------|------|
| `MEMORY_FACTS_ENABLED` | `false` | 回退 `false` + warning | 装配路径记忆注入总开关；**关闭时输出与现网逐字节一致** |
| `MEMORY_FACTS_MAX_ITEMS` | `8` | 回退 `8` + warning | 召回预算；超限按 `updated_at` 从尾部截断低优先级（最旧）条目，不随机 |
| `MEMORY_FACTS_MAX_VALUE_CHARS` | `2000` | 回退 `2000` + warning | 闸的 value 序列化长度上限 |

## 注入格式与位置

开启且有命中时，装配结果插入**一条独立 SystemMessage**，位置在既有前缀系统消息之后（无前缀则置队首）：

```text
[已知事实]
project.primary_repo=cyning/ops-desk
user.display_tz=Asia/Shanghai
```

- 每条 `key=value` 一行；str 值内换行转义为 `\n` 保住一行一条；非标量 JSON 序列化。
- 块与指令正文**结构隔离**：独立 SystemMessage，不掺入任何 prompt 模板。
- 身份（`tenant_id`/`user_id`）取自请求上下文：tenant = `app/ops/tenant_context.py` ContextVar（阶段 T 头校验链路设置），user = session 用户经 `router.py` / `sse_stream.py` 显式透传；**模型产出不得参与身份构造**。supervisor 内层 `rag_subtask` 不透传 user_id ⇒ 每请求只在顶层装配注入一次。
- 观测：span metadata `memory_facts_injected=N`（经 `app/ops/tracing.py::update_current_span_metadata`；tracing 未开时静默 no-op，同时有 log 兜底）。SSE / 用户面**不输出**原始事实。

## 故障语义

| 触发 | 行为 |
|------|------|
| 闸拒绝 | 不落库 + `GateRejectedError(reason_code)` + info 日志；调用方不得静默吞 |
| 同 key 并发写 | 事务内 supersede，后写赢，旧值留表可审计 |
| revoke 不存在的 source | 影响 0 行，幂等返回（审计日志仍记 `affected=0`） |
| sweep 未跑 / 失败 | **召回仍按 `expires_at` 过滤**（双保险，不依赖任务存活） |
| 跨 tenant 查询 | 所有 SQL 必带 `tenant_id` 谓词；跨 tenant = 空结果 |
| 召回 DB 故障 | 记 log + span `memory_degraded`，**降级为不注入**，不拖垮 chat |
| 写 DB 故障 | 异常向上抛（不静默、无半成功态） |

## 索引取舍

migration 为仓内裸 SQL 风格，`expires_at` 直接落**部分索引**
`WHERE status='active'`（sweep 只扫活跃行）；model `__table_args__` 以
`postgresql_where` 对齐同一语义。另两条：`(tenant_id,user_id,key,status)` 召回主谓词、`(source_run_id)` 纠错溯源。

## 非范围（P0）

向量召回 / embedding 列 / LLM 自动抽取 / 偏好画像（P1+）；对外 HTTP 写端点；对话摘要；物理删除。
