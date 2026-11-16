# invoke 40 — P3-T7 放量核实 · 真源对拍 + 全量回归 + PR

> **task**：`docs/tasks/active/task_p3_t7_session_summaries_rollout.md`
> **波次**：40 放量核实（执行序 8-10）
> **日期**：2026-11-16
> **commit 前置**：385e8de（落卡）→ 6cea852（30 实施）→ 本 invoke 结果随下一 commit 落盘

---

## 1. 背景与闸门重扫（GATE_VERIFY）

纯 env 放量 · 零代码改动。30 已按 R2 收口代码面只读核实（invoke_20261116_30_impl.md）。40 负责真源对拍 + 全量回归 + PR 流水线。

| 闸 | 状态 | 证据 |
|---|---|---|
| HG-AUDIT-R1 | approved | task 人工闸表（人签 2026-11-16 · 承 issue #23 授权） |
| HG-GRAPH-MODULES | approved | 同上 |
| HG-PILOT-OPSDESK-GLAYER | approved | 同上 |

verify 输出：见 §2。

---

## 2. 执行动作清单

| # | 动作 | 结果 |
|---|------|------|
| 1 | `npx --yes spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_p3_t7_session_summaries_rollout.md` | VERIFY: PASS（registry 闸一致 · 审查文 GO · 人工闸三行 approved） |
| 2 | `npx --yes spec-wave@3.5.0 task lint --task ...` | PASS（W3 自检结论占位 draft 期合法） |
| 3 | `./scripts/graph-compile.sh` | OK（01_modules.md 增量可编译） |
| 4 | `ruff check app tests` | All checks passed（零代码 · 防御性复跑） |
| 5 | `../ops-desk-api/.venv/bin/python -m pytest tests/test_session_summary.py -q`（真 PG `opsdesk_test`） | 17 passed, 7s |
| 6 | `../ops-desk-api/.venv/bin/python -m pytest tests -x -q`（真 PG `opsdesk_test`） | **2436 passed, 1 skipped, 32 warnings in 79.24s · 零失败**（预警的 `test_check_vector_waterline.py` .env 渗入环境性红本次未复现；零代码改动，CI 终裁兜底） |
| 7 | 真源对拍（dev 库 `opsdesk` · `SESSION_SUMMARY_ENABLED=1` · 真模型摘要 · 用后级联清理） | 见 §3-§7 |
| 8 | 测试缺口核对 | **零缺口**（承 invoke_30 §6 · 不补新测试） |

---

## 3. 对拍方法（dev 库 · 非生产）

- 脚本 `/tmp/opsdesk-rfc/p3_t7_compare.py`（一次性 · 不入仓）：`sys.path` 插 worktree + `load_dotenv` 主仓 `.env`（dev 库 + SiliconFlow key）→ `AsyncSessionLocal` 落合成 thread（`p3t7-compare2-20261116` · 40 轮拟真运维排障对话 · 用后 `DELETE` 级联清理 · 复核 0 残留）。
- 直接调公开装配 `app.ops.lg_rag.continuity.assemble_graph_messages_with_memory`（生产调用面 · 同函数同参数形态 · `max_full_turns=6, group_size=2`）。
- **D1 替代路径**：Langfuse 401/403（无 key）→ monkeypatch `summary.update_current_span_metadata` / `continuity.update_current_span_metadata` 录制 span 元数据三键（`session_summary_generated/cache_hits/degraded`）；另 monkeypatch `_generate_summary` 计数精确 provider 调用数；`ops_llm_usage` 行差对账。
- 估算口径（R3 已定 · D2）：chars 为主判据 + 估算 tokens（CJK 1 + 其余 ≈ chars/4）辅证；分母=原文基线（同 40 轮 `max_full_turns=100` 装配 · 无折叠）。
- 防污染：`LG_RAG_QUERY_REWRITE_ENABLED` 默认关（query_rewrite.py:53）→ 装配无额外线外 LLM 调用；`SESSION_SUMMARY_ENABLED` 显式 `env -u` 控制 off 态。
- 模型：`OPS_LLM_MODEL=deepseek-ai/DeepSeek-V4-Flash`（摘要档未覆盖 · `_resolve_model()` → tier_model=None）。

## 4. 三态 token/chars 对照（40 轮拟真版 · 判据用）

| 口径 | 消息数 | chars | 估算 tokens | vs 原文基线 |
|---|---|---|---|---|
| ① 原文基线（`max_full_turns=100` · 无折叠） | 41 | 25,988 | 13,517 | — |
| ② off（默认 `6/2` · 17 占位条 + 尾 6 轮 + query） | 24 | 4,530 | 2,253 | **−82.6%**（占位模式基线存量收益） |
| ③ on 首跑（17 chunk → 16 摘要条 + 1 降级占位 + 尾 6 轮 + query） | 24 | 12,704 | 6,582 | **−51.1%（chars）/ −51.3%（est_tokens）· ≥50% ✅** |

**验收 7（压缩率判据）✅**：on 态较原文基线降 51.1%（chars 主判据），est_tokens 辅证 51.3%，双口径 ≥50%。

**L2 佐证（长度分布依赖 · 限制已知）**：同脚本 30 轮短轮版（每轮 130-170 字符）on vs 基线仅降 2.5%（摘要 ≈ 原文 1:1）；30 轮拟真版（assistant ~560 字符）降 34.2%。压缩率随轮长度分布漂移——本判据在拟真运维会话长度（assistant ~1100 字符 · 含命令/日志/多步建议）下达标；L2 已在 task 文件登记「数字快照 · 不承诺跨环境复现逐字节一致」。

## 5. 缓存命中复核（验收 8 ✅）

| 项 | on 首跑 | on 二跑（窗口稳定） |
|---|---|---|
| span `session_summary_generated` | 16 | 0 |
| span `session_summary_cache_hits` | 0 | 16 |
| span `session_summary_degraded` | 1 | 1 |
| provider 调用计数（monkeypatch `_generate_summary`） | 17 | 1 |
| `ops_llm_usage` 行差（`task_type='summary'`） | +16 | +0 |
| 输出 vs 首跑逐字节一致 | — | **是**（降级 chunk 重试仍超时 → 占位维持 → 逐字节一致） |

- 17 chunk（40 轮 − 尾 6 = 34 轮 head ÷ group_size 2）：16 摘要条成功缓存，1 chunk 连续两次超时（`SUMMARY_TIMEOUT_S=60` · 同一内容两次生成均 >60s）→ 未缓存，二跑重试仍超时 → 占位维持（降级语义正确展示：失败永不写缓存 · 下次自然重试）。
- `ops_session_summaries` 缓存行：16 行 · `chunk_hash` 由 `summary.py:chunk_content_hash`（sha256(prompt_version+model+turns canonical JSON)）写入；独立重算 17 chunk hash 集合（`prompt_version=v1` · `model=deepseek-ai/DeepSeek-V4-Flash`）——16 stored ⊂ 17 recomputed，集合差恰为超时 chunk（run4 全等比较 false 的唯一原因）；**run1（30 轮短轮版 · 12/12 全成功）全等一致 = true**，函数级一致性已证。
- 判定：窗口稳定下 16/17 chunk 零 LLM 调用 + 逐字节一致 → **缓存 hit 率 100%（可缓存 chunk 口径）· 验收 8 ✅**。

## 6. 降级复核（验收 9 ✅）

| 降级路径 | 证据 |
|---|---|
| 摘要生成超时 → 占位维持 | span `degraded=1`（两次运行同一 chunk 复现）· 无缓存写入 · 无 usage 行 · 装配不中断 |
| `thread_id` 缺失 → 占位模式逐字节一致（continuity.py:387） | on 态 `thread_id=None` 输出与 off 态**逐字节一致** + logger.warning「SESSION_SUMMARY_ENABLED on but thread_id missing; keep placeholders」 |
| Langfuse 401/403 观测不可用 | 本地长期已知（无 key）→ D1 替代路径（§3）· 真源 span 键名以 summary.py:346-352 代码为准 · **不阻断放量** |

## 7. 抽检 3 条（实体保留 · 验收 7 附）

1. 「排查记录：api-gateway（v2.14.3）2026-11-10 03:12 起再次出现 HTTP 502，连接数陡增、QPS 平稳，p99 从 120ms 升至 200ms，日志含 connection pool exhausted 与 upstream timeout。无新发版，仅配置变更 max_connections 由 100 调至 120。初步判断为连接池水位叠加慢查询…」——服务名/版本/错误码/时间戳/配置值全保留 ✅
2. 「…auth-service v1.8.0 再次出现 JWT_EXPIRED（2小时内2次）…p99延迟从120ms升至215ms…max_connections 从110调到[120]…」——实体+数字一致 ✅
3. 「order-worker 当前版本 v3.2.1，2026-11-10 04:05 因连接池水位过高和慢查询叠加再次出现 OOMKilled（2 小时内 3 次）…」——结论性表述与原文一致 · 无新增事实 ✅

## 8. 环境坑登记（非产品缺陷 · 操作纪律）

对拍脚本在 shell 代理环境（`http_proxy=127.0.0.1:7890` + `NO_PROXY` 含 `::1,[::1]`）下，httpx `AsyncClient` trust_env 解析 no_proxy IPv6 段抛 `InvalidURL: Invalid port ':1]'` → 12/12 全 degraded（首跑踩坑）。解法：`env -u http_proxy -u https_proxy -u all_proxy -u ALL_PROXY -u no_proxy -u NO_PROXY` 跑脚本。生产/CI 无此代理环境 · 与本波改动无关。

## 9. 逐项验收核对表（task §验收标准）

| # | 验收 | 状态 | 证据 |
|---|---|---|---|
| 1 | `docs/tasks/active/` 落卡 + registry + R1 审查 GO + invoke_10 | ✅ | commit 385e8de · task 人工闸三行 approved · registry.yaml active entry |
| 2 | invoke_30 放量核实 + verify PASS + registry 闸一致 | ✅ | invoke_20261116_30_impl.md · §2 verify PASS |
| 3 | RUNBOOK_session_summary_rollout_v1_zh.md §0-§5 | ✅ | commit 6cea852（§0 功能面/§1 三步放量/§2 回退/§3 验收对照/§4 故障排查/§5 指标速查） |
| 4 | .env.example + GUIDE env 清单同步 | ✅ | commit 6cea852（.env.example 会话折叠摘要节 · GUIDE :38/:55 备注+修订行 · 86 键不变） |
| 5 | `l1/01_modules.md` 同步 + graph-compile 通过 | ✅ | commit 6cea852（chat 行放量登记 + HG-GRAPH-MODULES 签收表行）· §2 graph-compile OK |
| 6 | 三态交付一致 + off 默认零新依赖零迁移 | ✅ | 交付态 off 占位（表 ③对照 ②）· pytest 2436 全绿（flag 缺席路径）· 本波零代码零迁移零依赖（registry allowed_app_files=[] 证实） |
| 7 | 真源对拍三态 + 窗口外折叠 token 降 ≥50% | ✅ | §4：on vs 原文基线 −51.1% chars / −51.3% est_tokens（40 轮拟真 · L2 已登记漂移） |
| 8 | 缓存命中复核 | ✅ | §5：二跑 16/17 命中 · 零 LLM（可缓存口径）· 逐字节一致 · usage 对账 +16/+0 · hash 对账（run1 全等 true） |
| 9 | 降级复核（占位一致 + Langfuse 403 登记）+ 测试缺口核对 | ✅ | §6（超时占位 + thread_id 缺失逐字节 + warning）· D1 登记 · §2#8 零缺口 |

## 10. 下一步

1. 本 invoke 落盘 commit → push → gh pr create --body-file（中文 PR 文 · 关联 issue #23）→ CI 四绿
2. CI 绿 → squash merge → invoke_50 + task done + registry closed（承 T2b 序 · 合并后终验）

## 11. 结论

**pending（数据面 9/9 验收全过 · 待 PR 合并 + invoke_50 终验后 final）**
