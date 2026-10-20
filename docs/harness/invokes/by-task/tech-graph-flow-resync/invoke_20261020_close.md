# invoke · tech-graph-flow-resync · CLOSE（2026-10-20 · 五棒收官）

## 五棒闭环（本 task）
1. SPEC v0 signed（HG-SPEC-SIGNOFF=approved · 维护者裁定 D2-a 续冻 · m00100）
2. 10-task v0.1（237b763 · lint PASS）
3. 20-task-audit R1=conditional_pass 阻塞 0（fad448d · 锚点 30 全命中 · N1–N4）
4. HG-AUDIT-R1=approved（00 代签 c9df67f · m00147 授权链 · 代签即确认 N4 收窄）
5. 30 实施（47e51f6 · TC1–TC8 全 PASS · 零 app/tests）→ 40=approve 阻塞 0（4d914cb · 13 锚零漂移 · 幂等逐字节复验）

## 交付实质
- flow 拓扑重同步：yaml 源摘除 s_intent（dormant 说明指向 intent.py:52）· 新边 START→strategy_builder（真值 graph.py:96-104）· 生成物三件同源重生成
- l2 D2-a 冻结声明四要素落盘（version 2026-08-31 不 bump）· s_intent dormant 两处
- 零 app/ 零 tests · graph-compile EXIT=0 三重校验 · lint-wiki-delta PASS

## 移交挂账（另案收口）
1. app/ops/lg_rag/sse_stream.py:63-66 _ROLE_ALIAS 死键（fix/ 小 diff 另案）
2. app/ops/lg_rag/multi/__init__.py:5 docstring 旧拓扑（注释-only 另案）
3. l2 D2-b 扩面（待 SpecWave #40 或维护者裁定）

## 全波次收口（#1–#5 五棒流完结）
#1 query-coref-rewrite #284 ✅ · #2 memory-injection-consumer #285 ✅（④b 休眠 · DEF-005）· #3 scenario-stage-rewire #286+#287 ✅ · #4 delegation-naming-boundary #288+#289 ✅（FP-2 护栏默认开）· #5 本棒 #290。
