# Invoke：local-qdrant-orphan-points-cleanup · 20-task-audit R1（2026-10-17）

> **hat**：20-task-audit（书面审查 · 不落实质改动 · 不代签人工闸 · 零 git 操作）
> **授权链**：维护者 2026-10-17（会话 m00954）授权立本清理 task → 00 委派 20 R1 书面审（task `required_invoke_hats=10,40` 不含 20，本 invoke 按 `invoke_retention_profile` 注记「20 按授权」+ 委派指令落盘）
> **对象**：`docs/tasks/active/task_local_qdrant_orphan_points_cleanup.md`（10-task 落稿 2026-10-17 · draft · 三闸 pending · **含写动作**）

## 输入

- task 草稿全文 196 行
- 母体 `docs/tasks/done/task_local_vector_data_state_audit.md`（CLOSED · PR #270 MERGED squash 1570f82）
- F3 报告 `reports/local_vector_data_state_audit_20261017T135118Z.md` · 立案计数 `reports/vector_waterline_local_20261017T123649Z.yaml`
- dry-run 基准 `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/e04_scroll_ids_raw.json`
- 资产：`scripts/qdrant_migrate/` 目录全列 · `scripts/check_vector_waterline.py` · `tests/test_check_vector_waterline.py` · `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` · `docker-compose.yml`

## 动作实录

1. 真读复核锚点 13 组（明细与行号见审查文 §三）：F3 报告 §1/§4/§6 · 立案 yaml 66 行逐键 · e04 程序解析（9 页 · 8574 唯一 int id · min=1 max=8593 · 缺口 8546–8564 共 19 id）· export_vectors.py:12 四键指纹 · bulk_upsert.py:46 缺省 collection · qdrant_migrate 目录全列（9 脚本+README · create_collection.py:60/expand_synthetic.py:59 含 delete_collection --recreate 分支）· check_vector_waterline.py :4-6/:125-151/:274-281 · runbook §3:50/§4:70 · compose qdrant :22-39/volumes :82-84 · 桩测 13 个 def test_ · 上游 done 三档与 PR #270。
2. 复跑 `npx --yes spec-wave task lint --file docs/tasks/active/task_local_qdrant_orphan_points_cleanup.md` → EXIT=0 · LINT: PASS。
3. 本地 Qdrant **只读** curl 实证：`GET /collections/ops_knowledge` → points_count=8574 · status=green；`GET /collections/ops_knowledge/snapshots` → {"result":[],"status":"ok"}（端点形态实存 · 现无快照）。
4. 写动作安全链 F1–F4+回滚预案逐环复核 · TC-OC-1~6 ↔ FP-1~9 互锁 · 零落码理由与反方风险 · R0–R5 思考轮 · 元信息一致性。
5. 落盘审查文 `docs/harness/reviews/task_local_qdrant_orphan_points_cleanup_audit_R1_20261017.md`。

## 结论

- **签收（内容零阻塞）**；nit 2 项（非阻塞）：N1 task :60/:168「无 delete 工具」口径建议精化为「无点级删除工具」（目录 9 脚本枚举漏 fio_randread_gate.sh · 两脚本 --recreate 分支含 delete_collection）；N2 F1 备份完整性可选追加只读 tar -tf 归档可读性核验。
- 三闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）**全 pending 未代签**；审查文附维护者签闸清单（40 向），**未附 40 执行 Prompt**。
- 锚点核验命中率：13 组亲核 12 组全中 · 1 组部分命中（N1 · 措辞精度非事实错误）。

## 零越界声明

本 invoke 全程零改码、零 git 操作、零数据写（仅文件只读 + lint 复跑 + Qdrant 只读 GET curl）；未代签任何人工闸；未触碰 scripts/app/alembic/compose 改码面 · 未触 PG/Qdrant 任何写 API · 未动 ops_knowledge 以外 collection。
