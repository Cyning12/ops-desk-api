# CLOSE：api-embedder-internal-batching（ApiEmbedder 内部批切 · 2026-10-19）

> 关账日期：2026-10-19 · 关账人：00（goal-eb568703 · 承授权链 m00238/m01101 + m01262「全做」）· 体例承 close_hitl_resume_async_20261015.md

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_api_embedder_internal_batching.md](../done/task_api_embedder_internal_batching.md)（已归档 done/） |
| 性质 | 性能缺口收口（落码 30 棒 · embed() 内部批切 · Protocol 不变消费方零改动） |
| 上游 | `local-rag-knowledge-rebuild` §三.2/§五 批切建议（PR #276/#277 CLOSE · ingest.py:225 全量单请求超时面） |
| PR | [#278](https://github.com/Cyning12/ops-desk-api/pull/278) MERGED · squash `056d874` · CI 4/4 绿 |
| 审查 | R1 [task_api_embedder_internal_batching_audit_R1_20261019.md](../../harness/reviews/task_api_embedder_internal_batching_audit_R1_20261019.md) 通过零阻塞（锚点 14/14） |
| 闸 | 三闸 approved（授权链 00 代录）· **签注三裁定：默认批=128 · fail-fast（skip-and-DLQ 不采纳）· F3b 端到端写面复跑=不授权** |

## 二、交付清单

- `app/ops/rag/embedder.py`：embed() 内部批切（ceil(N/128) 次 POST · 跨批保序 · env `RAG_EMBED_API_BATCH_SIZE` 默认 128 承 embed_backend :113-125 先例 · 构造非法/≤0 沿链回退 warning · fail-fast 中间批耗尽整单 raise）
- `tests/test_rag_embedder.py`：+6 测（切分/保序/配置解析/fail-fast 四组）
- 图谱 G-L1 rag 行备注（`docs/_tech_graph/l1/01_modules.md:31` · env 旋钮+请求形态变更 · 零拓扑）· graph-compile EXIT=0
- commit 链：83a9c9d 红测 → f0d0398 实现 → c70fdf9 台账/图谱/档回填

## 三、验收核验（TC-EB-1~5 全 PASS）

- TC-EB-1 红测先行：6 新测先落 RED 5 failed（TypeError: no batch_size）→ 实现 GREEN 28 passed
- TC-EB-2 回归零 diff：既有 9+13 测零改动全绿 · 全量 19 failed/1834 passed 红集与基线逐名一致零新增
- TC-EB-3 小规模等价：≤128 输入 POST==1 且 payload 逐字节等价 · ingest.py/shadow_write.py/scripts/ 零 diff
- TC-EB-4 门禁：ruff 0 errors · task lint PASS · verify EXIT=0 · diff 白名单 8 件全中
- TC-EB-5（F3a 只读实证）：PG 1200 chunks 单 embed() 链 10 批全 200 OK · 16.9s · **70.9 chunks/s**（对照上游 ~34/s 2×）· 维数 1024 · 余弦保序抽对 cos(same)≥0.99992 >> cos(neighbor)≤0.93 · 知识库 8648/8648 verdict=match 零扰动 · **F3b 按签注不授权未执行未假绿**

## 四、偏差与照登

1. worktree 无 .venv，复用主仓 venv 解释器跑测（cwd=worktree · 代码面为本分支树）。
2. F3a 初版保序判据逐分量 1e-4 误报一次（API 批内数值非确定性 max|diff|~2.3e-3）→ 改余弦判据闭合；拼接确定性由单测乱序 index 钉死，非码缺陷。
3. shell 代理 NO_PROXY 含 [::1] 触发 httpx InvalidURL 上游缺陷 → 命令显式修 env（不改仓码）。
4. 构造参数非法（≤0）回退语义定为「warning+视为未设沿链回退」（task 未显式规定此分支 · 新测已钉死两分支 · **裁定口留维护者：可改判直接落默认**）。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| 构造非法回退语义裁定口 | 移交维护者（如需改判另立小案） |
| HG-PROD-READONLY-ACCESS | 仍 pending 不受影响 |

## 六、维护者 checklist

- [x] 红测先行实证（RED→GREEN 时序 commit 链）
- [x] 红集与基线逐名一致零新增
- [x] F3a 实证（10 批全 200 · 70.9 chunks/s · 水位 match）
- [x] G-L1 图谱已落 graph-compile 绿
- [x] 签注三裁定执行（128/fail-fast/F3b 未执行）
- [x] PR 合并 · 归档 done/ · README 登记 · 50 invoke 落盘
