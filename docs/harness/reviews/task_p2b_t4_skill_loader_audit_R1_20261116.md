# R1 审查 · task_p2b_t4_skill_loader

- 时刻：2026-11-16 · 审查人：执行代理（夜间授权窗口 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03216 + 11 设计终稿）
- 对象：task 档 + registry entry + 勘察定论（R0）

## 审查项

1. 范围与 11 §8 T4 行 + §6 全量逐项对齐：skill_registry 重写（§6.1）· slots 增槽（§6.2）· catalog 注入（§6.3）· skill_ref 闸条件化装配（§6.4 · R9b）· env 三件套（§6.5）· 删三 stub（§6.6）· compose 卷 · workspace 首枚样例 + README · §9.2 六项注入证据 · 图谱写实——无溢出（capability/manifest.py · mcp_client.py · config.py MCP 键属并行 T1 地盘 · 真 LLM 对照会话属 T5a · .importlinter 零改动，均明确非范围）。
2. R1-R10 硬约束逐条落位：R9a（全文 ≤20000 字符拒载）入 loader 闸 + 验收 (f)；R9b（off 态 subtask JSON schema 逐字节不变）落法=SubtaskItemSkillRef 子类按闸二选一 model_validate + off/on 对拍测试；§6.1「伪造标记拒载优于转义」裁定（trusted 静默转义改指令语义不可见）照录；§6.3 否 \$skills_block 不动模板资产照录；§6.6「capability 面不留 kind=skill」删除理由照录。
3. 红线：off 态双逐字节断言（supervisor system + subtask schema）+ loader 零调用 mock 计数——验收 (a) 可机断；合并预算 capability ≤6000 + skill ≤4000 ≤10000 CI 断言锚；失败路径七条（§10 + env 非法回退 + 回退路径）与验收逐项对应。
4. 勘察定论复核：nodes.py 双注入点锚定（catalog_block :1560 后追加两路共用 · _worker_state :1453-1483 装配面）与代码实证一致；三 stub 引用面全图五处（capability/__init__ · adapters/__init__ · probes · test_capability_gateway · test_skill_registry）无遗漏；probes.py 删 mcp 探针项波及 test_capability_gateway.py 四区的最小改写裁定（mcp 探针两例改 cli 等价 · boom 例 MockCliAdapter 子类 · p3 三例整删）合理——保断言语义、删退役面。
5. registry allowed 面完整（app 12 文件含三删除目标 + tree 10 文件 + invokes 前缀 · banned=alembic//scripts//app/ops/capability/manifests/ · yaml safe_load 验证过 19 entries）。
6. 并行 T1 撞车预案在案：capability/__init__.py 不同行（T1 :28/:35/:108 · 本单 :30/:32/:92）· registry.yaml/01_modules.md 追加型冲突保留双方 entry 手动解（授权口径）。
7. 思考轮：R0-R5 槽位齐 · R5 early_stop 理由成立（设计终稿即审计真源 · R1-R10 已评审关闭 · 验收全机断）。

## 结论

GO，可进 30 实施（夜间授权窗口 · 30 台账见 invoke_20261116_30_impl.md · 40 验收台账见 invoke_20261116_40_acceptance.md）。
