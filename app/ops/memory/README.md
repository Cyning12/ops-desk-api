# app/ops/memory — 事实型记忆 P0 + P1 + 画像 preference 首期（memory-facts-p0 / memory-facts-p1 / memory-preference-profile）

> 上游 SPEC：`docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`（signed）· `docs/spec/memory-facts-p1/SPEC-memory-facts-p1_v1.md`（signed）· `docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（signed）· `docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（signed）  
> 设计纪律：**只记事实，不记对话**；**判据在写入时判，不在检索时筛**；**不能自证的机制等于没装**。  
> P1 纪律：向量只解决"怎么召回"，写入判据永远闸判；抽取产物是候选不是事实；每条增强可独立关闭独立降级，**两开关全关 = P0 逐字节一致**。  
> preference 纪律（memory-preference-profile）：**首期只收显式声明**——闸双向 key 域绑定（`kind=preference` ⟺ key 首段 `pref`），抽取管道物理不产 preference（schema 无 kind 字段 + 构造点钉死 fact），推断型偏好**无写入通路**；召回注入分节（`[已知事实]` / `[用户偏好]` 单 SystemMessage 双节）；纠错入口 `revoke_by_key`。

## 模块职责

| 文件 | 职责 |
|------|------|
| `gate.py` | `should_write(candidate)` 写入闸**纯函数**；三判据落成显式规则，拒绝返回稳定原因码（`REJECT_REASONS`）。**闸拒 = 不落库**。kind 集合 `ALLOWED_KINDS={fact, preference}`；双向 key 域绑定违反 → `key_kind_mismatch`。 |
| `service.py` | 状态机：`write_fact`（过闸 → 落库；同 `(tenant_id,user_id,key,kind)` 有 active 则**同一事务**内置旧 `superseded` + 新行 `supersedes` 指旧 id——查重谓词含 kind，跨 kind 同 key 互不影响）· `revoke_by_source`（按源头批量 `revoked`，幂等，审计日志记影响行数）· `revoke_by_key`（按 key 一键 `revoked`，显式声明 `source_run_id` 为空的纠错入口；必带 tenant+user 谓词 · 幂等 · 审计）· `sweep_expired`（过期置 `expired`）· `recall_active`（仅 active 且未过期，`updated_at desc` top-N，**无 kind 谓词**——分节在渲染层）· `purge_by_user`（按 `(tenant_id,user_id)` **全 status 整行物理删除**——合规删除权 · 管理面唯一入口 · 见「合规物理删除」节）。 |
| `../lg_rag/continuity.py`（注入点） | `assemble_graph_messages_with_memory`：装配 + 可选记忆注入；渲染/插入助手 `render_memory_facts_block` / `inject_memory_facts_block`。P1：`MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` 时召回走 `service.recall_with_vector` 混合召回，否则 P0 确定性路径。 |
| `extract.py`（P1） | LLM 离线候选抽取（默认关）：run 完成后后台点火 → structured_output 管道 → 候选逐条过闸 → `write_fact`（带 `source_run_id`/`source_turn`）。 |

存储：`ops_memory_facts`（`app/db/models.py::OpsMemoryFact`；migration `alembic/versions/20260921_memory_facts.py`，CHECK 放宽 `kind IN ('fact','preference')` 见 `20260922_memory_kind_preference.py`——回滚须先清 preference 行）。失效一律走状态机，运行期**不物理删**（旧值留表供审计对账）；合规物理删除只走管理面 `purge_by_user`（见下节）。

## 合规物理删除（memory-compliance-delete）

- **运行期失效仍走状态机不物理删**；物理删除只有管理面一个入口：`POST /api/ops/admin/memory/purge`（`app/ops/admin/memory.py` · `AdminSyncAuth` 对齐 · **admin 面首个不可逆写端点**）。
- service 层 `purge_by_user(tenant_id, user_id, *, dry_run=True, session=None) -> PurgeReport`：谓词含且仅含 tenant+user（跨 tenant = 0 行）；**全 status**（active/superseded/revoked/expired）无差别整行 DELETE，embedding 列随行消失（向量 SQL 查表本身，行零残留 = 两通路零残留）；单条 DELETE 单事务原子（无半删中间态）；**幂等**（重复实删第二次 `deleted==0`）。
- **双闸门铁律**：`dry_run` 默认 true（盲发只读 · 干跑零写对拍）；实删必须 `expected_count` 与同谓词当前匹配计数一致——缺 → 400 · 不等 → **409 零删除**（调用方重新干跑）· 等 → 200 且 `deleted==expected_count`。「删多少」是显式对账不是盲发。
- **审计记动作不记内容**：`logger.info("memory purge_by_user tenant=%s user=%s dry_run=%s affected=%d", ...)`（无 key/value · revoke 先例同形 · 实删/干跑/幂等 0 行全含）；落既有 logger 面，零新表零 alembic。
- 报告：`PurgeReport(dry_run/scanned/deleted/by_status/elapsed_s/recorded_at)`（backfill 字段族 · **计数守恒**：实删 `deleted==scanned` · 干跑 `deleted==0` · `sum(by_status)==scanned`）。
- 残余风险（承 SPEC §7 如实承认）：expected_count 只锁数量不锁主体（计数碰巧相等的错目标不可防 · 管理面人工纪律兜底：先干跑核对计数再实删）；同计数内容替换竞态不可区分（管理面低频可接受）；审计落日志面不可机查台账（合规要求机查台账时回 SPEC 升级新表方案）。
- 非范围沿用：无用户自助端点 · 无批量/全表/定时 purge worker · 不删其它业务表 · 不删 RAG/Qdrant/Langfuse 侧数据。

## key 命名约定

- **小写点分层，至少两段**：`^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`，如 `project.primary_repo`、`user.display_tz`。
- 首段为**域**（project / user / repo / pref …），其后逐级收窄；禁止大写、连字符、单段键。
- **`pref` 域与 kind 双向绑定**（memory-preference-profile）：`pref.*` key 必须 `kind=preference`，`kind=preference` 必须 `pref.*` key；违反 → 闸拒 `key_kind_mismatch`。
- **易失前缀拒写**：`tmp.` / `session.` / `ephemeral.` / `draft.` —— 一次性上下文不是稳定事实。
- key 是冲突消解粒度：同 `(tenant_id, user_id, key, kind)` 写新值 = 旧值逻辑失效（supersede）。

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

memory-preference-profile **无新 env**：kind=preference 复用同一总开关 / 预算 / 值长上限（统一预算内两节混排截断）。

## 注入格式与位置

开启且有命中时，装配结果插入**一条独立 SystemMessage**，位置在既有前缀系统消息之后（无前缀则置队首）。块内按 kind **分节**（memory-preference-profile 方案 B1 单块双节）：

```text
[已知事实]
project.primary_repo=cyning/ops-desk
user.display_tz=Asia/Shanghai

[用户偏好]
用户显式陈述的偏好，用于调整回应方式；非客观事实。无偏好时不要假设或编造。
pref.answer_lang=中文
```

- 每条 `key=value` 一行；str 值内换行转义为 `\n` 保住一行一条；非标量 JSON 序列化。
- **无 preference → `[用户偏好]` 节物理不存在**（幻觉偏好红线结构断言落点）；无 fact → `[已知事实]` 节同样不出现；fact-only 输入渲染与 P0 现网逐字节一致。
- 块与指令正文**结构隔离**：独立 SystemMessage，不掺入任何 prompt 模板。
- 身份（`tenant_id`/`user_id`）取自请求上下文：tenant = `app/ops/tenant_context.py` ContextVar（阶段 T 头校验链路设置），user = session 用户经 `router.py` / `sse_stream.py` 显式透传；**模型产出不得参与身份构造**。supervisor 内层 `rag_subtask` 不透传 user_id ⇒ 每请求只在顶层装配注入一次。
- 观测：span metadata `memory_facts_injected=N`；有 preference 时并列 `memory_preferences_injected=M`（经 `app/ops/tracing.py::update_current_span_metadata`；tracing 未开时静默 no-op，同时有 log 兜底）。SSE / 用户面**不输出**原始事实与偏好。

## 故障语义

| 触发 | 行为 |
|------|------|
| 闸拒绝 | 不落库 + `GateRejectedError(reason_code)` + info 日志；调用方不得静默吞；kind 集合外 → `kind_not_allowed`；kind 与 key 域双向绑定违例（preference 非 `pref.*` / fact 用 `pref.*`）→ `key_kind_mismatch` |
| 同 key 并发写 | 事务内 supersede，后写赢，旧值留表可审计 |
| revoke 不存在的 source | 影响 0 行，幂等返回（审计日志仍记 `affected=0`） |
| revoke_by_key（显式声明纠错） | 按 `(tenant_id, user_id, key)` 把 active 行置 `revoked`；幂等（重复调用 0 行）· 跨 tenant 0 行 · 审计日志记 affected；清除后召回零命中、注入块无该 key |
| sweep 未跑 / 失败 | **召回仍按 `expires_at` 过滤**（双保险，不依赖任务存活） |
| 跨 tenant 查询 | 所有 SQL 必带 `tenant_id` 谓词；跨 tenant = 空结果 |
| purge_by_user（合规物理删除） | 按 `(tenant,user)` 全 status 整行 DELETE；dry_run 默认 true 零写 · 幂等（重复 0 行）· 审计记 affected 不记内容；越 tenant/越 user = 0 行；实删双闸门（缺 expected_count → 400 · 计数不等 → 409 零删除） |
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

## 非范围（P0/P1/memory-preference-profile）

推断型 preference（行为推断 / 抽取产偏好——首期物理拒收，无写入通路；未来另案 SPEC）；热路径/流中抽取；业务面对外 HTTP 写端点（合规物理删除走 admin 面 · 见「合规物理删除」节）；对话摘要；用户自助/批量/定时物理删除（管理面单 (tenant,user) purge 除外）；跨租户共享；偏好管理 UI（另案）。
