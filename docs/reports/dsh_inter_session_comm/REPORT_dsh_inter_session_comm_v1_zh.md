# REPORT · DSH 跨会话通信机制研究报告

> **版本**：v1 · **日期**：2026-10-16 · **性质**：研究报告（非 SPEC · 非 task · 不落实现码）
> **发起**：维护者直接变更请求（2026-10-16 会话）
> **定位**：为 ops-desk 项目未来的多会话/多 Agent 协作与鉴权设计储备方案参照。
> **明确非范围**：本地 DSH 研发工作流**不接入**（不起 relay 守护进程、不改 harness 文件总线惯例、不动 DSH 源码）。

---

## 0. 摘要

本报告勘察 DeepSeek Harness（DSH）web server 的浏览器认证子系统（`browser-auth`）与程序化接口面，评估「以同类方案实现 session 间通信」的可行性，并提炼可移植到 ops-desk 项目的设计启示。

核心结论：

1. DSH 认证是**三层凭证**（持久签名 secret → 每进程 launch token → HMAC 签名 cookie），无状态验签、无吊销面，工程细节扎实，值得作为参考实现精读；
2. DSH session 间**无原生 agent-to-agent 消息**；程序化面是内部 RPC（HTTP 一元调用 + `/api/remote.mux` WebSocket 流），非承诺稳定的公开 API；
3. 「cookie + relay 守护进程」方案技术可行，但凭证全权、无送达保证、注入纪律三大风险使其**不适合**当前 harness 研发流；其设计要素（信封、幂等、轮次冲突、事件流订阅）对 **ops-desk 自身产品**的多会话协作设计有直接参考价值。

---

## 1. 背景与目的

- **直接背景**：hitl-resume-async 跨仓闭环中，api/web 两侧 00 的协作走「invoke md 文件总线 + 维护者人中继」，维护者提出是否存在进程间沟通方案；
- **本报告回答**：
  1. DSH web 认证机制（token/cookie）的完整设计是什么；
  2. DSH session 间能否、以及如何程序化通信；
  3. 同类方案（令牌换凭证 + 消息中继）应用到 ops-desk 项目设计的价值与取舍；
- **资料来源**：DSH 源码（`/Users/cyning/Desktop/deepseek-harness/` 工作副本，2026-10-15/16 精读）+ 本仓实证（curl 401、gh API、SSH/代理网络诊断）。

---

## 2. DSH browser-auth 机制勘察

> 主文件：`packages/client/connection/src/browser-auth.ts`（394 行 · 单类 `BrowserAuth`）。行号为勘察时快照。

### 2.1 威胁模型与设计目标

本地 web server 暴露 **Agent 全权**（投消息 = 任意操作），但不做登录 UI。目标：

- 一次性令牌换持久凭证；
- token 不落地（不进浏览器历史 / 地址栏 / referrer）；
- cookie 绑定 authority（防 localhost 端口跳跃重放、防 HTTP/HTTPS 跨协议重放）；
- 全程时序安全比较（timingSafeEqual）；
- 签名密钥持久化，cookie 跨服务重启存活；
- 非 loopback 绑定须显式申报（trustedHosts 围栏）。

### 2.2 三层凭证

| 层 | 内容 | 生命周期 | 存储 | 证据 |
|---|---|---|---|---|
| 签名 secret | 32 字节随机 base64url | **持久**（每 Harness home 一份） | credentials 记录 `client-connection/browser-session`（grant 类） | `initializeSecret` browser-auth.ts:182-199 · 格式校验 fail-closed :97-108 |
| launch token | 32 字节随机 base64url | **每进程**（WeakMap 挂 process owner · 插件重载存活 · 进程死即焚） | 仅内存 | browser-auth.ts:22 · :61-67 |
| 签名 cookie | `v{1\|2}.{base64url(body)}.{base64url(HMAC-SHA256(secret, body))}` | 默认 30 天（Max-Age + Expires 双写） | 浏览器/客户端 | 编码 :146-149 · 属性 :131-140 |

token 语义实证：**每进程有效 · 非一次性**——进程存活期间同一 token 可反复换 cookie；重启即焚换新。启动时 `packages/bundle/web-app/src/index.ts:231` 必打印 `dsh web: <url>?token=...`（`printUrl` 默认 true，与 `--no-open` 无关）。

### 2.3 双版本 cookie（浏览器与 API operator 严格分流）

- **v1 浏览器会话**：payload `{version:1, authority, issuedAt, expiresAt}`；
- **v2 API operator**：多 `id: PeerId`（:36-39），由 `/connect` 换发；
- `isAuthenticated` 只认 v1、`authenticateApi` 只认 v2（:356-369）——**浏览器凭证不能当 API 凭证，反之亦然**，权限面刻意隔离；
- cookie 名按 authority 哈希：`dsh-auth-<base64url(sha256(authority))>`（:116-118），不同 host:port 互不覆盖。

### 2.4 三条流程

1. **index 换发**（`authorizeIndex` :263-305）：`GET /?token=…`（恰好一个 token · timingSafeEqual :110-114 · authority 可解析）→ 铸 v1 → **303 跳净 URL `./`**（`cache-control: no-store` + `referrer-policy: no-referrer`）。**303 不建浏览器历史条目**——token 三轴防泄（历史/地址栏/referrer）。已持有效 cookie 直接放行；否则 401，响应体：`dsh web authentication required; reopen the URL printed by dsh web.`（:385-393）；
2. **connect 换发**（`authorizeConnect` :314-348）：`GET /connect?token=…&interactions=answer|none`（声明超一次或非法 → 400）→ `publish()` 建独立 API operator（PeerId）→ 铸 v2 → **302 到 `./api/remote.mux`**。README 明示：「Only API callers use GET /connect」（`packages/client/connection/README.md:51`）；
3. **验票**（`authenticate` :371-383）：Host 头重算 authority（http 用 `host`、https 用 `origin` —— cookie 不可跨协议，:79-88 · README:45）→ 精确名取 cookie → HMAC 时序安全验签 → authority 相等 → 时间窗四项（未过期 · 非未来签发 · expiresAt>issuedAt · 寿命 ≤ maxAge 防篡改）。

准入前置：`packages/client/connection/src/index.ts:150-158` 对 `/api` 前缀先 `admit(req)`，401 `unauthorized` / 403 `forbidden` 分流；此前 curl 实证吃到的正是小写 `unauthorized`。

### 2.5 关键工程细节（可移植清单）

| 细节 | 价值 | 证据 |
|---|---|---|
| 303 换发 + no-referrer | token 不落历史/地址栏/referrer | :263-305 |
| 无状态验签 | 免查库 · 重启不刷凭证 | :371-383 |
| 无吊销列表 | 取舍：多把 cookie 并存有效，泄露只能靠 secret 轮换 | 设计推断 |
| SameSite=Strict + HttpOnly + Path=/ + Secure(仅 TLS) | CSRF/XSS 面收敛 | :131-140 |
| 严格 base64url 编解码（拒绝非规范编码 · 重编码比对） | 杜绝另类编码绕过验签 | :54-59 |
| maxAge `Number.isSafeInteger` 双检 fail-closed | 溢出防呆 | :217-220 |
| authority 绑定 + cookie 名哈希 | 防端口跳跃/跨协议重放 | :79-88 · :116-127 |
| trustedHosts 围栏 + HTTP 明文监听 warn | 非 loopback 暴露须显式申报 | web-app/src/index.ts:198 |
| 401 响应体指引用户找回 token（stdout 启动行） | 运维体验 | :385-393 |

---

## 3. DSH 程序化接口面

> **更正**：调研早期曾误判存在字面 REST 路由 `/api/session.prompt` / `/api/session.list`——实为 http-bridge 测试夹具 URL 与 ACP 方法名，**不是 HTTP 端点**。真实面如下。

- **Typert Remote RPC 层**：浏览器一元调用走 HTTP POST；**`/api/remote.mux` 是 API Gateway 拥有的 WebSocket**（`packages/api/gateway/src/stream-protocol.ts:7` `REMOTE_STREAM_MUX_PATH` · `packages/client/connection/README.md:34`）；
- **事件流**：mux 上逻辑端点 `$events`（订阅 Host 事件 · stream-protocol.ts:10）与 `$events/result`（事件结果回传 :13）——**推送式，无需轮询**；连接有 generation 语义，流终结/错误即失效重连（README:56-64）；
- **Peer 模型**：每请求代言一个 Peer（`PeerScope.principal` 命名调用方 · `interactions` 决定事件参与，README:49）；无方法级 ACL——**凭证即全权**；
- **会话引用 mention（半官方跨会话机制）**：ui-reference 包支持人在输入框插入 `@[label](dsh-session:…)` 原子引用随 prompt 发送，接收方 session-reference 服务解析——**人发起**的跨会话引用，非 agent 间消息；
- **headless 侧路**：`dsh headless --session-id` 可认领既有持久化 Session 续跑（同机 CLI 路径，不走 HTTP 认证）。

---

## 4. 会话间通信：现状与缺口

- DSH session 按工作区归属、上下文隔离，**无原生 session-to-session 消息原语**；
- 现行协作惯例：**invoke md 文件总线**（发方落盘 → 维护者人中继 → 收方读取回执），git 留痕、零凭证面、强制人在环，代价是手动、分钟级延迟；
- 缺口仅在**高频自动化编排**场景（watchdog 催办、多 session 流水线）才会真正显现。

## 5. relay 守护进程方案（参考架构 · 不在本地 DSH 落地）

### 5.1 架构

```
session A ──$events 流──▶ relay daemon（持 v2 operator cookie）──unary prompt RPC──▶ session B
                            │
                            ├─ 信封封装：【relay from <工作区>/<帽> · msg-id · 时间戳】
                            ├─ 幂等表：msg-id 去重 · ack 约定
                            ├─ 轮次仲裁：目标 mid-turn 时排队不插队
                            └─ 审计日志：全量转发记录落盘
```

### 5.2 优缺点

| 优点 | 缺点/风险 |
|---|---|
| 不改 DSH，全走支持的认证路径 | **凭证全权**：Peer 无方法级 ACL，daemon 成高价值靶子；泄露 = 全部 session 全控 |
| 一 server 全覆盖（跨工作区/跨 session） | **无送达保证**：排序/去重/ack 需自建 |
| mux 事件流推送，低延迟免轮询 | **注入纪律风险**：注入消息以「用户消息」面目出现，收方会把用户消息当维护者指令 → 冒名/带偏风险 |
| 可编程：触发器、扇出、重试、审计 | 协议面为内部 RPC，**非稳定公开 API**，升级漂移风险 |

### 5.3 若真要做的最小纪律

cookie 文件 0600 · 严格信封格式（来源/msg-id/时间戳）· mid-turn 排队 · relay 操作全量落审计日志 · secret 轮换预案（token 泄露即重启换发）。

### 5.4 运维教训（本调研实测）

- token 粘贴进聊天记录 = 泄露（本次调研中实测发生一次，以重启烧掉处置）——**令牌不进 transcript** 应成纪律；
- SSH 远端（`git@github.com`）不吃 http 代理且本机 22 端口挂起，`gh` CLI（HTTPS API 走代理）是可靠替代通道。

---

## 6. 对 ops-desk 项目的设计启示（本报告落点）

ops-desk-api（FastAPI + LangGraph + SSE Chat · DB session 鉴权 · `ops_users`/`ops_sessions`/`ops_invite_tokens` 三表）与 DSH 同为「Agent 全权后端」，其认证与协作设计可直接对照：

### 6.1 邀请/授权链路：一次性 token 换持久凭证

- DSH：launch token（每进程 · 可反复换发）→ cookie。ops-desk 现有 `ops_invite_tokens` 是同构场景；
- **启示**：换发后应**即焚**（DSH 因单机可信容忍反复换发，多用户 SaaS 不应）；换发响应参照 303 + no-referrer，token 不进 URL 历史；邀请链接泄露面按「token 三轴防泄」清单自查。

### 6.2 会话凭证选型：DB session vs 无状态 HMAC

| | DB session（ops-desk 现状） | 无状态 HMAC cookie（DSH） |
|---|---|---|
| 吊销 | **即时**（删行） | 无（靠过期/换 secret） |
| 每请求成本 | 查库一次 | 纯计算 |
| 多副本 | 天然一致 | 共享 secret 即可 |
| 续期 | 滑窗更新 | 重新铸签 |

- **启示**：面向多副本部署（本仓已有 `multi-replica-verify` 方向），可评估**混合方案**——短期无状态 access cookie（分钟级 · 免查库）+ 长期可吊销 refresh 记录（DB），即主流 access/refresh 双令牌；DSH 的时间窗四项校验（:371-383）可直接抄作 access 校验清单。

### 6.3 authority/audience 绑定

- DSH cookie 绑定 authority 且 HTTP/HTTPS 分流，防跨环境重放；
- **启示**：ops-desk 的 session/JWT 类凭证应嵌入 audience（环境/域名），dev/staging/prod 凭证互不通用；cookie 名可同法哈希隔离。

### 6.4 事件推送：SSE → 可订阅事件总线

- DSH `$events` mux 流（WS · generation 失效重连语义）对照 ops-desk 现行 SSE（`graph.astream_events` + `StreamingResponse`）；
- **启示**：当事件类型从「chat 帧」扩展到「审批/HITL/任务状态」多类时，可借鉴 mux 的逻辑流复用（单连接多逻辑流）与 generation 失效语义；HITL 场景 hitl.resumed/候批超时等事件已有订阅价值（参 hitl-resume-async 回执 TC3/TC4 帧序列）。

### 6.5 多会话/多 Agent 协作（远期）

若 ops-desk 产品侧未来支持「会话间委派/接力」（如值班 Agent 间移交工单）：

- **信封纪律**：来源标识 + msg-id + 时间戳，收方按来源分级信任（防冒名是首要威胁，参 §5.2）；
- **幂等与 ack**：msg-id 去重 + 回执闭环（现行 invoke 文件总线的「回执」惯例即是原型）；
- **轮次仲裁**：目标执行中时排队而非插队（mid-turn 注入冲突）；
- **人在环闸**：高危转发强制人审——harness 人工闸（HG-*）思想可产品化。

### 6.6 可直接抄用的安全工程清单

§2.5 全表 +：严格编码防验签绕过 · fail-closed 参数校验 · 明文监听显式 warn · 401 响应体附自助指引。

---

## 7. 结论与后续

1. DSH browser-auth 是一套**值得精读的单机 Agent 认证参考实现**；其「一次性 token 换 cookie · 无状态验签 · authority 绑定 · 三轴防泄」四件套可移植；
2. DSH session 间通信**现状无原生支持**；relay 方案可行但风险/收益不匹配本地研发流——**本地 DSH 不接入，维持文件总线**（维护者已裁定）；
3. 方案价值沉淀到 **ops-desk 产品设计**：§6 六条启示分别对应邀请链路、凭证选型、audience 绑定、事件总线、多 Agent 协作、安全清单；
4. **后续建议**：§6 任一条目若要立项，按 harness 纪律走 10-spec 起草 SPEC（本报告可作背景引用）；本报告不含实现码，无需 verify。

---

## 8. 参考

### DSH 源码（勘察快照 2026-10-15/16）

| 文件 | 内容 |
|---|---|
| `packages/client/connection/src/browser-auth.ts` | 认证全实现（394 行 · 行号见正文） |
| `packages/client/connection/src/index.ts:150-158` | admit 准入 401/403 |
| `packages/client/connection/README.md` | 认证与信任模型（:34 · :41-51 · :56-64） |
| `packages/api/gateway/src/stream-protocol.ts` | `/api/remote.mux` · `$events` 常量 |
| `packages/bundle/web-app/src/index.ts:231` | 启动打印 authenticatedUrl |
| `packages/client/ui-reference/README` | 会话引用 mention 机制 |

### 本仓相关

- `ops_users` / `ops_sessions` / `ops_invite_tokens` 三表（`app/db/`）· SSE Chat（`app/ops/chat/`）
- hitl-resume-async 闭环档：`docs/tasks/close/close_hitl_resume_async_20261015.md`（JC-F1 跨仓协作 · 文件总线实证）
- SPEC 方向参照：`docs/spec/multi-replica-verify/`、`docs/spec/hitl-approval-consumption/`
