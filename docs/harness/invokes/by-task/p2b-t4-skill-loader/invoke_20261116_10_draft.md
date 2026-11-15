# invoke · 10_draft · p2b-t4-skill-loader

## 内容

按 issue Cyning12/ops-desk-workspace#23（m03064 夜间授权 · m03216 追认并行波次）+ 设计真源 11-p2b-mcp-skill-design.md 终稿（§8 T4 行 + §6 全量 + §9.2 判据 · §0.1 R1-R10 硬约束），落 task 档 docs/tasks/active/task_p2b_t4_skill_loader.md + registry.yaml 第 19 entry（base=bf1c23f2）。

## 勘察定论（R0）

- **nodes.py 注入点双锚定**：catalog_block 在 supervisor_node :1560 由 _format_capability_catalog(caps) 产出、suffix/base 两路共用（_build_supervisor_system :131-135 / _build_supervisor_suffix_system :138-157）→ skill 节追加在其后一处函数内两路自动覆盖；skill 全文装配面 = _worker_state（:1453-1483 · 产 Send 载荷 assigned_subtask）。
- **R9b 落法**：schemas/subtasks.py 加 SubtaskItemSkillRef(SubtaskItem) 子类（+skill_ref: str|None=None），nodes.py _parse_subtasks（:194-239）按 skill_loader_enabled() 二选一 model_validate——off 态走原 SubtaskItem，JSON schema 逐字节不变。
- **三 stub 引用面全图**：capability/__init__.py（:30/:32/:92 import · :143/:150/:175 __all__ · docstring :7/:10-11）· adapters/__init__.py（:28/:37 · :52/:54 · docstring :3/:6）· probes.py（:23 import · :30 PROBE_MCP_ID · :34-46 首探针项）· tests/test_capability_gateway.py（:20-21/:33/:36 import · :363-417 mcp 探针两例 · :420-442 boom 例 · :448-488 p3 三例）· tests/test_skill_registry.py 整体重写。
- **并行 T1 撞车预案**：T1 删 mcp_client.py + capability/__init__.py :28/:35/:108（与本单 :30/:32/:92 不同行 · 最小交集）；registry.yaml/01_modules.md 同区追加型冲突 → 保留双方 entry 手动解（授权口径 m00002）。
- **compose 卷挂载点**：Dockerfile WORKDIR /app → 容器内默认根 ../ops-desk-workspace/skills 解析为 /ops-desk-workspace/skills（卷目标一致 · api 服务 :41-80 原无 volumes 段）。
- **图谱锚**：01_modules.md lg_rag 行「路径覆盖补记」内 skill_registry 备注原文 = `app/ops/skill_registry/**`（H5 stub · **dormant** · 无运行时消费方仅 `tests/test_skill_registry.py` 自引用 · 承同例归属本行备注）→ 写实移除为真加载器；签收行承 :136 先例 splice 末条后。
- **.importlinter**：lg-rag-outbound contract（:207）source_modules 已含 app.ops.skill_registry → 零新边，不碰 .importlinter（非范围钉死）。
- **slots 现状**：SLOT_REGISTRY 七槽 dict（slots.py:84-98）· wrap_slot :157-182 trusted 原样无标记 · _FORGE_ESCAPES :112-119 · tests/test_prompt_slots.py:37-58 七槽白名单断言需扩八槽（承 P1-T3 goal_objective 先例）。
- **env 体例真源**：goals/inject.py:27-46（_TRUTHY=("1","true","yes","on") · _FALSY 对称 · os.getenv 直读无缓存 · 非法 warning 回退 False）→ 本单三件套 OPS_SKILL_LOADER_ENABLED/OPS_SKILL_LOADER_ROOT/OPS_SKILL_CATALOG_MAX_CHARS 同体例。

## 闸

- HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 approved（task 档人工闸表 · 授权 issue #23 m03064 + 11 终稿 R1-R10 已评审关闭 · 不代签）。
