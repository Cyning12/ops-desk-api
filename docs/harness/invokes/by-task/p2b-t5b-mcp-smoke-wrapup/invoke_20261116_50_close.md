# invoke_50 · close（p2b-t5b-mcp-smoke-wrapup）

## 内容

50 关账：registry N3 entry status active→closed + wave_tip 钉 squash merge sha · task 档 active→done 归档（状态 closed + 关联 PR 回填）· 偏差终录。

## 验证台账

| 项 | 结果 |
|---|---|
| feat PR #416 | MERGED · squash merge sha 6613dbcc（branch task/p2b-t5b-mcp-smoke-wrapup · 提交 368c926 · CI 四绿后 merge） |
| CI 终裁（merge 前 · 368c926） | **四绿**：pytest 2m25s · check 16s · import-linter 10s · lint-wiki-delta 11s |
| 冒烟十行台账 | 全 PASS（invoke_30）：建连 2025-06-18 · 翻译 12 注册/3 拒载/1 排除 · catalog 投影 · 会话 3 命中+4 不命中零误选 · 闸链 span/receipt · args_schema_invalid fail-visible · identity_mismatch 拒连 · shutdown 摘除 12/12 |
| 三级裁定 | 成立（MCP 向）· R-A1 未触发 · 维持裁定 A |
| registry.yaml | p2b-t5b-mcp-smoke-wrapup status=closed · base=bfbb855c · wave_tip=6613dbcc |
| task 档 | docs/tasks/done/task_p2b_t5b_mcp_smoke_wrapup.md（状态 closed · 关联 PR #416 回填） |
| workspace 回写 | main a565e93 直推：04-roadmap:50 裁定 A · 05 R7 追加段 · 09 G12-G14 关闭注记+互毒残余 · 新建 12-p2b-verification.md · README 索引 |

## 偏差终录

1. **D1（文档位置）**：04-roadmap 在 01-scope/03-general-agent/ 非 05-plan/；委派书「09-p2a 附录 B（G1-G7 开关）」以设计 §8 T5b 行为准落为 G12-G14 关闭注记。
2. **D2（端口）**：8000 被 T5a 冒烟进程占用（PID 18921 不可杀）→ 冒烟走 8001。
3. **D3（Langfuse）**：OTLP exporter 403（dev 密钥失效）——真实会话 span 未上送，以本地 span 探针录制+日志为证据；非代码缺陷。
4. **L1（承 T3）**：supervisor 候选集默认仅 9 枚 builtin，会话冒烟经 OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS 注入三枚 mcp id。
5. **流程教训**：LLM 单 run 60-110s，curl 必须后台 job 防 120s 超时杀；泛化问法 planner 退化 rag 直答——会话冒烟须显式命名 capability id（弱面进 P2c 评估，12 文 §5.1）。

## 结果

50 关账完成 · P2b-T5b 交付：真社区 server（server-everything v2.3.0）冒烟全过 + 三级裁定成立（裁定 A 维持）+ 五文档回写 + 12-p2b-verification.md 新建（runbook + P2c 评估）· tool_use_error 复核 CLOSED（已 fail-visible）。
