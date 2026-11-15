# invoke · 40_acceptance · p2a-t4-verification-smoke

## 内容

P2a-T4（冒烟验证与验收落盘）验收：结构断言绿 + 四样例冒烟 (a)-(f) 判定 + 三级裁定 + 全量对拍 + CI 四绿 + 验收记录落 workspace + 偏差如实登记。

## 验证台账

| 项 | 命令 | 结果 |
|---|---|---|
| 结构断言新文件 | pytest tests/test_capability_supervisor_smoke_assertions.py -q（五键 blank） | 16 passed 0 failed |
| capability 电池（十一件） | pytest 新文件+manifest+panel_tools+panel_aggregate+testing_write+reconcile+stage_w+env_extra+domain_allowlist+overview+graph -q（五键 blank） | 166 passed 0 failed |
| 全量套件（分支） | pytest tests -q（五键 blank） | 2165 passed · 17 failed · 2 skipped |
| 全量对拍 | base 96ccf902 同键同跑 | **失败集恒等**：17 = base 16 枚（.env 污染既有红 · blank LG_RAG 三键抽查 3 枚复绿证实因果）+ wave_gate_registry 脏树期 1 红（p1-t5a-goal-docs closed entry banned tests/ 在途守卫 · 承 T2 先例 · 提交后 2 passed 复绿实证） |
| 四样例冒烟 | POST /api/ops/lg-rag/stream mode=supervisor（dev 库 seed · 真 .env siliconflow · 服务 blank 三键） | http200 ×4（66.6s/61.1s/44.6s/74.7s）· plan 选择 4/4 命中预期（get_overview/query_pull_requests/graph_snapshot/query_issues）· 数字与面板 REST 逐键一致 · (a)-(f) 全过 · 三级裁定 **成立（4/4）** |
| 冒烟证据链 | SSE 帧 s{1..4}.sse + DB ops_lg_rag_run_events 持久化 plan（四 run_id 核对 tool+args） | 双证一致 · (a) 走设计 §6 明示替代路径（Langfuse 云面不可证 · 偏差 2） |
| ruff | ruff check app tests | All checks passed |
| graph-compile | ./scripts/graph-compile.sh | ok（10 md · check-only） |
| spec-wave | task lint --file + verify --task | PASS（三闸 approved 可 30 · 仅 W3 占位 warn · close 前已回填） |
| CI（终裁 · 无 .env） | gh pr checks 406 --watch | **四绿**：pytest 2m20s · check 13s · import-linter 11s · lint-wiki-delta 12s（run 43749448474 等） |

## 结果

feat PR #406 squash merge → master 90729acb。验收六项全勾（task 档自检结论）。三级裁定 **成立（4/4 全过）** · 不触发 08 §3 FC 重估（plan-JSON 选择失败 0/4）· 失败处置（description 修订/mock 收窄/退回 T1/T2）均不启动。验收记录落 workspace docs/01-scope/03-general-agent/10-p2a-verification.md。

## 偏差记录

承 invoke_20261116_30_impl.md 八项（端点现实 lg-rag/stream · Langfuse 云面 (a) 终证不可达走替代路径 · 无 GUI 以 REST 对照替 · ci_status failure 词面 · S3 双参观察项 · 冒烟 blank 三键承 T1 先例 · seed 人工构造 · wave_gate 脏树期红承 T2 先例），无新增。
