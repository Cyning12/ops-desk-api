# SPEC（占位）：记忆合规物理删除权（v1）

> **状态**：`placeholder`（占位 · HG-SPEC-SIGNOFF=**pending** · 10-spec 补全前不出 task / 不改码）
> **track**：待 10-spec 裁定
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`

## 背景与目标

P0 状态机（active/superseded/revoked/expired）全部为**逻辑失效**，物理删除未做（P0 §3 非范围预留）。企业合规场景（用户行使删除权）需要按 user 物理删除的能力。属「成熟度标志」层——**有合规要求/真实流量前不做**（手册 §3.4 第三类）。

## 范围草案

- 按 `(tenant_id, user_id)` 物理删除（含 embedding 列与审计留痕：删除动作本身记审计，不记内容）
- 管理面入口（admin 侧 · 鉴权对齐 `AdminSyncAuth`）；删除范围确认与干跑模式
- 删除后断言：召回/向量两通路零残留

## 非范围

- 删除其它业务表数据；DSR 全流程自动化；改逻辑状态机

## 关键锚点

- `app/ops/memory/service.py`（revoke 语义延伸）· `app/ops/admin/`（AdminSyncAuth 先例）· 手册 L7（删除权）

## 验收草案方向

- 物理删除后两通路零命中 + 表行零残留；审计记录存在；越 tenant 调用拒绝

---

## 接续指引（占位 → 正式 SPEC）

1. **新会话启动**：读 `docs/spec/README.md` 占位表 → 选定本 slug → 声明「接续 <slug>」
2. **10-spec 补全**：把本占位升级为完整 SPEC——补 R0–R5 思考轮、方案对比（≥2）、failure_paths、验收断言化；范围/非范围草案可按实扫结果修订
3. **人签**：维护者签 `HG-SPEC-SIGNOFF=approved`
4. **后续**：00 出 task → 20-task-audit → 闸 → 30 → 40 → PR（与 memory-facts-p0/p1 同模式）
5. **排序依据**：见 `docs/spec/README.md` 占位表「建议序」列（原则：缺了会不会造成不可逆/静默的错）
