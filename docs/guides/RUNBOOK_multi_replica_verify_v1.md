# RUNBOOK · 多副本验证实测轨（multi-replica-verify D1/D4 · v1）

> **任务**：task multi-replica-verify（track=verify · F1 双轨之 runbook+实测报告轨）
> **前置**：dev compose 的 db 容器在跑（ops-desk-api-db-1）· 本机镜像 ops-desk-api-api:latest · docker 可用
> **产物**：reports/multi_replica_verify/deploy_<ts>.yaml（字段族：拓扑 · 网关形态 · 逐项 PASS/FAIL · 命令 · git sha · 镜像 ID · recorded_at · 清理数）

## 一句话

双进程 pytest 轨（tests/test_multi_replica_dualproc.py）证**语义**（可 CI 可回归）；
本 runbook 轨证**部署拓扑下成立**（2 容器 + 前置 LB · 亲和对照 · 报告留痕）。

## 跑法

```bash
./scripts/acceptance/multi_replica_verify.sh
```

编排序：专用库 opsdesk_mrv drop 重建 → alembic upgrade head → compose 双实例
（api-a:8101 / api-b:8102 · 共享 opsdesk_mrv · 镜像 digest 一致断言在驱动里）→
降级 LB 两组（rr:8199 · cookie-sticky:8200）→ 驱动断言 → 报告落盘 → 收尾
（compose down + drop 库 + 杀 LB）。全程约 1–3 分钟（容器启动大头）。

## 网关形态（诚实标注 · 不得改写）

- **首选形态未覆盖**：外部 Java 网关（ops-desk-api-java-gateway）+ Eureka
  （ops-desk-eureka-server）在外部仓，且本仓 FastAPI 无 Eureka 客户端 ——
  「Eureka 注册 2 实例」条目在报告中标 **未覆盖待补**。
- **SPEC 命名的降级形态不可得**：compose 内置 nginx/haproxy —— 本机 docker registry
  拉取受限（2026-09-22 实测 docker pull nginx/haproxy 均失败），仓内零镜像。
- **实际形态（再降级）**：宿主机自研 Python LB（scripts/acceptance/multi_replica_lb.py），
  round-robin（无亲和对照）+ cookie-sticky（会话亲和对照 · 自研 LB 支持面）双组。
  报告 gateway_form 字段同源如实写。**读报告时不得把降级形态当作「网关验证通过」。**

## 断言面（驱动 multi_replica_verify.py）

| 组 | 断言 |
|----|------|
| 拓扑 | 两实例 /health ok · whoami pid 相异 · env 对拍一致（LG_RAG_HTTP_CHECKPOINTER=postgres · OPS_HITL_PERSISTENCE=db · OPS_CAPABILITY_PERSISTENCE=db） |
| 登录态 | LB 登录拿 cookie → 直打 A 与 B /auth/me 均 200 同用户（ops_sessions DB 存 · 无需会话亲和） |
| thread 历史 | A 起 thread → B 同 thread_id 续跑不 404 · A 的 run B replay 逐帧一致 |
| 无亲和 | rr LB 同 cookie ×6 → X-MR-Upstream 两实例均有命中 · 6/6 语义一致 |
| 会话亲和 | cookie-sticky LB 同 cookie ×6 → 全部落同实例 |
| D4 | A 挂起 → B 见申请（签名拉待办）→ B 批准（签名回调）→ B resume 图真的续跑（state 推进 + answer 非空）→ A replay 全程：hitl.resumed + done(resumed) 续写同 run_id seq 连续 |
| 混合负载 | 无亲和组命中计数即混合负载证据（两实例均有命中 = LB 没只打到一个） |

## 替身声明（与 pytest 轨同一 seam）

容器内跑 tests/dualproc_server.py：确定性替身图替换 supervisor 图入口与 HITL 图工厂
（真 LLM 触发 prefix_touch_required 非确定性，不适合断言）；**状态外置链路全真**
（PG checkpointer / 事件表 / DbHitlStore / resume 驱动 / 配额计数）。app/ 以只读
bind-mount 挂当前工作区代码（镜像只提供依赖层）——验证对象 = 当前分支代码。

## 验证卫生

专用库 opsdesk_mrv（不碰共享开发库 opsdesk）· 用户/会话/thread 统一 mr<hex>- 前缀 ·
驱动收尾清库报清理数 · .sh 收尾 drop 库 + compose down · 报告不含真实用户数据/凭证。

## 复跑纪律（残余风险 ④ 承 SPEC §7）

runbook 轨结论随时间贬值（checkpointer/resume/事件表语义漂移时双进程 pytest 在 CI
兜核心语义，本轨须复跑）；镜像重建后须复核 digest 断言与依赖层一致性。
