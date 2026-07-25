# Task Audit R1：deploy-prod

> **hat_id**：20-task-audit（22）  
> **task**：`docs/tasks/active/task_deploy_prod.md`  
> **日期**：2026-07-25 · 审查人：00 统筹（兼 22 帽）

## 结论摘要

| 维度 | 结论 |
|---|---|
| **内容** | 零阻塞：范围明确（WS 开关 + 部署产物 + 服务器执行）；决策均已拍板（单域名路径分流 / WS 生产禁用 / 控制台证书 / 本地 build+rsync / 服务器跑数据导入 / v1 手动部署） |
| **流程闸** | HG-AUDIT-R1 = approved（用户 2026-07-25 签）；HG-GRAPH-MODULES = approved（chat 加开关，部署产物不入 graph） |

## 核对项

- [x] 验收标准可执行：WS 开关单测（机器）+ HTTPS E2E checklist（人工，含登录/数据页/Chat SSE）
- [x] 失败路径覆盖：SSH 不通 / 证书缺失（configtest 不 reload）/ 容器健康检查失败 / 迁移失败 / 导入失败降级
- [x] 真值来源清晰：`deploy-info.local.md`（gitignored）§1–§3 已就绪（IP/SSH/域名/DNS/SSL 方式）
- [x] 安全风险已识别：未鉴权 WS 端点生产禁用（OPS_CHAT_WS_ENABLED=false，验收含 wss 不可达）；生产密钥不入库；API/PG 端口不对外
- [x] 跨仓边界写明：ops-desk-api（代码）+ ops-desk-workspace（deploy/ 产物）+ 服务器执行
- [x] 回滚可行性：compose down + 旧 dist 保留（deploy.sh 带备份步骤）；v1 无流量切换需求

## 风险备注（不阻塞）

- SSL 证书文件需用户执行中提供（腾讯云控制台下载），已在 task 标注。
- 服务器为生产唯一实例，部署期间短暂停机（v1 可接受，无灰度）。

## 签收

本轮为终轮，**签收 / 关闭**。
