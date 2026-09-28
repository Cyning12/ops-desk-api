# multi-replica 回归报告 · dualproc post-#190 更新（2026-09-24）

> **性质**：G2 残余闭合（出口复核 PASS-WITH-GAP 次 GAP · 三方验收残余登记项）· **取代但不删除**旧 BLOCKED-ENV 报告（`REGRESSION_host_v1_splittability_hardening_20260924.md` 保留为历史真值 · 零删改）  
> **00 代录**：维护者令原话「签收，生成00 Prompt，在新窗口开始D1统筹」（2026-09-24）· 承长程令（2026-09-23）

| 字段 | 值 |
|------|-----|
| task | `multi-replica-dualproc-tenant-session`（fix PR #190 · FINDINGS #1 closed）· 上游 V1-E `host-v1-splittability-hardening` |
| git_sha | `1cae38f`（master · 三方验收亲跑时点 · #194 收口后） |
| recorded_at | 2026-09-24（环境指纹承三方验收窗 · 本地 PG 双进程） |
| topology | 双进程 uvicorn · 共享 PG（既有 `tests/dualproc_server.py` · 未重写基建） |
| gateway_form | 降级 / 直连双进程（承 #165 · **未**声称外部 Java 网关验证通过） |
| result | **PASS**：`pytest tests/test_multi_replica_dualproc.py` **9 passed** |
| evidence | ① #190 fixture fix：`_create_user` INSERT 补 `ops_sessions.tenant_id`（ORM `nullable=False` 对齐 · 值 `ops-desk-pilot` ∈ ALLOWED_TENANTS）· PR #190 MERGED（8f8427e）② #190 CI `pytest` pass ③ 三方验收亲跑 **9 passed** @ master `1cae38f`（`docs/reports/host_v1_exit_review/ACCEPTANCE_three_party_20260924_00.md` §全量验证）④ FINDINGS #1 closed（task #190 KPI · CLOSE 归档 #192） |
| supersedes | `REGRESSION_host_v1_splittability_hardening_20260924.md`（result=BLOCKED-ENV · **保留不删 · 历史真值**） |
| note | 出口复核 G2「缺更新版 REGRESSION 落盘」闭合：功能面 PASS 证据自 #190 KPI / CI / 三方验收回写本报告；fixture 修复属测试基建对齐（阶段 T 后 schema 漂移），基建与用例逻辑未改编 |

## 命令

```
pytest tests/test_multi_replica_dualproc.py -q --tb=short
```

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 初版：post-#190 更新 · result=PASS（9 passed @ `1cae38f`）· 00 代录（维护者令原话：「签收，生成00 Prompt，在新窗口开始D1统筹」2026-09-24） |
