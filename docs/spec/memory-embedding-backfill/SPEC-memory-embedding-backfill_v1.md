# SPEC（占位）：记忆既有行 embedding 回填批处理（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

P1 向量召回已上线（`embedding` 列 nullable · 既有行不回填 · null 走确定性通路）。本 SPEC 补**存量行回填**：让 P0 时期写入的事实也能被向量通路召回，提升召回覆盖。

## 范围草案

- 批处理脚本/管理命令：扫 `embedding IS NULL AND status='active'` → 调 Embedder（线程卸载/限流）→ 回写
- 幂等可断点续跑；限速与失败重试；跑批报告（成功/失败/跳过计数）
- 并入小项：**span `memory_facts_injected` 专门单测**（P0 已知未测项 ①）

## 非范围

- 改召回融合算法；改闸；对外端点；画像

## 关键锚点

- `app/ops/memory/service.py`（write_fact 嵌入路径 · 可复用其线程卸载与失败语义）
- `app/ops/rag/embedder.py`（Embedder 协议）
- 回填先例：`app/ops/rag/shadow_write.py`（影子写/迁移对账思路）· `reports/qdrant_migrate/`（对账报告形态）

## 验收草案方向

- 干跑/实跑计数对账；中断后重跑不重复嵌入；回填后复述召回用例命中提升（金样对照）

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
