# invoke：50-close（local-rag-knowledge-rebuild 关账 · 2026-10-18）

> 帽：50-CLOSE · 执行人：00（维护者 m01159 授权链自动推进）

## 一、前置核验

| 项 | 证据 |
|---|---|
| PR #276 MERGED | squash `8ac8ec0` · CI 4/4 绿 · 13 文件全 docs/reports 零码改 |
| 40 交付 | TC-RK-1~7 全 PASS · 8648 三对照 · 水位 match · invoke_20261018_40_rebuild.md + 证据 8 类 |
| R1 审查 | task_local_rag_knowledge_rebuild_audit_R1_20261018.md 签收零阻塞 nit×4 · 锚点 13/13 |
| 三闸 | approved（m01159 授权链代录）· verify EXIT=0 PASS |

## 二、关账动作清单

- [x] git mv → done/ · 状态行/修订记录 CLOSED · README 登记
- [x] CLOSE 档 close_local_rag_knowledge_rebuild_20261018.md
- [x] 本 invoke 落盘

## 三、质量钉

- task lint → LINT: PASS · verify → EXIT=0 PASS（存量豁免留痕无新增）
- 机检经验沉淀：审查文结论节须含通过词+审查行为陈述+被审对象/闸指涉三要素（3.0-W4 NEW-5）

## 四、移交

- ApiEmbedder 内部批切另立 task 候选
- HG-EVAL-LIVE-RUN 前置已备 · HG-PROD-READONLY-ACCESS 仍 pending 移交维护者
