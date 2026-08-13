# SPEC Audit R1：qdrant-migration

> **hat_id**：20-spec-audit  
> **SPEC**：`docs/spec/SPEC-qdrant-migration_v1.md`（status: `draft`）  
> **日期**：2026-08-13  
> **对照现状**：`app/ops/rag/retrieve.py`（pgvector dense + FTS/sparse）· `app/ops/rag/ingest.py` · `alembic/versions/20260808_rag_chunks.py` · N≈8,574 · BGE-M3@1024

---

## 结论

| 项 | 值 |
|---|---|
| **判定** | **conditional_pass**（R1）→ **v1.1 已覆盖 C1–C4 与三方阻塞项** |
| **HG-SPEC-SIGNOFF** | **approved**（维护者 2026-08-13 口头「签收」· 已落盘 SPEC） |
| **下一棒** | ~~人签~~ → ~~00 起草 task~~ → **20-task-audit** → 人签 `HG-AUDIT-R1` → 30 |

---

## 元信息核对

| 字段 | SPEC 值 | 审阅 |
|---|---|---|
| `spec_slug` | `qdrant-migration` | OK |
| `test_strategy` | `required` | OK（对账/内存/P95/回滚均可测） |
| Open Folder | `ops-desk-api/` | OK |
| 默认分支 | `task/qdrant-migration`（自 master） | OK（本分支已开） |
| `graph_change_layer` | G-L1 + G-L2 建议 | OK（00 须落死） |
| `HG-SPEC-SIGNOFF` | pending | 正确；未代签 |
| 思考轮 | Round 1–4 自纠闭合 | OK（DiskANN 幻觉已纠；内存估算可用） |

---

## 核对表

### 1 · 范围 / 非范围

| 检查点 | 结果 | 说明 |
|---|---|---|
| 仅迁 dense 主路 | **pass** | FTS/sparse 明确留 PG；混合融合仍在应用层 |
| 排除 Kafka CDC / GPU / DiskANN | **pass** | Bounded Context 与 Round 2 一致且可执行 |
| PG 为写真源 | **pass** | 影子双写 + DLQ；最终一致语义诚实 |
| 压测不过则停迁 | **pass** | 否决条件明确，避免「为迁而迁」 |
| 与现网接口衔接 | **pass** | 承认无 `BaseRetriever`；拟定 ABC 对齐 `RetrievedChunk` |

### 2 · 架构 / 硬件

| 检查点 | 结果 | 说明 |
|---|---|---|
| 2C4G 否决全内存 HNSW | **pass** | 3.28 GiB 向量本体估算充分 |
| on_disk HNSW 为首选 | **pass** | 对齐 Qdrant 产品能力 |
| 版本钉 v1.13.6 | **pass** | 保守合理；升级路径可后置 |
| P95 依赖 NVMe | **conditional** | 见 C1 |

### 3 · 迁移 / 一致性 / 回滚

| 检查点 | 结果 | 说明 |
|---|---|---|
| 5 分钟窗仅切读 | **pass** | 全量灌库在线，符合业务约束 |
| upsert 幂等 + DLQ | **pass** | point id = PG id 可对账 |
| Feature Flag 主回滚 | **pass** | 对齐现网单进程检索；Nginx 为辅 |
| 自动降级 streak≥3 | **pass** | 骨架可落地 |
| 写路径完整性 | **conditional** | 见 C2 |

### 4 · 验收 / 可测性

| 检查点 | 结果 | 说明 |
|---|---|---|
| SMART 清单 1–8 | **pass** | 误差/RSS/P95/召回/回滚/DLQ/窗/边界齐全 |
| 仿真压测表须实测替换 | **pass** | §3.1 / §6 已声明 |
| 独立 `failure_paths` 表 | **conditional** | 见 C3（内容散落 Round/SMART，00 起草易漏） |
| 金样基线指针 | **conditional** | 见 C4 |

### 5 · 思考轮闭合

| 轮次 | 结果 | 说明 |
|---|---|---|
| R1 目标重定义 | **pass** | 生产门禁 + 能力建设 + 否决条件 |
| R2 索引内存 | **pass** | 纠正 DiskANN；给出可算估算 |
| R3 双写 DLQ | **pass** | 停机全量不可行已论证 |
| R4 回滚 | **pass** | Flag + Nginx 骨架 |

---

## 条件（conditional_pass · 签收前接受或补进 SPEC）

### C1 · 目标机磁盘类型锁死

- SPEC 假定 NVMe；未写「非 NVMe → 直接走否决条件、不切流」。
- **要求**：人签时确认目标机为 NVMe；或在 SPEC/task 写死：磁盘类型不达标则 Phase4 禁止切流。

### C2 · 写路径枚举

- 影子写锚定 `ingest`；若存在其他写 `ops_knowledge_chunks` 的路径（手工 SQL / 未来 API），须同波接入或列入非范围并监控漂移。
- **要求**：00/30 前枚举写入口；本期仅保证 ingest（及已文档化的 CLI）双写。

### C3 · 显式 `failure_paths` 表（给 00）

- 失败路径已散落在 Round 3–4 与 SMART，但缺与现网 task 同形的汇总表。
- **要求**：人签后 00 出 task 时补表（至少：Qdrant 宕机、DLQ 积压、对账失败、P95/RSS 不达标、切流回滚）。不必改 SPEC 正文亦可，但 task 必有。

### C4 · 金样对照基线文件名

- 召回门禁写「同日 pgvector 基线」；建议锁死对照文件（如合入后的 `reports/r4-2.yaml` 或当时 master 默认关 rerank 的报告），避免评测日漂移。
- **要求**：00 写死 `compare_with` 路径。

---

## 阻塞 / 非阻塞

| 级别 | 项 |
|---|---|
| **阻塞签收** | 无（方案、边界、回滚、硬件否决逻辑主体成立） |
| **条件** | C1–C4（上表） |
| **非阻塞** | payload 含 `content` 体积大——已 `on_disk_payload`；实现时注意过滤字段建 index；RocksDB 监控属运维债已记 |

---

## HG-SPEC-SIGNOFF（建议文案 · 待维护者）

```text
状态：pending → （人签后）approved
条件：接受 C1–C4
SPEC status：draft → accepted
```

---

## 下一棒

1. **维护者**：接受 C1–C4 → 改 SPEC 闸表 `HG-SPEC-SIGNOFF=approved`、状态 `accepted`  
2. **00**：起草 `docs/tasks/active/task_qdrant_migration.md`（含 failure_paths、compare_with、graph_delta）  
3. **20-task-audit** → 人签 `HG-AUDIT-R1` → **30**（本审 **不**附 30 Prompt）  
4. 30 首步必须是 **80 万级压测门禁**；不过则停迁、不切流

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-13 | 20-spec-audit R1：conditional_pass；建议人签（附 C1–C4） |
| 2026-08-13 | SPEC **v1.1** 已吸收三方审阻塞项与 C1–C4。 |
| 2026-08-13 | 维护者「签收」→ SPEC `accepted` · `HG-SPEC-SIGNOFF=approved`；00 已出 `task_qdrant_migration` |
