# SPEC（占位）：continuity 重复实现合并（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

存在两份逻辑相同的窗口压缩实现：`app/ops/lg_rag/continuity.py`（生产路径）与 `app/ops/session/continuity.py`（**只被测试引用**）——漂移风险，手册 §1.2.2 标注的已知债。小任务，建议与 memory-embedding-backfill 或任一小波次合并交付。

## 范围草案

- 单一真源：生产路径保留 `lg_rag/continuity.py`；`session/continuity.py` 改为 re-export 或删除并迁移其测试
- 行为零变化（两实现当前逻辑相同 · 合并以测试全绿为证）

## 非范围

- 改压缩语义；改占位符格式；真摘要（另 SPEC session-summary-fallback）

## 关键锚点

- 两文件本体 + `tests/test_session_continuity.py` · `tests/test_lg_rag_session_continuity.py`（17 处命中 · 20 审已扫）

## 验收草案方向

- 单真源；两测试文件全绿零改动或仅 import 调整

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
