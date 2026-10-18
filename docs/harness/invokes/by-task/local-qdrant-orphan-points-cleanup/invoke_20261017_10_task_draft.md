---
hat: 10-task
task_slug: local_qdrant_orphan_points_cleanup
date: 2026-10-17
---

# invoke · 10-task 起草 · local_qdrant_orphan_points_cleanup（本地 Qdrant 8574 遗留孤儿点清理 · 含写动作）

## 落稿摘要

- 起因：上游 task_local_vector_data_state_audit（PR #270 已并 squash 1570f82）40 实证钉死：本地 Qdrant `ops_knowledge` 8574 点 = 2026-08-18 迁移期 `export_vectors.py` → `bulk_upsert.py` 正当重迁写入（150/150 样本 payload 恰 4 键 {source_type,repo,source_id,chunk_index} 与 export_vectors.py:12 ALLOWED_PAYLOAD 逐键相等 · WAL/段 mtime 钉死 08-18 02:54Z 单次批量写入）；PG `ops_knowledge_chunks` 于 (2026-08-13, 2026-09-07] 窗口被表级清空（堆文件归零 2026-09-07 02:19:59Z · 绕过应用层无影子删除）→ count_diff=-8574 mismatch。F3 处置建议 = 清理脚本（重建索引无本地源数据支撑 · 保持原样持续 mismatch 噪音）。维护者 2026-10-17（会话 m00954）选定立本清理 task。
- **本质差异钉死**：本 task 含写动作（删除 Qdrant 遗留点 · 不可逆），与上游只读核查不同 —— 安全前置四条先于一切删除落实：F1 备份硬闸（无备份禁删）· F2 dry-run 一致核验（计数+id 集双重）· F3 白名单钉死（仅显式 id 集 · 禁 filter/truncate）· 回滚预案预写（snapshot recover）。
- 实证锚点（全部亲读复核）：
  - `reports/local_vector_data_state_audit_20261017T135118Z.md`（§4 处置建议三选一各附实证支撑/排除理由 · §6 证据附件索引 e00–e05）
  - `reports/vector_waterline_local_20261017T123649Z.yaml`（立案计数 pg=0 · dlq=0 · qdrant=8574 · count_diff=-8574 · verdict=mismatch · degraded=false）
  - `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/e04_scroll_ids_raw.json`（8574 全量 id 原始输出 = dry-run 逐集对照基准 · min=1 max=8593 含 1 处宽 20 缺口）
  - `scripts/qdrant_migrate/export_vectors.py:12`（ALLOWED_PAYLOAD 恰 4 键）· `bulk_upsert.py:46`（collection 缺省 ops_knowledge）
  - **`scripts/qdrant_migrate/` 目录亲核：9 脚本+README，无现成 delete 工具**（bench_hnsw/bulk_upsert/check_dlq_schema/create_collection/ensure_payload_indexes/expand_synthetic/export_vectors/fio_randread_gate.sh/reconcile）
  - `scripts/check_vector_waterline.py`（只读硬约束 :4-6 禁写 API · scroll 形态 :131-144 · 报告落盘 :274-281；删后复跑预期 0/0/0 verdict=match）
  - `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` §4（mismatch → 另立处置 task · 本 task 即处置执行）
  - `docker-compose.yml` qdrant 段（:22-39 qdrant/qdrant:v1.19.0 · :82-84 qdrant_data 卷 · 6333/6334 映射）
  - Qdrant v1.19.x 官方文档 web 核：`POST /collections/{name}/snapshots` 同步建快照（tar 含配置+全部点+payload）· `GET .../snapshots` 列出 · `GET .../snapshots/{name}` 下载 · `PUT .../snapshots/recover` 恢复 · `POST /collections/{name}/points/delete?wait=true` body 二选一 PointIdsList `{"points":[ids]}` / FilterSelector `{"filter":...}`（本 task 只用前者）
- 范围设计：F1 快照/备份前置（host 钉死路径 `backups/local_qdrant_orphan_cleanup_<UTCts>/` · sha256 台账 · 无备份禁删硬闸）→ F2 dry-run（只读 scroll 全量 id · |S|=8574 且与 e04 逐集相等 · 不一致 STOP）→ F3 白名单分批删除（points/delete 显式 id · 每批 ≤1000 对齐 SCROLL_BATCH · wait=true · 逐批台账）→ F4 删后核验（count=0 · check_vector_waterline.py 复跑 verdict=match · 处置报告落盘 reports/）→ F5 留档收口。
- 非范围五条钉死：生产任何访问（HG-PROD-READONLY-ACCESS pending 不消解）· PG 任何写 · 应用功能改码（须落码即 STOP 补 30 棒+图谱闸 · FP-8）· ops_knowledge 以外 collection · 备份产物入 git/监控接线/新测试。
- **落码与否建议：零落码（一次性 curl 命令行执行）**。理由四条：(1) 删除目标为已实证钉死的固定 8574 id 集 · 一次性无复用场景；(2) scripts/qdrant_migrate/ 无 delete 工具，新落脚本=为单次动作引入永久维护面+触发 30 棒+HG-GRAPH-MODULES 评估，成本远超收益；(3) 上游审计 task 先例：一次性脚本走 stdin 零落码、命令全文落台账保障可复现；(4) 零落码则 graph_change_layer=none、required_invoke_hats=10,40 成立。反方风险照登：curl 手工多批误粘/漏批 → 分批台账+F4 count=0 兜底。**最终裁定权在维护者**（task 正文「落码与否的 10 建议」节）。
- failure_paths 九条：FP-1 闸 pending 拒开工 · FP-2 无备份禁删硬闸 · FP-3 dry-run 漂移即 STOP 回抛 · FP-4 删除中途失败禁盲目重试放大（续删须重新 dry-run 或整体回滚）· FP-5 删后核验 FAIL 走快照恢复 · FP-6 白名单钉死禁 filter/truncate · FP-7 本地口径防外推生产 · FP-8 顺手落码即 STOP · FP-9 证据附件钉死禁记忆转述。
- TC 六条（实证+机断混合）：TC-OC-1 备份硬闸（产物+sha256 · 无则后续全 FAIL）· TC-OC-2 dry-run 逐集相等 · TC-OC-3 白名单删除（批次并集==S · 零 filter/零 truncate · 他 collection 零触碰）· TC-OC-4 删后核验（count=0 · verdict=match · 报告落盘 · 计数对照 8574/0/-8574 → 0/0/0）· TC-OC-5 不假绿+回滚预案预写 · TC-OC-6 零越界（git status 白名单+pytest 13 passed+task lint）。
- 闸设计：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES **全 pending 未代签**（阻塞面 = 40 · 零落码建议下无 30 棒）。graph_change_layer=none · review_hat=20 · required_invoke_hats=10,40。
- 纪律遵守：零 git 操作 · 仅新增 untracked 文件（本 task 档 + 本 invoke · git status 旁证见下）。
- 交付：`docs/tasks/active/task_local_qdrant_orphan_points_cleanup.md`。

## lint 结果

`npx --yes spec-wave task lint --file docs/tasks/active/task_local_qdrant_orphan_points_cleanup.md` → `LINT: PASS · task_local_qdrant_orphan_points_cleanup.md` · EXIT=0（一次过）。

## git status 旁证（零越界）

起草后 `git status --porcelain` 仅新增两个 untracked：`docs/tasks/active/task_local_qdrant_orphan_points_cleanup.md` · `docs/harness/invokes/by-task/local-qdrant-orphan-points-cleanup/invoke_20261017_10_task_draft.md`；零既有文件改动。

## 实证发现（起草期 · 供 20/40 参考）

1. **无现成 delete 工具**：`scripts/qdrant_migrate/` 9 脚本全列亲核，零删除工具 —— 落码与否裁定成为本 task 必经决策点，10 建议零落码（理由见上）。
2. **dry-run 基准现成**：上游 e04_scroll_ids_raw.json 即 8574 全量 id 原始输出，dry-run 可逐集 diff（空集为通过），比单核对计数更强。
3. **删除目标恰等于全集合**：PG=0 且 8574=collection 全量，filter/truncate 在实证上与 id 白名单等价 —— 但本 task 仍钉死走显式 id 白名单路径（白名单可 diff 可审计 · filter 删除无 id 级留痕），维护者书面批准除外（FP-6）。
4. **备份产物处理**：snapshot tar 为二进制，不入 git（untracked 留本机），路径+sha256 落台账；容器内副本同时在 qdrant_data 卷 /qdrant/storage/snapshots/ 下，recover 可用 file:// 位置直引。

## 留 20 审要点

- 写动作安全前置是否钉死（FP-2 备份硬闸 · FP-3 dry-run STOP · FP-6 白名单 · FP-5 回滚预案预写）· 零落码建议理由是否成立（维护者裁定点）· 删除目标白名单与「全集合等价」的边界表述（FP-6 例外条款是否过宽/过严）· 闸阻塞面 = 40（零落码无 30 棒）口径是否认可 · TC-OC-3「批次并集==S」可机断性。
