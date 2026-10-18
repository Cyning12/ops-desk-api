# 审查文：task_local_qdrant_orphan_points_cleanup R1（20-task-audit · 2026-10-17）

> **hat**：20-task-audit（R1 书面审 · 维护者 2026-10-17（会话 m00954）授权立本清理 task → 00 委派本帽）
> **审查对象**：`docs/tasks/active/task_local_qdrant_orphan_points_cleanup.md`（196 行 · 10-task 2026-10-17 落稿 · 三闸 pending · **含写动作——删除 Qdrant 8574 遗留点**）
> **母体**：`docs/tasks/done/task_local_vector_data_state_audit.md`（CLOSED · PR #270 MERGED squash 1570f82）+ `reports/local_vector_data_state_audit_20261017T135118Z.md`（F3 处置建议 = 清理脚本）
> **方法**：锚点逐条真读复核（F3 报告 / 立案 yaml / e04 证据程序解析 / 迁移脚本 / 水位脚本 / runbook / compose / 桩测 / 上游 done 档）+ task lint 复跑 + 本地 Qdrant **只读** curl 实证；零改码 · 零 git 操作 · 未代签任何闸

---

## 结论摘要

- **内容审查**：**通过（签收 · 零内容阻塞）** —— 写动作安全链 F1 备份硬闸 → F2 dry-run 双重一致 → F3 白名单批删 → F4 删后核验 + 回滚预案逐环闭合，无漏洞级缺口；TC-OC-1~6 全部可实证或机断断言；FP-1~9 与 TC 互锁完备、不假绿机制成立；思考轮 R0–R5 齐套闭合（early_stop 理由成立）；元信息一致（review_hat=20 · graph_change_layer=none · required_invoke_hats=10,40）。
- **流程闸**：**HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸全 pending（未代签）** —— 本 task 含不可逆写动作，**闸签前禁止 40 执行**（FP-1）。
- **lint 复跑（本帽实证）**：`npx --yes spec-wave task lint --file docs/tasks/active/task_local_qdrant_orphan_points_cleanup.md` → **EXIT=0 · LINT: PASS**（2026-10-17 R1 审查时）。
- **nit 2 项**（非阻塞 · 明细见 §六）：N1 `scripts/qdrant_migrate/` 删除能力口径建议精化；N2 备份完整性核验可选强化（tar 归档可读性）。

---

## 一 · 写动作安全链完备性（本审重点）

| 环节 | task 钉死（行号） | 本帽复核 | 结论 |
|------|------------------|----------|------|
| F1 备份硬闸 | snapshot 建+列+下载拷出 host 钉死路径 + sha256 台账（:74-77）；无备份产物+sha256 核验 → 禁入 F3（FP-2 · TC-OC-1「无此核验记录则后续 TC 全判 FAIL」） | 链条闭合：硬闸有 TC 级连坐兜底，备份产物 untracked 留本机纪律明确 | ✅ 完备；核验深度=产物存在+size>0+sha256 记录。空白点照登：归档可读性（tar -tf）与 recover 预演未列 → N2（非阻塞，评估见 §六） |
| F2 dry-run | 只读 scroll 全量 id（形态参照 `scripts/check_vector_waterline.py:131-144` 亲验为真）· |S|=8574 且与 e04 逐集相等 · 漂移即 STOP（:78-80 · FP-3） | 双重一致基准（e04）本帽程序解析亲验为真（§三 #3）；STOP 纪律与「禁按旧报告删」表述明确 | ✅ 完备 |
| F3 白名单删除 | `points/delete?wait=true` 显式 id 批次 ≤1000 · 逐批台账 · 禁 filter/禁 delete collection/禁 truncate 等价物（:81-83 · FP-6） | 白名单为显式 id 集，误删面被钉死在 F2 已核验集合内；禁令有实义——`create_collection.py:60` 实有 delete_collection 能力（--recreate 分支），纪律恰防顺手 | ✅ 完备 |
| F4 删后核验 | count=0（exact）· 水位脚本复跑 verdict=match · 处置报告落盘（:84-87 · TC-OC-4） | `scripts/check_vector_waterline.py` 只读硬约束亲验（:4-6 逐字：PG 只 SELECT · Qdrant 只 count/scroll）· 报告落盘路径模板 :277 亲验；复跑可行性成立 | ✅ 完备 |
| 回滚预案 | FP-5 recover 命令预写：`PUT /collections/ops_knowledge/snapshots/recover` body `{"location": "file:///qdrant/storage/snapshots/ops_knowledge/<snapshot_name>"}` | 路径形态与快照容器内存储布局（snapshots/{collection}/{name}）一致；recover 可行性=官方文档核 + 本帽只读实证 snapshot 端点形态实存（§三 #10），未做恢复预演 → 已含于 N2 评估 | ✅ 预案预写达标（TC-OC-5） |
| FP-4 中途失败续删纪律 | 立即停止后续批次 · 已删/未删如实记 · 二选一：重新 dry-run 核验剩余集后续删 / 整体回滚（FP-5）· 禁盲目重试放大 | 可执行：白名单显式 id 使「剩余集」定义明确，重新 dry-run 无歧义；回滚恢复至快照态，collection 自 08-18 零写入（上游 e05 api 容器未运行旁证），恢复覆盖无损风险低 | ✅ 可执行 |

**小结**：安全链无漏洞级缺口；N2 属深度强化建议而非缺口（最坏情形有界：回滚失败 = 孤儿点保持已删状态，恰为本 task 目标态；且快照同时留存于 qdrant_data 卷内）。

## 二 · TC-OC-1~6 ↔ FP-1~9 互锁与不假绿机制

| TC | 互锁 FP | 可验收性复核 |
|----|---------|--------------|
| TC-OC-1 备份硬闸 | FP-2 | 产物存在+size>0+sha256+全链命令输出落档，机断可断言 ✅ |
| TC-OC-2 dry-run 一致 | FP-3 | diff 为空集可机断；不一致则全链 STOP 记录 ✅ |
| TC-OC-3 白名单删除 | FP-6 | 批次并集==S · 每批 ≤1000 · 删除前后 collections 列表对照（零触碰他集合）可机断 ✅ |
| TC-OC-4 删后核验 | FP-5 | count=0 + 水位报告六字段（pg=0/qdrant=0/diff=0/match/dlq empty/degraded=false）逐键可断言 ✅ |
| TC-OC-5 不假绿+可回滚 | FP-4/FP-5/FP-7 | 判定-证据可回溯 + recover 命令预写 + disclaimer 双落 ✅ |
| TC-OC-6 零越界 | FP-8/FP-9 | git status 白名单 + pytest 13 复证（13 个 def test_ 亲数一致）+ task lint ✅ |

- **不假绿机制**：FP-9 全链命令全文+原始输出附件必落档（缺附件即 TC 判 FAIL · 禁凭记忆转述）+ TC-OC-5 如实记 FAIL 不冒充 + FP-1 闸 pending 即拒开工 —— 三层闭环 ✅。
- **行为变更类 checklist 提醒**（K7）：本 task 建议零落码、无默认值/校验/策略门变更，「旧测 grep 影响面」项不适用；越界面由 TC-OC-6 git 白名单+pytest 复证覆盖 ✅。
- **关联闸照登**：HG-PROD-READONLY-ACCESS pending 照登且「不受其阻、也不消解之」（:43 · FP-7）——口径正确 ✅。

## 三 · 锚点实证核验（逐条真读复核 · 13 组）

| # | 锚点（task 行号） | 本帽核验 | 结论 |
|---|-------------------|----------|------|
| 1 | F3 建议原文 `reports/local_vector_data_state_audit_20261017T135118Z.md`（:57） | §4 :90-98「建议：清理脚本」+ 三选项实证支撑表 + :98「处置执行另立 task」· §6 :116 e04 证据索引 · §1 :40-41 指纹锁定 | ✅ 全中 |
| 2 | 立案计数 `reports/vector_waterline_local_20261017T123649Z.yaml`（:58） | 66 行全读：pg row_count=0 · dlq depth=0 verdict=empty · points_count=scrolled_ids=8574 · count_diff=-8574 verdict=mismatch · degraded=false | ✅ 逐键全中 |
| 3 | dry-run 基准 `e04_scroll_ids_raw.json`（:59） | 本帽程序解析：9 页 result.points · **8574 个唯一 int id** · min=1 max=8593 · 缺失恰为 8546–8564 共 **19 id（宽 20 缺口）** · 无越界 id | ✅ 与 task 逐字吻合 |
| 4 | `export_vectors.py:12` ALLOWED_PAYLOAD（:60） | 原文 `ALLOWED_PAYLOAD = ("source_type", "repo", "source_id", "chunk_index")` 恰 4 键 | ✅ 全中 |
| 5 | `bulk_upsert.py:46` collection 缺省（:60） | :46 原文 `parser.add_argument("--collection", default="ops_knowledge")` | ✅ 全中 |
| 6 | `scripts/qdrant_migrate/` 无 delete 工具（:60 · :168） | 目录实有 **9 脚本+README**（task :60 枚举 8 个，漏 `fio_randread_gate.sh`；:168「9 个」计数对但枚举不全）；`create_collection.py:60` 与 `expand_synthetic.py:59` 在 --recreate 分支含 `delete_collection` 调用 | ◐ 部分命中 → N1（「无**点级**删除工具」成立；毯式「零删除工具」措辞偏宽 · 非事实性错误） |
| 7 | `scripts/check_vector_waterline.py`（:61 · :144） | 只读硬约束 :4-6 逐字真 · scroll 形态 :125-151（limit=SCROLL_BATCH :137 · SCROLL_BATCH=1000 :64，与 F3「每批 ≤1000 对齐」参照一致）· write_report :274-281（def :274 · 报告路径模板 :277） | ✅ 全中 |
| 8 | runbook §3/§4（:62） | §3 报告解读 :50 · §4 降级判读 :63 · mismatch →「另立处置 task」:70 原文 | ✅ 全中 |
| 9 | `docker-compose.yml` qdrant 段 :22-39 · volumes :82-84（:63） | image qdrant/qdrant:v1.19.0 :23 · 6333/6334 :25-26 · `qdrant_data:/qdrant/storage` :28 · mem_limit 8192m :34 · volumes: :82 / qdrant_data: :84 | ✅ 全中 |
| 10 | Qdrant v1.19.x snapshots/points delete API 形态（:64 · :135） | 文档形态合理性成立（snapshots 建/列/下载 + recover PUT file:// + points/delete 二选一 body 均为 v1.x 稳定形态）；本帽**只读实证**：`GET /collections/ops_knowledge` → **points_count=8574 · status=green**（现网计数与立案一致）· `GET /collections/ops_knowledge/snapshots` → `{"result":[],"status":"ok"}`（端点实存 · 现无快照）；写侧端点（建快照/下载/recover/delete）未实操，task 已钉「以实例实测为准」 | ✅ 合理且有只读实证支撑 |
| 11 | 桩测 `tests/test_check_vector_waterline.py` 13 passed（:127） | 13 个 `def test_` 亲数（聚合/空 DLQ/scroll 分页/reconcile 三向/降级三态/双不可达 exit 2/只读断言/CLI） | ✅ 基准数一致 |
| 12 | 上游 done 链与 PR 事实（:5 · :33 · :131） | done 三档俱在；state_audit done 档 :3/:194「PR #270 MERGED squash 1570f82 · F3=清理脚本 · 遗留=另立本 task」逐字登记；#271 仓内无锚点（task 本文亦仅引 #270，一致无冲突） | ✅ 全中 |
| 13 | task lint（:127） | 本帽复跑 → EXIT=0 · LINT: PASS | ✅ 全中 |

**命中率**：13 组亲核，**12 组全中 · 1 组部分命中**（N1 · 措辞精度问题，非事实错误，不影响安全链结论）。

## 四 · 零落码建议审查

四条理由逐条复核成立：(1) 删除目标为已实证钉死的固定 8574 id 集、一次性处置无复用场景 ✅（e04 亲验集钉死）；(2) `scripts/qdrant_migrate/` 无点级删除工具（亲核 · 口径精化见 N1），新落脚本=永久维护面+30 棒+HG-GRAPH-MODULES 评估，成本远超收益 ✅；(3) 上游一次性只读脚本 stdin 零落码先例（e00 台账）真实存在且可复现 ✅；(4) 零落码 ↔ `graph_change_layer=none` ↔ `required_invoke_hats=10,40` 自洽 ✅。反方风险（curl 手工多批误粘/漏批）照登且有对冲（F3 分批台账逐批核验 + F4 count=0 兜底）✅。落码备选后果说明（:23 · :41 · :94 · FP-8：STOP → 补 30 棒 + 图谱闸评估）准确 ✅。维护者裁定点明示于 :98 与 R5 收口 ✅。

## 五 · 思考轮与元信息一致性

- R0–R5 齐套；early_stop=R5 理由（上游证据链齐备 + 删除目标已实证钉死为固定 id 集 + API 已文档核，再轮无新信息）成立；residual_risks 如实照登（闸未签 · API 以实例实测为准 · curl 手工风险有对冲）；`actual_last_round=R5` 落档 ✅。
- 元信息：`review_hat=20` ✅ · `graph_change_layer=none` 与零落码建议自洽（含落码即 STOP 回补条款）✅ · `required_invoke_hats=10,40` 与 `invoke_retention_profile` 注记（20 按授权）一致 ✅ · `test_strategy=required` 与实证+机断混合 note 一致 ✅ · 人工闸表三闸 blocks_hats=40 与零落码（无 30 棒）编排自洽 ✅。

## 六 · 阻塞与 nit

**阻塞**：零。

**nit（非阻塞 · 维护者裁定顺手精化或留 40 照实执行）**：

- **N1（task :60 · :168）**：「`scripts/qdrant_migrate/` 无现成 delete 工具」口径建议精化为「无**点级（points）**删除工具」——目录实有 9 脚本+README（枚举漏 `fio_randread_gate.sh`），且 `create_collection.py:60` / `expand_synthetic.py:59` 在 --recreate 分支内嵌 `delete_collection` 调用。对本 task 无实质影响（F3/FP-6 已明文禁 delete collection，禁令反而因此更有实义）。
- **N2（task :77 · TC-OC-1 · FP-5）**：备份完整性核验目前为「产物存在+size>0+sha256 记录」；recover 可行性为文档核（task 已自认「以实例实测为准」）。可选强化：F1 追加只读 `tar -tf` 归档可读性核验（snapshot 为 tar 归档，一条只读命令即可）。维持签收的理由：最坏情形有界（回滚失败=孤儿点保持已删状态，恰为本 task 目标态）+ 快照同时留存 qdrant_data 卷内 + 官方 API 形态。

## 维护者签闸（20 后 · 40 前）

- [ ] 已读 R1 审查结论（含 nit N1/N2 处置裁定：顺手精化措辞 / 追加 tar 校验，或照实执行）
- [ ] 裁定落码与否（10 建议零落码一次性 curl · 理由四条+反方照登见 task「落码与否的 10 建议」节）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 40 实证执行 Prompt（闸未签前 40 须拒执行 · FP-1）

40 执行棒将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md 同口径）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | R1 落文：内容审查通过（签收 · 零内容阻塞）· nit 2 项（N1 删除能力口径精化 · N2 备份完整性可选强化）· 三闸 pending 未代签 · 锚点 13 组亲核 12 全中 1 部分 · 本帽只读实证（lint PASS · Qdrant GET 只读）· 零 git 操作 |
