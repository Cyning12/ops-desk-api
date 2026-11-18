# invoke · 50 收尾（CLOSE 波）· p4-t4-rag-domain-config

> **task_slug**：p4-t4-rag-domain-config
> **日期**：2026-11-18

## 内容

CLOSE 登记：registry entry status active→closed + 钉 wave_tip=e29f6a34（feat PR #447 squash 合入）；task 档 docs/tasks/active/ → docs/tasks/done/ 迁移。

## 验证台账

| 检查 | 结果 |
|------|------|
| feat PR #447 | MERGED（squash e29f6a34 · 2026-11-18） |
| CI 四绿（feat PR · rebase 后终裁） | check 13s ✓ · import-linter 10s ✓ · lint-wiki-delta 10s ✓ · pytest 2m49s ✓ |
| 提交后 wave_gate 闭窗复跑 | 3 passed（test_wave_gate_registry + tc8 diff 闸复绿确认 · 脏树期红为结构性） |
| committed 闭窗面 | base 370a137a..wave_tip e29f6a34 = feat squash 单提交（11 文件 ⊆ allowed 三集合） |
| 并行冲突处置 | T6（p4-t6-run-tree-ddl）先合 → CONFLICTING → rebase origin/master（297363bd）保留双方 registry entry + 01_modules 双方备注/签收行 → CI 四绿（委派书并行铁律） |
| pytest 全量（脏树期） | 2480 passed / 27 failed 逐签解剖：20 签与 base 全量基线逐签一致（环境性红 · CI 终裁）· multi_replica ×5 flake（复跑全过）· tc8/wave_gate 2 签 dirty-tree 结构性红（提交后转绿实证） |
| ingest.py 零 diff 机判 | 0 行（§4.3 source_type 词表不泛化钉死） |
| task lint（迁 done 后） | npx --yes spec-wave@3.5.0 task lint --file docs/tasks/done/task_p4_t4_rag_domain_config.md → 见本 PR CI |
| CLOSE PR CI | 见本 PR checks（终裁） |

## 偏差

- rag→prompts 与 lg_rag→rag 两处 importlib 运行期解析守静态边界（`.importlinter` 零改动 · 承 lg_rag/continuity.py 既定先例 · 图谱备注级登记 · 已登记 task 档）。
- 非子任务 RAG 路径（chat/rag 直接检索）域闸不设（契约 fail-closed 面=rag 子任务闸 · 已登记 task 档限制）。
- 刻意不交付 oa glossary（不交付死配置 · 契约原话 · 运行时回退 glossary.yaml 实证）。
- mypy 四件 26 errors 与 master 基线逐类别一致（既有形态不修 · 零新增实证）。

## 结果

波次闭合：qdrant_collection(domain) 三级回退 fail-closed（ops 零 diff · 非 ops 缺省不回落）· glossary 按域文件回退+按域缓存 · rag 子任务域闸「本域未配置检索」（后端调用零发生断言实证）· 影子写 None-skip 不进 DLQ 已落 master；oa 语料与 collection 实配置归 T5。
