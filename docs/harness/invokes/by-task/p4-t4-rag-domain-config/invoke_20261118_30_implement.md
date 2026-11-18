# invoke · 30 实现 · p4-t4-rag-domain-config

> **task_slug**：p4-t4-rag-domain-config
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权 · 委派书 p4-t4-rag-domain-config）· 闸真源 task 人工闸表三行 approved（HG-AUDIT-R1 = R1 审查文 GO）· VERIFY: PASS 放行

## 内容

1. **app/ops/rag/backend.py**（19 §4.1）：+import importlib；新增 `_current_domain() -> str`——importlib.import_module("app.ops.prompts.domain_context").current_domain() 运行期解析（守 rag-outbound 静态边界 · 承 lg_rag/continuity.py 先例 · .importlinter 零改动），异常 logger.exception("rag domain resolution failed; fallback to ops") + return "ops"；`qdrant_collection(domain: str | None = None) -> str | None`——resolved=(domain or "").strip() or _current_domain()；ops 域三级链 QDRANT_COLLECTION_OPS → QDRANT_COLLECTION → "ops_knowledge"（与原实现逐值零 diff · 对拍实证）；非 ops 域单级 `QDRANT_COLLECTION_{resolved.upper()}`，缺省/空白 ⇒ None（本地 RAG 显式禁用 · 不回落 ops_knowledge · LB3/R-P4-7 防跨域向量泄漏）。
2. **app/ops/rag/glossary.py**（19 §4.2）：`_TABLES: dict[str, dict[str, list[str]]] = {}` 按域缓存（替换原 `_ZH_TO_EN` · grep 实证无 tests 引用旧名）；`_glossary_path(domain)`——`glossary.<domain>.yaml` is_file 则域件否则回退 glossary.yaml（缺域件不炸 · 不交付 oa glossary=刻意不交付死配置 · 19 §4.2 原话）；`_load(domain)` 按域懒加载缓存；`expand_query_for_fts(query, domain=None)`——resolved=(domain or "").strip() or _current_domain()（backend._current_domain 静态 import · rag 包内合法）；展开算法零改。
3. **app/ops/rag/shadow_write.py**：`_shadow_upsert_safe`/`_shadow_delete_safe` 两函数 try 之前 hoist `collection = qdrant_collection()`，None ⇒ logger.warning（点名 n=%s 与「本域未配置检索 collection」）+ return——影子写显式 skip 不进 DLQ（DLQ 语义=异常路径 · fail-closed 配置缺失非异常）；import 面 :16 未动（qdrant_collection 保持模块属性 · 测试可 patch）。
4. **app/ops/lg_rag/multi/nodes.py**：+import importlib（:17）+from app.ops.prompts.domain_context import current_domain（:77 · lg-rag-outbound 同族既有边内 · :76 prompts.render 静态边先例）；rag_subtask_node 域闸插点=emit_subtask_running 块（:1940-1945）之后、_chain_hook 定义之前——domain = current_domain()；ops 域恒放行（完全不经 importlib · 现状零 diff）；非 ops 域才 importlib.import_module("app.ops.rag.backend").qdrant_collection(domain)（异常 logger.exception + collection=None fail-closed）；None ⇒ result["output"]="本域未配置检索" + logger.warning 点名 QDRANT_COLLECTION_<DOMAIN_UPPER> + return _finish_worker(state, bump, result)（不触 astream_router_agent · 后端调用零发生 · 断言实证）。
5. **tests/test_rag_domain_config.py**（新建 · 32 用例 · autouse fixture delenv 五键 QDRANT_COLLECTION_OPS/OA/ZZ/QDRANT_COLLECTION/OPS_DOMAIN + 清 _TABLES）：回退矩阵全格（ops 域 OPS/OPS+总/仅总/皆缺/OPS 空白落总/总空白落默认 ×8）· ops 零 diff 对拍（`_base_qdrant_collection()` 复刻 base 语义做真源 ×6 含 domain=None/domain="ops"）· 非 ops fail-closed（oa 配置/缺省/空白/zz 隔离 ×5）· domain=None 两通路（set_current_domain("oa")+reset · OPS_DOMAIN=oa）· 解析失败回落 ops（monkeypatch.setitem(sys.modules, "app.ops.prompts.domain_context", None)）· 域闸四例（fail-closed contextvar/env 断言 astream 零调用+output=「本域未配置检索」+无 error · oa 已配置放行检索 · ops 缺省放行）· glossary 四例（oa 无件与 ops 逐字节等 · monkeypatch _glossary_path 读域件 "( 压缩 | ziponly )" · 缓存按域隔离 · domain=None 走 current_domain）· 影子写 skip 两例（patch app.ops.rag.shadow_write.qdrant_collection→None · 零 DLQ · caplog 断言 skip warning）。
6. **图谱登记**：docs/_tech_graph/l1/01_modules.md rag 行（:31）+lg_rag 行（:35）各 append P4-T4 备注（行级脚本插入 · 超长行避字面 edit 陷阱）+ HG-GRAPH-MODULES 签收行插 :48 后（承 :48 p4-t2 先例）；graph-compile.sh done OK。

## 验证台账

| 检查 | 结果 |
|------|------|
| pytest 新文件 tests/test_rag_domain_config.py（真 PG 五键 blank） | 32 passed |
| pytest 目标回归四件（test_rag_qdrant_backend/test_rag_fts_config/test_lg_rag_multi/test_supervisor_parallel_join） | 40 passed |
| ruff check app tests（0.15.21 · CI 钉版） | All checks passed |
| lint-imports（12 contracts） | 12 kept, 0 broken |
| scripts/graph-compile.sh | done OK（exit 0） |
| ingest.py 零 diff 机判（git diff 370a137a -- app/ops/rag/ingest.py） | 0 行（验收 7） |
| mypy 四件 app 文件 | 26 errors 与 master 297363bd 基线逐类别一致（bump_supervisor_step LgRagState invariance 等既有形态 · 零新增） |
| pytest 全量（真 PG 五键 blank） | 2480 passed, 2 skipped, 27 failed——逐签解剖：20 签与 base 297363bd 全量基线（20 failed / 2462 passed）逐签一致（环境性红 · CI 绿为终裁）· test_multi_replica_dualproc ×5 为全量负载下 flake（worktree 单独复跑 5 passed）· test_lg_rag_write_replay_guard::test_tc8_diff_whitelist 1 签=2026-10-20 旧波白名单测试（_BASE=d337486/_WAVE_TIP=c17e63b 硬编码）对 vs HEAD 未提交面生效的 dirty-tree 结构性红（commit 后复跑转绿）· test_wave_gate_registry 1 签=本波 dirty-tree 结构性红（仓内常态 · close 后回绿） |

## 偏差

1. 无实质偏差：四件 app 文件全部在 allowed_app_files 内；rag→prompts 与 lg_rag→rag 两处 importlib 运行期解析承 lg_rag/continuity.py 既定先例（R1 审查文已确认 · .importlinter 零改动）。
2. mypy 26 errors 为 master 基线同形态既有错误（逐类别对拍一致）· 本波零新增——如实登记不修（非范围）。

## 结果

30 实现完成 · 进 40 验证波（commit → rebase origin/master → push + feat PR → CI 四绿 → squash merge → 50 close）。
