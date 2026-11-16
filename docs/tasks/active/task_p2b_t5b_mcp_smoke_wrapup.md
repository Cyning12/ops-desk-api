---
title: task · chore · P2b-T5b 真社区 MCP server 冒烟 + 文档回写（纯文档波）
---

# task · chore · P2b-T5b 真社区 MCP server 冒烟 + 文档回写

> **状态**：`active`（2026-11-16 落卡 · 夜间自动执行波）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03216 夜间授权 · 设计真源 workspace 11-p2b-mcp-skill-design.md 终稿 §8 T5b 行 + §9.1 三层验收 + §9.3 三级裁定）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p2b-t5b-mcp-smoke-wrapup |
| base | bfbb855c |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | （本波 feat PR · 待回填） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为纯文档冒烟+回写 |
| graph_change_layer | G-L1（01_modules.md HG-GRAPH-MODULES 签收行 · 模块行零改动） |
| review_hat | 20（窄面：纯文档零代码 · R1 审查随 30 交付落盘） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03216（夜间授权）+ 11 设计终稿 §8 T5b 行 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（11 设计终稿即审计真源）· 纯文档零代码窄面过闸 |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（无新一级模块/路由/表/SSE 事件类型 · 本波零代码零模块行改动 · 仅签收行回填，承 :137-:140 先例） |

## 背景

P2b 收官单。T1-T3 已合 MCP 配置面/薄 transport/翻译器（PR #408-#415 全 MERGED），T4 已合 skill 加载器。本单执行 11 终稿 §9.1 MCP 向验收第三层（真社区 server 互操作 · R6）与用户会话判据（R7），并做三级裁定（§9.3）。**纯文档波**：不碰 app/ 一行代码；冒烟全部在仓外 /tmp 配置驱动（总闸 env 开启）。

## 范围

1. **真社区 server 冒烟**：npx stdio 拉 `@modelcontextprotocol/server-everything` v2.3.0；建连/tools/list 翻译/tools/call 全链；负例 server（expected_server.name 故意错）证 identity_mismatch 拒连。
2. **用户会话判据**（真 LLM supervisor · POST /api/ops/lg-rag/stream）：≥3 命中 mcp.*（echo/get_sum/get_env）+ ≥2 不命中；P2a 四样例复跑零误选 mcp.*。
3. **调用边界负例**（直调闸链）：错类型/缺必填 → 稳定码 args_schema_invalid（V1-V13 对真 server fail-visible）。
4. **观测面**：delegation token_verified / catalog 投影 / span metadata 载荷 / shutdown unregister 证据。
5. **文档回写**：01_modules.md HG-GRAPH-MODULES 签收行（本仓）；workspace 侧 04-roadmap:50 裁定 A 表述 + 05-discussion-log R7 追加段 + 09 文 G12-G14 关闭注记与互毒残余风险 + 新建 12-p2b-verification.md（含 env 开启 runbook）+ README 索引（workspace 仓直推 main，不属本仓 PR 面）。
6. **三级裁定出具**：工程判据+用户会话判据 → 成立/部分成立/不成立（R-A1 触发闸）。

## 非范围

- app/ 任何代码改动、测试改动、配置面改动（含 mcp_servers.yaml 仓内化——冒烟配置驻 /tmp）
- skill 面（T4/T5a 域）· MCP SDK 引入（裁定 A 零新依赖）· CI marker 挂接（§9.1 留后续）
- Langfuse 密钥更换（环境层面 · 登记遗留）

## 验收标准

- [x] §9.1 用户会话判据全过：3 命中（echo/get_sum/get_env）+ 4 不命中（P2a 四样例复跑零误选 mcp.*）（证据 /tmp/opsdesk-rfc/p2b-t5b/ + 长日志 /tmp/opsdesk-rfc/p2b-t5b-exec.md）
- [x] 真 server 互操作零失败（建连/list/call/拒载/identity_mismatch 负例/优雅关停）→ 三级裁定=成立（MCP 向），R-A1 不触发，维持裁定 A
- [x] 调用边界负例：错类型/缺必填 → 稳定码 args_schema_invalid（直调闸链 · fail-visible）
- [ ] HG-GRAPH-MODULES 签收行回填（30 交付时勾）
- [x] registry 波次 entry + task lint PASS · pytest 不跑（零代码，锚点计数断言不受影响：默认面 9 枚不变）

## failure_paths

| 失败 | 行为 |
|------|------|
| 真 server 建连/握手失败 | 触发 R-A1 重议（§9.3 不成立分流）· 不硬改代码 |
| 会话判据缺口 | 三级裁定=部分成立 · 缺口进 P2c 清单 · MCP 面保闸关态 |
| 端口冲突 | 换端口（8000 被 T5a 占 → 8001）· 不杀他波进程 |
| Langfuse 云不可证 | 替代证据路径（span_probe 录制 metadata 载荷 · 承 P2a (a) 先例） |

### 自检结论

- 范围/非范围/failure_paths 与 11 终稿 §8 T5b 行 + §9.1/§9.3 逐项对齐，无超范围项。
- 纯文档波：allowed_app_files=[] + banned_prefixes=[app/, tests/, alembic/, scripts/] 机械钉死。
- 人工闸三枚 approved（issue #23 m03064/m03216 夜间授权）· R1 审查文 GO。