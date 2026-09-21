# invoke · 00 · memory-golden-eval · live 真跑裁决记录（代维护者执行 · worktree 轨）

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 00（维护者令「真跑在单独的 worktree 执行」· detached worktree `../ops-desk-api-mge` · 跑后已清理） |
| **报告** | `reports/memory_golden_eval_20260921.yaml`（live 全量 50 用例 + 扫参 · bge-m3 真 embedder · 真 LLM） |
| **库** | dev `opsdesk`（migration schema · timestamptz）· 清场核验：`memory-eval` 租户 **0 残留**（revoked=54 · deleted=165 全部限该租户） |

## 门槛裁决（SPEC §2 D5）：**四条全 NOT MET**

| 门槛 | 要求 | 实测 | 判定 |
|---|---|---|---|
| extraction_precision | ≥ 0.9 | **0.2286** | ❌ |
| noise_write_rate | ≤ 0.1 | **0.3571** | ❌ |
| paraphrase_top3 | ≥ 0.8 | **null（12 用例全 error）** | ❌（未测得） |
| supersede_accuracy | = 1.0 | **0.3** | ❌ |

## 裁决结论：两个开关都保持关闭（含向量召回——推翻"先开向量开关"的初步倾向）

### 发现 1（阻塞向量开关 · 生产 bug）：`_time_decay` naive/aware 混算

- 链：migration 建 `timestamptz`（真库读回 aware）← → `now_utc()=datetime.utcnow()`（naive）→ `(now - fact.updated_at)` 在 `service.py:347` 抛 `TypeError`
- **测试库 schema 漂移掩盖**：`opsdesk_test` 由 ORM `create_all` 建表（plain DateTime · naive）→ P1 的 95 条测试全绿；真库（migration schema）才暴露——fake 测不到真 schema（M1 存在意义的实证）
- 生产后果推演：`_fuse_recall` 在向量降级 try 块**外**（`service.py:446`）→ TypeError 上抛至 continuity 外层 → `memory_degraded` + **不注入**——chat 不炸，但向量（乃至记忆注入）静默失效
- 处置：**bugfix task**（双轨可跳 SPEC · 仍须 task+闸）：tz 归一化 + aware 回归测试 + 测试库 schema 漂移注记

### 发现 2（确认烟跑信号）：抽取精度远不达标

precision 0.23 / 噪声 0.36 / 漏记 0.64 · supersede 0.3（key 漂移规模化确认）→ **prompt + key 约定校准 task**（`MEMORY_FACTS_EXTRACT_ENABLED` 长期保持关）

### 发现 3：复述召回未测得

12 条 PR 全因发现 1 的 TypeError 中断 → 向量召回有效性**仍无证据** → bugfix 后须重跑 live 方能裁决向量开关

## 后续顺序（建议）

1. **bugfix**：tz 归一化（小 · 高价值 · 阻塞一切后续）
2. 重跑 live → 裁决 `MEMORY_FACTS_VECTOR_RECALL_ENABLED`
3. 抽取 prompt/key 校准（独立 task · 可能多轮）→ 再议抽取开关
