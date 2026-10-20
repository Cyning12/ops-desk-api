# invoke · HG-AUDIT-R1 落签（delegation-naming-boundary · 2026-10-20 · 00 代签）

## 授权链
- 维护者 m00147「授权00签收后续文档」（本波 5 份 SPEC 后续文档闸含 HG-AUDIT-R1）
- R1=conditional_pass（阻塞 0 · 门控修正核验成立 · M1–M3 签前修订）→ 10-task v0.2（a892547）→ R2=pass（b70c28c · 全闭合 · 零夹带）

## 落签动作
- task 人工闸表 HG-AUDIT-R1 pending → **approved**（2026-10-20）

## 移交 30 要点
- 门控真锚点：nodes.py:903 + :931 两处解耦；:970 签发审批门与 :1271 scope 门保持 delegation 耦合不动
- 30 按实校正：def 行实测 :339/:353/:359（N-b）
- 30 执行层口径：TC1 grep 加 -I 或 --exclude-dir=__pycache__ 防 .pyc 误报（R2 §4）
- 改名面 8 处含 tests/test_capability_testing_write.py:185/:412/:468 注释级改名（M1）

## 30 开工前提（已全满足）
- HG-SPEC-SIGNOFF=approved · HG-AUDIT-R1=approved · HG-GRAPH-MODULES=approved（graph_change_layer=none）
- 实施分支 task/delegation-naming-boundary 自文档线 HEAD 切出（同 #2/#3 格局 · PR 含文档+代码全链）
