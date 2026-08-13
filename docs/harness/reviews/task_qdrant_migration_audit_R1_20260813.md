# Task Audit R1：qdrant-migration

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_qdrant_migration.md`  
> **对照 SPEC**：`docs/spec/SPEC-qdrant-migration_v1.md`（v1.1 · `accepted` · `HG-SPEC-SIGNOFF=approved`）  
> **日期**：2026-08-13  
> **分支**：`task/qdrant-migration`  
> **结论**：`conditional_pass` · 建议维护者接受 C1–C3 后签 `HG-AUDIT-R1=approved`（本审**不**代签）

---

## 结论摘要

| 维度 | 判定 | 说明 |
| --- | --- | --- |
| **内容可执行** | **conditional_pass** | 范围/非范围/failure_paths/思考轮与 SPEC v1.1 主体对齐；有 3 项签收前条件（见下） |
| **流程闸 `HG-AUDIT-R1`** | **pending** | 真值在 task 人工闸表；本审仅建议，**禁止**改表 |
| **思考轮审查** | **pass** | 控制表闭合；early_stop 有理由与 residual_risks |
| **是否退回 10-task** | **否** | 无内容阻塞；C1–C3 可由 00 微补或签闸时书面「以 SPEC SMART/ADR 为准」 |

---

## 元信息核对

| 字段 | task 值 | 审阅 |
| --- | --- | --- |
| `task_slug` | `qdrant-migration` | OK |
| `git_branch` | `task/qdrant-migration` | OK（与当前分支一致） |
| `test_strategy` | `required` | OK |
| `test_strategy_note` | fio / L∞+Top-k / RSS / Flag / bench 双臂 / r4-2 | OK；金样侧缺显式「关 rerank」→ C1 |
| `graph_change_layer` | `G-L1` | OK（SPEC 另建议 G-L2 运维；task `wiki_delta=n/a` 允许运维短文另落 · 非阻塞） |
| `graph_delta` | `pending` | OK（30 实现时回填） |
| `review_hat` | `20` | OK |
| `required_invoke_hats` | `10,30` | OK（不含 20；本 invoke 可选） |
| `HG-TASK-DRAFT` | approved | OK（00 代签 · 维护者授权留痕） |
| `HG-AUDIT-R1` | pending | 正确；blocks 30 |
| 上游 SPEC | v1.1 accepted | OK |

---

## 核对表

### 1 · 范围 / 非范围 ↔ SPEC

| 检查点 | 结果 | 说明 |
| --- | --- | --- |
| Phase0 fio + Qdrant v1.13.6（2C4G） | **pass** | 对齐 SPEC Phase0 / 硬性增量 |
| Collection：Cosine/1024 · on_disk 向量+HNSW · 轻量 payload | **pass** | 禁止 content/metadata/images；与 ADR-001 / Payload 策略 A 一致 |
| Hydrate：id → PG → `RetrievedChunk` | **pass** | 对齐 SPEC |
| 迁移脚本族 + RSS schema + 构建期 RSS 采样 | **pass** | 对齐 Taskfile 骨架职责 |
| 读路径 Flag 默认 pgvector + 即时降级 | **pass** | 对齐 Round4；禁全局 streak 唯一熔断（failure_paths 已体现） |
| 影子写：commit 后非阻塞 + DLQ | **pass** | 语义对齐；删除入队见 **C2** |
| 验收报告路径 + compare_with=`reports/r4-2.yaml` | **pass** | 基线文件存在；评测开关见 **C1** |
| 非范围：CDC / GPU / DiskANN / 全内存 / FTS·sparse / 默认切 qdrant / 反灌 / 微服务 | **pass** | 覆盖 SPEC §5 Bounded + 非目标 |

### 2 · 签收锁死 / 验收 ↔ SMART

| SPEC SMART | task 覆盖 | 结果 |
| --- | --- | --- |
| #0 磁盘门禁（IOPS≥3000 且 p95≤1ms，或预配≥5000） | 锁死写「fio 过门禁或预配 ≥5000」；数值阈值未写入 task | **conditional** → C3 |
| #1 向量 L∞ + Top-5 重叠≥95%；count 差=0 | 验收勾选项齐全 | **pass** |
| #1b 标量分（辅） | 未列入验收（辅证） | **pass**（允许） |
| #2 稳态 &lt;3.2GB / 构建峰值 ≤3.8GB | 锁死 + 验收 + failure_paths | **pass** |
| #3 Qdrant search P95 &lt;150ms（80万 Top-10+filter） | 锁死 + 验收 | **pass** |
| #4 金样 vs r4-2 不劣于；`RAG_RERANK_ENABLED=false` | 金样勾选有；**关 rerank 未写进验收/锁死** | **conditional** → C1 |
| #5 Flag 回滚演练 | 验收有 | **pass** |
| #6 DLQ / 非阻塞 ingest | 验收 + failure_paths | **pass** |
| #7 Phase4 ≤5min / 无 &gt;30min 不可用 | 未单列验收 | **非阻塞**（跟 SPEC 运维节奏即可） |
| #8 Bounded | 非范围覆盖 | **pass** |
| #9 bench `--baseline pgvector` | test_strategy_note + 验收 | **pass** |

### 3 · failure_paths

| 触发族 | 结果 | 说明 |
| --- | --- | --- |
| fio / IOPS 不达标 → 禁灌禁切 | **pass** | 对齐否决条件 |
| 构建 RSS / 稳态 RSS·P95 → 降参或否决 | **pass** | 含 `ef_construct→64`、SQ int8 保险 |
| Qdrant 读失败 → 重试 1 → PG + 指标 | **pass** | 对齐即时降级 |
| 影子写失败 / DLQ / 积压超阈 | **pass** | 含禁止切流议案 |
| 对账失败 / 金样劣于 r4-2 | **pass** | 禁默认切 qdrant |
| 删除/整组替换漂移 | **缺口** | SPEC Round3 要求非阻塞删点；task 表未点名 → **C2** |

### 4 · 思考轮审查

| 项 | 结果 | 说明 |
| --- | --- | --- |
| 控制表字段 | **pass** | `actual_last_round=R5` · `early_stop=yes` · reason / residual_risks 齐全 |
| R0–R5 回填闭合 | **pass** | 框定→范围→方案→风险→验收→交接；与 SPEC Round1–4 不冲突 |
| early_stop 理由 | **pass** | SPEC v1.1 已承载深度论证；task 收敛为可执行门禁合理 |
| residual_risks | **pass** | 生产盘型/IOPS、压测机≠生产盘 —— 与 Phase0 fio 硬门禁呼应 |

### 5 · 实施顺序 / 编排

| 项 | 结果 | 说明 |
| --- | --- | --- |
| 30 顺序 fio→灌库→读路径→影子写→对账/bench→图谱/回滚 | **pass** | 对齐 SPEC §6 |
| 编排：00 不实现 / 子 agent 跑 20·30·40 | **pass** | 与 task 头注一致 |
| 默认不切 `qdrant` | **pass** | 非范围 + 签收锁死 |

---

## 条件（conditional_pass · 签闸前接受或 00 微补）

### C1 · 金样评测锁死关 rerank

- SPEC SMART #4 / `compare_with` 要求评测时 **`RAG_RERANK_ENABLED=false`**。
- task 验收仅写「金样 vs `reports/r4-2.yaml` 不劣于」，未显式锁死开关。
- **要求**：00 在验收或签收锁死补一行；或维护者签闸时书面接受「金样跑法以 SPEC SMART #4 为准」。

### C2 · 影子写覆盖 delete / 整组替换

- SPEC Round3：删除/整组替换须对 Qdrant 对应 id **非阻塞入队删除**（幂等）。
- 现网 `ingest` 含 `DELETE` + `INSERT`；task 范围只强调 upsert 入队，易被 30 漏删点。
- **要求**：30 开工范围以「ingest 提交后的 upsert **与** delete 入队」为准；或 00 在范围 §6 / failure_paths 补一句。写入口枚举：本期仅保证 `ingest`（及已文档化 CLI），其他手工 SQL 列入非范围并监控漂移（承接 SPEC 审 C2）。

### C3 · 磁盘门禁数值写入签收面

- SPEC：fio 4K randread **IOPS ≥ 3000 且 p95 ≤ 1ms**，或预配随机读 IOPS ≥ 5000。
- task 签收锁死仅「fio 过门禁或预配 IOPS ≥ 5000」，阈值依赖打开 SPEC。
- **要求**：00 补数值到签收锁死；或签闸接受「fio 判据以 SPEC 硬性增量 `hardware_prerequisite` 为准」。

---

## 阻塞 / 非阻塞

| 级别 | 项 |
| --- | --- |
| **内容阻塞（退回 10）** | 无 |
| **条件（签闸前）** | C1–C3 |
| **非阻塞** | Phase4≤5min / Phase5≥72h 观察窗；`graph_change_layer` 未单列 G-L2；HNSW `m`/`ef*` 参数细节以 SPEC ADR 为准；标量分 1b 辅证可不进验收勾选 |

---

## 回填清单（可选 · 非强制退回）

若维护者希望 task 自洽、少翻 SPEC：

1. 签收锁死或验收：补 `RAG_RERANK_ENABLED=false`（金样）  
2. 范围影子写：补「delete / 整组替换 → Qdrant 删点入队」  
3. 签收锁死磁盘：补 IOPS≥3000 且 p95≤1ms  

不补亦可签闸，但须在签闸说明中接受 C1–C3「以 SPEC 为准」。

---

## HG-AUDIT-R1 建议

| 项 | 值 |
| --- | --- |
| **建议 status** | `approved`（接受 C1–C3 后） |
| **本审是否改表** | **否** |
| **30** | 仅当 task 表 `HG-AUDIT-R1=approved` 后方可开工；pending 必须拒开工 |

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文件 · `conditional_pass` · C1–C3）
- [ ] 接受 C1–C3（或已令 00 微补 task）
- [ ] 在 task 人工闸表将 `HG-AUDIT-R1` 改为 `approved`（维护者或授权 00 代签 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 `TEMPLATE_30_gate_stop.md`）。

---

## 修订记录

| 日期 | 说明 |
| --- | --- |
| 2026-08-13 | 20-task-audit R1：`conditional_pass`；条件 C1 关 rerank · C2 delete 入队 · C3 fio 数值；未代签 HG-AUDIT-R1；未附 30 Prompt |
