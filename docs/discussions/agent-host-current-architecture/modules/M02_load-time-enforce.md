# M02 · 加载期强制

> **大纲编号**：#2 · **层**：控制面  
> **当前状态**：**部分落地 / 雏形**  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

加载期 ManifestError 整文件失败；V1-B 四字段硬规则 + 缺失 HITL 三档（默认 off）；Policy 默认 blocked。缺独立 CI 静态「工程红线→拒加载」产品面（import-linter 是模块边闸，非 manifest 红线扫描）。

## 2. 模块内架构

```mermaid
flowchart TD
  RAW[YAML/JSON] --> VAL[schema/词表/矛盾校验]
  VAL -->|非法| ERR[ManifestError 整文件失败]
  VAL -->|合法| SPEC[CapabilitySpec]
  SPEC --> HITL{REVERSIBILITY_MODE}
  HITL -->|enforce 未声明| DER[hitl_required=True]
```

## 3. 代码 / 文档落点

**包路径**：`app/ops/capability/manifest.py · types.CapabilitySpec`

- manifest.py：加载隔离、禁热加载、三硬规则
- types.py：四字段 reversible/execution_type/…
- OPS_CAPABILITY_REVERSIBILITY_MODE

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#2**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

CI 静态红线面；加载期与策略包全量收敛

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
