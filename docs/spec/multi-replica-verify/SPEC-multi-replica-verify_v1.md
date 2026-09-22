# SPEC（占位）：L0 多副本验证（单实例 → 多实例）（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

L0 现状：鉴权/租户/Principal 代码构造 ✅ · Java 侧网关+Eureka 存在 · **但单实例，多副本未验证**（手册 L0 ⚠️ · 边界纪律：别说成"已做服务发现与多副本"）。属「成熟度标志」前置验证——有真实流量前必须回答的问题。

## 范围草案

- 多副本部署验证（2 实例 + 网关）：会话亲和/无亲和两种策略的行为对照
- 状态外置正确性实证：A 实例起 run · B 实例恢复/查询（checkpointer + 事件表已是 PG · 验证跨实例语义）
- 跨实例一致性：capability 注册表/Policy/预算计数在多副本下的行为（进程内状态的边界盘点）
- HITL 跨实例：A 挂起 · B resume（hitl resume 走 checkpoint · 应天然成立 · 实证）

## 非范围

- 真上生产多副本（验证≠投产）；服务发现选型变更；容量规划/灾备（更后续）

## 关键锚点

- `app/ops/lg_rag/checkpointer.py` · `event_store.py` · `app/ops/hitl/resume.py` · `app/ops/capability/`（进程内注册表边界）
- 手册 L0 行 · 附录 A L0 行

## 验收草案方向

- 跨实例恢复 run 断言；跨实例查他人 run 404；进程内状态边界清单（哪些计数在多副本下失真）

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
