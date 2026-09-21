# SPEC（占位）：Prompt 资产化三阶段（改得动→看得见→分得开）（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

Prompt registry 仅覆盖 3 个模板，其余散在各模块；`str.format` 与 JSON 花括号打架 ⇒ **改 prompt 必须找开发**（手册 §2.1.1 真痛点）。本 SPEC 按手册 §2.4 三阶段推进，**顺序不可跳**：先改得动，再看得见，最后分得开。

## 范围草案（按阶段 · 可拆 task）

| 阶段 | 内容 | 到位判据 |
|---|---|---|
| 一 · 改得动 | 去 `str.format` 转义（换 `string.Template` 或独立块拼接）；prompt 从代码搬数据；变更审计 | 非开发同学能改一句文案并上线 |
| 二 · 看得见 | 每次调用记 template_id+version+渲染 hash；效果指标按 version 聚合 | 改动可归因「哪版 · 变好还是变差」 |
| 三 · 分得开 | 按 user/thread 打标分流；灰度；一键回退到具体人群 | 新用户试新版、老用户不动 |

## 非范围

- A/B 统计平台；改 prompt 内容本身（文案优化另案）；注入防护（security-hardening 的事）

## 关键锚点

- `app/ops/prompts/templates.py`（3 模板 · JSON 双写实例）· `app/ops/prompts/render.py` · `app/ops/prompts/packs.py` · `app/ops/rag/grader.py:144`（env 切版本先例）
- 手册 §2.1–§2.4

## 验收草案方向

- 阶段一：改文案零转义 · 非开发可上线；阶段二：日志可见命中版本；阶段三：按人群分流+回退

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
