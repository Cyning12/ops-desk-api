# 交接 · 最近两天（2026-09-20 ~ 09-21）的更新与未来方向

> **这份文档给谁看**：接手这条线的下一个 agent / 人。
> **怎么用**：先读 §0 拿到"当前在哪、边界在哪"，再按 §1 挑你要碰的主题，
> **§4 的坑务必先看**（否则会把别人踩过的坑重踩一遍）。
> **真源**：代码与脚本本身 > 本文 > 记忆文件。本文里的数字都是 2026-09-21 实测。
> **详细日志**在 `.workbuddy/memory/2026-09-20.md`（49KB）与 `2026-09-21.md`（34KB，含踩坑全过程）。

---

## 0 · 当前状态（先看这段再动手）

| 项 | 值 |
|---|---|
| 仓库 | `ops-desk-api`（本仓）+ `ops-desk-workspace`（`deploy/` 两文件） |
| 分支 | `chore/upgrade-langgraph-1.2` |
| 相对 master | **领先 25 个提交（09-20 的 18 个 + 09-21 本轮的若干个），尚未合并、未开 PR** |
| 依赖基线 | langgraph `1.2.11` / checkpoint `4.2.0` / checkpoint-postgres `3.1.2` / prebuilt `1.1.0` / langchain-core `1.6.3`（伞包 `langchain` 已卸） |
| 全量单测 | `1013 passed / 2 failed / 1 skipped` —— 那 2 条**恒为** `tests/test_chat_ws.py` 的 asyncio 偶发（既有，与近期改动无关；有时 1 条有时 2 条） |
| DB 迁移 | 已到 head `20260920_hitl_requests`（`ops_hitl_requests` 表 + 2 索引在位） |
| 验收 | capability **九层全 PASS**；HITL 联调内存 17 项 / PG 16 项全过；`docs/guides/RUNBOOK_local-acceptance_v1_zh.md` §5 八步整体跑通 |

**边界（别越）**：
- 本仓 `ops-desk-api` 是独立 git repo；`ops-desk-workspace` 是另一个 repo。**跨仓改代码要显式确认**（AGENTS.md 有纪律）。
- 能力清单（`app/ops/capability/manifests/*.yaml`）的改动**必须走 Git + PR + 人闸**，禁止热加载。

---

## 1 · 09-20 做了什么（18 个提交，全部已入库）

按主题，不按时间：

### A · Capability 治理层（P0/P1 硬化）—— 这条线最完整

| 提交 | 内容 |
|---|---|
| `f1905dd` | 观测端点 + 红线 + 黑盒题集 + 基线 diff + **一键九层验收** |
| `14f44a6` | 两项 P0：输出契约 `output_schema` + 会话配额 / kill switch |
| `0120cb8` | 失败成因结构化 —— 熔断判定不再依赖错误文案 |
| `7240ae0` | 下游熔断内核 + gateway 接入 |
| `3d568fd` | R12 红线 + 题集 + 熔断验收层 |
| `e007911` `/` `645bab8` | 降级链（声明才降级、降级必带标记、标记跟着数据走让模型看得见） |
| `c38905f` | 红线 R8（db 持久化下同步 invoke 必须 fail-closed）、R9（幂等命中必须重放上次结果） |
| `c6c08c8` | 幂等命中重放上次结果 |

红线清单现为 **R0–R15 十六条**（`evals/agent/redlines/capability_v1.yaml`）。

### B · 编排与 HITL —— 两天里"真联调抓 bug"最密集的一段

| 提交 | 内容 |
|---|---|
| `3d87f00` | 步骤契约（consumes/produces）+ 可恢复点（八问 Q4/Q8） |
| `e80378c` | 外层 ReAct 收口 + 上下文截断 + HITL 申请落库骨架 |
| `c6c1741` | 两套存储的"重复决定"语义对齐 + 审批回路真联调脚本 |
| `2658870` | **等待授权真挂起 + 批准后真恢复**（`observe` 节点真 `interrupt()`） |
| `6190a59` | 恢复段接回前端（事件接着同一条 run 编号 + replay cursor） |
| `fd8c9b1` | **langgraph 0.2.76 → 1.2.11**（跨大版本迁移） |

### C · 过程基建

`047ddfc` 修脚本在 UTF-8 locale 下必崩（全角字符被吞进变量名）·
`62e8b06` 测试库切换改成硬闸（库名必须以 `_test` 结尾）·
`75cd29c` 默认关闭 Langfuse 上报 + JAVA_HOME 提示随桩服务降到 JDK 21

---

## 2 · 09-21 做了什么（本轮，已提交）

| 主题 | 产物 |
|---|---|
| **真 bug 修复** | `DbHitlStore.alist` 在 asyncpg 下**每次都抛** `AmbiguousParameterError`（参数只出现在 `$1 IS NULL` 位置时驱动推不出类型）。两个调用方都在 `try` 里兜住 ⇒ 静默退化成"只能看单条" ⇒ 会复发"批准一次又冒出一条重复申请"。修法：`CAST(:status AS text)`；并补了**真连库跑 SQL** 的测试（旧测试只断言 SQL 子串、从不执行，所以一直没抓到） |
| **落库这条线可验** | `scripts/acceptance/hitl_persistence_smoke.{sh,py}` —— 零外部依赖、秒级，10 项断言 |
| **OA 出网可验** | `scripts/acceptance/capability_oa_smoke.{sh,py}` —— 自己起 mock-oa，**断言"没有走降级"**（`ok=True` 不够：声明了降级的能力在下游不可达时也返回 True） |
| **自然语言入口可验** | `scripts/acceptance/agent_nl_smoke.{sh,py}` —— 真登录（铸一次性邀请 token）→ 真提交一句话 → 收 SSE → 断言六条结构不变量 → 收尾清理 |
| **运行图/调用链** | `scripts/acceptance/dump_agent_graph.py`（静态拓扑，不调 LLM）+ NL 冒烟落盘**运行链**（按帧序，含循环与未走到的节点） |
| **mermaid 可移植** | `scripts/acceptance/mermaid_util.py` —— 归一化（去 YAML front matter / `<p>` / `&nbsp;`）+ 落**自渲染 HTML** |
| **文档** | `docs/guides/RUNBOOK_local-acceptance_v1_zh.md`（本地五+一条线逐条验收，期望输出全是实测值）；`.env.example` 补全到**代码里 97 个键全覆盖** |
| **生产透传** | `ops-desk-workspace/deploy/.env.example` + `docker-compose.prod.yml` **成对**补 10 个键（跨仓，已按指示修改） |
| **测试卫生** | 三个 SSE 测试模块加 autouse fixture 显式关掉 `LG_RAG_HTTP_CHECKPOINTER`（原来会从 `.env` 继承"生产式"配置，把反向对照断言悄悄翻掉） |

### 自然语言入口在哪（最常被问）

**唯一入口** = `POST /api/ops/lg-rag/stream`（SSE，`freeze lg-rag-sse-v1`，默认 `mode=supervisor`）；
同步版 `POST /api/ops/lg-rag/invoke`。
`POST /api/ops/chat/stream` **已于 2026-08-31 下线**（`app/ops/chat/router.py` 留了 successor 提示）。
两者都要 **cookie 会话**（`CurrentUser`），**没有 Bearer 旁路**；`/hitl/*` 管理面才吃
`Authorization: Bearer <OPS_ADMIN_SYNC_TOKEN>`。

### 并行 / 裁剪 / 权限（被问过，结论记这里）

- **并行** = LangGraph `Send` fan-out：`subtask_join` 算出 `ready`（依赖全终态 + 过步骤契约闸）
  → 写 `inflight_subtask_ids` → `route_next_subtask` 返回 `list[Send]`。节点只有三个工人节点
  （`rag_subtask`/`info_extract`/`tool_exec`），同一节点被并行调用多份。
  **不是"每个子任务起一个 subagent"**，也**不是"先找工具再 send"**——工具在计划阶段就选定。
- **裁剪在构建期**（`strategy_builder`，无 LLM）：`candidates ∩ 可见集`；
  可见集 = `baseline_filter`（只 `local_fn` + `oa` 域 tag 放行 + `deny_high_risk` + `deny_write`）。
  运行期**没有** top-k 工具检索。
- **执行期每次过闸**：gateway `_precheck` = lookup → enabled → **Policy** → 熔断(写探测)
  → **配额/kill switch** → **args_schema** → 执行；被 Policy 拦下的**不计配额**。
- **执行期被拒 ≠ run 死掉**：写失败终态 → `observe` 判 unsatisfied → replan（**不重算 allowlist**）
  → 有界于 `LG_RAG_REACT_MAX_ROUNDS=2` → settle 出带失败说明的结论。
  **Policy 类拒绝不触发 HITL**；只有步骤契约闸（`prefix_touch_required`）才 `hitl_required` + interrupt。

---

## 3 · 未来方向（按优先级）

### P0 · 合并前必做

1. **开 PR 合并到 master**（当前 25 个提交还都在分支上）。合并后建议在干净 venv 里按 CI 方式
   （`uv pip install -r requirements.txt` → `pytest tests`）再走一遍。
2. **上生产前跑一次排空审计**：`./.venv/bin/python scripts/acceptance/hitl_drain_audit.py`
   —— 升级时正好挂在"等待授权"的 run **升级后不可恢复**（旧格式 checkpoint 的 interrupt
   元数据新栈认不出，硬恢复会炸 `TypeError: 'Interrupt' object is not subscriptable`）。
   退出码三态：`0` 干净 / `1` 有没排空的 / **`2` 审计没查成 ≠ 没有**。

### P1 · 已知缺口（都已定位，未做）

3. **修 Langfuse trace 断裂**（两个独立原因，都已实测确认）：
   - **结构性**：根 trace 由 **LangChain CallbackHandler** 建，图节点 span 走我们自己的
     `trace_span`（SDK 的 OTel 接口）⇒ **每个节点各自成独立 root trace**
     （`session=None`、1 个 span）。受控实验证明"同机制就正确嵌套"⇒ 修法是**统一机制**
     （推荐把根 trace 也改成 `trace_span`）。
   - **网络**：SDK 默认走 `HTTPS_PROXY`，而 `jp.cloud.langfuse.com` 经该代理**握手/读超时**
     （绕过代理直连 200）；日志里能看到 `Failed to export span batch ... Read timed out`。
     缓解：`NO_PROXY` 加上 langfuse 主机。
4. **三个验收脚本仍在强制关追踪**（`capability_acceptance.sh` 有 `OPS_ACCEPTANCE_TRACING=1`
   开关；`capability_oa_smoke.sh` / `hitl_persistence_smoke.sh` 连开关都没给）—— 建议统一语义。
5. **`_persist_hitl` 里 `acreate` 未加保护**（`app/ops/lg_rag/multi/nodes.py`）：落库失败会
   整条 run 挂掉（用户明确要求"先裸奔着，我先跑通落库这条线"）。要不要降级为
   `unpersisted=True` + 继续挂起，属行为变更，**待决策**。
6. **`test_chat_ws.py` 的 2 条偶发失败**：一直污染"全量单测"这个判据，值得单独查（像事件循环收尾时序）。

### P2 · 能力增强（讨论过，未开工）

7. **按需工具检索（top-k）**：现在模型看到的是 allowlist 全集，没有检索这一步。
8. **"被 Policy 拒过的能力，在 replan 时从 catalog 摘掉"**：现在 replan 沿用同一 allowlist，
   模型可能再选一次同一个被拒的能力（有界于 2 轮）。
9. **F 线扩成一组 query**（工具路径 / 纯 RAG / 拒答 / 触发人工审批），每条断言它该走的角色。
   注意 LLM 不确定性：同一句话实测耗时 **85s~333s**、走 rag 还是 tool 也会变。

---

## 4 · 踩过的坑（先看，别再踩）

### 工程类

1. **`grep` 在本沙箱会静默返回空**（退出码 0、零结果）。一律用 Grep 工具，别用 bash grep。
2. **`curl` 不能当就绪探针**：未监听的端口也会返回 502 且退出码 0。**且"内容型就绪探针"必须
   配"端口前置检查"**——否则一个**残留的旧服务**能满足内容探针，脚本全程在跟别人的服务说话
   （实测：内存模式却返回 409，查半天代码）。三个起服务的脚本已加 `require_free_port`。
3. **8000 端口被 Docker Desktop 长期占着**：uvicorn 起不来，但 `lsof` 仍显示"在听"。本项目一律用 8123。
4. **`app.config` 在 import 时 `load_dotenv`**：独立脚本不先 `import app.config` 就读不到 `.env`。
   而 `override=False` 只认"键是否存在"⇒ **空值环境变量能压住 `.env`**（验收脚本靠这个隔离）。
5. **清尾只删"自己创建的"**：绝不按范围条件批量删（"所有未使用的…"）——那是别人的数据，
   而且 `--help`（argparse 直接 SystemExit）也会走到 `finally`。**我曾因此在开发库误删 20 条未消费邀请**。
6. **async SQLAlchemy 连接池绑事件循环**：把"创建"和"清理"分别放进两次 `asyncio.run`，
   第二次会抛 `attached to a different loop`，且发生在 `finally` ⇒
   表现是"检查全过、最后报清理失败、垃圾数据留在库里"。
7. **`bash 3.2` + UTF-8**：`$VAR` 后紧跟中文要用 `${VAR}`，否则多字节字符被吞进变量名。
8. **`python-dotenv` 之外**：`.env` 里 `OPS_NL_SMOKE_TRACING` 那类"我以为是开关"的变量，
   要先 grep 确认代码真的读它。

### Agent/框架类

9. **`from __future__ import annotations` + 节点 `config` 注解**：注解是字符串，langgraph 只认
   `RunnableConfig` / `Optional[RunnableConfig]` 两种字面写法。写成 `RunnableConfig | None`
   它不认，**后果不只是告警——config 不会被注入** ⇒ `observe_node` 拿不到 thread_id
   ⇒ 审批申请没有归属 ⇒ 批准之后无从恢复。
10. **`langgraph-prebuilt` 会装漏文件**（同一次 pip 事务里目录只落 3 个 py 而应有 7 个，
    到 import 才炸）。装完必须 `from langgraph.prebuilt import ToolNode` 验证。
11. **`ToolNode` 不能裸调**（要图注入的 Runtime）；挂了 checkpointer 的图必须传 `thread_id`。
12. **带降级声明的能力，下游不可达时也返回 `ok=True`**（内容是兜底）⇒
    "能力通不通"的检查**不能只看 `ok`**，必须同时看 `degraded` 标记。
13. **测试不该读 `.env`**：凡"只在生产开"的开关，测试要么显式关要么显式开。
14. **只断言 SQL/请求字符串的子串 ≈ 没测**：证明不了它在真驱动上跑得通（第 1 条真 bug 就这么活下来的）。

---

## 5 · 上手最快的一条路径

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
export PATH="/opt/homebrew/bin:$PATH"          # Homebrew CLI 不在默认 PATH 里
export no_proxy=127.0.0.1,localhost

bash scripts/acceptance/hitl_persistence_smoke.sh    # 秒级：落库线通不通
bash scripts/acceptance/capability_oa_smoke.sh       # 起 mock-oa，验 OA 出网
bash scripts/acceptance/capability_acceptance.sh     # 九层门禁（含真桩服务）
bash scripts/acceptance/agent_nl_smoke.sh            # 真 LLM 端到端（1.5–5 分钟，花钱）
```
完整顺序与每步期望输出见 `docs/guides/RUNBOOK_local-acceptance_v1_zh.md`。

---

## 6 · 待核实清单（别当成已确认）

| 项 | 核实方式 |
|---|---|
| 新栈写的 checkpoint 旧栈能否读（回滚可行性） | 用 0.2.76 的栈去 `aget_state` 一个 1.2.11 种下的挂起 thread |
| langfuse SDK 导出超时是否可通过构造参数调大 | 查 langfuse 3.15 的 `Langfuse(...)` 签名/文档源码 |
| 生产镜像里 `app/ops/capability/manifests/*.yaml` 是否被 `.dockerignore` 排除 | `docker compose ... run --rm api ls /app/app/ops/capability/manifests/` |
