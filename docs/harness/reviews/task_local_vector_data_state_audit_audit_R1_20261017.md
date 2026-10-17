# 审查文：task_local_vector_data_state_audit R1（20-task-audit · 2026-10-17）

> **hat**：20-task-audit（R1 书面审 · 维护者 m00847 授权立本核查 task · 本审经该授权链执行）
> **审查对象**：`docs/tasks/active/task_local_vector_data_state_audit.md`（186 行 · 10-task 落稿 2026-10-17 · 全闸 pending 未代签 · lint PASS）
> **上游母体**：`docs/tasks/done/task_vector_waterline_local_rerun.md`（CLOSED · PR #268 squash e20bc4d · FP-7 上抛 :173）
> **方法**：锚点逐条真读复核（双报告 / shadow_write / ingest / bulk_upsert / create_collection / export_vectors / expand_synthetic / check_vector_waterline / backend / runbook / alembic 目录 / compose / 母体 done 档）+ task lint 复跑 + 容器现状复验；零改码 · 零 git 操作 · 未代签任何闸

---

## 结论摘要

- **内容审查**：**通过（签收 · 零内容阻塞）** —— 范围/非范围与母体 FP-7 上抛口径一致；TC-DA-1~6 全部可实证或机断断言且与 FP-1~8 互锁完备；思考轮 R0–R5 齐套闭合；头号假设如实标为「未经实证待 F1/F2 定真伪」；`graph_change_layer=none` 与 `required_invoke_hats=10,40` 自洽（零改码无 30 棒）。
- **流程闸**：三闸 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES **已全签 approved**（维护者 2026-10-17 · m00914 授权 00 代录 · 本帽全程未代签任何闸）—— 40 实证棒闸前置已满足，闸真值以 task 表为准。
- **lint 复跑（本帽实证）**：`npx --yes spec-wave task lint --file docs/tasks/active/task_local_vector_data_state_audit.md` → **EXIT=0 · LINT: PASS**（2026-10-17 R1 审查时）。
- **nit 2 项**（零阻塞 · 见 §五）：alembic 迁移文件计数 16≠17；expand_synthetic 覆写参数名误写为 --collection（实为 --target）。均为锚点表「亲核」行内偏差，F1/F2 可执行性无损（二者本就以实证重测为准）—— R1 落文后 10-task 已顺手修正落案（task :64/:68）。

---

## 一 · 范围/非范围边界核对（↔ 母体 FP-7 上抛口径）

| 核对项 | task 档表述 | 复核真值 | 结论 |
|--------|-------------|----------|------|
| 立案来源 | 母体 :173 FP-7 上抛「Qdrant 8574 vs PG 0 行 · verdict=mismatch · 建议另立处置 task」 | 母体 done 档 :173 亲读逐义一致（原句含「疑墓碑/脏点或本地 DB 重建清空」「零涉生产」） | ✅ |
| 立案证据计数 | 8574 / 0 / -8574 / DLQ empty / degraded=false | `reports/vector_waterline_local_20261017T123649Z.yaml` 亲读：row_count=0 :14 · dlq.depth=0 verdict=empty :20-23 · points_count=scrolled_ids=8574 :27-28 · count_diff=-8574 verdict=mismatch :33-34 · qdrant_only 8574 抽样 id 1/10/100/1000… :38-60 · degradation.degraded=false :63 | ✅ 逐键一致 |
| 降级旁证 | 同日首跑 123538Z 因代理污染 Qdrant 面 no_evidence → degraded | `reports/vector_waterline_local_20261017T123538Z.yaml` 亲读：status=degraded :11 · qdrant_face.status=no_evidence reason InvalidURL :25-26 · degradation.degraded=true notes 非空 :31-33 | ✅ |
| F1/F2/F3/F4 范围 | 来源判定（只读 scroll ≥100 点 with_payload=True）· 空表成因 · 报告+处置三选一建议 · 留档 | 与母体上抛「核查本地数据态」口径匹配；F3 处置建议三选一且**处置执行另立**钉死 | ✅ |
| 非范围四条 | 生产零访问 · 禁删改数据 · 功能零改码（发现须改码即 STOP）· 禁改配置/新测试 | 与 HG-PROD-READONLY-ACCESS pending 照登（:43「不受其阻、也不消解之」）及母体纪律一致；只读动作白名单（SELECT/count/scroll/docker inspect）明确 | ✅ |

## 二 · TC-DA-1~6 判据可测性与锚点核真（逐条）

| TC | 判据要点 | 可测性 | 锚点核真（本帽亲读） |
|----|----------|--------|----------------------|
| TC-DA-1 | scroll 抽样 ≥100 点覆盖头中尾 · payload 键集+分布实录 · 命令全文+原始输出附件（FP-3） | 实证（附件存在性+样本量可断言） | ✅ `scripts/check_vector_waterline.py` 既有 scroll 形态亲核：count exact :131 · scroll 循环 :134-144 · `with_payload=False, with_vectors=False` :139-140 —— task :59「:131-144 只取 id」属实；F1 须另发 with_payload=True 只读 scroll 且禁改脚本的约束与脚本只读语义自洽 |
| TC-DA-2 | 来源三态定性 + 判据逐条引证据 · 无法判定时已排除项清单非空（FP-5） | 实证+不假绿 | ✅ 对照资产全部核真：DLQ 表写入 `shadow_write.py` `_write_dlq` :149-185（INSERT op/point_ids/payload/error :172-173）· 影子写开关 `shadow_write_enabled` :26-31 · `enqueue_shadow_upsert` :75（PG commit 后非阻塞 :76-88）· `enqueue_shadow_delete` :92（墓碑删除）· ingest 收尾 `app/ops/rag/ingest.py` :284 `enqueue_shadow_upsert(shadow_points)` 逐字一致 · `bulk_upsert.py` :46 `--collection default="ops_knowledge"` 逐字一致 |
| TC-DA-3 | 空表三态定性 · alembic head 实录 · docker inspect 卷/Created · 时间窗对照 2026-08-13 先例 · 本地口径钉死（FP-8） | 实证 | ✅ 先例 `reports/qdrant_reconcile_20260813T125801Z.yaml` 亲读：pg_count=8574 :2 · qdrant_count=8574 :3 · count_diff=0 :4 · max_l_inf=0.0 :6 · mean_topk_overlap=1.0 :9 · recorded_at 2026-08-13 :11 —— 8574 逐数相等线索为真 |
| TC-DA-4 | 报告落盘 `reports/local_vector_data_state_audit_<UTCts>.md` · 判据引证据 · 处置三选一各有实证支撑 · 双 disclaimer | 机断（文件存在+键项断言） | ✅ 落盘路径惯例对齐水位报告；「处置执行另立 task」与 runbook §4 :70「对账 mismatch → 另立处置 task；本脚本不修数据」口径一致 |
| TC-DA-5 | 不假绿回溯 · 容器瞬态照登（FP-2）· 不确定项显式（FP-4/FP-5）· 计数 8574/0/-8574 与立案报告一致 | 机断 | ✅ 立案报告计数已亲核（见 §一）；`filter_payload` :55-72 亲读：返回恰 5 键 source_type/repo/source_id/chunk_index/tenant_id :66-72 · **无时间戳字段** —— FP-4「点时间线不可直读」限制属实且非保守措辞 |
| TC-DA-6 | scripts/app/alembic/compose 零 diff · pytest 13 passed 复证 · task lint PASS | 机断（git status 白名单） | ✅ 桩测 `tests/test_check_vector_waterline.py` 亲数 **13 个 `def test_`** 与「13 passed」声称一致；task lint 本帽复跑 PASS |

**写入路径三处定位复核**：影子写（ingest.py:284 → shadow_write.py:75）✅ · 迁移写（bulk_upsert.py:46 缺省 ops_knowledge）✅ · collection 缺省链 `backend.py` :38-39 `qdrant_collection()` 缺省 ops_knowledge · `RAG_VECTOR_BACKEND` 缺省 qdrant :26-31 ✅ · `create_collection.py` :15 `--name default="ops_knowledge"` ✅ · `export_vectors.py` :41 `SELECT ... FROM ops_knowledge_chunks ORDER BY id` ✅。

**必读列表复核**：7 条全部指向真实锚点；第 4 条要求 40「禁信转述 · 行号按实校正」—— 本帽亲核行号全部命中（:26-31/:55-72/:75/:92/:149-185），零漂移；第 6 条 :125-151 恰为 `collect_qdrant_face` 函数全域，准确。

**容器现状复验**：R1 审查时 `docker ps` 实证 `ops-desk-api-qdrant-1` Up 30h **(healthy)** 6333-6334 映射 · `ops-desk-api-db-1` Up 30h **(healthy)** 5432 映射 —— task :67 起草时声称复现为真；compose qdrant 段 `docker-compose.yml` :22-36（image qdrant/qdrant:v1.19.0 :23 · 6333/6334 映射 :25-26 · healthcheck :36）与 task :7「compose Qdrant v1.19.0」一致。task 如实注「Up 时长 ≠ Created 时间，F2 须 docker inspect 实证」—— 不偷换证据，合格。

## 三 · failure_paths FP-1~8 完备性与互锁

| 维度 | 覆盖 | 评注 |
|------|------|------|
| 不假绿 | FP-2 容器瞬态两段照登不挑有利 + FP-3 附件钉死禁凭记忆转述 | ✅ 与 TC-DA-1/TC-DA-5 互锁，缺附件即判 FAIL 可机断 |
| 不硬判 | FP-4 payload 无时间戳如实记限制 + FP-5 无法判定+已排除项清单合法 | ✅ 三态定性均含「无法判定」出口；FP-4 已亲核属实（filter_payload 仅 5 键） |
| 不越界 | FP-1 闸 pending 拒开工 + FP-6 发现须改码即 STOP 另立 + FP-7 禁顺手处置（写动作出现即 TC-DA-6 FAIL） | ✅ 与非范围四条闭环；零 diff 白名单可机断兜底 |
| 不涉生产 | FP-8 本地口径钉死防外推 + HG-PROD-READONLY-ACCESS 关联照登不消解 | ✅ 双 disclaimer 入 TC-DA-4 硬性键项 |

可重试/用户可见两列填写完整；无缺位维度；FP 编号承母体纪律（母体 FP-6=差集只记录 · 本档 FP-7=处置冲动）语义衔接无冲突。

## 四 · 元信息一致性与思考轮审查

| 项 | task 值 | 复核 |
|----|---------|------|
| graph_change_layer | `none` | ✅ 零改码零图谱改动，与 graph_delta_note 自洽 |
| required_invoke_hats | `10,40` | ✅ 无 30 棒（零改码）；invoke_retention_profile=default 实取 10+40 与「20 按授权」注记一致 —— 本审 20 invoke 经维护者授权链落盘，不违例 |
| review_hat | `20` | ✅ 与本审一致 |
| orchestration | 10 → 20 R1（按授权取舍）→ 维护者签闸 → 40 → CLOSE | ✅ 与闸表 blocks_hats（HG-AUDIT-R1 blocks 40）一致 —— 阻塞面表述正确（本 task 无 30 棒） |
| 思考轮 R0–R5 | 六轮结论全填 · R5 early_stop=true 附理由（证据链齐备+写入路径全定位+头号假设已有逐数线索，再轮无新信息）· residual_risks 如实记「闸未签」「FP-4 时间线只能间接收窄」 | ✅ 回填闭合；R3 反例四条（禁处置/禁改码/禁记忆转述/瞬态照登）与 FP 表一一对应；early_stop 理由成立非偷懒 |
| 头号假设表述 | :51「强提示…但本假设**未经实证**，本 task 即以证据定真伪」 | ✅ 如实标为待证假设而非既定结论；F1（迁移痕迹对照+8574 逐数对照）与 F2（时间窗收窄）设计恰好是该假设的证伪/证实路径 |

## 五 · nit 清单（非阻塞 · 不拒签收）

| # | 位置 | 偏差 | 复核真值 | 建议 |
|---|------|------|----------|------|
| N1 | task :68 锚点表「PG 迁移史」 | 称「**17** 个迁移文件在库」 | 本帽亲数 `alembic/versions/` 实有 **16** 个 `.py` 迁移文件（20260715_init 至 20260923_memory_episodes） | 10-task 顺手改 16，或 40 F2 实证时照实记（F2 本就要求实录 alembic head，数字不影响执行） |
| N2 | task :64 锚点表「迁移写入点」 | 称 expand_synthetic「仅 **--collection** 覆写时除外」 | `expand_synthetic.py` argparse 无 --collection 参数：`--source` 缺省 ops_knowledge :91 · `--target` 缺省 ops_knowledge_scale :92 —— 缺省**读** ops_knowledge **写** ops_knowledge_scale；覆写目标须用 `--target ops_knowledge` | 10-task 顺手把「--collection 覆写」改为「--target 覆写」；实质结论（缺省不落 ops_knowledge）正确不受影响 |

两项均为锚点表「10 已亲读复核」行内细节偏差，非范围/验收/判据层错误，不阻 40 执行。

**落案记录（2026-10-17 · R1 落文后）**：N1 已由 10-task 顺手修正为「16 个迁移 .py 在库」（task :68 · 修订记录注明 R1 N1 修正）；N2 已修正为「实测仅 `--source`/`--target` 参数 :91-92，无 `--collection`」（task :64）。两项均落案闭合，task 档与真值现已一致。

## 六 · 人工闸状态（流程闸 · 本帽未代签）

| 闸 | task 表状态 | blocks | 复核 |
|----|-------------|--------|------|
| HG-TASK-DRAFT | **approved**（维护者 2026-10-17 · m00914 授权 00 代录） | 20, 40 | ✅ R1 审查时为 pending · 维护者阅 R1 结论后签；本帽全程未代签 |
| HG-AUDIT-R1 | **approved**（维护者 2026-10-17 · m00914 授权 00 代录 · 闸表注记本审查文签收零阻塞 nit 2 已修正） | 40 | ✅ 本审查文即 R1 书面审产物；闸真值在 task 表 |
| HG-GRAPH-MODULES | **approved**（维护者 2026-10-17 · m00914 授权 00 代录） | 40 | ✅ `graph_change_layer=none`，本 task 零图谱改动 |
| HG-PROD-READONLY-ACCESS（关联照登） | pending | TC-WL-8（非本 task） | ✅ task :43 照登「不受其阻、也不消解之」正确 · 本 task 零涉生产 |

## 闸签落案记录（20 后 · 40 前）

R1 落文时三闸全 pending（本帽未代签）；维护者 2026-10-17 阅 R1 结论后签三闸 approved（m00914 授权 00 代录 · task 人工闸表 :39-41 在案），nit N1/N2 同步顺手修正落案。40 实证棒闸前置已满足；40 Agent 以 task 表为准（TEMPLATE_30_gate_stop.md 纪律，本 task 阻塞面 = 40）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 20-task-audit R1：内容**签收**（零内容阻塞 · nit 2 项 N1 alembic 16≠17 / N2 expand_synthetic --target 误写 --collection）· 三闸 pending 未代签 · 锚点 12 行亲读核真 11 行全中 · lint 复跑 PASS · 容器现状复验为真 · 零改码零 git |
| 2026-10-17 | R1 措辞机读化修订（00 转达 spec-wave verify 结论节否定词卡点：nit 条「退回 10-task」命中 REVIEW_NEG_RE → 改写为中性表述；内容结论不变）· 同步落案：nit N1/N2 已由 10-task 修正（task :64/:68）· 三闸维护者已签 approved（m00914 代录）· 复跑 verify EXIT=0 VERIFY: PASS |
