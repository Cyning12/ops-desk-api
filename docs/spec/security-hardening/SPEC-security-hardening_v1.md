# SPEC（占位）：L7 安全与合规硬化（注入/PII/脱敏/真沙箱）（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

L7 现状：凭据走 env · 密钥形键拒入清单 · args 摘要脱敏 · sandbox/cli/MCP 默认关 ✅；**缺注入防护（输入结构隔离+检测）、PII 识别、出口脱敏、真沙箱（adapter 是 Mock）**（手册 L7 ❌）。纪律（手册 §2.2 第四问）：**顺序不能倒**——①执行层堵死（已有）②输入结构隔离 ③最后才检测。

## 范围草案（按钉死顺序）

1. **输入结构隔离**：用户内容只能进被声明的槽位，不参与指令拼装（记忆注入块已是先例 · 推广到 RAG 片段/工具回执）
2. **检测层**：规则 + 抽样 judge（离线 · 热路径禁 LLM-as-judge 纪律沿用）
3. **PII 识别与出口脱敏**：SSE/日志/卡片出口侧
4. **真沙箱**：sandbox adapter Mock → 真实隔离（独立 worker/容器）

## 非范围

- 提示词层"护栏"（手册口径：行为建议不是安全控制 · 不作为本 SPEC 交付）
- 改 Policy 门语义（已 fail-closed）

## 关键锚点

- `app/ops/capability/policy.py` / `visibility.py`（执行层现状）· `app/ops/memory/`（结构隔离先例）· `app/ops/rag/`（检索片段注入面）
- 手册 §2.2 第四问 · L7 行 · 附录 A L7 行

## 验收草案方向

- 越权 prompt 构造用例：下游零请求（不是"被拒绝"是"没发出去"）；注入样本检出率；出口脱敏对照；沙箱隔离边界断言

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
