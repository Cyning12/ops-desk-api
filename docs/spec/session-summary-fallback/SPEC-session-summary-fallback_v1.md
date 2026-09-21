# SPEC（占位）：会话记忆真摘要（可回退原文）（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

当前窗口压缩 = **截断+占位标记**（占位符只有轮数+角色，无内容）——保住窗口有界，没保住语义连续（手册 §1.2.2「明确知道缺的一环」）。本 SPEC 引入真摘要，**铁律：摘要必须可回退到原文**（摘错=静默造错误前提；回退路径是摘要上线的前提，不是可选项）。

## 范围草案

- 更早轮次经模型生成摘要替换占位符（额外一次调用 · 离线或请求时懒生成+缓存）
- 原文保留可查（DB 已有 `ops_runs`/threads 表原文）；摘要有版本与来源标记；可配置回退到占位模式
- 评测：摘要保真度用例（关键事实不丢 · 不新增原文没有的内容）

## 非范围

- 改窗口压缩的轮数策略；改 SSE；对话记忆进长期记忆（那是 memory 轨的事）

## 关键锚点

- `app/ops/lg_rag/continuity.py`（compress_window · 占位符构造）· `app/ops/session/history.py`
- 手册 §1.2.2（口径与纪律）· §1.9（反模式：摘要不可回退）

## 验收草案方向

- 摘要模式 vs 占位模式回归对照；保真度金样；回退路径一键切换断言

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
