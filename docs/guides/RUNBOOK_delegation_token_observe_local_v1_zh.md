# RUNBOOK · 委派令牌闸本地观察（observe）checklist（v1 · 2026-09-24）

> **范围**：D2 六闸灰度第一闸 · `LG_RAG_DELEGATION_TOKEN_MODE=observe` 本地 docker 全流流程  
> **真值锚点**：`app/ops/capability/gateway.py:287-323`（三档闸）· `app/ops/capability/delegation.py:41-149`（env 键/mode/台账）· SPEC `docs/spec/host-v1-wrap-up/SPEC-host-v1-wrap-up_v0.md` §2 D2（报告格式钉死）  
> **维护者令（原话留痕）**：「仓内改动也可以吧，LG_RAG_DELEGATION_TOKEN_SECRET本地如何生成？落盘一份完成的本地checklist」（2026-09-24 · 00 代录）  
> **铁律**：默认关（不设 env = off 零 diff）· 密钥禁入库 · 记动作不记内容 · 宁停勿闯（误判口径不明则维持 observe）

---

## §0 速览（TL;DR）

```bash
# 1. 生成密钥（不入库）
openssl rand -hex 32
# 2. 写进本地 .env（gitignored）
cat >> .env <<'EOF'
LG_RAG_DELEGATION_TOKEN_MODE=observe
LG_RAG_DELEGATION_TOKEN_SECRET=<上一步生成的 hex>
EOF
# 3. 起栈（observe override：放开 INFO 台账 · 仓内文件 · 勿用 /tmp 临时文件——会被系统清理致启动失败）
docker compose -f docker-compose.yml -f docker-compose.observe.yml up -d --build api
# 4. 冒烟：触发一次带工具调用的 chat，确认台账行出现
docker compose logs -f api | grep 'delegation token_'
# 5. 观察期结束 → 聚合 → 填报告（§6/§7）
```

---

## §1 前置检查

- [ ] 分支/代码 = master 最新（V1-A 闸码已在仓 · 本棒 compose 透传已合入）
- [ ] `docker compose config` 渲染结果含三键（`LG_RAG_DELEGATION_TOKEN_MODE/SECRET/TTL_SECONDS`）
- [ ] db / qdrant 健康（`docker compose ps`）· api 就绪（`curl localhost:8000/health` 或既有就绪面）
- [ ] 本地无 Langfuse 亦可——**单通道（日志）是合法形态**，报告里如实标注「无 span 对拍」

## §2 SECRET 本地生成

```bash
openssl rand -hex 32                                    # 推荐
python3 -c "import secrets; print(secrets.token_hex(32))"  # 等价备选
```

| 纪律 | 说明 |
|---|---|
| 禁入库 | 值只写本地 `.env`（gitignored）· 仓内任何文件（含本 RUNBOOK / compose / .env.example）**只写命令不写值** |
| 轮换=重启 | `_kid_of` 单密钥派生（`delegation.py:119-121`）· 换密钥即重启 api · 多密钥并存属 v2.0 |
| observe 也必须配 | **不配 SECRET 则所有事件全是 `secret_missing`**，观察无意义（验签门：`verify_token` 首查密钥） |
| 本地值无强度要求外的讲究 | 随机 32 字节即可；本地不与任何外部环境共用 |

## §3 env 注入（三选一 · 推荐 A）

| 方案 | 做法 | 取舍 |
|---|---|---|
| **A · `.env`（推荐）** | `.env` 追加 `LG_RAG_DELEGATION_TOKEN_MODE=observe` + `LG_RAG_DELEGATION_TOKEN_SECRET=<hex>` → `docker compose up -d --build api` | compose 透传已仓内置备（默认 off）· `.env` gitignored · 最简 |
| B · shell export | `export LG_RAG_DELEGATION_TOKEN_MODE=observe LG_RAG_DELEGATION_TOKEN_SECRET=<hex>` 后同 A 起栈 | 不落盘 · 关 shell 即失效 |
| C · 仓内 observe override（**推荐配合 A**） | `docker compose -f docker-compose.yml -f docker-compose.observe.yml up -d --build api` | 换启动命令放开 INFO 台账（uvicorn 默认 root=WARNING 会吞 `delegation token_` 审计行 · 见 §10）· **勿放 /tmp**（系统清理后挂载源消失 → 容器 exit 127 起不来 · 2026-09-30 实战） |

> 注意：compose api 服务是**显式 environment 白名单**（无 `env_file:`）——本棒已把三键加进白名单（默认 `off`/空/600），在此之前的 checkout 上 `.env` 写了也进不了容器。

## §4 起栈与冒烟（**「闸真活了」断言 · 不可省**）

- [ ] `docker compose -f docker-compose.yml -f docker-compose.observe.yml up -d --build api`（compose 启动自动 `alembic upgrade head` · observe override 放开 INFO 台账）
- [ ] 触发一次**会走 capability 网关的工具调用 chat**——冒烟查询用**工具类问题**（如「调用工具查一下当前的部署信息」→ `mock_get_deploy_info`）；**纯知识库检索类问题走 rag 链路不过委派闸，零台账**（2026-09-29 实战 · 注入点 `multi/nodes.py:1230-1236` 仅在 `tool_exec` 工人路径）
- [ ] **断言台账行出现**：`docker compose logs api | grep 'delegation token_'` 能见到 `token_issued` / `token_verified`（合法调用）
  - 看不到 → §10 故障排查（先查 env 是否真进容器：`docker compose exec api printenv LG_RAG_DELEGATION_TOKEN_MODE`）
- [ ] 记录冒烟时间 = 观察期起点

## §5 观察期（真实流量 + 合成演练补覆盖面）

**诚实口径**：纯 RAG 用量下能力集窄、部分拒绝分类自然命中可能为零——这不阻塞观察，但报告§覆盖面声明必须如实写；覆盖面用**合成演练**补。

| # | 场景 | 预期台账 | 触发手法 |
|---|---|---|---|
| S1 | 合法委派（基线） | `token_issued` → `token_verified` | 正常 chat 触发工具调用（检索/查询） |
| S2 | 无令牌 | `token_rejected:no_token` + `would_block=true` | 令牌未签发路径（requested_scope 空集等 · 自然流量可能出现；白盒构造见下） |
| S3 | 篡改令牌 | `token_rejected:signature_invalid` | 白盒：改签名字段后走闸（一次性脚本调 gateway 验签路径） |
| S4 | 缺密钥 | `token_rejected:secret_missing` | 临时去掉 SECRET 重启打一发（**打完即恢复** · 仅演练用） |
| S5 | 越能力集 | `token_rejected:out_of_set` | 白盒：签发 scope 不含目标 capability 后调用 |
| S6 | 过期 | `token_rejected:expired` | 白盒：`LG_RAG_DELEGATION_TOKEN_TTL_SECONDS=1` 起栈 · 挂起/延迟后调用 |
| S7 | nonce 重用 | `token_rejected:nonce_reused` | 白盒：同一令牌序列化体重放两次 |
| S8 | 参数越约束 | `token_rejected:param_violation` | 白盒：参数超签发约束（enum/max_len/pattern） |
| S9 | 主体不符 | `token_rejected:subject_mismatch` | 白盒：换 user/tenant 上下文重放 |

> 白盒脚本（一次性 · 不入库或入 `scripts/acceptance/` 另棒裁定）：直接驱动签发/验签路径构造场景；仓内测试 `tests/test_capability_delegation.py` / `tests/test_lg_rag_delegation_wiring.py` 是现成场景蓝本。**只断台账行出现与分类正确，不改被验证对象。**

## §6 数据捞取与聚合（观察期结束）

```bash
# 全量台账导出
docker compose logs --since <观察期起点> api | grep 'delegation token_' > /tmp/delegation_observe.log
# 按动作/拒绝分类计数（示例 · jq 可按环境调整）
grep -o 'delegation token_[a-z_]*\(:[a-z_]*\)\?' /tmp/delegation_observe.log | sort | uniq -c | sort -rn
# would_block 事件（observe 关键面）
grep 'token_rejected' /tmp/delegation_observe.log | grep '"would_block":true' > /tmp/would_block.log
```

- [ ] 计数表：每类 `token_rejected:<class>` 计数 + `token_verified` 计数
- [ ] **误判抽样 ≤10 条**（记动作不记内容）：逐条判「按现行语义本应放行却被记 would_block」= 误判；全真阳性 → 零误判
- [ ] （可选）Langfuse 已配环境：span metadata `delegation_would_block=true` 对拍计数

## §7 报告落盘

复制模板 `reports/gate_observe/_TEMPLATE_delegation_token.yaml` → `reports/gate_observe/delegation_token_<yyyymmdd_period>.yaml`，逐字段填实（字段族由 SPEC §2 D2 钉死）：gate · mode · period · would_block 计数与分类 · 误判抽样（≤10）· 结论建议（维持 observe / 可 enforce / 需修）· recorded_at。**单通道如实标注。**

## §8 结论与 enforce 前置（SPEC 锁死）

- [ ] 结论三选一：维持 observe（默认）/ 可 enforce / 需修（发现闸或签发链路问题 → 另开 fix task · 不顺手修）
- [ ] enforce 前置两件：**would_block 零误判报告** + **`LG_RAG_DELEGATION_TOKEN_SECRET` 已配置**——缺一不开
- [ ] 宁停勿闯：误判率无可接受口径 → 维持 observe 并如实写原因

## §9 复位

```bash
# 摘 env（或改 off）后重启
sed -i '' '/LG_RAG_DELEGATION_TOKEN/d' .env   # macOS；Linux 去 ''
docker compose up -d api
# 断言复位：日志不再出现 delegation token_ 新行（off 短路 · gateway.py:291）
```

## §10 故障排查

| 症状 | 先查 |
|---|---|
| 日志零 `delegation token_` 行 | ① `docker compose exec api printenv LG_RAG_DELEGATION_TOKEN_MODE`（env 没进容器 = checkout 早于透传 PR）② 触发的是否真·委派链路（纯对话无工具调用不出台账） |
| 全是 `secret_missing` | SECRET 没配/没进容器（§2 · 同 printenv 查） |
| 全是 `no_token` | 签发侧未发令牌（requested_scope 空/签发闸未过）——如实记，属观察发现不是故障 |
| 日志行有但 grep 聚合为空 | 时间窗 `--since` 起算点写错 · 或日志被 json 转义（调整 grep 模式） |
| 登录/请求 500 且 traceback 路径是 `.venv/`（宿主机） | **host 侧旧 uvicorn 抢 `127.0.0.1:8000`** 阴影 docker api（宿主占用优先于 docker 通配绑定）· `lsof -nP -iTCP:8000 -sTCP:LISTEN` 找出杀掉；同坑：Homebrew PG 占 `127.0.0.1:5432` 阴影 docker db（host 脚本连空库）→ db 脚本一律 `docker compose exec api python ...` 容器内跑 |
| 容器里零 `delegation token_` 行但 env 是对的 | **uvicorn 默认 root=WARNING 吞掉 app INFO 台账** → 必须用 `-f docker-compose.observe.yml` 起栈（`scripts/serve_observe.py` 放开 INFO） |
| 冒烟时零台账（纯 RAG 问题） | 检索走 rag 链路不经委派闸 → 换工具类查询（注册能力见 `GET /api/ops/admin/capability/catalog`） |
| api 容器 exit 127 起不来 | override 挂载源被 /tmp 清理 → **override 用仓内 `docker-compose.observe.yml`**（勿 /tmp）· 若已坏：`rm -rf /tmp/serve_observe.py` 残留目录后重建 |
| run 工具调完无终答 | 多半是 **HITL 挂起**（`done{status:waiting_approval}`）非失败：查 `ops_lg_rag_run_events` 末帧；批准=签名 callback（`OPS_HITL_CALLBACK_SECRET` 本地算 HMAC）+ `POST /api/ops/hitl/requests/<id>/resume`（cookie maintainer 可过）；**观察期建议 `.env` 补 `OPS_HITL_PERSISTENCE=db`**（默认 null 进程内 store · api 重启丢挂起申请） |

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 初版：本地 observe 全流 checklist（§0-§10）· 维护者令原话留痕见头部 · 00 代录 |
| 2026-09-30 | 实战补丁：override 收编仓内（`docker-compose.observe.yml` + `scripts/serve_observe.py` · /tmp 方案被系统清理致 exit 127）· §4 冒烟改工具类查询 · §10 补五坑（8000/5432 宿主抢占 · WARNING 吞台账 · 纯 RAG 零触发 · /tmp 清理 · HITL 挂起批准链）· 00 代录 |