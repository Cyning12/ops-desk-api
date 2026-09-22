# invoke · CLOSE · memory-fuse-tz-fix

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 00（delegate-only · 全程未改实现码 · worktree 作业 · 30/40 子 Agent） |

## 闭环摘要

bugfix 双轨（跳 SPEC · live 裁决记录为据）→ task F1–F3 · 20 R1 终轮零阻塞 → 三闸 00 代录 · VERIFY PASS → 30（_as_utc 双侧归一 · 18 四象限测试 · 扫描清单 7 类点位 · 最小改动零越面）→ 40 PASS（8/8 · 真 PG aware 实证复跑）→ 归档 CLOSE。

## 交接

1. 合并本 PR（CI 须绿）
2. **重跑 live 评测**（memory-golden-eval runner · 复述用例此前因本 bug 全 error）→ 拿到 paraphrase 真实数据 → 正式裁决 `MEMORY_FACTS_VECTOR_RECALL_ENABLED`
3. 抽取 prompt/key 校准另 task（live 已证 precision 0.23 / 噪声 0.36 · 距门槛远）
4. 非范围遗留（另议）：测试库 schema 漂移重建 · 显式 aware now 绑参限制 · 仓级 now_utc 审计
