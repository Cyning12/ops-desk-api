# SPEC（占位）：画像记忆（kind=preference）（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

记忆四层中画像层仍空（手册 §1.2.4）。本 SPEC 引入 `kind=preference`。纪律（手册 §1.2.4）：**先做事实型画像**（如"该用户主要负责的项目/仓库"——可对着数据源核对），**后做偏好型画像**（只能推断、错了难发现）。

## 范围草案

- 闸放开 `kind=preference`（P0 闸已预留 kind 位 · 当前仅 fact）+ 判据差异化（偏好需更高准入：显式表达 > 行为推断）
- 来源分级与权重（显式声明 1.0 > 推断低权）；召回注入分块或标注区分事实/偏好
- 冲突与纠正：偏好变更走 supersede；推断型偏好必须可一键清除
- 评测：幻觉偏好红线（无偏好记忆时不得编造 · 手册 §1.8 红线③扩展）

## 非范围

- 跨用户画像聚合；推荐系统；改事实型记忆语义

## 关键锚点

- `app/ops/memory/gate.py`（kind 判据）· `app/ops/memory/extract.py`（抽取 prompt 是否产偏好候选 · 建议首期只显式声明）
- 手册 §1.2.4 / §1.3（四问）/ §1.8（红线③）

## 验收草案方向

- 偏好闸判据单测；显式 vs 推断来源权重断言；幻觉偏好红线；清除后零召回

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
