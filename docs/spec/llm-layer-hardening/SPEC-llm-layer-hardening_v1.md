# SPEC（占位）：L5 模型层硬化（重试/熔断/路由/成本归集）（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

L5 现状：provider 抽象 + 显式超时 + fallback 链 + 结构化输出（parse/repair/validate）✅；**缺通用重试退避（有链无退避）、熔断、分层路由、成本按 run 聚合**（手册 L5 ⚠️）。属承重墙缺角——模型层静默失败会带错数据往下走。

## 范围草案

- 通用重试：指数退避+抖动（仅对可重试错误类 · 对齐 capability 熔断 errors.py 的分类思想，不靠错误文案）
- 熔断：provider 级（pybreaker 已在仓 · capability/circuit.py 先例可复用模式）
- 分层路由：按任务类型/成本档选模型（grader 与生成可分档）
- 成本归集：usage 按 run_id 聚合落表（成本表当前为占位价 · 手册 L8 ⚠️ 联动）

## 非范围

- 新 provider 接入；改结构化输出语义；流式协议改动

## 关键锚点

- `app/llm/`（provider 工厂 · fallback 链 · 超时）· `app/ops/capability/circuit.py` + `errors.py`（熔断/错误分类先例）· `app/ops/tracing.py`
- 手册 L5 行 + 附录 A L5 行

## 验收草案方向

- 可重试错误退避重试 · 不可重试零重试；熔断开/半开/关三态；usage 按 run 可查；故障不返回半成功数据

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
