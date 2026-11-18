# invoke · 50 收尾（CLOSE 波）· p4-t3-manifest-domain-tags

> **task_slug**：p4-t3-manifest-domain-tags
> **日期**：2026-11-18

## 内容

CLOSE 登记：registry entry status active→closed + 钉 wave_tip=a87503d4（feat PR #448 squash 合入）；task 档 docs/tasks/active/ → docs/tasks/done/ 迁移 + 自检结论终版回填 + 修订记录 CLOSE 行。

## 验证台账

| 检查 | 结果 |
|------|------|
| feat PR #448 | MERGED（squash a87503d4 · 2026-11-18） |
| CI 四绿（feat PR · rebase 后终裁） | check 18s ✓ · import-linter 10s ✓ · lint-wiki-delta 14s ✓ · pytest 2m20s ✓ |
| 提交后 wave_gate 闭窗复跑 | 22 passed（test_wave_gate_registry + tc8 diff 闸 · 在途面提交后转绿实证） |
| committed 闭窗面 | base 297363bd..wave_tip a87503d4（经 T4 e29f6a34 居中 · closed 档不再机审 · 实际波面=rebase 后五提交：manifest.py +69 · 新测试 297 行 · 01_modules.md 两件 · 落卡/invoke/收口文档 ⊆ allowed 三集合） |
| 并行冲突处置 | T4（p4-t4-rag-domain-config）先合 #447 → feat PR CONFLICTING/CI 不触发 → rebase origin/master（e29f6a34）01_modules.md 双保留解冲突（capability/lg_rag 行各留双方叙事 · 签收表两行并存 · registry 自动合入）→ CI 四绿（委派书并行铁律 · 偏差登记 2） |
| pytest 全量（solo 对照） | 36 failed vs master 基线 32 failed：差 5=dualproc 实证孤儿 pytest(pid 3801) 交叉污染（杀后双侧 9 passed）· 31 共有=本地环境性既有 · CI pgvector:pg16 service 终裁 |
| 目标与电池 | 目标三文件 45 passed（真 PG 五键 blank）· capability 电池 673 passed/5 failed 与干净 master 同 5（顺序依赖既有 · 单跑均过） |
| task lint（迁 done 后） | npx --yes spec-wave@3.5.0 task lint --file docs/tasks/done/task_p4_t3_manifest_domain_tags.md → PASS（本波本地复跑 · CI 终裁） |
| CLOSE PR CI | 见本 PR checks（终裁） |

## 偏差

- base 修正（委派书钉 370a137a → 实际尖 297363bd · 委派书「git fetch 核实实际尖 · rebase 纪律」内裁定 · 已登记 task 档偏差 1）。
- T4 先合 rebase（feat PR 开出后 #447 先合 → CONFLICTING · rebase 双保留解冲突 · 已登记 task 档偏差 2 · 失败路径预案原文命中）。
- mypy manifest.py 2 errors 与 master 基线逐类别一致（既有形态不修 · 零新增实证）。
- 仓 ruff format 81 件未 format 为既有面（master 同 81 · 本波两件 format-clean · 不趁机格式化全仓）。

## 结果

波次闭合：manifest 顶层 domain 键消费已落 master——_parse_domain（词表 [a-z0-9_]+ 独立 R5 · 保留字 (DOMAIN_ALLOW_TAGS−{oa})∪{mcp}∪env 拒载 · oa 不溯及 R6）+ _inject_domain_tag（手写 ∪ {domain} 并集去重 · 手写在前兜底追加 · 键缺失零注入存量零 diff）· MCP 翻译条目 domain 真源 server 配置侧（§2.3 不经本 loader）；oa 资产包实配置归 T5。
