# RUNBOOK · 本地跑通与验收（langgraph 1.2 + HITL）

> **范围**：只讲**本地**——从配好环境到五条线逐条跑通。生产部署 / 容器透传不在本文（见 §7）。
>
> **可信度声明**：本文每一个「期望输出」都是 **2026-09-21 在本机实测**得到的，不是"应该是"。
> 命令可直接复制粘贴；哪一步不通过，对应小节里写了"先看哪里"。
>
> **验收对象**：分支 `chore/upgrade-langgraph-1.2`。该分支**尚未合并到 master**——
> 本文验收通过 ≠ 已上线，合并才算。

---

## 0 · 本地要跑通的是哪五条线

这五条**互相独立**，坏一条不代表别条坏——所以分开验，不合并成一个"通过率"：

| 线 | 验什么 | 命令 | 依赖 |
|---|---|---|---|
| **A** 治理层 | capability 九层门禁（单测 / 题集 / 红线 / 配额 / 熔断 / 降级 / 持久化 / 编排 / 真桩联调） | `capability_acceptance.sh` | PG + Java + jar |
| **B** 落库线 | HITL 申请落得下、查得到、**列表 SQL 跑得通**、回调幂等 | `hitl_persistence_smoke.sh` | **仅 PG（+ 迁移）** |
| **C** 出网线 | OA 能力真能打通 mock-oa（凭证 + base_url + 清单加载都对） | `capability_oa_smoke.sh` | jar + JDK ≥ 21 |
| **D** 审批回路 | 挂起 → OA 批准 → 恢复（含"不许假装恢复"的对照） | `hitl_approval_loop.sh` | jar；PG 模式还要 PG |
| **E** 回流线 | 批准后的结论能回前端（事件接着同一条 run 编号） | §4-E | 无（纯测试） |
| **F** **自然语言入口** | 真登录 → 真提交一句话 → 真跑多智能体图 → 真调到能力 | `agent_nl_smoke.sh` | **真 LLM key**（花钱、慢） |

> **F 是前五条都替代不了的**：A–E 全是单测级、CD 级或**进程内直调**。
> 入口那一层（鉴权 / SSE 帧序 / 租户解析 / 图装配 / 能力调用）任何一环断了，
> 前五条照样全绿。**A–E 绿 + F 红 = 问题在入口层**，反之亦然。

**为什么 B 要单独一条**：`DbHitlStore.alist` 曾经在 asyncpg 下**每次都抛**
`AmbiguousParameterError`（参数只出现在 `$1 IS NULL` 位置时驱动推不出类型）。
它的两个调用方（`_persist_hitl` 去重、`resume` 汇总同批申请）**都在 `try` 里兜住**了
⇒ 静默退化成"只能看单条" ⇒ 表现为"批准一次又冒出一条重复申请"。
而当时的单测**只断言 SQL 字符串子串、从不真跑**，所以它一直没被发现。
B 这条线就是它的第一现场。

---

## 1 · 前置条件

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
export PATH="/opt/homebrew/bin:$PATH"          # Homebrew 的 CLI 默认不在 PATH 里

echo "--- 端口 ---"
for p in 5432 6333 8000 8123 18080; do
  printf "%-6s " "$p"
  lsof -nP -iTCP:$p -sTCP:LISTEN >/dev/null 2>&1 && echo "占用" || echo "空闲"
done

echo "--- 工具链 ---"
java -version 2>&1 | head -1                   # 需要 ≥ 21（mock-oa jar 按 21 构建）
command -v mvn >/dev/null && mvn -v 2>&1 | head -1 || echo "缺 maven（只在构建 jar 时需要）"
./.venv/bin/python -V                          # 应为 3.11.x

echo "--- 迁移是否已到 head ---"
./.venv/bin/python -m alembic current 2>/dev/null | tail -1

echo "--- 桩服务 jar ---"
ls -la ../ops-desk-mock-oa/target/mock-oa-0.0.1-SNAPSHOT.jar
```

| 项 | 要求 | 不满足时 |
|---|---|---|
| PostgreSQL | 5432 在听；库 `opsdesk` 存在 | 起 Docker Desktop 的 PG |
| Qdrant | 6333 在听（**可选**） | 缺了只出 `Failed to obtain server version` 告警，测试仍过 |
| JDK | ≥ 21 | `export JAVA_HOME=$(/usr/libexec/java_home -v 21)` |
| 端口 8123 / 18080 | 空闲 | 换 `AGENT_PORT` / `MOCK_OA_PORT` |
| 端口 **8000** | **不要用** | 本机被 `com.docker.backend` 占着：uvicorn bind 失败，但 `lsof` 仍显示"在听"——就绪探针会被骗过 |
| 迁移 | `alembic current` 显示 `20260920_hitl_requests (head)` | 见 §3.1 |

---

## 2 · 配置

### 2.1 `.env`（本地已配好；这里写"为什么"）

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
[ -f .env ] || cp .env.example .env
```

`.env` 已被 gitignore。与这五条线相关的键（**值都是本地开发值，不是真密钥**）：

| 键 | 本地值 | 不配会怎样 |
|---|---|---|
| `DATABASE_URL` | `…/opsdesk` | — |
| `OPS_HITL_PERSISTENCE` | `db` | 默认 `null` = **不落库**，且"人在等一个不存在的审批" |
| `OPS_HITL_CALLBACK_SECRET` | `s3cr3t` | 空 ⇒ 回调端点**拒绝一切请求**（不设密钥=不开放） |
| `OPS_ADMIN_SYNC_TOKEN` | `admintok` | `/hitl/*` 管理端点的 Bearer 路径被禁用（401） |
| `OPS_CAPABILITY_PERSISTENCE` | `db` | 默认 `null` = 不落防重与回执 |
| `OPS_CAPABILITY_EXTRA_MANIFESTS` | 指向 `oa.readonly.v1.yaml` | **默认只加载 builtin 的 5 个 local_fn**；不显式列出，OA 三个能力不进注册表 |
| `OPS_CAP_CRED_OA_GATEWAY_TOKEN` | `local-dev-token` | 清单只写**凭证名**，值在这里；缺 ⇒ 该能力恒 `permission_denied` |
| `OA_BASE` | `http://127.0.0.1:18080` | 清单里写的是 `base_url: OA_BASE`；缺 ⇒ `upstream_error: 未配置 base_url 环境变量: OA_BASE` |
| `LG_RAG_HTTP_CHECKPOINTER` | `postgres` | **P0' T3 起默认开**（不设即 postgres）；显式空/off ⇒ 内存 saver ⇒ 跨请求恢复**不可能成立**（恢复端点 503 fail-closed） |
| `OPS_CHAT_TRACER` | `langfuse` | **手工起服务会真往外发 trace**；跑验收脚本时脚本会把它置空（见下） |

> **两个必须知道的机制**（都实测确认过）：
>
> 1. `app.config` 在 **import 时**做 `load_dotenv`，且 `override=False`。
>    ⇒ **独立脚本若没先 import `app.config`，`.env` 不会被读**，会静默退化。
>    自己写脚本时第一行就 `import app.config`。
> 2. `override=False` 只认"**键是否已存在**"，不看值。
>    ⇒ 用一个**空值环境变量**就能压住 `.env`（实测 `LG_RAG_HTTP_CHECKPOINTER= …` → `False`）。
>    验收脚本正是靠这个把 `.env` 里的 `postgres` / `db` / `langfuse` 临时关掉，
>    所以脚本的断言不受 `.env` 当前写什么影响。

### 2.2 关键默认值（会被断言的）

| 环境变量 | 默认 | 含义 |
|---|---|---|
| `OPS_CAPABILITY_MAX_CALLS_PER_SESSION` / `…MAX_WRITES_PER_SESSION` | `64` / `8` | 会话配额（**按 `run_id` 分桶**） |
| `OPS_CAPABILITY_KILL_SWITCH` | 空 | **逗号分隔的匹配模式列表，不是布尔开关**；`*`=全停，`oa.ticket.*`=停该前缀 |
| `OPS_CAPABILITY_CB_ENABLED` / `_FAIL_MAX` / `_RESET_TIMEOUT` / `_SUCCESS_THRESHOLD` | `1` / `5` / `60` / `1` | 熔断总闸 + 三态阈值 |
| `OPS_CAPABILITY_CB_BACKEND` | `mock-unavailable` | `memory` / `redis` / `mock-unavailable`。**默认那个是刻意让存储不可用的"测试模式"**（逼回落路径被走到）；本地想干净可给 `memory` |
| `LG_RAG_SUPERVISOR_MAX_STEPS` / `…_MAX_WALL_SECONDS` | `32` / `0`（不限） | 内层步数 / 墙钟 |
| `LG_RAG_REACT_MAX_ROUNDS` | `2` | 外层 ReAct 轮次（**与步数是两个维度**，不能互相替代） |

---

## 3 · 启动

### 3.0 依赖（只在环境是新的时做）

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
./.venv/bin/python -V || python3.11 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip install "pytest>=8.2,<9" "pytest-asyncio>=0.23,<1"
```

> `Makefile` 的 `make install/dev` 走 `uv`；**`make dev` 固定 8000 端口，本机别用**。

### 3.1 数据库迁移

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
./.venv/bin/python -m alembic current     # 看现在到哪
./.venv/bin/python -m alembic upgrade head
./.venv/bin/python -m alembic current     # 期望：20260920_hitl_requests (head)
```

该迁移是**纯增量**（`CREATE TABLE IF NOT EXISTS` + 两个 `CREATE INDEX IF NOT EXISTS`），
重跑安全。**本机当前已到 head**（表 `ops_hitl_requests` 与两个索引都在位）。

不跑这步的直接后果：§4-B 第 1 条就 `relation "ops_hitl_requests" does not exist`；
而且这个异常会从 `observe_node` 抛穿到 SSE 外层，表现为**流尾一帧 `error`**
（`stage: lg_rag.stream`、`retryable: true`，detail 截断 200 字）——
不是崩溃也不是卡住，很难一眼看出是缺表。

### 3.2 起 API（避开 8000）

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
export no_proxy=127.0.0.1,localhost NO_PROXY=127.0.0.1,localhost
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8123
```

就绪判据**必须校验内容**（8000 的坑就是这么来的）：

```bash
curl -s http://127.0.0.1:8123/health
# 实测：{"status":"ok"}

curl -s http://127.0.0.1:8123/openapi.json | grep -c "/hitl/callback"
# 实测：1（0 说明路由没挂上，端口在听也是别人的服务）
```

> 出口代理会把打 `127.0.0.1` 的请求送到代理去（拿到看不懂的 502）。
> shell 里先导 `no_proxy`；脚本里用 `urllib.request.build_opener(urllib.request.ProxyHandler({}))`。

### 3.3 构建并起 mock-oa

**先构建**（只在 jar 不存在或源码改过时做）：

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-mock-oa
export PATH="/opt/homebrew/bin:$PATH"
mvn -B clean package -DskipTests        # 产物：target/mock-oa-0.0.1-SNAPSHOT.jar
```

**再起服务**（⚠️ 这一步经常被漏掉，见 §4-C 的说明）：

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-mock-oa
java -jar target/mock-oa-0.0.1-SNAPSHOT.jar --server.port=18080
```

就绪判据（另开终端）：

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/actuator/health
# 期望 200（body 是 {"status":"UP"}，**大写 UP** —— 别和 FastAPI 的 "ok" 混）
```

停：前台 `Ctrl-C`，或 `pkill -f 'mock-oa-0.0.1-SNAPSHOT.jar'`。

> **构建前 `clean` 是必要的**：`target/` 里残留旧 JDK 版本的 class 会直接编译失败。
> **必须用命令行参数指定端口**：环境里有 `SERVER__PORT`，Spring 宽松绑定会把它当成
> `server.port` 覆盖 `application.yml`，而命令行参数优先级最高。
>
> §4-A / §4-C / §4-D 的脚本都会**自己起停桩服务**（只要 jar 在），
> 所以走脚本时不需要你手工起——**但 §4-C 的手工片段需要**。

---

## 4 · 五条线逐条验收

### A · Capability 九层门禁

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
bash scripts/acceptance/capability_acceptance.sh
```

**实测输出**（2026-09-21 10:02）：

```
▶ 单测     capability 单测            PASS
▶ 题集     黑盒题集（含基线 diff） PASS
▶ 红线     红线（否决项）        PASS
▶ 失控兜底 kill switch + 会话配额   PASS
▶ 熔断     三态 + 只熔环境类失败 PASS
▶ 降级     声明才降级 + 必须带标记 PASS
▶ 持久化  DB 版 store/sink            PASS
▶ 编排     步骤契约 + 可恢复点  PASS
▶ 联调     真桩服务 26 项          PASS
失败 0 · 跳过 0
```

报告落在 `.acceptance-reports/capability-acceptance-<时间戳>.md`（已 gitignore），每层带证据。

**可调参数**：`SKIP_SMOKE=1`（只跑前八层，不需要桩服务）、`MOCK_OA_PORT`、`MOCK_OA_DIR`、
`ACCEPTANCE_REPORT_DIR`、`OPS_ACCEPTANCE_TRACING=1`（打开外部 trace 上报，**默认关**——
验收不该有外部副作用）。

**不通过先看这里**：联调层 SKIP ⇒ jar 没构建或 java < 21；熔断层 FAIL ⇒ 去看是不是
有别的能力也声明了降级（本层用的是自备探针清单 `circuit.probe`，别改成业务清单）。

---

### B · 落库这条线（**最快、建议第一个跑**）

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
bash scripts/acceptance/hitl_persistence_smoke.sh
```

它自己起 API（强制 `OPS_HITL_PERSISTENCE=db`、把 `OPS_CHAT_TRACER` 置空）、等就绪、跑完杀进程。

**实测输出**：

```
[PASS] GET /hitl/runtime 可达 —— code=200
[PASS] 持久化模式 = db（否则验的是内存版） —— db
[PASS] 回调签名密钥已配置
[PASS] POST /hitl/requests 落库 —— code=200 id=hitl_smoke_…
[PASS] GET /hitl/requests/{id} 查得到 —— code=200 status=pending
[PASS] GET /hitl/requests?status=pending 真跑通（alist） —— code=200
[PASS] 列表里能看到刚建的那条 —— 本批 1 条
[PASS] POST /hitl/callback 批准成功 —— code=200
[PASS] 重复回调 → 409（不是 404） —— code=409
[PASS] 审批人落库且中文未乱码 —— '张三'

落库冒烟全部通过
收尾：删除本次造的申请 1 条
```

退出码 0。**它造的申请会自己删掉**（没有删除端点，脚本直连库清，并把清了几条打出来）。

**不通过先看这里**：
- `持久化模式 = db` FAIL ⇒ `OPS_HITL_PERSISTENCE` 没生效（或 `.env` 没被加载）
- 第 1 条就 `relation … does not exist` ⇒ §3.1 迁移没跑
- 只有列表那条 FAIL 而单条 OK ⇒ 又踩到 `alist` 那类"只在真驱动上炸"的 SQL

---

### C · OA 能力出网（验证三个配置项真配对）

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
export PATH="/opt/homebrew/bin:$PATH"        # 需要 java
bash scripts/acceptance/capability_oa_smoke.sh
```

它自己起 mock-oa（`--server.port=18080`）、等 actuator 就绪、跑完杀进程；
前置用**显式环境变量**固定（`OPS_CAPABILITY_EXTRA_MANIFESTS` / `OA_BASE` /
`OPS_CAP_CRED_OA_GATEWAY_TOKEN`），不依赖 `.env` 当前写的是什么；
`OPS_CHAT_TRACER` 置空，避免验收产生外部 trace。

**实测输出**：

```
桩服务就绪（mock-oa=18080）；日志目录：…
（OA_BASE=http://127.0.0.1:18080 凭证名 oa_gateway_token）

[PASS] OA 清单已加载（能力数应 ≥ 8） —— 共 8 个，3 个 OA 能力都在

原始返回：
  ok = True | error = None
  degraded = None | trigger = None
  result.code = 0 | tenant = acme
  output._degraded = False
  items[0] = {"code": "ZD-2026-014", "title": "差旅费报销管理办法（2026 修订）", …

[PASS] 调用成功
[PASS] **没有走降级**（ok=True 不够，降级也是 True） —— trigger=None
[PASS] output 里也没有降级标记
[PASS] 下游业务码 = 0 —— 0
[PASS] 租户谓词下推可见（隔离的硬证据） —— 'acme'

OA 出网冒烟全部通过
```

**四处各自证明一件事**：`8 个能力` ⇒ `OPS_CAPABILITY_EXTRA_MANIFESTS` 生效；
`没有走降级` ⇒ 真的连上了下游；`result.code = 0` ⇒ `OA_BASE` 与
`OPS_CAP_CRED_OA_GATEWAY_TOKEN` 都对了；`tenant = acme` ⇒ **租户谓词真的下推到了下游**
（租户隔离唯一的硬证据）。

#### ⚠️ 为什么这条**不能只看 `ok=True`**

`oa.doc.search` 的清单里**声明了降级**（`action: static`，触发词含 `transport`）。
所以 **mock-oa 没起时它照样返回 `ok=True`**，只是内容是那句静态兜底：

```json
{"code": 503, "message": "文档检索服务暂时不可用，请稍后重试（这是降级结果，不是检索结果）",
 "data": {"items": []},
 "_degraded": {"capability": "oa.doc.search", "action": "static", "trigger": "transport", "depth": 1}}
```

**只看 `ok` 会把"根本没连上"判成通过**（这正是本文档第一版的缺陷：那段手工片段里
"先起 mock-oa"只写在引用块里，照着敲很容易只跑了 `mvn package` 就往下走）。
必须同时看三样：`ok is True` **且** `degraded` 为空 **且** `result.code == 0`——
脚本已经这么断言了。

#### 四种形态的实测对照（照它定位）

| 情形 | ok | error | degraded.trigger | result.code / tenant |
|---|---|---|---|---|
| **服务没起** | **True** | — | **transport** | None / None |
| 凭证错 | False | `permission_denied: upstream_code=2003` | — | — |
| `OA_BASE` 空 | False | `upstream_error: 未配置 base_url 环境变量: OA_BASE` | — | — |
| 全对 | True | — | — | `0` / `acme` |

**反向对照**（脚本会红，退出码 1）：把 `OA_BASE` 指到没人监听的端口 →
4 条断言 FAIL，并打印
`transport 降级 = 根本没连上下游。查：mock-oa 起了吗？端口对不对？出口代理会拦 127.0.0.1 吗？`。
jar 缺失 → 直接提示先 `mvn -B clean package -DskipTests`。

#### 想看细节时的手工复现

```bash
# ⚠️ 先按 §3.3 把 mock-oa 起起来（这一步漏了就会得到上面那个"看起来成功"的降级结果）
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
export no_proxy=127.0.0.1,localhost
./.venv/bin/python - <<'PY'
import app.config, asyncio, json          # ← 必须先 import app.config，否则 .env 不生效
from app.ops.capability import list_capabilities
from app.ops.capability.manifest import load_extra_manifests_from_env

load_extra_manifests_from_env()
rows = list_capabilities()
print("注册能力数:", len(rows), "->", [r.capability_id for r in rows])

from app.ops.capability.gateway import ainvoke
async def main():
    res = await ainvoke("oa.doc.search", {"keyword": "报销", "top_k": 5},
                        ctx={"tenant_id": "acme", "run_id": "smoke", "subtask_id": "smoke:1"})
    m = res.meta or {}
    print("ok =", res.ok, "| error =", res.error)
    print("degraded =", m.get("degraded"), "| trigger =", m.get("degraded_trigger"))
    print("output:", json.dumps(res.output, ensure_ascii=False)[:200] if res.output else None)
asyncio.run(main())
PY
```

---

### D · HITL 审批回路（两种模式都要跑）

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
bash scripts/acceptance/hitl_approval_loop.sh                    # 内存模式 → 17 项
HITL_RESUME_PG=1 bash scripts/acceptance/hitl_approval_loop.sh   # PG 模式  → 16 项
```

**实测**：两次都以「联调全部通过」结尾（2026-09-21 复跑确认）。

**第 9 步的期望值随模式变**，这是整套脚本里最有价值的一对断言：

| 模式 | 恢复端点期望 | 为什么 |
|---|---|---|
| 默认（内存 saver） | **503** | 内存 saver 每请求新建 ⇒ 跨请求恢复**不可能成立**。返回 200 = "人点批准、什么都没发生" |
| `HITL_RESUME_PG=1` | **409** | 走真 PG checkpointer；这里造的 thread 没真挂起过 ⇒ 必须拒绝，**而不是把 `Command` 当成新输入重开一局** |

另外两条对照：`已批但无 unlock_subtask_id ⇒ 409`（与 503 区分）、`pending 不许恢复 ⇒ 409`。

> 这套脚本是**唯一**抓到过「JDK HttpClient 的 h2c 升级头让 uvicorn 不读请求体」和
> 「两套存储对"重复决定"的语义分叉」的手段——单测与桩都抓不到，别用单测替代它。

**不通过先看这里（这条很坑，实测踩过）**：如果你**没动过相关代码**，却看到
「内存模式却返回 409」或「`持久化=memory` 断言失败」，**先查端口是不是被别人占着**：

```bash
lsof -nP -iTCP:8123 -sTCP:LISTEN     # 代理侧 API 用的端口
lsof -nP -iTCP:18081 -sTCP:LISTEN    # 这套脚本用的桩服务端口
```

原因：uvicorn bind 失败会**很快退出**，而就绪探针是"内容型"的——
**一个残留的旧服务同样满足"内容对得上"**，于是整轮脚本都在跟别人的服务说话
（那个旧服务可能是用别的环境变量起来的，所以断言全错位）。
现在三个起服务的脚本都加了**端口前置检查**：被占用就明确拒绝并列占用者，退出码 1，
不会再静默连错。清掉残留或换端口（`AGENT_PORT` / `OA_PORT` / `MOCK_OA_PORT`）再跑。

---

### E · 恢复段回流

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
./.venv/bin/python -m pytest tests/test_hitl_resume.py tests/test_hitl_resume_events.py \
  tests/test_react_observe.py tests/test_lg_rag_sse_hitl.py -q --basetemp=.pytest-tmp
rm -rf .pytest-tmp
```

**实测**：`65 passed`。

三条"换过环境就必须重跑"的硬证据：

| 测试 | 在证明什么 |
|---|---|
| `test_resume_across_two_saver_instances` | **真 PG**：两个独立 saver 实例＝两个 HTTP 请求，能跨实例找回挂起点并恢复 |
| `test_seq_continues_from_start_seq` | 恢复段事件**接着同一条 run 继续编号**；从 1 重开会被 replay 的 `seq > after_seq` 整段过滤掉，客户端只看到"replay 返回空" |
| `test_hitl_pending_really_interrupts_the_graph` | 图**真的挂起**（而不是写个标签继续出结论） |

---

### F · 自然语言入口（真登录 · 真模型 · 真多智能体）

**自然语言入口只有一个**：`POST /api/ops/lg-rag/stream`（SSE，freeze `lg-rag-sse-v1`，默认
`mode=supervisor`）。同步版 `POST /api/ops/lg-rag/invoke`。
`POST /api/ops/chat/stream` **已于 2026-08-31 下线**（`app/ops/chat/router.py` 里留了
successor-version 提示）。两者都需要 **cookie 会话**，`Authorization: Bearer` 对它无效。

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
export PATH="/opt/homebrew/bin:$PATH"
bash scripts/acceptance/agent_nl_smoke.sh                      # 默认 query 会命中文档里的工具
bash scripts/acceptance/agent_nl_smoke.sh --expect-tool         # 硬断言"这次真调到能力了"
bash scripts/acceptance/agent_nl_smoke.sh --query "现在几点了？"  # 换一句
```

它自己起 API、**铸一枚一次性邀请 token 并真登录**（等价 `scripts/create_initial_user.py`），
把自然语言 POST 进去、逐帧收 SSE，跑完删掉自己造的邀请/会话/用户。

**实测输出**（2026-09-21，`--query "查一下 issue 21 的标题和状态" --expect-tool`）：

```
provider=siliconflow model=deepseek-ai/DeepSeek-V4-Flash
[PASS] LLM key 已配置（这条冒烟会真调模型）
[PASS] 登录成功（cookie 会话） —— {"ok": true, "user": {"username": "nl-smoke", "role": "maintainer"}}

提交自然语言：'查一下 issue 21 的标题和状态'（mode=supervisor）
共 220 帧，耗时 107.9s
帧序： run.start → node.progress ×4 → subtask.progress ×2 → node.progress ×2 → answer …
出现过的 agent_role： ['aggregator', 'critic', 'intent', 'observe', 'strategy_builder',
                     'subtask_join', 'supervisor', 'system', 'tool_exec']
[PASS] 首帧是 run.start
[PASS] 图真的跑了（看到节点帧）
[PASS] 没有 error 帧
[PASS] 出结论（answer 非空）或转入等待授权 —— answer 391 字
[PASS] 正常收口（有 done）
[PASS] 这次确实用到了能力/子任务（--expect-tool）

本次是否用到能力/子任务：True（子任务里出现过 tool 类型：True）
answer 预览：### 子任务 1：查询 Issue 21 详情
             - **来源**：工具查询（`get_issue_by_number`）
             - 标题：`什么时候支持Memory` / 状态：`open`

自然语言冒烟全部通过
收尾：删除邀请 1 条、session 1 条、用户 nl-smoke
```

**这一次就同时证明了六件事**：入口可达、cookie 鉴权能过、SSE 帧序对、
**多智能体图真的装配并跑完**（9 个角色里含 `supervisor` / `observe` / `critic`）、
**能力真的被调到**（`tool_exec` + `get_issue_by_number` 返回真实数据）、收口干净。

**它验什么 / 不验什么**：只验**结构不变量**（上面六条），
**不验"答得对不对"**——那是评测集（`evals/`）与 `scripts/router_accuracy.py` 的职责。

**代价与注意**：
- **真调 LLM**：实测同一句话耗时 **85s ~ 293s** 波动很大（模型选 rag 还是 tool 差别很大）。
- 需要 `.env` 里的 `SILICONFLOW_API_KEY`。
- 默认 query 依赖开发库里有 `issue 21`；换库时用 `--query` 指定。
- `--expect-tool` **依模型选择而定**，会偶发失败：同一句话这次拆成 `rag_subtask`、
  下次才拆成 `tool_exec`。失败信息会写明「模型这轮没走工具——非链路故障」。
  **要确定性的能力调用断言，用图级 mock 测试，不要靠这条。**

#### 追踪（Langfuse）：默认跟随 `.env`，并且会**查证**真的收到

本脚本**不**再强制关追踪——它是给人看的，trace 正是要看的东西。
要"零外部副作用"就跑 `OPS_NL_SMOKE_NO_TRACING=1`。

```bash
bash scripts/acceptance/agent_nl_smoke.sh                 # 跟随 .env（有 langfuse 就上报）
OPS_NL_SMOKE_NO_TRACING=1 bash scripts/acceptance/agent_nl_smoke.sh   # 不上报
```

跑完它会**主动查一次 Langfuse**（按 `session_id = thread_id`），而不是假设上报成功：

```
追踪已开（OPS_CHAT_TRACER），查 Langfuse 是否真的收到这一轮…
[PASS] Langfuse 收到本轮 trace（session_id=thread_id） —— trace_id=6b2f40dc3d4da65fc96e44acaecd9cf2 name=lg-rag
```

> **为什么要"查"**：上报是异步的，SDK 不报错 ≠ 平台收到了。常见的静默失败是
> **environment 选错**（`LANGFUSE_ENV=prod`，UI 里选了 dev 就"看起来没有"）、
> key 属于另一个 project、网络被拦。查一次三种都能立刻排掉。
>
> 若这里 FAIL，先看：`.env` 的 `OPS_CHAT_TRACER` 是否为 `langfuse`、
> `LANGFUSE_PUBLIC_KEY/SECRET_KEY/BASE_URL` 是否齐全、UI 的 Environment 是否与
> `LANGFUSE_ENV` 一致。

#### 运行链落盘（mermaid）

跑完自动写一份 Markdown 到 `--mermaid-out`（默认 `.acceptance-reports/agent-runs/`，已 gitignore）：

```
运行链已落盘：.acceptance-reports/agent-runs/20260921-112948-查一下issue21的标题.md
（Markdown 里的 mermaid 块在 VS Code / GitHub 可直接预览）
```

产物里有四块，**这是"这次到底走了哪些节点"最直观的东西**：

1. **实际运行链**——按帧序、每次访问一个独立节点，所以循环与重复访问如实画出来
   （箭头带条件边标签，如 `observe -- settle --> aggregator`）：
   ```mermaid
   flowchart TD
     S([START]) --> n1["1. intent_node"]
     n1 --> n2["2. strategy_builder"]
     n2 --> n3["3. supervisor"]
     n3 --> n4["4. subtask_join"]
     n4 --> n5["5. tool_exec ×2"]
     n5 --> n6["6. subtask_join"]
     n6 --> n7["7. observe"]
     n7 -- settle --> n8["8. aggregator"]
     n8 --> n9["9. critic_node"]
     n9 --> E([END])
   ```
2. **节点访问次数表**（一眼看出哪儿转了两圈）
3. **本次未走到的节点**（对照拓扑点出没执行的分支）
4. **静态拓扑**（LangGraph 原生 `draw_mermaid()`，含 `settle`/`replan`/`rebind`/`retry_planner` 等分支标签）

#### 只想看静态拓扑（不花钱、秒出）

```bash
./.venv/bin/python scripts/acceptance/dump_agent_graph.py                 # 三张图都导
./.venv/bin/python scripts/acceptance/dump_agent_graph.py --graph supervisor --print
```

实测：`supervisor 12 节点/17 边`、`router 8/11`、`basic 3/2`；
产物 `.acceptance-reports/agent-graphs/<name>-topology.{mmd,md}`。
**不调 LLM，所以随时可跑**；mermaid 源能进 diff ⇒ 拓扑改了看得见。
（刻意不用 `draw_mermaid_png()`：它要走外网渲染服务。）

---

### 附加 · 全量单测 + 排空审计

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
./.venv/bin/python -m pytest tests/ -q --basetemp=.pytest-tmp; rm -rf .pytest-tmp
```
**实测**：`1013 passed / 2 failed / 1 skipped`。

- `--basetemp=.pytest-tmp` **必须带**：不带的话 `tmp_path` 的 mkdir 会被沙箱文件代理拦，
  表现为**大批用例 ERROR 而不是 FAIL**，很容易误判成代码问题。
- 那 **2 个失败恒为 `tests/test_chat_ws.py`** 的 asyncio 偶发（有时 1 有时 2，**波动≠回归**）。
- `1 skipped` 是「真 MCP 外网/本机 server」那条（要 `-m integration` + 真 endpoint）。
- 判断"失败是不是我引入的"最快手段：`git stash` 再跑一遍对照。

```bash
./.venv/bin/python scripts/acceptance/hitl_drain_audit.py; echo "exit=$?"
```
**实测**：输出 `没有在飞的审批 —— 可以安全升级`，`exit=0`。
（三态退出码：`0` 干净 / `1` 有没排空的 / **`2` 审计本身没查成——绝不等于"没有"**。）

---

## 5 · 一次跑完的顺序清单

```bash
cd /Users/cyning/Desktop/Ops-desk/ops-desk-api
export PATH="/opt/homebrew/bin:$PATH"          # ③④⑤ 要用 java

./.venv/bin/python -m alembic upgrade head                          # ① 表建起来
bash scripts/acceptance/hitl_persistence_smoke.sh                   # ② B 落库线（最快，先跑）
bash scripts/acceptance/capability_oa_smoke.sh                      # ③ C 出网线（自己起 mock-oa）
bash scripts/acceptance/capability_acceptance.sh                    # ④ A 九层（含真桩服务 26 项）
bash scripts/acceptance/hitl_approval_loop.sh                       # ⑤ D 内存模式
HITL_RESUME_PG=1 bash scripts/acceptance/hitl_approval_loop.sh      # ⑥ D PG 模式
# ⑦ 全量单测：**这个退出码会是 1**（下面有已知的 2 条偶发失败），看输出而不是退出码
./.venv/bin/python -m pytest tests/ -q --basetemp=.pytest-tmp 2>&1 | tail -5; rm -rf .pytest-tmp
./.venv/bin/python scripts/acceptance/hitl_drain_audit.py           # ⑧ 排空审计（退出码应 0）

# ⑨ F 自然语言入口 —— **按需**：真调 LLM、单次 1.5–5 分钟、花钱
bash scripts/acceptance/agent_nl_smoke.sh
#   跑完落盘两份直观产物：
#     .acceptance-reports/agent-runs/*.md      本轮**运行链** mermaid
#     .acceptance-reports/agent-graphs/*.mmd   三张图的**静态拓扑**（也可单独跑 §4-F 里的 dump 脚本）
```

②③④⑤⑥ 都是**起服务/起桩 → 跑 → 收尾杀进程**，跑完不留后台进程。
③④⑤ 需要 jar，前两步（`mvn -B clean package -DskipTests`）在 §3.3。

**⑦ 的正确读法**：输出是 `2 failed, 1013 passed, 1 skipped` 就算过——那 2 条是
`tests/test_chat_ws.py` 的既有偶发，与本次无关（§4-附加 有说明）。
因为 pytest 有失败就返回非零，**别拿退出码当这一级的判据**。

**跑完顺手确认没有残留服务**（有残留会让下一次跑撞上端口前置检查）：

```bash
for p in 8123 18080 18081; do
  printf "%-6s " "$p"
  lsof -nP -iTCP:$p -sTCP:LISTEN >/dev/null 2>&1 && echo "占用" || echo "空闲"
done
```

---

## 6 · 回滚与不可逆点（本地）

- 代码：`git status` 看改动；未合并的分支直接切走即可。
- 依赖：`git checkout <升级前 commit> -- pyproject.toml requirements.txt uv.lock` 后重装。
- DB：迁移是**纯增量**的，`alembic downgrade 20260919_capability_receipts` 可退回（会 drop 表）。
- ⚠️ **checkpoint 不可回滚**：langgraph 0.2 挂起的 checkpoint，1.2 **读得回 values 和
  pending task，但 `task.interrupts` 是空的**；硬喂 `Command(resume=…)` 会在 pregel 内部炸
  `TypeError: 'Interrupt' object is not subscriptable`。反向（新栈写、旧栈读）**未实测**。
  ⇒ 升级窗口内先冻结新的挂起、排空存量再升；`hitl_drain_audit.py` 就是干这个的。

---

## 7 · 已知缺口 / 不在本文范围

1. **生产容器透传**不在本文。已在 `ops-desk-workspace/deploy/` 补过一轮
   （`docker-compose.prod.yml` + `deploy/.env.example` **成对**加键），那属于生产范围。
2. **langfuse × langchain-core 1.x 只验到"不报错"**，没做 trace 内容比对。要看 trace 就
   `OPS_ACCEPTANCE_TRACING=1` 单独跑一次，并人工比对 Langfuse 里的结构。
3. **"走运行中的服务"调 OA 能力没有端点**（没有 invoke 端点），所以 §4-C 的脚本是
   **进程内**调 gateway；要经服务走完整链路得等 supervisor 图跑起来（需要真 LLM）。
   ⇒ 因此脚本里显式设了 `OPS_CAPABILITY_EXTRA_MANIFESTS` / `OA_BASE` /
   `OPS_CAP_CRED_OA_GATEWAY_TOKEN`，让它不依赖 `.env` 当前写的是什么。
4. **supervisor 图的深度**只到"能挂起 + 能恢复"，没覆盖"恢复后又挂起"的真实多轮场景
   （只在单元层测了 `re_interrupted` 标志）。
5. 测试**不该读 `.env`**：凡是"只在生产开"的开关，测试要么显式关、要么显式开。
   已给三个 SSE 测试模块加了 autouse fixture 显式关掉 `LG_RAG_HTTP_CHECKPOINTER`
   （否则 `.env` 一开，测试就会真连库开 saver，对照断言还会被环境悄悄翻掉）。
6. **"能力通不通"的检查不能只看 `ok`**：凡是在清单里声明了降级的能力，下游不可达时
   也会返回 `ok=True`（内容变成兜底）。必须同时看 `degraded` 标记。
   §4-C 与 §0 的 B 线都按这条写。**推论**：任何"绿灯"型检查都要先问一句
   "它在坏的情况下会不会也亮绿灯"。

## 8 · 待核实

| 项 | 核实方式 |
|---|---|
| 新栈写的 checkpoint 旧栈能否读（回滚可行性） | 用 0.2.76 的栈去 `aget_state` 一个 1.2.11 种下的挂起 thread |
