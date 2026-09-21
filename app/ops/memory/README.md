# app/ops/memory — 事实型记忆 P0 + P1（memory-facts-p0 / memory-facts-p1）

> 上游 SPEC：`docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`（signed）· `docs/spec/memory-facts-p1/SPEC-memory-facts-p1_v1.md`（signed）  
> 设计纪律：**只记事实，不记对话**；**判据在写入时判，不在检索时筛**；**不能自证的机制等于没装**。  
> P1 纪律：向量只解决"怎么召回"，写入判据永远闸判；抽取产物是候选不是事实；每条增强可独立关闭独立降级，**两开关全关 = P0 逐字节一致**。

## 模块职责

| 文件 | 职责 |
|------|------|
| `gate.py` | `should_write(candidate)` 写入闸**纯函数**；三判据落成显式规则，拒绝返回稳定原因码（`REJECT_REASONS`）。**闸拒 = 不落库**。 |
| `service.py` | 状态机：`write_fact`（过闸 → 落库；同 `(tenant_id,user_id,key)` 有 active 则**同一事务**内置旧 `superseded` + 新行 `supersedes` 指旧 id）· `revoke_by_source`（按源头批量 `revoked`，幂等，审计日志记影响行数）· `sweep_expired`（过期置 `expired`）· `recall_active`（仅 active 且未过期，`updated_at desc` top-N）。 |
| `../lg_rag/continuity.py`（注入点） | `assemble_graph_messages_with_memory`：装配 + 可选记忆注入；渲染/插入助手 `render_memory_facts_block` / `inject_memory_facts_block`。P1：`MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` 时召回走 `service.recall_with_vector` 混合召回，否则 P0 确定性路径。 |
| `extract.py`（P1） | LLM 离线候选抽取（默认关）：run 完成后后台点火 → structured_output 管道 → 候选逐条过闸 → `write_fact`（带 `source_run_id`/`source_turn`）。 |

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
| `MEMORY_FACTS_VECTOR_RECALL_ENABLED` | `false` | 回退 `false` + warning | P1 向量召回开关；关闭时召回路径与 P0 逐字节一致 |
| `MEMORY_FACTS_EXTRACT_ENABLED` | `false` | 回退 `false` + warning | P1 LLM 离线候选抽取开关；关闭时零 LLM 调用 |
| `MEMORY_BACKFILL_BATCH_SIZE` | `32` | 回退 `32` + warning | 回填 CLI 页大小（对齐 Embedder 批形态；见「存量行 embedding 回填」） |
| `MEMORY_BACKFILL_SLEEP_MS` | `200` | 回退 `200` + warning | 回填批间限速（ms） |
| `MEMORY_BACKFILL_CHECKPOINT` | 空（禁用） | 指向目录回退禁用 + warning；文件损坏从头重扫 + warning | 可选 checkpoint 文件路径，**仅加速**，不作正确性依据 |

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

## 测试库 schema 漂移注记（memory-fuse-tz-fix）

测试库 `opsdesk_test` 由 ORM `create_all` 建表（plain `DateTime` → **naive**），
真库由 migration 建 `timestamptz` → asyncpg 读回 **aware**。两侧 schema 不一致
曾掩盖 naive/aware 混算故障：`now_utc()=datetime.utcnow()`（naive）与真库读回的
aware `updated_at` 在 `_time_decay` 直接相减抛 `TypeError`，而测试库双侧同 naive
使 P1 测试全绿。修复：`service.py::_as_utc` 在 Python 算术点前归一
（**naive 一律视为 UTC**）；回归见 `tests/test_memory_time_decay_tz.py` 四象限。
重建测试库为 migration schema 属仓级另议，不在本修复范围。

## P1 · 向量召回融合算法（recall_with_vector）

1. **确定性 top-N**：P0 recency 语义不变（active + 未过期，`updated_at desc`，N = `MEMORY_FACTS_MAX_ITEMS`）。
2. **向量 top-M**：写入时经 `Embedder`（rag 协议，同步接口 `asyncio.to_thread` 线程卸载，对齐 rag_nodes 先例）计算 embedding 落 `embedding` 列；召回时对 query 嵌入，裸 SQL `embedding <=> :qvec`（cosine）取 top-M，**必带 tenant_id + user_id + active + 未过期谓词**。M 初值 = N。
3. **去重融合**：两路按 fact id 取并集。
4. **排序**：`score = 向量相似 × 时间衰减 × 来源权重`（初值，SPEC R5 residual ① 需实测调参）：
   - 相似 = `1 - cosine_distance`（截到 [0,1]）；无向量分（embedding NULL 存量行 / 未进 top-M）取 `SIM_FLOOR=0.5`；
   - 衰减 = `0.5 ** (age_days / HALF_LIFE_DAYS=30)`；
   - 来源权重：`source_run_id` 为空（显式/人工）= 1.0，抽取写入 = 0.8。
5. **截断**：按 score desc 截到预算，截低分不随机；并列按 `updated_at desc, created_at desc, id desc` 兜底（确定性 tiebreak）。

降级：embedder / 向量查询 / 列不存在任何失败 → 回退 P0 确定性召回 + span/log `memory_vector_degraded`，不拖垮请求。写入侧嵌入失败不阻断写入：该行 `embedding=NULL`，只走确定性通路（log 标记）。model 列 `deferred=True`：普通 SELECT 不带向量列，migration 未跑时 P0 读通路 SQL 不含它。

## P1 · 抽取时序（extract.py）

```
invoke / SSE run 完成（done 收口后）
  → schedule_memory_extraction（create_task 点火，不 await；热路径零抽取调用零额外延迟，对齐 T5.1 后台 persist 模式）
  → run_memory_extraction：
      文本窗（本轮 query + 终答，单侧截断 4000；证据本体不进 prompt）
      → acomplete_structured（EXTRACTION_SYSTEM_PROMPT 常量 + 文本窗 user 消息；
         parse → repair → validate；correction 重试 ≤1；整体超时 60s）
      → MemoryFactExtraction.facts 逐条 should_write → 过闸 write_fact
        （必带 source_run_id + source_turn，revoke_by_source 一键全撤）
  → log/span：memory_extract_candidates=N written=M
```

- 抽取 prompt 为 **memory 模块内常量**（`extract.py::EXTRACTION_SYSTEM_PROMPT`），文本窗走独立 user 消息，**不做 str.format 插值**——规避 JSON 示例花括号转义痛点（仓内已知）。
- LLM 失败 / 非法 JSON / 超时 → **零写入** + log；每 run 至多 1 次抽取调用。
- 抽取写入入口：`app/ops/lg_rag/router.py`（invoke）与 `app/ops/lg_rag/sse_stream.py`（SSE done 后），两入口均只点火不 await；SSE 零新事件类型。

## 存量行 embedding 回填（memory-embedding-backfill）

P0 时期写入的存量 active 行 `embedding IS NULL`，永远进不了向量 top-M（`_VECTOR_RECALL_SQL` 带
`embedding IS NOT NULL`）。`scripts/memory_embedding_backfill.py` 是一次性运维回填 CLI：

```bash
python scripts/memory_embedding_backfill.py --dry-run   # 只扫描计数 + 前置校验，零嵌入零写库
python scripts/memory_embedding_backfill.py             # 实跑
```

- **口径同源**：嵌入文本 = `service.py::_fact_embed_text(key, value)` 原样复用，与在线写入
  （`_maybe_embed_fact`）同一序列化，向量空间一致；禁止另造口径。
- **幂等续跑**：扫描谓词 `embedding IS NULL AND status='active'` + id ASC keyset 分页，
  已嵌行不再命中 → 中断/双跑/重跑零重复嵌入；checkpoint 文件仅加速（损坏从头重扫）。
- **回写再核**：`UPDATE ... WHERE id AND status='active'`，rowcount=0 记 skipped
  （回填期间被 supersede/revoke/expire 的行不误嵌）。
- **前置校验**（exit 2 零写入）：`embedder.name` 必须等于 `RAG_EMBED_MODEL`，试嵌维度必须 ==
  `MEMORY_FACT_EMBEDDING_DIM`(1024)；`SILICONFLOW_API_KEY` 缺失 / embedding 列不存在同 exit 2
  （干跑/零候选时零嵌入调用，跳过试嵌）。
- **重试纪律**：回填层零行级重试（`ApiEmbedder` 内置 3 次指数退避已足，叠加 = 双重放大）；
  页失败整页记 failed；连续 3 页全败判下游不可用提前终止（status=failed，exit 1）。
- **报告**：`reports/memory_embedding_backfill/backfill_<UTC 时间戳>.yaml`（对齐 qdrant_migrate
  形态）：status（pass/partial/failed）· scanned/embedded/skipped/failed · failed_ids（截断 1000）·
  embedder_name · batch_size/sleep_ms · dry_run · remaining_null_active（实跑后重扫对账，
  剩余 != failed → status=failed，不伪装成功）· elapsed_s · recorded_at；计数守恒
  `embedded+skipped+failed==scanned`；只记 id/计数/模型名，**不存** fact 明文 value。
- **退出码**：0 = pass；1 = partial/failed；2 = 前置校验失败。
- **中断**：SIGINT/SIGTERM 页边界响应，当前页完成后落 `status: partial` 报告再退出。
- 回填**不挂** `MEMORY_FACTS_VECTOR_RECALL_ENABLED`（该开关管在线路径；CLI 本身即开关）。

## 非范围（P0/P1）

画像 / preference；热路径/流中抽取；对外 HTTP 写端点；对话摘要；物理删除；跨租户共享。
