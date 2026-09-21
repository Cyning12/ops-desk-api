# app/ops/session — Session 连续性：历史加载 · SSE replay · 真摘要（session-summary-fallback · 默认关）

> 上游 SPEC：`docs/spec/session-summary-fallback/SPEC-session-summary-fallback_v1.md`（signed · 2026-09-22）
> 设计纪律：**结构由纯函数 `compress_window` 定（零改动），本模块只做占位条内容替换**；
> **回退铁律是上线前提**——回退 = 关开关（零代码零迁移 · env 重读即时生效 · 进程内无状态）；
> 原文 SoT（`ops_lg_rag_turns` / `ops_runs`）零写入，摘要与原文**物理分表**。

## 模块职责

| 文件 | 职责 |
|------|------|
| `history.py` | `load_session_turns`：chat 轨历史面（`ops_runs` 最近 20 条）；**实扫 app 内无生产调用方**，原文保留现状零改动 |
| `sse_replay.py` | SSE replay 纯函数（replay_events / cursor / payload 契约） |
| `summary.py` | **会话真摘要（L1 懒生成 + C1 独立表缓存）**：`summarize_placeholders(compressed, *, thread_id, ...)` 把 `compress_window` 产物中的占位条（`[历史摘要 · N 轮 · roles=...]`）逐条替换为真摘要条；逐占位 chunk 查缓存 → miss 才调 LLM（summary 档）→ 生成成功才写缓存 |

装配接线点：`app/ops/lg_rag/continuity.py::assemble_graph_messages_with_memory`（记忆注入**之前**）；
lg_rag → 本模块静态 import 被边界测试禁止（`tests/test_lg_rag_session_continuity.py`），
故经 **importlib 运行期解析**（仅开关 on 时触达；off 态静态加载链零变化）。

## env 表

| env | 默认 | 非法值行为 | 作用 |
|-----|------|-----------|------|
| `SESSION_SUMMARY_ENABLED` | `false` | 回退 `false` + warning（`invalid SESSION_SUMMARY_ENABLED=%r; fallback to false` · continuity 三件套逐字复刻） | 真摘要总开关；**off（未设/false/非法值）→ 装配输出与占位模式逐字节一致**（双对拍钉死 · 上线前提） |
| `OPS_LLM_TIER_SUMMARY_MODEL` | 空（不落档） | 不在已知模型目录 → 回退档默认 + warning | summary 档模型覆盖（`model_catalog.TASK_TIER_MODELS["summary"] = None` = 沿用现网默认；灰度期调档零改码） |

## 摘要条格式与缓存 key

真摘要条 content（占位条格式零改动 · 三标记进上下文，模型可见「这是摘要不是原文」）：

```text
[历史摘要 · v1 · N 轮 · 模型:<model> · 有损压缩，细节以最近轮为准]
<摘要正文>
```

- **缓存 key 铁律**：`chunk_hash = sha256(prompt_version + model + chunk turns canonical JSON)`；
  唯一约束 `(thread_id, chunk_hash)`。窗口滑动 → chunk 内容变 → hash 变 → 自然 miss，
  **无主动失效逻辑**；只用序号会命中旧摘要 = 缓存污染静默错（物理防）。
- 缓存表 `ops_session_summaries`（migration `20260922_session_summaries` · 可逆往返）；
  `prompt_version` / `model` / `turn_count` / `source`（恒 `llm`）落库可版本归因；
  FK CASCADE 随 thread 清理。
- 改 prompt 必须 bump version（`app/ops/prompts/assets/README.md` 纪律）→ key 变自然重生成。

## 故障语义

| 触发 | 行为 |
|------|------|
| 开关 off（未设/false/非法值） | 跳过摘要面：零 LLM 调用、零缓存读写、零 span；输出与占位模式**逐字节一致** |
| on 态 LLM 失败 / 超时（`SUMMARY_TIMEOUT_S=60s` · extract 先例）/ 熔断 | **该 chunk 保留占位符**降级（单 chunk 粒度 ≠ 全局回退开关）；span `session_summary_degraded=N` + log；**永不阻塞主答、绝无半摘要条** |
| prompt 资产缺失/版本非法 | loader 显式炸 → 调用面 try 包住 → 摘要面整体降级占位 + log（不炸请求） |
| 缓存读失败 | 视同 miss 走生成/降级链 |
| 缓存写失败 / migration 未跑 | log + 本次仍用生成的摘要（缓存是优化不是正确性依赖） |
| 并发同 chunk 双生成 | 唯一约束先写赢 · 后者冲突容忍（同 key 同参数语义等价） |
| on 态但 thread_id 缺失 | 保留占位 + warning（身份取自请求上下文既有校验链 · 模型产出不得参与） |

观测：span metadata `session_summary_generated` / `session_summary_cache_hits` /
`session_summary_degraded`；usage 落 `ops_llm_usage`（`task_type="summary"` ·
`surface="lg_rag"` · ContextVar 归因继承零改造）。SSE / 用户面**不输出**摘要过程。

灰度纪律：默认关上线 → 灰度环境 env 开 → 观测（span 降级率 / usage 账 / 摘要条占比）
→ 全量；异常即关 env 回退（**回退动作零代码零迁移** · 缓存表留库无害 · off 态不读不写）。

保真度金样：`evals/session/summary_fidelity_v1.yaml` + `tests/eval/test_session_summary_fidelity.py`
（sentinel must_keep/must_not_add 正反双断言 + 空摘要假通过防线 · 热路径零 LLM-as-judge）。
