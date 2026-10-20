# invoke · 30 Phase B ④b 全模式收窄 + 功能休眠（task_memory_injection_consumer）

- 日期：2026-10-20 · 帽：30（实现者）
- 分支：task/memory-injection-consumer（Phase A a9fde63 之上续作）
- 闸态：HG-AUDIT-R1=approved（2026-10-19 代签链）· HG-PHASE-B-DECISION=approved（2026-10-20 维护者裁定「当前任务走4b」· 落签 invoke_20261020_phase_b_decision_4b.md · task 闸表 :40）
- GATE_VERIFY 误报延续记录：spec-wave verify 对 HG-PHASE-B-DECISION 粗粒度判 blocks 30（VERIFY: BLOCKED EXIT=2）——task 闸表真值 blocks_hats=「30（Phase B）」，裁定 approved 后 Phase B 开工合法；沿 #1 先例以 task 闸表真值为准。

## 切割面（唯一生产码改动）

- app/ops/lg_rag/continuity.py `_assemble_graph_messages_with_memory_impl`：:456-527 注入双分支（facts 段：开关/身份 skip/向量分流/recall_active/降级 span/双计数/注入；episodes 段：开关/tenant skip/fingerprint/recall/降级/零命中 span/注入）整体替换为 `return messages` + ④b 休眠注释块（钉裁定日期、闸、Phase A 实证结论、复活对接 docs/tasks/deferred/task_memory_facts_build_4a.md）。
- 休眠声明四落点：continuity.py 切割处注释 + 模块 docstring（:4-13 改写）+ impl/wrapper docstring + :125 节首；docs/_tech_graph/l1/01_modules.md memory 行末追加 ④b 钉文「当前无任何消费点，功能休眠」（graph-compile 绿）；app/ops/memory/README.md :14 表格行 + app/ops/memory/__init__.py docstring。
- 保留面零改动：resolved_query/session_summary 双分支（:440-455）、wrapper 隔离归因/校验（:528+）、写入侧（memory service/gate/episode/recall API）、render/inject helper、开关函数（单测保持绿）。

## 红测先行 → 绿

1. 八文件测试改写先行（生产码未动时首跑 21 failed/74 passed，签名全为休眠语义：stub 触达 AssertionError / span 计数非空 / 注入块出现）。
2. 切割后全绿：八文件 95 passed / 35 skipped（DB 面 skipif）。
3. 改写期间两处测试自修正（非生产码）：_norm spy 名去 .on/.off 尾标（开/关双拍可比）；supervisor run_id 改常量（子任务 id 嵌入 run_id，thread_id 仍带 tag 隔离）。
4. TC5 白名单补登 _UPSTREAM_SIGN_PATHS（docs/tasks 三文件 = 00/维护者落签面 · 分支提交 29cd456/ed2c150 带 [00] 标记 · 30 禁改仅登记）。

## 旧测改写清单（休眠断言三件套：stub 零调用 + 逐字节基线 + 零块/零 span/零告警）

- tests/test_memory_injection_consumer.py：全量改写为 ④b 验收版（4 矩阵场景 dormant+parity · TC2 默认关 · 自牙测 2 枚 · TC5 diff 白名单）。
- tests/test_memory_injection.py：8 测试 → *_dormant（skip 告警/recall 故障降级/span 单双计数全翻）。
- tests/test_memory_episode_recall.py：6 测试 → *_dormant（FP-5 核心 test_episode_recall_never_called_dormant；docstring 留存 fingerprint 谓词真值供 ④a 恢复）。
- tests/test_memory_extract_p1.py::test_assemble_never_recalls_det_or_vector_dormant（det/vec 双 stub）。
- tests/test_memory_service_db.py：两变异检验三态下沉服务层（recall_active 污染可见→装配面恒零块→revoke 痊愈）。
- tests/test_memory_vector_p1.py::test_mutation_wrong_fact_vector_recalled_then_revoke 装配段翻休眠（服务层 recall_with_vector 三态保留）。
- tests/test_input_isolation_wiring.py::test_continuity_on_memory_dormant_no_memory_slot（零 memory_fact 槽 · out[-1]=user_query 归因不变）。
- **枚举外命中两件（task 枚举清单外 · 切割连带）**：
  - tests/test_lg_rag_query_rewrite.py::test_tc8 → test_tc8_rewrite_applied_recall_never_called_dormant（原「rewrite→recall 调用序」断言随切割失效；翻为重写照常 + 向量召回零触达；docstring 留 ④a 恢复指引）；
  - .importlinter：continuity -> memory.{service,episode_gate,episode_service} 三条 ignore 条目随切割移除（lint-imports 「No matches for ignored import」会挂 D2 契约测试；router/sse_stream -> memory.extract 两条保留——写入侧不动）；已补入 TC5 白名单并注释。
- tests/eval/test_memory_preference_redline.py P1（**裁定点 · 00 方案甲授权** messageId de643b43→m00372）：反向对照翻 ④b 休眠断言（stub 零调用 + 逐字节基线），改名 *_dormant，docstring 注 ④a 复活恢复指引；P0/P2/P3 不动（P2/P3 render helper 面保持绿——helper 保留）。

## TC 覆盖（task :120-150）

- TC2 默认关零 diff：test_default_off_zero_diff 绿。
- TC5 diff 白名单：test_phase_b_diff_whitelist 绿（白名单 tests/ + invoke docs/ + 01_modules.md + continuity.py + memory README/__init__；黑名单 scripts/ alembic/ 其余 app/ 含 untracked）。
- TC8/FP-5 收窄后 recall 零调用：4 矩阵场景 _assert_dormant（facts 确定性/向量 + episodes 三通路 await_count==0 ∧ 零 marker ∧ spy 面零命中）。
- 注入开/关行为零 diff 对拍 Phase A 基线：_assert_on_off_parity（spy 请求清单归一化 + state.messages 逐字节相等）× 4 场景。
- TC11 反回归全量：park .env 全量 pytest（结果见下节）。
- TC12 九旧测文件：默认关面保持绿（逐字节对拍断言）；注入开面按 task :147 授权改写为休眠断言；三桩文件核对零冲突。

## 禁区自查

- app/ diff 仅 continuity.py + memory README/__init__（白名单内）；scripts/ alembic/ 零触达；零新 event_type/路由/表；SSE 帧/请求体零变化；memory 写入侧零改动；task/SPEC/闸表零改动（docs/tasks 三文件为 00 落签，git log 作者面核验）。
- 已知残留（如实登记）：app/ops/lg_rag/graph.py:161/:195、router.py:176-177、sse_stream.py:401 注释仍提「记忆注入（memory-facts-p0）」user_id 语义——形参仍传、注释陈旧但非本棒委派面（白名单外文件禁动），④a 复活或后续任务顺手校正；app/ops/session/README.md:16「记忆注入之前」措辞同源残留。

## 结果

- park .env 全量：1732 passed / 0 failed / 182 skipped（25s）。
- .env 在场全量：37 failed / 1695 passed——**对拍铁证**：同 .env 在基线提交 a9fde63（git worktree 对拍）失败集逐项全同（diff IDENTICAL · /tmp 对拍清单），37 项全为 .env 环境泄漏噪声（strategy env 追加集/live PG/embedder 类），与本 diff 无关；失败文件零交集于本棒触碰面。
- ruff check app tests 全绿（.venv ruff 0.15.21）；./scripts/graph-compile.sh 全绿（9 md OK）；lint-imports 12 kept 0 broken。
- 提交见本节末尾补记。
